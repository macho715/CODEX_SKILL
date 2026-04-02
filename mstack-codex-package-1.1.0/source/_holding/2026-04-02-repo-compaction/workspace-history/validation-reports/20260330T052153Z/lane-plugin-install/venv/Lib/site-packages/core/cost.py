"""core/cost.py — JSONL 파서 + 비용 집계기"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
import json
from .types import CostEntry, DashboardData, PipelineResult

logger = logging.getLogger(__name__)


def parse_jsonl(log_path: Path) -> list[CostEntry]:
    """JSONL 비용 로그 파일을 파싱한다.

    Args:
        log_path: cost.jsonl 파일 경로

    Returns:
        CostEntry 리스트 (파일 없으면 빈 리스트)
    """
    if not log_path.exists():
        return []

    entries = []
    for i, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(CostEntry.from_jsonl(line))
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[mstack] ⚠ cost.jsonl line {i} skipped: {e}")
    return entries


def aggregate(entries: list[CostEntry]) -> DashboardData:
    """CostEntry 리스트를 대시보드용 집계 데이터로 변환한다."""
    if not entries:
        return DashboardData(
            daily=[], by_model={}, by_session=[],
            total_cost=0.0, total_sessions=0, period="N/A"
        )

    # session 이벤트만 필터
    sessions = [e for e in entries if e.event_type == "session"]

    # 일별 집계
    daily_map: dict[str, dict] = defaultdict(
        lambda: {"total_cost": 0.0, "sessions": 0, "total_tokens": 0}
    )
    for e in sessions:
        date = e.timestamp[:10]  # YYYY-MM-DD
        daily_map[date]["total_cost"] += e.cost_usd
        daily_map[date]["sessions"] += 1
        daily_map[date]["total_tokens"] += e.input_tokens + e.output_tokens

    daily = [
        {"date": d, **v, "avg_tokens": v["total_tokens"] // max(v["sessions"], 1)}
        for d, v in sorted(daily_map.items())
    ]

    # 모델별 집계
    by_model: dict[str, float] = defaultdict(float)
    for e in sessions:
        by_model[e.model] += e.cost_usd

    # 세션별 리스트
    by_session = [
        {
            "session_id": e.session_id,
            "cost": e.cost_usd,
            "duration": e.duration_sec,
            "model": e.model,
            "tokens": e.input_tokens + e.output_tokens,
        }
        for e in sessions
    ]

    # 기간
    dates = [e.timestamp[:10] for e in sessions]
    period = f"{min(dates)} ~ {max(dates)}" if dates else "N/A"

    return DashboardData(
        daily=daily,
        by_model=dict(by_model),
        by_session=by_session,
        total_cost=sum(e.cost_usd for e in sessions),
        total_sessions=len(sessions),
        period=period,
    )


def format_ascii_table(data: DashboardData) -> str:
    """비용 데이터를 ASCII 테이블로 포맷한다."""
    lines = []
    lines.append("┌─────────────────────────────────────┐")
    lines.append("│  mstack Cost Report                 │")
    lines.append(f"│  Period: {data.period:<27s}│")
    lines.append("├─────────────────────────────────────┤")
    lines.append(f"│  Total Cost:    ${data.total_cost:>8.2f}           │")
    lines.append(f"│  Total Sessions: {data.total_sessions:>5d}              │")
    lines.append("├─────────────────────────────────────┤")
    lines.append("│  Model Breakdown:                   │")
    for model, cost in sorted(data.by_model.items()):
        lines.append(f"│    {model:<15s} ${cost:>8.2f}       │")
    lines.append("└─────────────────────────────────────┘")
    return "\n".join(lines)


DEFAULT_COST_LOG = Path(".claude/cost-logs/sessions.jsonl")


def record_session(
    entry: CostEntry,
    *,
    log_path: Path | None = None,
) -> Path:
    """CostEntry를 JSONL 로그 파일에 추가한다.

    Args:
        entry: 기록할 CostEntry
        log_path: 로그 파일 경로 (기본: DEFAULT_COST_LOG)

    Returns:
        기록된 로그 파일 경로
    """
    path = log_path or DEFAULT_COST_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(entry.to_jsonl() + "\n")
    return path


def create_entry_from_pipeline(
    session_id: str,
    pipeline_result: PipelineResult,
    *,
    model: str = "claude-opus-4-6",
    input_tokens: int = 0,
    output_tokens: int = 0,
    duration_sec: float = 0.0,
) -> CostEntry:
    """PipelineResult로부터 CostEntry를 생성한다.

    Args:
        session_id: 세션 ID
        pipeline_result: 파이프라인 실행 결과
        model: 사용된 모델명
        input_tokens: 입력 토큰 수
        output_tokens: 출력 토큰 수
        duration_sec: 실행 시간 (초)

    Returns:
        pipeline 이벤트 타입의 CostEntry
    """
    return CostEntry(
        session_id=session_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=0.0,
        duration_sec=duration_sec,
        event_type="pipeline",
        details=pipeline_result.to_dict(),
    )
