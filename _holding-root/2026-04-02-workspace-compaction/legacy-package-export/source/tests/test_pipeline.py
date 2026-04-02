"""tests/test_pipeline.py — pipeline.py 단위 테스트"""
from unittest.mock import patch
import pytest
from pathlib import Path
from core.types import WorkType, StageStatus, StageResult, PipelineResult
from core.pipeline import (
    PIPELINE_TEMPLATES,
    STAGE_TO_SKILL,
    AUTO_RETRY_STAGES,
    MAX_RETRIES,
    resolve_git_lock,
    MAX_LOCK_RETRIES,
    get_pipeline,
    should_retry,
    build_retry_stages,
    execute_pipeline,
    format_pipeline_summary,
    generate_dispatch_prompt,
)


# ── 파이프라인 템플릿 매핑 ──────────────────────────────


class TestPipelineTemplates:
    """PIPELINE_TEMPLATES 매핑 검증."""

    def test_feature_pipeline(self) -> None:
        stages = get_pipeline(WorkType.FEATURE)
        assert stages == ("plan", "implement", "review", "qa", "ship", "retro")

    def test_bugfix_pipeline(self) -> None:
        stages = get_pipeline(WorkType.BUGFIX)
        assert stages == ("investigate", "implement", "qa", "ship", "retro")

    def test_refactor_pipeline(self) -> None:
        stages = get_pipeline(WorkType.REFACTOR)
        assert stages == ("plan", "implement", "review", "qa", "ship", "retro")

    def test_test_pipeline(self) -> None:
        stages = get_pipeline(WorkType.TEST)
        assert stages == ("qa",)

    def test_deploy_pipeline(self) -> None:
        stages = get_pipeline(WorkType.DEPLOY)
        assert stages == ("ship", "qa", "retro")

    def test_retro_pipeline(self) -> None:
        stages = get_pipeline(WorkType.RETRO)
        assert stages == ("retro",)

    def test_all_work_types_have_template(self) -> None:
        for wt in WorkType:
            assert wt in PIPELINE_TEMPLATES, f"Missing template for {wt}"

    def test_templates_are_immutable(self) -> None:
        with pytest.raises(TypeError):
            PIPELINE_TEMPLATES[WorkType.FEATURE] = ("oops",)  # type: ignore[index]


# ── 스테이지 → 스킬 매핑 ──────────────────────────────


class TestStageToSkill:
    """STAGE_TO_SKILL 매핑 검증."""

    def test_plan_maps_to_mstack_plan(self) -> None:
        assert STAGE_TO_SKILL["plan"] == "mstack-plan"

    def test_implement_maps_to_none(self) -> None:
        assert STAGE_TO_SKILL["implement"] is None

    def test_qa_maps_to_mstack_qa(self) -> None:
        assert STAGE_TO_SKILL["qa"] == "mstack-qa"

    def test_all_pipeline_stages_mapped(self) -> None:
        all_stages = set()
        for stages in PIPELINE_TEMPLATES.values():
            all_stages.update(stages)
        for stage in all_stages:
            assert stage in STAGE_TO_SKILL, f"Missing skill mapping for {stage}"


# ── 재시도 로직 ──────────────────────────────────────


class TestRetryLogic:
    """should_retry, build_retry_stages 검증."""

    def test_qa_failed_triggers_retry(self) -> None:
        assert should_retry("qa", StageStatus.FAILED) is True

    def test_qa_passed_no_retry(self) -> None:
        assert should_retry("qa", StageStatus.PASSED) is False

    def test_non_qa_stage_no_retry(self) -> None:
        assert should_retry("review", StageStatus.FAILED) is False
        assert should_retry("ship", StageStatus.FAILED) is False

    def test_retry_stages_tuple(self) -> None:
        stages = build_retry_stages()
        assert stages == ("review", "fix", "qa")

    def test_max_retries_is_3(self) -> None:
        assert MAX_RETRIES == 3


# ── 파이프라인 실행 ──────────────────────────────────


def _make_runner(fail_stages: set[str] | None = None,
                 fail_until: int = 0):
    """테스트용 stage_runner 팩토리.

    Args:
        fail_stages: 실패할 스테이지 이름 집합
        fail_until: 이 횟수까지 qa가 실패 (이후 PASS)
    """
    call_count: dict[str, int] = {}

    def runner(stage: str) -> StageResult:
        call_count[stage] = call_count.get(stage, 0) + 1

        if fail_stages and stage in fail_stages:
            # qa는 fail_until 횟수까지만 실패
            if stage == "qa" and call_count[stage] > fail_until:
                return StageResult(stage=stage, status=StageStatus.PASSED)
            return StageResult(
                stage=stage, status=StageStatus.FAILED,
                errors=[f"{stage} failed"],
            )
        return StageResult(stage=stage, status=StageStatus.PASSED)

    return runner, call_count


class TestExecutePipeline:
    """execute_pipeline 실행 검증."""

    def test_all_stages_pass(self) -> None:
        runner, _ = _make_runner()
        result = execute_pipeline(WorkType.TEST, runner)
        assert result.final_status == StageStatus.PASSED
        assert len(result.stages) == 1
        assert result.stages[0].stage == "qa"

    def test_feature_pipeline_all_pass(self) -> None:
        runner, counts = _make_runner()
        result = execute_pipeline(WorkType.FEATURE, runner)
        assert result.final_status == StageStatus.PASSED
        assert len(result.stages) == 6
        stage_names = [s.stage for s in result.stages]
        assert stage_names == ["plan", "implement", "review", "qa", "ship", "retro"]

    def test_non_qa_failure_stops_pipeline(self) -> None:
        runner, _ = _make_runner(fail_stages={"implement"})
        result = execute_pipeline(WorkType.FEATURE, runner)
        assert result.final_status == StageStatus.FAILED
        # plan 통과 → implement 실패 → 중단
        assert len(result.stages) == 2

    def test_qa_failure_triggers_retry(self) -> None:
        # qa가 1회 실패 후 2번째에 PASS
        runner, counts = _make_runner(fail_stages={"qa"}, fail_until=1)
        result = execute_pipeline(WorkType.TEST, runner)
        assert result.final_status == StageStatus.PASSED
        assert result.total_retries == 1
        # 첫 qa(FAIL) + retry사이클(review,fix,qa) = 4 stages
        assert len(result.stages) == 4

    def test_qa_max_retries_exceeded(self) -> None:
        # qa가 항상 실패 (fail_until=999)
        runner, _ = _make_runner(fail_stages={"qa"}, fail_until=999)
        result = execute_pipeline(WorkType.TEST, runner)
        assert result.final_status == StageStatus.FAILED
        assert result.total_retries == MAX_RETRIES

    def test_skip_stages(self) -> None:
        runner, counts = _make_runner()
        result = execute_pipeline(
            WorkType.FEATURE, runner,
            skip_stages=frozenset({"plan", "retro"}),
        )
        assert result.final_status == StageStatus.PASSED
        skipped = [s for s in result.stages if s.status == StageStatus.SKIPPED]
        assert len(skipped) == 2
        assert {s.stage for s in skipped} == {"plan", "retro"}

    def test_approval_gate_stops_pipeline_and_marks_pending(self) -> None:
        runner, _ = _make_runner()
        result = execute_pipeline(
            WorkType.FEATURE,
            runner,
            approval_gate="plan",
        )
        stage_names = [s.stage for s in result.stages]
        skipped = [s.stage for s in result.stages if s.status == StageStatus.SKIPPED]
        assert stage_names == ["plan", "implement", "review", "qa", "ship", "retro"]
        assert skipped == ["implement", "review", "qa", "ship", "retro"]
        assert result.final_status == StageStatus.PENDING

    def test_pipeline_result_structure(self) -> None:
        runner, _ = _make_runner()
        result = execute_pipeline(WorkType.DEPLOY, runner)
        assert isinstance(result, PipelineResult)
        assert result.work_type == WorkType.DEPLOY
        assert isinstance(result.stages, list)
        assert all(isinstance(s, StageResult) for s in result.stages)

    def test_pipeline_aggregates_stage_files_changed(self) -> None:
        def runner(stage: str) -> StageResult:
            if stage == "implement":
                return StageResult(
                    stage=stage,
                    status=StageStatus.PASSED,
                    files_changed=["src/csv_import.py", "tests/test_csv_import.py"],
                )
            return StageResult(stage=stage, status=StageStatus.PASSED)

        result = execute_pipeline(WorkType.FEATURE, runner)
        assert result.files_changed == ["src/csv_import.py", "tests/test_csv_import.py"]


# ── 포맷 / 프롬프트 생성 ────────────────────────────


class TestFormatPipelineSummary:
    """format_pipeline_summary 포맷 검증."""

    def test_contains_status_icon(self) -> None:
        result = PipelineResult(
            work_type=WorkType.FEATURE,
            final_status=StageStatus.PASSED,
            stages=[StageResult(stage="qa", status=StageStatus.PASSED)],
        )
        summary = format_pipeline_summary(result)
        assert "✅" in summary
        assert "PASSED" in summary

    def test_failed_result_shows_cross(self) -> None:
        result = PipelineResult(
            work_type=WorkType.BUGFIX,
            final_status=StageStatus.FAILED,
            stages=[StageResult(
                stage="qa", status=StageStatus.FAILED,
                errors=["test_foo failed"],
            )],
        )
        summary = format_pipeline_summary(result)
        assert "❌" in summary
        assert "test_foo failed" in summary

    def test_files_changed_shown(self) -> None:
        result = PipelineResult(
            work_type=WorkType.FEATURE,
            final_status=StageStatus.PASSED,
            files_changed=["a.py", "b.py"],
        )
        summary = format_pipeline_summary(result)
        assert "Files changed: 2" in summary


class TestGenerateDispatchPrompt:
    """generate_dispatch_prompt 프롬프트 생성 검증."""

    def test_contains_work_type(self) -> None:
        prompt = generate_dispatch_prompt(WorkType.FEATURE, "plan content")
        assert "feature" in prompt

    def test_contains_plan_doc(self) -> None:
        prompt = generate_dispatch_prompt(WorkType.FEATURE, "implement login page")
        assert "implement login page" in prompt

    def test_contains_max_retries(self) -> None:
        prompt = generate_dispatch_prompt(WorkType.BUGFIX, "fix bug")
        assert str(MAX_RETRIES) in prompt

    def test_team_config_included(self) -> None:
        prompt = generate_dispatch_prompt(
            WorkType.FEATURE, "plan",
            team_config={"lead": "opus", "impl": "sonnet"},
        )
        assert "팀 구성" in prompt

    def test_plan_doc_truncated(self) -> None:
        long_plan = "x" * 5000
        prompt = generate_dispatch_prompt(WorkType.FEATURE, long_plan)
        # plan_doc[:2000] 적용 확인
        assert "x" * 2000 in prompt
        assert "x" * 2001 not in prompt


class TestResolveGitLock:
    """resolve_git_lock 검증."""

    def test_no_lock_returns_true(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        assert resolve_git_lock(git_dir) is True

    def test_index_lock_resolved(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "index.lock").touch()
        assert resolve_git_lock(git_dir) is True
        assert not (git_dir / "index.lock").exists()
        assert (git_dir / "index.lock.bak").exists()

    def test_head_lock_resolved(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD.lock").touch()
        assert resolve_git_lock(git_dir) is True
        assert not (git_dir / "HEAD.lock").exists()
        assert (git_dir / "HEAD.lock.bak").exists()

    def test_both_locks_resolved(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "index.lock").touch()
        (git_dir / "HEAD.lock").touch()
        assert resolve_git_lock(git_dir) is True
        assert not (git_dir / "index.lock").exists()
        assert not (git_dir / "HEAD.lock").exists()
        assert (git_dir / "index.lock.bak").exists()
        assert (git_dir / "HEAD.lock.bak").exists()

    def test_nonexistent_git_dir_returns_true(self, tmp_path: Path) -> None:
        """git_dir 자체가 없으면 lock도 없으므로 True."""
        git_dir = tmp_path / "nonexistent"
        assert resolve_git_lock(git_dir) is True

    def test_default_git_dir_is_dot_git(self) -> None:
        """git_dir=None이면 Path('.git')을 기본값으로 사용."""
        with patch("core.pipeline.os.rename") as mock_rename:
            # .git 디렉토리가 존재하지 않으면 lock도 없으므로 True
            result = resolve_git_lock(None)
            assert result is True

    def test_oserror_returns_false(self, tmp_path: Path) -> None:
        """os.rename이 OSError를 발생시키면 False를 반환."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "index.lock").touch()
        with patch("core.pipeline.os.rename", side_effect=OSError("permission denied")):
            result = resolve_git_lock(git_dir)
            assert result is False
            # lock 파일은 그대로 남아있어야 함
            assert (git_dir / "index.lock").exists()

    def test_oserror_partial_resolution(self, tmp_path: Path) -> None:
        """첫 번째 lock은 성공, 두 번째에서 OSError → False."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "index.lock").touch()
        (git_dir / "HEAD.lock").touch()

        call_count = 0
        original_rename = __import__("os").rename

        def selective_fail(src: str, dst: str) -> None:
            nonlocal call_count
            call_count += 1
            if "HEAD.lock" in src:
                raise OSError("permission denied")
            original_rename(src, dst)

        with patch("core.pipeline.os.rename", side_effect=selective_fail):
            result = resolve_git_lock(git_dir)
            assert result is False
            # index.lock은 해결됨, HEAD.lock은 남아있음
            assert not (git_dir / "index.lock").exists()
            assert (git_dir / "HEAD.lock").exists()
