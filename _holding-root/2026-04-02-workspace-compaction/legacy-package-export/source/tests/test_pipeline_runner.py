"""Tests for the real pipeline stage runner backends."""

from __future__ import annotations

from pathlib import Path
import subprocess

from core.parallel_executor import ParallelExecutionContext
from core.pipeline_generic_backends import build_generic_implement_backend
from core.pipeline_runner import build_stage_runner
from core.types import RouterDecision, RouterResult, StageResult, StageStatus


def _init_python_repo(
    tmp_path: Path,
    *,
    branch: str = "feature/pipeline",
    failing_test: bool = False,
) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    assertion = "4" if failing_test else "3"
    (tmp_path / "tests" / "test_app.py").write_text(
        (
            "from src.app import add\n\n\n"
            "def test_add() -> None:\n"
            f"    assert add(1, 2) == {assertion}\n"
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    if branch == "main":
        subprocess.run(["git", "branch", "-M", "main"], cwd=tmp_path, check=True)
    else:
        subprocess.run(["git", "checkout", "-b", branch], cwd=tmp_path, check=True, capture_output=True, text=True)
    return tmp_path


def test_stage_runner_plan_and_investigate_backends_emit_real_output(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    runner = build_stage_runner(repo, "Investigate CSV import failure")

    plan = runner("plan")
    investigate = runner("investigate")

    assert plan.status == StageStatus.PASSED
    assert "Phase 1" in plan.output
    assert "pytest tests/ -x" in plan.output
    assert investigate.status == StageStatus.PASSED
    assert "Hypotheses:" in investigate.output
    assert "Regression test:" in investigate.output


def test_stage_runner_implement_backend_adds_csv_import_scaffold(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    runner = build_stage_runner(repo, "Add CSV import end-to-end")

    implement = runner("implement")
    review = runner("review")

    assert implement.status == StageStatus.PASSED
    assert "applied python csv import scaffold" in implement.output
    assert implement.files_changed == ["src/csv_import.py", "tests/test_csv_import.py"]
    assert (repo / "src" / "csv_import.py").exists()
    assert (repo / "tests" / "test_csv_import.py").exists()
    assert review.status == StageStatus.PASSED
    assert "src/csv_import.py" in review.output
    assert "tests/test_csv_import.py" in review.output


def test_stage_runner_parallel_implement_backend_uses_worker_output(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    runner = build_stage_runner(
        repo,
        "Add CSV import end-to-end",
        dispatch_result=RouterResult(
            decision=RouterDecision.AGENT_TEAMS,
            reason="recipe supports parallel work",
            file_count=6,
            coordination_needed=True,
            estimated_cost_ratio=3.5,
        ),
    )

    implement = runner("implement")

    assert implement.status == StageStatus.PASSED
    assert "applied parallel python-csv-feature implementation with 2 workers" in implement.output
    assert "csv-module:" in implement.output
    assert "csv-tests:" in implement.output
    assert implement.files_changed == ["src/csv_import.py", "tests/test_csv_import.py"]


def test_stage_runner_implement_backend_skips_unmatched_request(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    runner = build_stage_runner(repo, "Write release notes for this project")

    implement = runner("implement")

    assert implement.status == StageStatus.SKIPPED
    assert implement.output == "no deterministic implementation recipe matched the request"
    assert implement.files_changed == []


def test_stage_runner_review_passes_with_clean_git_diff(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    runner = build_stage_runner(repo, "Review this feature")

    review = runner("review")

    assert review.status == StageStatus.PASSED
    assert review.output == "No changed files detected for review."
    assert review.errors == []


def test_stage_runner_review_detects_missing_tests_and_secrets(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    (repo / "src" / "app.py").write_text(
        "OPENAI_API_KEY = 'sk-abc1234567890'\n\ndef add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )
    runner = build_stage_runner(repo, "Review the modified app module")

    review = runner("review")

    assert review.status == StageStatus.FAILED
    assert any("Tests appear missing" in error for error in review.errors)
    assert "possible secret found in src/app.py" in review.errors


def test_stage_runner_review_ignores_parallel_artifacts_and_cache_files(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    (repo / ".mstack-parallel-artifacts" / "run1").mkdir(parents=True)
    (repo / ".mstack-parallel-artifacts" / "run1" / "stdout.txt").write_text("log\n", encoding="utf-8")
    (repo / "__pycache__").mkdir()
    (repo / "__pycache__" / "noise.pyc").write_bytes(b"noise")
    (repo / "src" / "app.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a - b\n",
        encoding="utf-8",
    )
    runner = build_stage_runner(repo, "Review app changes")

    review = runner("review")

    assert "src/app.py" in review.output
    assert ".mstack-parallel-artifacts" not in review.output
    assert "__pycache__" not in review.output


def test_stage_runner_qa_and_ship_succeed_on_feature_branch(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    runner = build_stage_runner(repo, "Ship this feature safely")

    qa = runner("qa")
    ship = runner("ship")
    retro = runner("retro")

    assert qa.status == StageStatus.PASSED
    assert "1 passed" in qa.output
    assert qa.errors == []
    assert ship.status == StageStatus.PASSED
    assert "branch: feature/pipeline" in ship.output
    assert "test: 1 passed" in ship.output
    assert ship.errors == []
    assert retro.status == StageStatus.PASSED
    assert "cost summary:" in retro.output


def test_stage_runner_qa_failure_surfaces_real_failure_line(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path, failing_test=True)
    runner = build_stage_runner(repo, "Validate failing test path")

    qa = runner("qa")

    assert qa.status == StageStatus.FAILED
    assert qa.output == "failed (pytest tests/ -x)"
    assert qa.errors
    assert qa.errors[0].startswith("FAILED tests")


def test_stage_runner_ship_blocks_protected_branch(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path, branch="main")
    runner = build_stage_runner(repo, "Deploy this release")

    ship = runner("ship")

    assert ship.status == StageStatus.FAILED
    assert "direct release from protected branch requires manual review" in ship.errors


def test_stage_runner_fail_hook_and_unknown_stage_are_exposed(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    hooked = build_stage_runner(repo, "Add CSV import", fail_stage="implement")
    normal = build_stage_runner(repo, "Add CSV import")

    failed = hooked("implement")
    unknown = normal("unknown")

    assert failed.status == StageStatus.FAILED
    assert failed.output == "implement failed by test hook"
    assert failed.errors == ["implement failed"]
    assert unknown.status == StageStatus.SKIPPED
    assert unknown.output == "no backend registered for unknown"


def test_stage_runner_uses_generic_implement_backend_for_unmatched_request(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)

    runner = build_stage_runner(
        repo,
        "Write release notes for this project",
        generic_implement_backend=build_generic_implement_backend("notes"),
    )

    implement = runner("implement")

    assert implement.status == StageStatus.FAILED
    assert implement.files_changed == ["IMPLEMENTATION_NOTES.md"]
    assert (repo / "IMPLEMENTATION_NOTES.md").exists()


def test_stage_runner_uses_external_parallel_executor_for_unmatched_request(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)

    class FakeParallelExecutor:
        capabilities = frozenset({RouterDecision.SUBAGENT, RouterDecision.AGENT_TEAMS})

        def execute(self, context: ParallelExecutionContext) -> StageResult:
            target = context.project_dir / "src" / "external_parallel.py"
            target.write_text("VALUE = 1\n", encoding="utf-8")
            return StageResult(
                stage="implement",
                status=StageStatus.PASSED,
                output=f"external executor handled {context.decision.value}",
                files_changed=["src/external_parallel.py"],
            )

    runner = build_stage_runner(
        repo,
        "Build an admin dashboard shell",
        dispatch_result=RouterResult(
            decision=RouterDecision.SUBAGENT,
            reason="single external worker",
            file_count=4,
            coordination_needed=False,
            estimated_cost_ratio=1.5,
        ),
        parallel_executor=FakeParallelExecutor(),
    )

    implement = runner("implement")

    assert implement.status == StageStatus.PASSED
    assert implement.output == "external executor handled subagent"
    assert implement.files_changed == ["src/external_parallel.py"]
    assert (repo / "src" / "external_parallel.py").exists()
