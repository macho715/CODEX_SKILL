"""Tests for the mstack-pipeline adapter layer."""

from __future__ import annotations

from core.pipeline_adapter import (
    build_pipeline_skill_summary,
    classify_pipeline_request,
    render_pipeline_skill_summary,
    run_pipeline_request,
)
from core.types import (
    PipelineRequestClassifierInput,
    PipelineResult,
    RouterDecision,
    RouterResult,
    StageResult,
    StageStatus,
    WorkType,
)


def test_classify_pipeline_request_defaults_to_feature() -> None:
    result = classify_pipeline_request(
        PipelineRequestClassifierInput(request="Add CSV import end-to-end")
    )
    assert result.work_type == WorkType.FEATURE
    assert result.stage_order == ("plan", "implement", "review", "qa", "ship", "retro")
    assert result.reason == "defaulted to feature workflow"


def test_classify_pipeline_request_detects_bugfix_and_dispatch_mode() -> None:
    dispatch = RouterResult(
        decision=RouterDecision.AGENT_TEAMS,
        reason="cross-module",
        file_count=6,
        coordination_needed=True,
        estimated_cost_ratio=3.5,
    )
    result = classify_pipeline_request(
        PipelineRequestClassifierInput(
            request="Fix crash in CSV import and investigate root cause",
            dispatch_result=dispatch,
        )
    )
    assert result.work_type == WorkType.BUGFIX
    assert result.execution_mode == RouterDecision.AGENT_TEAMS
    assert result.stage_order == ("investigate", "implement", "qa", "ship", "retro")
    assert result.requires_parallel_decision is False


def test_classify_pipeline_request_detects_stop_after_stage_and_approval_gate() -> None:
    result = classify_pipeline_request(
        PipelineRequestClassifierInput(
            request="Plan this feature and stop after qa with approval",
        )
    )
    assert result.work_type == WorkType.FEATURE
    assert result.stop_after_stage == "qa"
    assert result.approval_gate == "qa"


def test_classify_pipeline_request_detects_refactor_and_plan_gate() -> None:
    result = classify_pipeline_request(
        PipelineRequestClassifierInput(
            request="Refactor the import flow and pause after plan",
            approval_gate_requested=True,
        )
    )
    assert result.work_type == WorkType.REFACTOR
    assert result.approval_gate == "plan"
    assert result.stop_after_stage == "plan"


def test_build_pipeline_skill_summary_derives_blockers_from_pipeline_result() -> None:
    classification = classify_pipeline_request(
        PipelineRequestClassifierInput(request="Fix crash in CSV import")
    )
    pipeline_result = PipelineResult(
        work_type=WorkType.BUGFIX,
        stages=[
            StageResult(stage="investigate", status=StageStatus.PASSED),
            StageResult(stage="implement", status=StageStatus.FAILED, errors=["syntax error"]),
        ],
        total_retries=1,
        final_status=StageStatus.FAILED,
    )
    summary = build_pipeline_skill_summary(classification, pipeline_result)
    assert summary.execution_mode == "direct"
    assert summary.decision_engine == "none"
    assert summary.files_changed == ()
    assert summary.blockers == ["implement: syntax error"]
    assert summary.retries_used == 1
    assert summary.next_action == "Resolve the listed blocker(s) and rerun the pipeline."


def test_render_pipeline_skill_summary_contains_required_fields() -> None:
    classification = classify_pipeline_request(
        PipelineRequestClassifierInput(
            request="Deploy this release candidate",
            dispatch_result=RouterResult(
                decision=RouterDecision.SUBAGENT,
                reason="bounded work",
                file_count=3,
                coordination_needed=False,
                estimated_cost_ratio=1.5,
            ),
        )
    )
    pipeline_result = PipelineResult(
        work_type=WorkType.DEPLOY,
        stages=[
            StageResult(stage="ship", status=StageStatus.PASSED, files_changed=["src/release.py"]),
            StageResult(stage="qa", status=StageStatus.PASSED),
            StageResult(stage="retro", status=StageStatus.PASSED),
        ],
        total_retries=0,
        final_status=StageStatus.PASSED,
        files_changed=["src/release.py"],
    )
    summary = build_pipeline_skill_summary(classification, pipeline_result)
    rendered = render_pipeline_skill_summary(summary)
    assert "## MStack Pipeline Summary" in rendered
    assert "- work type: deploy" in rendered
    assert "- execution mode: subagent" in rendered
    assert "- stage order: ship -> qa -> retro" in rendered
    assert "- files changed: src/release.py" in rendered
    assert "- blockers: none" in rendered
    assert "- final status: passed" in rendered


def test_run_pipeline_request_executes_full_adapter_flow() -> None:
    def runner(stage: str) -> StageResult:
        return StageResult(stage=stage, status=StageStatus.PASSED)

    result = run_pipeline_request(
        PipelineRequestClassifierInput(request="Add CSV import end-to-end"),
        runner,
    )

    assert result.classification.work_type == WorkType.FEATURE
    assert result.pipeline_result.final_status == StageStatus.PASSED
    assert result.summary.execution_mode == "direct"
    assert result.classification.requires_parallel_decision is False
    assert "- files changed: none" in result.rendered_summary
    assert "- stage order: plan -> implement -> review -> qa -> ship -> retro" in result.rendered_summary


def test_classify_pipeline_request_detects_parallel_decision_requirements() -> None:
    dispatch = RouterResult(
        decision=RouterDecision.AGENT_TEAMS,
        reason="cross-module",
        file_count=7,
        coordination_needed=True,
        estimated_cost_ratio=3.5,
    )
    result = classify_pipeline_request(
        PipelineRequestClassifierInput(
            request="Compare 3 rollout options for this high-risk refactor",
            dispatch_result=dispatch,
        )
    )

    assert result.work_type == WorkType.REFACTOR
    assert result.requires_parallel_decision is True
    assert result.decision_engine == "pipeline-coordinator"
    assert result.coordinator_input_ready is True


def test_render_pipeline_skill_summary_includes_coordinator_fields_when_used() -> None:
    classification = classify_pipeline_request(
        PipelineRequestClassifierInput(
            request="Compare 3 rollout options for this high-risk refactor",
            dispatch_result=RouterResult(
                decision=RouterDecision.AGENT_TEAMS,
                reason="cross-module",
                file_count=7,
                coordination_needed=True,
                estimated_cost_ratio=3.5,
            ),
        )
    )
    pipeline_result = PipelineResult(
        work_type=WorkType.REFACTOR,
        stages=[StageResult(stage="plan", status=StageStatus.PASSED)],
        total_retries=0,
        final_status=StageStatus.PASSED,
    )
    summary = build_pipeline_skill_summary(
        classification,
        pipeline_result,
        coordinator_verdict="AMBER",
        remaining_gaps=("document rollback plan",),
    )

    rendered = render_pipeline_skill_summary(summary)
    assert "- decision engine: pipeline-coordinator" in rendered
    assert "- coordinator verdict: AMBER" in rendered
    assert "- remaining gaps: document rollback plan" in rendered


def test_build_pipeline_skill_summary_blocks_ship_when_coordinator_verdict_fails() -> None:
    classification = classify_pipeline_request(
        PipelineRequestClassifierInput(
            request="Compare 3 deployment options for this release",
            dispatch_result=RouterResult(
                decision=RouterDecision.AGENT_TEAMS,
                reason="release trade-offs",
                file_count=6,
                coordination_needed=True,
                estimated_cost_ratio=3.5,
            ),
        )
    )
    pipeline_result = PipelineResult(
        work_type=WorkType.DEPLOY,
        stages=[StageResult(stage="ship", status=StageStatus.PASSED)],
        total_retries=0,
        final_status=StageStatus.PASSED,
    )

    summary = build_pipeline_skill_summary(
        classification,
        pipeline_result,
        coordinator_verdict="FAIL",
        remaining_gaps=("collect rollback evidence",),
    )

    assert summary.final_status == StageStatus.PENDING
    assert summary.blockers[-1] == "pipeline-coordinator: verifier FAIL"
    assert summary.next_action == "Resolve the coordinator gaps before ship."


def test_run_pipeline_request_respects_stop_after_stage() -> None:
    seen: list[str] = []

    def runner(stage: str) -> StageResult:
        seen.append(stage)
        return StageResult(stage=stage, status=StageStatus.PASSED)

    result = run_pipeline_request(
        PipelineRequestClassifierInput(
            request="Plan this feature and stop after qa with approval",
        ),
        runner,
    )

    assert result.classification.stop_after_stage == "qa"
    assert seen == ["plan", "implement", "review", "qa"]
    assert result.pipeline_result.final_status == StageStatus.PENDING
    assert result.summary.next_action == "Await approval after qa before continuing."
    skipped = [s.stage for s in result.pipeline_result.stages if s.status == StageStatus.SKIPPED]
    assert skipped == ["ship", "retro"]


def test_run_pipeline_request_stops_at_approval_gate() -> None:
    seen: list[str] = []

    def runner(stage: str) -> StageResult:
        seen.append(stage)
        return StageResult(stage=stage, status=StageStatus.PASSED)

    result = run_pipeline_request(
        PipelineRequestClassifierInput(
            request="Add CSV import end-to-end",
            approval_gate_requested=True,
        ),
        runner,
    )

    assert result.classification.approval_gate == "plan"
    assert seen == ["plan"]
    assert result.pipeline_result.final_status == StageStatus.PENDING
    assert result.summary.next_action == "Await approval after plan before continuing."
    skipped = [s.stage for s in result.pipeline_result.stages if s.status == StageStatus.SKIPPED]
    assert skipped == ["implement", "review", "qa", "ship", "retro"]


def test_run_pipeline_request_propagates_failures_into_summary() -> None:
    def runner(stage: str) -> StageResult:
        if stage == "implement":
            return StageResult(stage=stage, status=StageStatus.FAILED, errors=["compile error"])
        return StageResult(stage=stage, status=StageStatus.PASSED)

    result = run_pipeline_request(
        PipelineRequestClassifierInput(request="Add CSV import end-to-end"),
        runner,
    )

    assert result.pipeline_result.final_status == StageStatus.FAILED
    assert result.summary.blockers == ["implement: compile error"]
    assert "Resolve the listed blocker(s) and rerun the pipeline." in result.rendered_summary
