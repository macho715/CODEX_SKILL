"""core/pipeline.py — 파이프라인 자동 실행 엔진

dispatch 승인 후 plan→구현→review→fix→qa→ship→retro를 자동 체이닝.
qa FAIL 시 review→fix→qa 자동 재시도 (최대 MAX_RETRIES회).
"""
from __future__ import annotations
import os
import logging
from pathlib import Path
from types import MappingProxyType
from typing import Callable
from .types import (
    WorkType, StageStatus, StageResult, PipelineResult,
)

logger = logging.getLogger(__name__)

# ── 파이프라인 템플릿 ─────────────────────────────────

PIPELINE_TEMPLATES = MappingProxyType({
    WorkType.FEATURE:  ("plan", "implement", "review", "qa", "ship", "retro"),
    WorkType.BUGFIX:   ("investigate", "implement", "qa", "ship", "retro"),
    WorkType.REFACTOR: ("plan", "implement", "review", "qa", "ship", "retro"),
    WorkType.TEST:     ("qa",),
    WorkType.DEPLOY:   ("ship", "qa", "retro"),
    WorkType.RETRO:    ("retro",),
})

# qa 실패 시 자동 반복하는 스테이지
AUTO_RETRY_STAGES = ("review", "fix", "qa")
MAX_RETRIES = 3
MAX_LOCK_RETRIES = 3

# 각 스테이지가 매핑되는 mstack 스킬
STAGE_TO_SKILL = MappingProxyType({
    "plan":        "mstack-plan",
    "implement":   None,             # 직접 코딩 (Agent 위임)
    "review":      "mstack-review",
    "fix":         None,             # AUTO-FIX 적용
    "qa":          "mstack-qa",
    "ship":        "mstack-ship",
    "retro":       "mstack-retro",
    "investigate": "mstack-investigate",
})


def resolve_git_lock(git_dir: Path | None = None) -> bool:
    """git index.lock / HEAD.lock 파일을 감지하고 안전하게 rename한다.

    Cowork 환경에서 .git/index.lock이 남아있으면 git commit이 실패한다.
    이 함수를 ship 단계 전에 호출하여 자동으로 우회한다.

    Args:
        git_dir: .git 디렉토리 경로 (기본: Path(".git"))

    Returns:
        True if all locks resolved or none present, False if any unresolvable.
    """
    if git_dir is None:
        git_dir = Path(".git")

    lock_names = ("index.lock", "HEAD.lock")
    all_resolved = True

    for name in lock_names:
        lock_path = git_dir / name
        if not lock_path.exists():
            continue
        bak_path = lock_path.with_suffix(".lock.bak")
        try:
            os.rename(str(lock_path), str(bak_path))
            logger.warning("Resolved git lock: %s → %s", lock_path, bak_path)
        except OSError as e:
            logger.error("Cannot resolve git lock %s: %s", lock_path, e)
            all_resolved = False

    return all_resolved


def get_pipeline(work_type: WorkType) -> tuple[str, ...]:
    """작업 유형에 맞는 파이프라인 스테이지 목록을 반환한다."""
    return PIPELINE_TEMPLATES[work_type]


def should_retry(stage: str, status: StageStatus) -> bool:
    """qa 실패 시 재시도 여부를 판단한다."""
    return stage == "qa" and status == StageStatus.FAILED


def build_retry_stages() -> tuple[str, ...]:
    """재시도 사이클 스테이지를 반환한다."""
    return AUTO_RETRY_STAGES


def execute_pipeline(
    work_type: WorkType,
    stage_runner: Callable[[str], StageResult],
    *,
    skip_stages: frozenset[str] | None = None,
    approval_gate: str | None = None,
) -> PipelineResult:
    """파이프라인을 순차 실행한다.

    Args:
        work_type: 작업 유형 (feature, bugfix, ...)
        stage_runner: 각 스테이지를 실행하는 콜백 함수
        skip_stages: 건너뛸 스테이지 집합
        approval_gate: 이 스테이지 완료 후 사용자 승인 대기

    Returns:
        PipelineResult 전체 실행 결과

    Note:
        stage_runner는 외부에서 제공하는 함수로, 각 스테이지명을 받아
        StageResult를 반환한다. 실제 Cowork에서는 Agent 도구 호출,
        Claude Code에서는 slash command 호출이 된다.
    """
    skip = skip_stages or frozenset()
    stages = get_pipeline(work_type)
    result = PipelineResult(work_type=work_type)

    for stage_name in stages:
        if stage_name in skip:
            result.stages.append(StageResult(
                stage=stage_name, status=StageStatus.SKIPPED,
            ))
            continue

        # 스테이지 실행
        stage_result = stage_runner(stage_name)
        result.stages.append(stage_result)
        _merge_files_changed(result, stage_result)

        # 실패 시 재시도 사이클
        if should_retry(stage_name, stage_result.status):
            retry_count = 0
            while retry_count < MAX_RETRIES:
                retry_count += 1
                result.total_retries += 1

                # review → fix → qa 사이클
                for retry_stage in build_retry_stages():
                    retry_result = stage_runner(retry_stage)
                    retry_result.retry_count = retry_count
                    result.stages.append(retry_result)
                    _merge_files_changed(result, retry_result)

                    if retry_stage == "qa" and retry_result.status == StageStatus.PASSED:
                        # qa 통과 — 사이클 종료
                        stage_result = retry_result
                        break
                else:
                    # qa 미통과 — 다음 retry로
                    continue
                break  # qa 통과했으므로 외부 while도 종료

            # MAX_RETRIES 초과 시 실패
            if stage_result.status == StageStatus.FAILED:
                result.final_status = StageStatus.FAILED
                return result

        elif stage_result.status == StageStatus.FAILED:
            # 재시도 불가능한 스테이지 실패 → 파이프라인 중단
            result.final_status = StageStatus.FAILED
            return result

        if approval_gate and stage_name == approval_gate:
            if _append_trailing_skips(result, stages, stage_name, skip):
                result.final_status = StageStatus.PENDING
                return result

    result.final_status = StageStatus.PASSED
    return result


def _merge_files_changed(result: PipelineResult, stage_result: StageResult) -> None:
    """Merge stage-level changed files into the pipeline result without duplicates."""
    for path in stage_result.files_changed:
        if path not in result.files_changed:
            result.files_changed.append(path)


def _append_trailing_skips(
    result: PipelineResult,
    stages: tuple[str, ...],
    completed_stage: str,
    skip: frozenset[str],
) -> bool:
    """Append trailing skipped stages when execution pauses at an approval gate."""
    completed_index = stages.index(completed_stage)
    trailing = stages[completed_index + 1:]
    if not trailing:
        return False

    for stage_name in trailing:
        if any(existing.stage == stage_name for existing in result.stages):
            continue
        result.stages.append(
            StageResult(
                stage=stage_name,
                status=StageStatus.SKIPPED,
                output=f"awaiting approval after {completed_stage}",
            )
        )
    return True


def format_pipeline_summary(result: PipelineResult) -> str:
    """파이프라인 결과를 읽기 쉬운 문자열로 포맷한다."""
    icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️",
            "running": "🔄", "pending": "⏳", "blocked": "🛑"}

    lines = [
        f"## Pipeline Result: {result.work_type.value}",
        f"Status: {icon.get(result.final_status.value, '?')} {result.final_status.value.upper()}",
        f"Retries: {result.total_retries}",
        "",
        "| # | Stage | Status | Retry | Errors |",
        "|---|-------|--------|-------|--------|",
    ]

    for i, s in enumerate(result.stages, 1):
        err = "; ".join(s.errors[:2]) if s.errors else "-"
        lines.append(
            f"| {i} | {s.stage} | {icon.get(s.status.value, '?')} "
            f"| {s.retry_count} | {err} |"
        )

    if result.files_changed:
        lines.append(f"\nFiles changed: {len(result.files_changed)}")

    return "\n".join(lines)


def generate_dispatch_prompt(
    work_type: WorkType,
    plan_doc: str,
    team_config: dict | None = None,
) -> str:
    """dispatch가 Agent 도구에 전달할 자동 실행 프롬프트를 생성한다.

    이 프롬프트를 Agent(prompt=...) 에 전달하면 파이프라인이 자동 실행된다.
    """
    stages = get_pipeline(work_type)
    skill_list = [
        f"- {s}: {STAGE_TO_SKILL.get(s, '직접 구현')}"
        for s in stages
    ]

    prompt = f"""## 자동 파이프라인 실행 ({work_type.value})

### 계획 문서
{plan_doc[:2000]}

### 실행할 파이프라인
{chr(10).join(skill_list)}

### 실행 규칙
1. 각 단계를 순서대로 실행하라
2. mstack-careful 규칙을 모든 단계에서 준수하라
3. qa 실패 시 review→fix→qa 사이클을 최대 {MAX_RETRIES}회 반복하라
4. 모든 단계 완료 후 결과 요약을 출력하라
5. 세션 결과를 memory에 기록하라

### 금지 사항
- force push 금지
- 담당 범위 외 파일 수정 금지
- 테스트 미통과 상태로 ship 금지
"""
    if team_config:
        prompt += f"\n### 팀 구성\n{team_config}\n"

    return prompt
