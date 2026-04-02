"""core/memory.py — 세션 간 메모리 (JSONL 기반)

세션 결과를 JSONL로 저장하고, 다음 세션에서 자동 로드하여 연속 작업을 지원한다.
context.md를 자동 생성하여 CLAUDE.md에 삽입할 수 있는 요약을 제공한다.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
from .group_logs import tail_room_messages
from .session import read_session_data
from .types import MemoryEntry, PipelineResult

# ── 경로 상수 ──────────────────────────────────────────
MEMORY_DIR = Path(".claude/memory")
MEMORY_FILE = MEMORY_DIR / "sessions.jsonl"
CONTEXT_FILE = MEMORY_DIR / "context.md"

# ── 설정 상수 ──────────────────────────────────────────
MAX_SESSIONS = 100          # 최대 보관 세션 수
DEFAULT_RECENT = 5          # 기본 최근 로드 수
CONTEXT_RECENT = 10         # context.md에 포함할 최근 세션 수
ROOM_TAIL_RECENT = 5        # 활성 room 최근 메시지 수
ROOM_TAIL_MAX_CHARS = 800   # 활성 room 메시지 최대 길이


def _ensure_dir(path: Path) -> None:
    """메모리 디렉토리가 존재하지 않으면 생성한다."""
    path.parent.mkdir(parents=True, exist_ok=True)


def save_session(entry: MemoryEntry, *, memory_file: Path | None = None) -> Path:
    """세션 결과를 JSONL 파일에 append한다.

    Args:
        entry: 저장할 세션 메모리 엔트리
        memory_file: 대상 JSONL 파일 (기본: MEMORY_FILE)

    Returns:
        저장된 파일 경로
    """
    target = memory_file or MEMORY_FILE
    _ensure_dir(target)
    with target.open("a", encoding="utf-8") as f:
        f.write(entry.to_jsonl() + "\n")

    # 자동 로테이션
    _rotate_if_needed(target)
    return target


def load_all(*, memory_file: Path | None = None) -> list[MemoryEntry]:
    """전체 세션 메모리를 로드한다.

    Args:
        memory_file: 대상 JSONL 파일 (기본: MEMORY_FILE)

    Returns:
        MemoryEntry 리스트 (오래된 순)
    """
    target = memory_file or MEMORY_FILE
    if not target.exists():
        return []

    entries: list[MemoryEntry] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(MemoryEntry.from_jsonl(line))
        except (json.JSONDecodeError, TypeError):
            continue  # 손상된 라인 무시
    return entries


def load_recent(n: int = DEFAULT_RECENT, *,
                memory_file: Path | None = None) -> list[MemoryEntry]:
    """최근 n개 세션을 로드한다.

    Args:
        n: 로드할 세션 수
        memory_file: 대상 JSONL 파일

    Returns:
        최근 n개 MemoryEntry (오래된 순)
    """
    all_entries = load_all(memory_file=memory_file)
    return all_entries[-n:] if len(all_entries) > n else all_entries


def get_pending_tasks(*, memory_file: Path | None = None) -> list[dict]:
    """이전 세션들에서 미완료 작업(next_steps)을 추출한다.

    최근 DEFAULT_RECENT 세션의 next_steps 중 이후 세션에서
    완료되지 않은 항목을 반환한다.

    Returns:
        [{"session_id": str, "timestamp": str, "task": str}, ...]
    """
    recent = load_recent(memory_file=memory_file)
    if not recent:
        return []

    # 모든 세션의 summary를 합쳐서 "완료 판정" 기준으로 사용
    completed_keywords = set()
    for entry in recent:
        # summary에 언급된 키워드를 완료로 간주
        completed_keywords.update(entry.summary.lower().split())

    pending: list[dict] = []
    for entry in recent:
        for task in entry.next_steps:
            # 간단한 휴리스틱: next_step의 핵심 단어가 이후 summary에 없으면 미완료
            task_words = set(task.lower().split())
            # 3단어 이상 겹치면 완료로 간주
            overlap = task_words & completed_keywords
            if len(overlap) < 3:
                pending.append({
                    "session_id": entry.session_id,
                    "timestamp": entry.timestamp,
                    "task": task,
                })
    return pending


def generate_context(*, memory_file: Path | None = None,
                     context_file: Path | None = None,
                     project_dir: Path | None = None) -> str:
    """CLAUDE.md 삽입용 세션 컨텍스트 요약을 생성한다.

    context.md 파일도 자동 업데이트한다.

    Returns:
        마크다운 포맷 컨텍스트 문자열
    """
    recent = load_recent(n=CONTEXT_RECENT, memory_file=memory_file)
    pending = get_pending_tasks(memory_file=memory_file)

    # 상태 아이콘
    status_icon = {
        "passed": "✅", "failed": "❌", "pending": "⏳",
        "running": "🔄", "skipped": "⏭️",
    }

    lines = ["## 이전 세션 컨텍스트", ""]

    if not recent:
        lines.append("_세션 기록 없음_")
    else:
        for entry in recent:
            # pipeline_result에서 final_status 추출
            final_status = entry.pipeline_result.get("final_status", "")
            icon = status_icon.get(final_status, "❓")

            # 테스트 결과 요약
            test_info = f" — {entry.test_result}" if entry.test_result else ""

            lines.append(
                f"- [{entry.timestamp}] {entry.work_type}: "
                f"{entry.summary} {icon}{test_info}"
            )

    # 미완료 작업
    if pending:
        lines.extend(["", "### 미완료 작업", ""])
        for item in pending:
            lines.append(f"- [ ] {item['task']} (from {item['session_id'][:8]})")

    room_tail = _build_room_tail_section(project_dir or Path("."))
    if room_tail:
        lines.extend(["", *room_tail])

    context = "\n".join(lines)

    # context.md 파일 저장
    target = context_file or CONTEXT_FILE
    _ensure_dir(target)
    target.write_text(context, encoding="utf-8")

    return context


def create_entry_from_pipeline(
    session_id: str,
    pipeline_result: PipelineResult,
    *,
    summary: str = "",
    decisions: list[str] | None = None,
    next_steps: list[str] | None = None,
) -> MemoryEntry:
    """PipelineResult로부터 MemoryEntry를 생성하는 헬퍼.

    Args:
        session_id: 세션 식별자
        pipeline_result: 파이프라인 실행 결과
        summary: 요약 (빈 문자열이면 자동 생성)
        decisions: 주요 결정 사항
        next_steps: 다음 단계

    Returns:
        저장 가능한 MemoryEntry
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 자동 요약 생성
    if not summary:
        stage_names = [s.stage for s in pipeline_result.stages]
        summary = (
            f"{pipeline_result.work_type.value} pipeline "
            f"({' → '.join(stage_names)}) — "
            f"{pipeline_result.final_status.value.upper()}"
        )

    # 에러 수집
    errors = []
    for s in pipeline_result.stages:
        errors.extend(s.errors)

    # 테스트 결과 추출 (qa 스테이지에서)
    test_result = ""
    for s in pipeline_result.stages:
        if s.stage == "qa" and s.output:
            test_result = s.output[:200]
            break

    return MemoryEntry(
        session_id=session_id,
        timestamp=timestamp,
        work_type=pipeline_result.work_type.value,
        summary=summary,
        files_changed=pipeline_result.files_changed,
        test_result=test_result,
        errors=errors[:10],  # 최대 10개
        decisions=decisions or [],
        next_steps=next_steps or [],
        pipeline_result=pipeline_result.to_dict(),
    )


def _rotate_if_needed(memory_file: Path) -> None:
    """세션 수가 MAX_SESSIONS를 초과하면 오래된 것을 삭제한다."""
    if not memory_file.exists():
        return

    lines = memory_file.read_text(encoding="utf-8").splitlines()
    valid_lines = [l for l in lines if l.strip()]

    if len(valid_lines) <= MAX_SESSIONS:
        return

    # 최근 MAX_SESSIONS개만 유지
    trimmed = valid_lines[-MAX_SESSIONS:]
    memory_file.write_text("\n".join(trimmed) + "\n", encoding="utf-8")


def _build_room_tail_section(project_dir: Path) -> list[str]:
    """활성 room이 있으면 최근 tail 섹션을 생성한다."""
    session_data = read_session_data(project_dir)
    if session_data is None:
        return []

    room_name = session_data.get("room_name")
    room_slug = session_data.get("room_slug")
    if not room_name or not room_slug:
        return []

    entries = tail_room_messages(
        project_dir,
        str(room_slug),
        limit=ROOM_TAIL_RECENT,
        max_chars=ROOM_TAIL_MAX_CHARS,
    )
    if not entries:
        return []

    lines = [f"### 활성 Room Tail ({room_name})", ""]
    for entry in entries:
        lines.append(f"- [{entry.timestamp}] {entry.sender}/{entry.event_type}: {entry.message}")
    return lines
