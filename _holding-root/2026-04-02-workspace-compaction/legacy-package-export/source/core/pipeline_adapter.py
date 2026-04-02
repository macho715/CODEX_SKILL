"""Adapter utilities that connect mstack-pipeline prompts to core/pipeline.py."""

from __future__ import annotations

from types import MappingProxyType
from typing import Callable

from .pipeline import execute_pipeline, get_pipeline
from .types import (
    PipelineInvocationResult,
    PipelineRequestClassifierInput,
    PipelineRequestClassifierResult,
    PipelineResult,
    PipelineSkillSummary,
    RouterDecision,
    RouterResult,
    StageResult,
    StageStatus,
    WorkType,
)


KEYWORD_GROUPS: MappingProxyType[str, tuple[str, ...]] = MappingProxyType({
    "deploy": ("deploy", "release", "ship it", "배포", "릴리스", "merge"),
    "retro": ("retro", "retrospective", "postmortem", "회고"),
    "bugfix": ("bug", "bugfix", "fix crash", "failure", "error", "crash", "regression", "버그", "장애", "에러"),
    "test": ("test", "qa", "validate", "verification", "smoke", "검증", "테스트"),
    "refactor": ("refactor", "cleanup", "restructure", "리팩터"),
})

STAGE_ALIAS_MAP: MappingProxyType[str, tuple[str, ...]] = MappingProxyType({
    "plan": ("plan", "계획"),
    "review": ("review", "리뷰"),
    "qa": ("qa", "test", "검증", "테스트"),
    "ship": ("ship", "deploy", "release", "배포"),
    "retro": ("retro", "retrospective", "회고"),
    "investigate": ("investigate", "bugfix investigation", "조사"),
})

APPROVAL_KEYWORDS = ("approval", "approve", "승인", "checkpoint", "gate")
STOP_AFTER_PREFIXES = ("stop after ", "pause after ", "after ", "까지만")


def classify_pipeline_request(
    payload: PipelineRequestClassifierInput,
) -> PipelineRequestClassifierResult:
    """Classify a free-form request into a pipeline work type and controls."""
    request = payload.request.strip()
    lowered = request.lower()
    stop_after_stage = _detect_stop_after_stage(lowered)
    work_type, reason = _detect_work_type(_strip_stop_after_phrases(lowered))
    stage_order = get_pipeline(work_type)
    execution_mode = payload.dispatch_result.decision if payload.dispatch_result else None
    required_execution_mode = _detect_required_execution_mode(payload.dispatch_result)
    approval_requested = payload.approval_gate_requested or _has_any(lowered, APPROVAL_KEYWORDS)
    approval_gate = _select_approval_gate(work_type, approval_requested, stop_after_stage)

    return PipelineRequestClassifierResult(
        request=request,
        work_type=work_type,
        stage_order=stage_order,
        execution_mode=execution_mode,
        required_execution_mode=required_execution_mode,
        approval_gate=approval_gate,
        stop_after_stage=stop_after_stage,
        allow_single_agent_fallback=payload.allow_single_agent_fallback,
        reason=reason,
    )


def build_pipeline_skill_summary(
    classification: PipelineRequestClassifierResult,
    result: PipelineResult,
    *,
    blockers: list[str] | None = None,
    next_action: str | None = None,
) -> PipelineSkillSummary:
    """Build a mstack-pipeline summary from a pipeline result."""
    derived_blockers = blockers[:] if blockers else _collect_blockers(result)
    return PipelineSkillSummary(
        work_type=result.work_type,
        execution_mode=_format_execution_mode(classification.execution_mode),
        required_execution_mode=_format_execution_mode(classification.required_execution_mode),
        stage_order=classification.stage_order,
        files_changed=tuple(result.files_changed),
        blockers=derived_blockers,
        blocked_reason=classification.blocked_reason,
        retries_used=result.total_retries,
        final_status=result.final_status,
        next_action=next_action or _derive_next_action(result, derived_blockers),
    )


def render_pipeline_skill_summary(summary: PipelineSkillSummary) -> str:
    """Render the final mstack-pipeline summary in the documented shape."""
    blockers = ", ".join(summary.blockers) if summary.blockers else "none"
    files_changed = ", ".join(summary.files_changed) if summary.files_changed else "none"
    stage_order = " -> ".join(summary.stage_order)
    return "\n".join([
        "## MStack Pipeline Summary",
        f"- work type: {summary.work_type.value}",
        f"- execution mode: {summary.execution_mode}",
        f"- required execution mode: {summary.required_execution_mode or 'none'}",
        f"- stage order: {stage_order}",
        f"- files changed: {files_changed}",
        f"- blockers: {blockers}",
        f"- blocked reason: {summary.blocked_reason or 'none'}",
        f"- retries used: {summary.retries_used}",
        f"- final status: {summary.final_status.value}",
        f"- next action: {summary.next_action}",
    ])


def run_pipeline_request(
    payload: PipelineRequestClassifierInput,
    stage_runner: Callable[[str], StageResult],
    *,
    skip_stages: frozenset[str] | None = None,
    blockers: list[str] | None = None,
    next_action: str | None = None,
) -> PipelineInvocationResult:
    """Run the full mstack-pipeline adapter flow for one request."""
    classification = classify_pipeline_request(payload)
    execution_block = _resolve_execution_block(classification, payload.executor_capabilities)
    if execution_block is not None:
        classification.blocked_reason = execution_block
        if classification.allow_single_agent_fallback:
            classification.execution_mode = RouterDecision.SINGLE
        else:
            pipeline_result = _build_blocked_pipeline_result(classification, execution_block)
            summary = build_pipeline_skill_summary(
                classification,
                pipeline_result,
                blockers=[execution_block],
                next_action=next_action,
            )
            rendered = render_pipeline_skill_summary(summary)
            return PipelineInvocationResult(
                classification=classification,
                pipeline_result=pipeline_result,
                summary=summary,
                rendered_summary=rendered,
            )

    combined_skip = _build_effective_skip_stages(
        classification.stage_order,
        classification.stop_after_stage,
        skip_stages or frozenset(),
    )
    pipeline_result = execute_pipeline(
        classification.work_type,
        stage_runner,
        skip_stages=combined_skip,
        approval_gate=classification.approval_gate,
    )
    summary = build_pipeline_skill_summary(
        classification,
        pipeline_result,
        blockers=blockers,
        next_action=next_action,
    )
    rendered = render_pipeline_skill_summary(summary)
    return PipelineInvocationResult(
        classification=classification,
        pipeline_result=pipeline_result,
        summary=summary,
        rendered_summary=rendered,
    )


def _build_blocked_pipeline_result(
    classification: PipelineRequestClassifierResult,
    blocked_reason: str,
) -> PipelineResult:
    """Build a pipeline result for execution blocked before stage execution."""
    stage_name = classification.stop_after_stage or classification.stage_order[0]
    return PipelineResult(
        work_type=classification.work_type,
        stages=[
            StageResult(
                stage=stage_name,
                status=StageStatus.BLOCKED,
                output=blocked_reason,
                errors=[blocked_reason],
            )
        ],
        total_retries=0,
        final_status=StageStatus.BLOCKED,
    )


def _detect_work_type(lowered_request: str) -> tuple[WorkType, str]:
    """Detect the pipeline work type from a lowered request string."""
    if _has_any(lowered_request, KEYWORD_GROUPS["deploy"]):
        return WorkType.DEPLOY, "matched deploy/release keywords"
    if _has_any(lowered_request, KEYWORD_GROUPS["retro"]):
        return WorkType.RETRO, "matched retrospective keywords"
    if _has_any(lowered_request, KEYWORD_GROUPS["bugfix"]):
        return WorkType.BUGFIX, "matched bugfix/failure keywords"
    if _has_any(lowered_request, KEYWORD_GROUPS["test"]):
        return WorkType.TEST, "matched test/validation keywords"
    if _has_any(lowered_request, KEYWORD_GROUPS["refactor"]):
        return WorkType.REFACTOR, "matched refactor keywords"
    return WorkType.FEATURE, "defaulted to feature workflow"


def _detect_required_execution_mode(dispatch_result: RouterResult | None) -> RouterDecision | None:
    """Return the required execution mode implied by dispatch."""
    if dispatch_result is None or dispatch_result.decision == RouterDecision.SINGLE:
        return None
    return dispatch_result.decision


def _select_approval_gate(
    work_type: WorkType,
    approval_requested: bool,
    stop_after_stage: str | None,
) -> str | None:
    """Select an approval gate when the request asks for one."""
    if not approval_requested:
        return None
    if stop_after_stage is not None:
        return stop_after_stage
    if work_type in (WorkType.FEATURE, WorkType.REFACTOR):
        return "plan"
    return get_pipeline(work_type)[0]


def _detect_stop_after_stage(lowered_request: str) -> str | None:
    """Detect an explicit stop-after stage from the request."""
    for stage, aliases in STAGE_ALIAS_MAP.items():
        for alias in aliases:
            if any(
                f"{prefix}{alias}" in lowered_request
                for prefix in STOP_AFTER_PREFIXES[:3]
            ):
                return stage
            if f"{alias}까지만" in lowered_request:
                return stage
    return None


def _strip_stop_after_phrases(lowered_request: str) -> str:
    """Remove stop-after hints so they do not affect work-type detection."""
    stripped = lowered_request
    for aliases in STAGE_ALIAS_MAP.values():
        for alias in aliases:
            for prefix in STOP_AFTER_PREFIXES[:3]:
                stripped = stripped.replace(f"{prefix}{alias}", "")
            stripped = stripped.replace(f"{alias}까지만", "")
    return stripped


def _collect_blockers(result: PipelineResult) -> list[str]:
    """Collect blocker messages from failed stages."""
    blockers: list[str] = []
    for stage in result.stages:
        if stage.status not in {StageStatus.FAILED, StageStatus.BLOCKED}:
            continue
        if stage.errors:
            blockers.extend(f"{stage.stage}: {error}" for error in stage.errors[:2])
        else:
            blockers.append(f"{stage.stage}: failed without error details")
    return blockers


def _build_effective_skip_stages(
    stage_order: tuple[str, ...],
    stop_after_stage: str | None,
    initial_skip: frozenset[str],
) -> frozenset[str]:
    """Build the skip set for execute_pipeline including stop-after behavior."""
    if stop_after_stage is None or stop_after_stage not in stage_order:
        return initial_skip
    stop_index = stage_order.index(stop_after_stage)
    trailing = frozenset(stage_order[stop_index + 1:])
    return initial_skip.union(trailing)


def _derive_next_action(result: PipelineResult, blockers: list[str]) -> str:
    """Derive the next action from the pipeline result."""
    if result.final_status == StageStatus.PASSED:
        if result.work_type == WorkType.RETRO:
            return "Share the retrospective or close the task."
        if result.work_type == WorkType.DEPLOY:
            return "Proceed with release handoff or post-deploy monitoring."
        return "Proceed to the next manual checkpoint or close the task."

    if result.final_status == StageStatus.FAILED:
        if blockers:
            return "Resolve the listed blocker(s) and rerun the pipeline."
        return "Inspect the failed stage and rerun the pipeline."

    if result.final_status == StageStatus.BLOCKED:
        if blockers:
            return "Provide the required executor capability or approve a single-agent fallback."
        return "Resolve the execution blocker before rerunning the pipeline."

    if result.final_status == StageStatus.PENDING:
        approval_stage = _find_approval_stage(result)
        if approval_stage is not None:
            return f"Await approval after {approval_stage} before continuing."

    return "Review the incomplete pipeline state before continuing."


def _format_execution_mode(decision: RouterDecision | None) -> str:
    """Format the execution mode for user-facing summaries."""
    if decision is None:
        return "direct"
    return decision.value


def _resolve_execution_block(
    classification: PipelineRequestClassifierResult,
    executor_capabilities: frozenset[RouterDecision],
) -> str | None:
    """Return a blocker when required execution mode is unavailable."""
    required = classification.required_execution_mode
    if required is None:
        return None
    if required in executor_capabilities:
        return None
    if classification.allow_single_agent_fallback:
        return (
            f"{required.value} executor unavailable; proceeding with approved single-agent fallback"
        )
    return f"{required.value} executor unavailable and single-agent fallback not approved"


def _find_approval_stage(result: PipelineResult) -> str | None:
    """Infer the approval stage from skipped outputs emitted by execute_pipeline."""
    for stage in result.stages:
        if stage.status != StageStatus.SKIPPED:
            continue
        if not stage.output.startswith("awaiting approval after "):
            continue
        return stage.output.removeprefix("awaiting approval after ").strip() or None
    return None


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    """Return True when any keyword appears in the input text."""
    return any(keyword in text for keyword in keywords)
