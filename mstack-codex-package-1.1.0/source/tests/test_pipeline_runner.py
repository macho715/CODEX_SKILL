"""Tests for the real pipeline stage runner backends."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

from core.pipeline_generic_backends import build_generic_implement_backend
from core.pipeline_runner import _build_command_env, _select_summary_line, build_stage_runner
from core.types import StageResult, StageStatus
import pytest


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


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific PATH behavior")
def test_build_command_env_sanitizes_windows_node_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_python_repo(tmp_path)
    fake_path = r"C:\tool-a;C:\tool-b"
    monkeypatch.setenv("PATH", fake_path)
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    monkeypatch.setenv("APPDATA", r"C:\Users\Test\AppData\Roaming")

    def fake_which(name: str) -> str | None:
        mapping = {
            "node": r"C:\Program Files\nodejs\node.exe",
            "git": r"C:\Program Files\Git\cmd\git.exe",
        }
        return mapping.get(name)

    monkeypatch.setattr("core.pipeline_runner.shutil.which", fake_which)

    node_env = _build_command_env(repo, "npm test")
    node_parts = node_env["PATH"].split(os.pathsep)
    assert node_parts[:2] == [str(repo), str(repo / "node_modules" / ".bin")]
    assert r"C:\Program Files\nodejs" in node_parts
    assert fake_path not in node_env["PATH"]

    python_env = _build_command_env(repo, "pytest tests/ -x")
    assert python_env["PATH"] == f"{repo}{os.pathsep}{fake_path}"


def test_select_summary_line_prefers_node_tap_pass_counts() -> None:
    output = "\n".join([
        "TAP version 13",
        "ℹ tests 2",
        "ℹ suites 0",
        "ℹ pass 2",
        "ℹ fail 0",
        "ℹ duration_ms 11440.3065",
    ])

    assert _select_summary_line(output) == "2 passed"


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
