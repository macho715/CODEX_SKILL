"""tests/test_memory.py — memory.py 단위 테스트"""
import json
import pytest
from pathlib import Path
from core.group_logs import append_group_message
from core.session import set_room_binding
from core.types import MemoryEntry, StageStatus, WorkType, StageResult, PipelineResult
from core.types import GroupMessageEntry
from core.memory import (
    MEMORY_FILE,
    CONTEXT_FILE,
    MAX_SESSIONS,
    DEFAULT_RECENT,
    save_session,
    load_all,
    load_recent,
    get_pending_tasks,
    generate_context,
    create_entry_from_pipeline,
    _rotate_if_needed,
)


# ── 테스트 픽스처 ──────────────────────────────────────


@pytest.fixture
def tmp_memory(tmp_path: Path) -> Path:
    """임시 메모리 파일 경로."""
    return tmp_path / "memory" / "sessions.jsonl"


@pytest.fixture
def tmp_context(tmp_path: Path) -> Path:
    """임시 컨텍스트 파일 경로."""
    return tmp_path / "memory" / "context.md"


@pytest.fixture
def sample_entry() -> MemoryEntry:
    return MemoryEntry(
        session_id="test-001",
        timestamp="2026-03-22T10:00:00Z",
        work_type="feature",
        summary="pipeline.py 구현",
        files_changed=["core/pipeline.py", "core/types.py"],
        test_result="148 passed",
        errors=[],
        decisions=["MappingProxyType 사용"],
        next_steps=["memory.py 구현", "dispatch SKILL.md 업데이트"],
        pipeline_result={"final_status": "passed", "total_retries": 0},
    )


@pytest.fixture
def sample_entry_2() -> MemoryEntry:
    return MemoryEntry(
        session_id="test-002",
        timestamp="2026-03-22T11:00:00Z",
        work_type="refactor",
        summary="hooks.py freeze 적용",
        files_changed=["core/hooks.py"],
        test_result="148 passed",
        errors=[],
        decisions=["frozenset 사용"],
        next_steps=["cmd_init 장함수 분리"],
        pipeline_result={"final_status": "passed", "total_retries": 0},
    )


# ── save / load 라운드트립 ─────────────────────────────


class TestSaveLoad:
    """save_session, load_all, load_recent 검증."""

    def test_save_creates_file(self, tmp_memory: Path, sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        assert tmp_memory.exists()

    def test_save_appends_jsonl(self, tmp_memory: Path,
                                sample_entry: MemoryEntry,
                                sample_entry_2: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        save_session(sample_entry_2, memory_file=tmp_memory)
        lines = tmp_memory.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2

    def test_load_all_returns_entries(self, tmp_memory: Path,
                                      sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        entries = load_all(memory_file=tmp_memory)
        assert len(entries) == 1
        assert entries[0].session_id == "test-001"

    def test_load_all_preserves_fields(self, tmp_memory: Path,
                                        sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        restored = load_all(memory_file=tmp_memory)[0]
        assert restored == sample_entry

    def test_load_all_empty_file(self, tmp_memory: Path) -> None:
        entries = load_all(memory_file=tmp_memory)
        assert entries == []

    def test_load_all_skips_corrupt_lines(self, tmp_memory: Path,
                                           sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        # 손상된 라인 추가
        with tmp_memory.open("a", encoding="utf-8") as f:
            f.write("CORRUPT LINE\n")
            f.write("{invalid json\n")
        entries = load_all(memory_file=tmp_memory)
        assert len(entries) == 1

    def test_load_recent_default(self, tmp_memory: Path,
                                  sample_entry: MemoryEntry) -> None:
        # 7개 엔트리 생성
        for i in range(7):
            entry = MemoryEntry(
                session_id=f"sess-{i:03d}",
                timestamp=f"2026-03-22T{10+i}:00:00Z",
                work_type="feature",
                summary=f"작업 {i}",
            )
            save_session(entry, memory_file=tmp_memory)

        recent = load_recent(memory_file=tmp_memory)
        assert len(recent) == DEFAULT_RECENT  # 5
        assert recent[0].session_id == "sess-002"  # 가장 오래된 것
        assert recent[-1].session_id == "sess-006"  # 가장 최근

    def test_load_recent_custom_n(self, tmp_memory: Path) -> None:
        for i in range(10):
            entry = MemoryEntry(
                session_id=f"sess-{i:03d}",
                timestamp=f"2026-03-22T{10+i}:00:00Z",
                work_type="test",
                summary=f"테스트 {i}",
            )
            save_session(entry, memory_file=tmp_memory)

        recent = load_recent(3, memory_file=tmp_memory)
        assert len(recent) == 3
        assert recent[-1].session_id == "sess-009"


# ── 자동 로테이션 ──────────────────────────────────────


class TestRotation:
    """_rotate_if_needed 검증."""

    def test_rotation_trims_to_max(self, tmp_memory: Path) -> None:
        # MAX_SESSIONS + 10개 엔트리 생성
        for i in range(MAX_SESSIONS + 10):
            entry = MemoryEntry(
                session_id=f"sess-{i:04d}",
                timestamp=f"2026-01-01T00:{i:02d}:00Z",
                work_type="test",
                summary=f"세션 {i}",
            )
            save_session(entry, memory_file=tmp_memory)

        lines = tmp_memory.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == MAX_SESSIONS

        # 가장 오래된 것은 삭제됨
        first = json.loads(lines[0])
        assert first["session_id"] == "sess-0010"

    def test_no_rotation_under_limit(self, tmp_memory: Path) -> None:
        for i in range(5):
            entry = MemoryEntry(
                session_id=f"sess-{i}",
                timestamp="2026-01-01T00:00:00Z",
                work_type="test",
                summary=f"세션 {i}",
            )
            save_session(entry, memory_file=tmp_memory)

        lines = tmp_memory.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 5


# ── 미완료 작업 추출 ──────────────────────────────────


class TestPendingTasks:
    """get_pending_tasks 검증."""

    def test_returns_pending_from_next_steps(self, tmp_memory: Path,
                                              sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        pending = get_pending_tasks(memory_file=tmp_memory)
        assert len(pending) > 0
        tasks = [p["task"] for p in pending]
        assert any("memory.py" in t for t in tasks)

    def test_empty_when_no_sessions(self, tmp_memory: Path) -> None:
        pending = get_pending_tasks(memory_file=tmp_memory)
        assert pending == []

    def test_returns_dict_structure(self, tmp_memory: Path,
                                    sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        pending = get_pending_tasks(memory_file=tmp_memory)
        for item in pending:
            assert "session_id" in item
            assert "timestamp" in item
            assert "task" in item


# ── 컨텍스트 생성 ──────────────────────────────────────


class TestGenerateContext:
    """generate_context 검증."""

    def test_generates_markdown(self, tmp_memory: Path,
                                 tmp_context: Path,
                                 sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        context = generate_context(
            memory_file=tmp_memory, context_file=tmp_context,
        )
        assert "## 이전 세션 컨텍스트" in context
        assert "pipeline.py" in context

    def test_saves_context_file(self, tmp_memory: Path,
                                 tmp_context: Path,
                                 sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        generate_context(memory_file=tmp_memory, context_file=tmp_context)
        assert tmp_context.exists()
        content = tmp_context.read_text(encoding="utf-8")
        assert "이전 세션 컨텍스트" in content

    def test_shows_status_icon(self, tmp_memory: Path,
                                tmp_context: Path,
                                sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        context = generate_context(
            memory_file=tmp_memory, context_file=tmp_context,
        )
        assert "✅" in context

    def test_empty_sessions(self, tmp_memory: Path,
                             tmp_context: Path) -> None:
        context = generate_context(
            memory_file=tmp_memory, context_file=tmp_context,
        )
        assert "세션 기록 없음" in context

    def test_includes_pending_tasks(self, tmp_memory: Path,
                                     tmp_context: Path,
                                     sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        context = generate_context(
            memory_file=tmp_memory, context_file=tmp_context,
        )
        assert "미완료 작업" in context

    def test_includes_active_room_tail(self, tmp_path: Path,
                                       tmp_memory: Path,
                                       tmp_context: Path,
                                       sample_entry: MemoryEntry) -> None:
        save_session(sample_entry, memory_file=tmp_memory)
        set_room_binding(tmp_path, "Ops Review", "ops-review")
        append_group_message(
            tmp_path,
            GroupMessageEntry(
                room_name="Ops Review",
                room_slug="ops-review",
                event_type="task_completed",
                sender="system",
                message="hook connected",
                timestamp="2026-03-25T10:00:00Z",
            ),
        )
        context = generate_context(
            memory_file=tmp_memory,
            context_file=tmp_context,
            project_dir=tmp_path,
        )
        assert "활성 Room Tail (Ops Review)" in context
        assert "hook connected" in context


# ── create_entry_from_pipeline ─────────────────────────


class TestCreateEntryFromPipeline:
    """PipelineResult → MemoryEntry 변환 검증."""

    def test_creates_valid_entry(self) -> None:
        pr = PipelineResult(
            work_type=WorkType.FEATURE,
            stages=[
                StageResult(stage="plan", status=StageStatus.PASSED),
                StageResult(stage="qa", status=StageStatus.PASSED, output="5 passed"),
            ],
            final_status=StageStatus.PASSED,
            files_changed=["a.py"],
        )
        entry = create_entry_from_pipeline("sess-123", pr)
        assert entry.session_id == "sess-123"
        assert entry.work_type == "feature"
        assert "a.py" in entry.files_changed
        assert entry.test_result == "5 passed"

    def test_auto_summary(self) -> None:
        pr = PipelineResult(
            work_type=WorkType.BUGFIX,
            stages=[StageResult(stage="qa", status=StageStatus.PASSED)],
            final_status=StageStatus.PASSED,
        )
        entry = create_entry_from_pipeline("sess-456", pr)
        assert "bugfix" in entry.summary
        assert "PASSED" in entry.summary

    def test_custom_summary(self) -> None:
        pr = PipelineResult(
            work_type=WorkType.FEATURE,
            final_status=StageStatus.PASSED,
        )
        entry = create_entry_from_pipeline(
            "sess-789", pr, summary="커스텀 요약",
        )
        assert entry.summary == "커스텀 요약"

    def test_collects_errors(self) -> None:
        pr = PipelineResult(
            work_type=WorkType.FEATURE,
            stages=[
                StageResult(stage="qa", status=StageStatus.FAILED,
                            errors=["err1", "err2"]),
            ],
            final_status=StageStatus.FAILED,
        )
        entry = create_entry_from_pipeline("sess-err", pr)
        assert "err1" in entry.errors
        assert "err2" in entry.errors

    def test_pipeline_result_dict(self) -> None:
        pr = PipelineResult(
            work_type=WorkType.DEPLOY,
            stages=[StageResult(stage="ship", status=StageStatus.PASSED)],
            final_status=StageStatus.PASSED,
            total_retries=1,
        )
        entry = create_entry_from_pipeline("sess-dict", pr)
        assert entry.pipeline_result["work_type"] == "deploy"
        assert entry.pipeline_result["total_retries"] == 1

    def test_serialization_roundtrip(self) -> None:
        pr = PipelineResult(
            work_type=WorkType.FEATURE,
            stages=[StageResult(stage="qa", status=StageStatus.PASSED)],
            final_status=StageStatus.PASSED,
        )
        entry = create_entry_from_pipeline("sess-rt", pr)
        jsonl = entry.to_jsonl()
        restored = MemoryEntry.from_jsonl(jsonl)
        assert restored.session_id == entry.session_id
        assert restored.pipeline_result == entry.pipeline_result


# ── 미커버 라인 보강 (v1.4) ──────────────────────────────


class TestLoadAllEdgeCases:
    """load_all 빈 줄 처리 (L65)."""

    def test_blank_lines_skipped(self, tmp_memory: Path,
                                   sample_entry: MemoryEntry) -> None:
        """빈 줄과 공백만 있는 줄은 무시된다."""
        save_session(sample_entry, memory_file=tmp_memory)
        # 빈 줄 삽입
        with tmp_memory.open("a", encoding="utf-8") as f:
            f.write("\n\n  \n")
        entries = load_all(memory_file=tmp_memory)
        assert len(entries) == 1


class TestRotateEdgeCases:
    """_rotate_if_needed 엣지 케이스 (L235)."""

    def test_missing_file_no_error(self, tmp_path: Path) -> None:
        """파일이 존재하지 않으면 아무것도 하지 않고 반환."""
        missing = tmp_path / "nonexistent.jsonl"
        _rotate_if_needed(missing)  # 예외 없이 완료
        assert not missing.exists()
