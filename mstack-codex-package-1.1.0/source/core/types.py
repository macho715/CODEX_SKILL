"""core/types.py — mstack 공통 데이터 구조"""
from __future__ import annotations
from dataclasses import dataclass, field, fields as dataclass_fields
from enum import Enum
from pathlib import Path
from typing import TypedDict
import json


# ── Enums ──────────────────────────────────────────────

class Lang(str, Enum):
    PYTHON = "python"
    TS = "ts"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"

class HookEvent(str, Enum):
    TASK_COMPLETED = "TaskCompleted"
    TEAMMATE_IDLE = "TeammateIdle"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    STOP = "Stop"
    SUBAGENT_STOP = "SubagentStop"

class HookType(str, Enum):
    COMMAND = "command"

class RouterDecision(str, Enum):
    SINGLE = "single"
    SUBAGENT = "subagent"
    AGENT_TEAMS = "agent_teams"


# ── Dataclasses ────────────────────────────────────────

@dataclass
class Preset:
    """프로젝트 프리셋 정의"""
    name: str
    lang: Lang
    test_cmd: str
    lint_cmd: str
    type_cmd: str
    rules: list[str] = field(default_factory=list)
    permissions: dict[str, bool] = field(default_factory=dict)
    hooks_level: str = "basic"
    custom_skills: list[str] = field(default_factory=list)
    domain_terms: dict[str, str] = field(default_factory=dict)
    fanr_rules: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: Path) -> "Preset":
        data = json.loads(path.read_text(encoding="utf-8"))
        data["lang"] = Lang(data.get("lang", "unknown"))
        allowed = {f.name for f in dataclass_fields(cls)}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)


@dataclass
class CostEntry:
    """비용 로그 단일 엔트리 (JSONL 1줄)"""
    session_id: str
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_sec: float
    event_type: str = "session"
    details: dict = field(default_factory=dict)

    def to_jsonl(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, line: str) -> "CostEntry":
        return cls(**json.loads(line))


@dataclass
class HookConfig:
    """settings.json hooks[] 단일 항목"""
    event: HookEvent
    hooks: list[dict]

    def to_settings_entry(self) -> dict:
        return {
            "matcher": {"event": self.event.value},
            "hooks": self.hooks
        }


@dataclass
class DriftItem:
    """드리프트 탐지 결과 항목"""
    file_path: str
    expected_hash: str
    actual_hash: str | None
    status: str


@dataclass
class RouterResult:
    """Agent Teams 라우터 판단 결과"""
    decision: RouterDecision
    reason: str
    file_count: int
    coordination_needed: bool
    estimated_cost_ratio: float


@dataclass
class DashboardData:
    """대시보드 집계 데이터"""
    daily: list[dict]
    by_model: dict[str, float]
    by_session: list[dict]
    total_cost: float
    total_sessions: int
    period: str


# ── Pipeline / Memory ─────────────────────────────────

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkType(str, Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    TEST = "test"
    DEPLOY = "deploy"
    RETRO = "retro"


@dataclass
class StageResult:
    """파이프라인 단일 스테이지 실행 결과"""
    stage: str
    status: StageStatus
    output: str = ""
    errors: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    duration_sec: float = 0.0
    retry_count: int = 0


@dataclass
class PipelineResult:
    """파이프라인 전체 실행 결과"""
    work_type: WorkType
    stages: list[StageResult] = field(default_factory=list)
    total_retries: int = 0
    final_status: StageStatus = StageStatus.PENDING
    files_changed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "work_type": self.work_type.value,
            "stages": [
                {
                    "stage": s.stage,
                    "status": s.status.value,
                    "output": s.output,
                    "errors": s.errors,
                    "files_changed": s.files_changed,
                    "retry_count": s.retry_count,
                    "duration_sec": s.duration_sec,
                }
                for s in self.stages
            ],
            "total_retries": self.total_retries,
            "final_status": self.final_status.value,
            "files_changed": self.files_changed,
        }


@dataclass
class PipelineRequestClassifierInput:
    """mstack-pipeline 요청 분류 입력."""
    request: str
    dispatch_result: RouterResult | None = None
    approval_gate_requested: bool = False


@dataclass
class PipelineRequestClassifierResult:
    """mstack-pipeline 요청 분류 결과."""
    request: str
    work_type: WorkType
    stage_order: tuple[str, ...]
    execution_mode: RouterDecision | None = None
    approval_gate: str | None = None
    stop_after_stage: str | None = None
    requires_parallel_decision: bool = False
    decision_engine: str | None = None
    coordinator_input_ready: bool = False
    reason: str = ""


@dataclass
class PipelineSkillSummary:
    """mstack-pipeline 최종 요약용 구조."""
    work_type: WorkType
    execution_mode: str
    stage_order: tuple[str, ...]
    decision_engine: str = "none"
    files_changed: tuple[str, ...] = ()
    blockers: list[str] = field(default_factory=list)
    coordinator_verdict: str | None = None
    remaining_gaps: tuple[str, ...] = ()
    retries_used: int = 0
    final_status: StageStatus = StageStatus.PENDING
    next_action: str = ""


@dataclass
class PipelineInvocationResult:
    """mstack-pipeline adapter의 통합 실행 결과."""
    classification: PipelineRequestClassifierResult
    pipeline_result: PipelineResult
    summary: PipelineSkillSummary
    rendered_summary: str


@dataclass
class GroupRoomMeta:
    """단체방 메타데이터."""
    room_name: str
    room_slug: str
    display_name: str
    created_at: str
    updated_at: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "GroupRoomMeta":
        return cls(**json.loads(text))


@dataclass
class GroupMessageEntry:
    """단체방 메시지/이벤트 로그 엔트리."""
    room_name: str
    room_slug: str
    event_type: str
    sender: str
    message: str
    timestamp: str
    session_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_jsonl(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, line: str) -> "GroupMessageEntry":
        return cls(**json.loads(line))


@dataclass
class MemoryEntry:
    """세션 메모리 단일 엔트리 (JSONL 1줄)"""
    session_id: str
    timestamp: str
    work_type: str
    summary: str
    files_changed: list[str] = field(default_factory=list)
    test_result: str = ""
    errors: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    pipeline_result: dict = field(default_factory=dict)

    def to_jsonl(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @classmethod
    def from_jsonl(cls, line: str) -> "MemoryEntry":
        return cls(**json.loads(line))


# ── TypedDict (JSON Schema 대응) ─────────────────────

class SkillFrontmatter(TypedDict):
    name: str
    persona: str
    description: str
    category: str

class HookDecision(TypedDict):
    """PreToolUse Hook stdout JSON"""
    decision: str
    reason: str
