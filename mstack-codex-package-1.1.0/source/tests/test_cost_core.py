"""tests/test_cost_core.py — cost.py 단위 테스트"""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from core.types import CostEntry, DashboardData, PipelineResult, WorkType, StageStatus, StageResult
from core.cost import (
    parse_jsonl,
    aggregate,
    format_ascii_table,
    record_session,
    create_entry_from_pipeline,
    DEFAULT_COST_LOG,
)


def _make_entry(
    session_id: str = "test-001",
    cost: float = 1.0,
    model: str = "claude-opus-4-6",
    timestamp: str = "2026-03-22T10:00:00",
    input_tokens: int = 1000,
    output_tokens: int = 500,
    duration_sec: float = 60.0,
    event_type: str = "session",
) -> CostEntry:
    return CostEntry(
        session_id=session_id,
        timestamp=timestamp,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        duration_sec=duration_sec,
        event_type=event_type,
    )


# ── parse_jsonl ──────────────────────────────────


class TestParseJsonl:
    """parse_jsonl 파싱 검증."""

    def test_file_not_exists(self, tmp_path: Path) -> None:
        result = parse_jsonl(tmp_path / "missing.jsonl")
        assert result == []

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.jsonl"
        f.write_text("")
        assert parse_jsonl(f) == []

    def test_single_entry(self, tmp_path: Path) -> None:
        entry = _make_entry()
        f = tmp_path / "cost.jsonl"
        f.write_text(entry.to_jsonl() + "\n")
        result = parse_jsonl(f)
        assert len(result) == 1
        assert result[0].session_id == "test-001"

    def test_multiple_entries(self, tmp_path: Path) -> None:
        e1 = _make_entry(session_id="s1", cost=1.0)
        e2 = _make_entry(session_id="s2", cost=2.0)
        f = tmp_path / "cost.jsonl"
        f.write_text(e1.to_jsonl() + "\n" + e2.to_jsonl() + "\n")
        result = parse_jsonl(f)
        assert len(result) == 2

    def test_invalid_line_skipped(self, tmp_path: Path) -> None:
        entry = _make_entry()
        f = tmp_path / "cost.jsonl"
        f.write_text("INVALID JSON\n" + entry.to_jsonl() + "\n")
        result = parse_jsonl(f)
        assert len(result) == 1


# ── aggregate ──────────────────────────────────


class TestAggregate:
    """aggregate 집계 검증."""

    def test_empty_entries(self) -> None:
        data = aggregate([])
        assert data.total_cost == 0.0
        assert data.total_sessions == 0
        assert data.period == "N/A"

    def test_single_session(self) -> None:
        entries = [_make_entry(cost=5.0)]
        data = aggregate(entries)
        assert data.total_cost == 5.0
        assert data.total_sessions == 1

    def test_multiple_days(self) -> None:
        entries = [
            _make_entry(session_id="s1", timestamp="2026-03-20T10:00:00", cost=1.0),
            _make_entry(session_id="s2", timestamp="2026-03-21T10:00:00", cost=2.0),
        ]
        data = aggregate(entries)
        assert data.total_cost == 3.0
        assert len(data.daily) == 2

    def test_non_session_events_excluded(self) -> None:
        entries = [
            _make_entry(event_type="session", cost=5.0),
            _make_entry(event_type="pipeline", cost=0.0),
        ]
        data = aggregate(entries)
        assert data.total_sessions == 1
        assert data.total_cost == 5.0

    def test_model_breakdown(self) -> None:
        entries = [
            _make_entry(model="opus", cost=3.0),
            _make_entry(model="sonnet", cost=1.0),
        ]
        data = aggregate(entries)
        assert data.by_model["opus"] == 3.0
        assert data.by_model["sonnet"] == 1.0


# ── format_ascii_table ──────────────────────────────────


class TestFormatAsciiTable:
    """format_ascii_table 포맷 검증."""

    def test_empty_data(self) -> None:
        data = aggregate([])
        table = format_ascii_table(data)
        assert "mstack Cost Report" in table
        assert "$    0.00" in table

    def test_with_data(self) -> None:
        entries = [_make_entry(cost=7.50, model="opus")]
        data = aggregate(entries)
        table = format_ascii_table(data)
        assert "$    7.50" in table
        assert "opus" in table


# ── record_session ──────────────────────────────────


class TestRecordSession:
    """record_session 기록 검증."""

    def test_creates_file(self, tmp_path: Path) -> None:
        log = tmp_path / "logs" / "cost.jsonl"
        entry = _make_entry()
        result_path = record_session(entry, log_path=log)
        assert result_path == log
        assert log.exists()

    def test_appends_entry(self, tmp_path: Path) -> None:
        log = tmp_path / "cost.jsonl"
        record_session(_make_entry(session_id="s1"), log_path=log)
        record_session(_make_entry(session_id="s2"), log_path=log)
        lines = log.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        log = tmp_path / "deep" / "nested" / "cost.jsonl"
        record_session(_make_entry(), log_path=log)
        assert log.exists()

    def test_roundtrip(self, tmp_path: Path) -> None:
        """기록 후 parse_jsonl로 읽기."""
        log = tmp_path / "cost.jsonl"
        entry = _make_entry(session_id="roundtrip", cost=3.14)
        record_session(entry, log_path=log)
        parsed = parse_jsonl(log)
        assert len(parsed) == 1
        assert parsed[0].session_id == "roundtrip"
        assert parsed[0].cost_usd == 3.14


# ── create_entry_from_pipeline ──────────────────────────────────


class TestCreateEntryFromPipeline:
    """create_entry_from_pipeline 검증."""

    def _make_pipeline_result(self) -> PipelineResult:
        return PipelineResult(
            work_type=WorkType.FEATURE,
            stages=[StageResult(stage="qa", status=StageStatus.PASSED)],
            final_status=StageStatus.PASSED,
            files_changed=["a.py"],
        )

    def test_returns_cost_entry(self) -> None:
        pr = self._make_pipeline_result()
        entry = create_entry_from_pipeline("sess-1", pr)
        assert isinstance(entry, CostEntry)

    def test_event_type_is_pipeline(self) -> None:
        pr = self._make_pipeline_result()
        entry = create_entry_from_pipeline("sess-1", pr)
        assert entry.event_type == "pipeline"

    def test_session_id_set(self) -> None:
        pr = self._make_pipeline_result()
        entry = create_entry_from_pipeline("my-session", pr)
        assert entry.session_id == "my-session"

    def test_details_contains_work_type(self) -> None:
        pr = self._make_pipeline_result()
        entry = create_entry_from_pipeline("sess-1", pr)
        assert entry.details["work_type"] == "feature"

    def test_details_contains_final_status(self) -> None:
        pr = self._make_pipeline_result()
        entry = create_entry_from_pipeline("sess-1", pr)
        assert entry.details["final_status"] == "passed"

    def test_custom_model(self) -> None:
        pr = self._make_pipeline_result()
        entry = create_entry_from_pipeline("sess-1", pr, model="claude-sonnet-4-6")
        assert entry.model == "claude-sonnet-4-6"


# ── 미커버 라인 보강 (v1.4) ──────────────────────────────


class TestParseJsonlEdgeCases:
    """parse_jsonl 빈 줄 처리 (L29)."""

    def test_blank_lines_skipped(self, tmp_path: Path) -> None:
        """빈 줄과 공백만 있는 줄은 무시된다."""
        entry = _make_entry()
        f = tmp_path / "cost.jsonl"
        f.write_text("\n\n" + entry.to_jsonl() + "\n  \n\n")
        result = parse_jsonl(f)
        assert len(result) == 1
