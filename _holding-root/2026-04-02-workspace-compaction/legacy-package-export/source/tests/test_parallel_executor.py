"""Tests for external parallel executor helpers."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

from core.parallel_executor import (
    CodexExecParallelExecutor,
    ParallelExecutionContext,
    build_worker_prompt,
    build_codex_exec_parallel_executor,
    plan_generic_parallel_tasks,
)
from core.pipeline_recipes import ParallelImplementTask
from core.types import RouterDecision, StageStatus


def test_build_worker_prompt_includes_owned_paths_and_validation() -> None:
    prompt = build_worker_prompt(
        "Implement the summary feature",
        ParallelImplementTask(
            worker_name="code-owner",
            summary="Handle src changes",
            writes=(),
            owned_paths=("src", "tests/test_app.py"),
        ),
        validation_command="pytest tests/ -x",
        failure_excerpt="FAILED tests/test_app.py::test_add",
    )

    assert "Task request: Implement the summary feature" in prompt
    assert "- src" in prompt
    assert "- tests/test_app.py" in prompt
    assert "Current failing evidence:" in prompt
    assert "FAILED tests/test_app.py::test_add" in prompt
    assert "Preferred validation command: pytest tests/ -x" in prompt
    assert "Do not use sys.path.insert" in prompt
    assert "Keep imports package-safe" in prompt


def test_build_worker_prompt_warns_tests_only_worker_not_to_compensate() -> None:
    prompt = build_worker_prompt(
        "Implement the summary feature",
        ParallelImplementTask(
            worker_name="tests-owner",
            summary="Handle tests only",
            writes=(),
            owned_paths=("tests/test_summary.py",),
        ),
    )

    assert "Do not rewrite tests to compensate for broken source behavior" in prompt


def test_plan_generic_parallel_tasks_splits_src_tests_docs(tmp_path: Path) -> None:
    for name in ("src", "tests", "docs"):
        (tmp_path / name).mkdir()

    tasks = plan_generic_parallel_tasks(
        tmp_path,
        "Add reporting support",
        RouterDecision.AGENT_TEAMS,
        ["src", "tests", "docs"],
    )

    assert tasks is not None
    assert [task.worker_name for task in tasks] == ["code-owner", "docs-owner"]
    assert tasks[0].owned_paths == ("src", "tests")
    assert tasks[1].owned_paths == ("docs",)


def test_plan_generic_parallel_tasks_prefers_plan_file_targets(tmp_path: Path) -> None:
    (tmp_path / "plan.md").write_text(
        "\n".join([
            "# Approved Plan",
            "",
            "- File targets:",
            "  - `src/summary.py`",
            "  - `src/__init__.py`",
            "  - `tests/test_summary.py`",
            "  - `docs/summary.md`",
            "  - `pyproject.toml`",
            "",
        ]),
        encoding="utf-8",
    )
    for name in ("src", "tests", "docs"):
        (tmp_path / name).mkdir()

    tasks = plan_generic_parallel_tasks(
        tmp_path,
        "Finish normalized summary feature",
        RouterDecision.AGENT_TEAMS,
        ["src", "tests", "docs"],
    )

    assert tasks is not None
    subagent_tasks = plan_generic_parallel_tasks(
        tmp_path,
        "Finish normalized summary feature",
        RouterDecision.SUBAGENT,
        ["src", "tests", "docs"],
    )
    assert subagent_tasks is not None
    assert len(subagent_tasks) == 1
    assert subagent_tasks[0].worker_name == "subagent-owner"
    assert subagent_tasks[0].owned_paths == (
        "src/summary.py",
        "src/__init__.py",
        "tests/test_summary.py",
        "docs/summary.md",
        "pyproject.toml",
    )
    assert [task.worker_name for task in tasks] == ["code-owner", "docs-owner"]
    assert tasks[0].owned_paths == (
        "src/summary.py",
        "src/__init__.py",
        "tests/test_summary.py",
    )
    assert tasks[1].owned_paths == ("docs/summary.md",)


def test_plan_generic_parallel_tasks_returns_none_when_no_safe_second_group(tmp_path: Path) -> None:
    (tmp_path / "plan.md").write_text(
        "\n".join([
            "# Approved Plan",
            "",
            "- File targets:",
            "  - `src/summary.py`",
            "  - `tests/test_summary.py`",
            "",
        ]),
        encoding="utf-8",
    )
    for name in ("src", "tests"):
        (tmp_path / name).mkdir()

    tasks = plan_generic_parallel_tasks(
        tmp_path,
        "Finish normalized summary feature",
        RouterDecision.AGENT_TEAMS,
        ["src", "tests"],
    )

    assert tasks is None


def test_plan_generic_parallel_tasks_includes_meta_when_request_requires_config(tmp_path: Path) -> None:
    (tmp_path / "plan.md").write_text(
        "\n".join([
            "# Approved Plan",
            "",
            "- File targets:",
            "  - `src/summary.py`",
            "  - `tests/test_summary.py`",
            "  - `pyproject.toml`",
            "  - `docs/summary.md`",
            "",
        ]),
        encoding="utf-8",
    )
    for name in ("src", "tests", "docs"):
        (tmp_path / name).mkdir()

    tasks = plan_generic_parallel_tasks(
        tmp_path,
        "Fix import path and pyproject config for normalized summary feature",
        RouterDecision.AGENT_TEAMS,
        ["src", "tests", "docs"],
    )

    assert tasks is not None
    assert tasks[0].owned_paths == ("src/summary.py", "tests/test_summary.py", "pyproject.toml")


def test_codex_exec_parallel_executor_applies_worker_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    launcher = tmp_path / "fake_codex.py"
    launcher.write_text(
        "\n".join([
            "from __future__ import annotations",
            "from pathlib import Path",
            "import re",
            "import sys",
            "",
            "args = sys.argv[1:]",
            "cwd = Path(args[args.index('-C') + 1])",
            "output_path = Path(args[args.index('-o') + 1])",
            "prompt = sys.stdin.read() if args[-1] == '-' else args[-1]",
            "matches = re.findall(r'^- (.+)$', prompt, flags=re.MULTILINE)",
            "target = cwd / matches[0]",
            "target.parent.mkdir(parents=True, exist_ok=True)",
            "target.write_text('generated = True\\n', encoding='utf-8')",
            "output_path.write_text('ok\\n', encoding='utf-8')",
            "",
        ]),
        encoding="utf-8",
    )

    executor = CodexExecParallelExecutor((sys.executable, str(launcher)))
    result = executor.execute(
        ParallelExecutionContext(
            project_dir=repo,
            request="Add generated module",
            decision=RouterDecision.AGENT_TEAMS,
            validation_command=None,
            tasks=(
                ParallelImplementTask(
                    worker_name="code-owner",
                    summary="Create generated module",
                    writes=(),
                    owned_paths=("src/generated.py",),
                ),
            ),
        )
    )

    assert result.status == StageStatus.PASSED
    assert result.files_changed == ["src/generated.py"]
    assert (repo / "src" / "generated.py").read_text(encoding="utf-8") == "generated = True\n"
    artifact_dirs = list((repo / ".mstack-parallel-artifacts").glob("*"))
    assert artifact_dirs
    worker_artifacts = artifact_dirs[0] / "code-owner"
    assert (worker_artifacts / "prompt.txt").exists()
    assert (worker_artifacts / "stdout.txt").exists()
    assert (worker_artifacts / "changed_paths.json").exists()


def test_codex_exec_parallel_executor_fails_when_workers_make_no_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "src").mkdir()
    launcher = tmp_path / "fake_codex_noop.py"
    launcher.write_text(
        "\n".join([
            "from pathlib import Path",
            "import sys",
            "args = sys.argv[1:]",
            "output_path = Path(args[args.index('-o') + 1])",
            "_ = sys.stdin.read() if args[-1] == '-' else args[-1]",
            "output_path.write_text('no edits made\\n', encoding='utf-8')",
        ]),
        encoding="utf-8",
    )

    executor = CodexExecParallelExecutor((sys.executable, str(launcher)))
    result = executor.execute(
        ParallelExecutionContext(
            project_dir=repo,
            request="No-op request",
            decision=RouterDecision.AGENT_TEAMS,
            validation_command=None,
            tasks=(
                ParallelImplementTask(
                    worker_name="code-owner",
                    summary="Inspect src",
                    writes=(),
                    owned_paths=("src",),
                ),
            ),
        )
    )

    assert result.status == StageStatus.FAILED
    assert result.output == "external parallel executor produced no copy-back changes"
    assert result.errors[0] == "external executor completed without modifying owned paths"
    assert any("artifacts=" in error for error in result.errors[1:])
    artifact_dirs = list((repo / ".mstack-parallel-artifacts").glob("*"))
    assert artifact_dirs
    worker_artifacts = artifact_dirs[0] / "code-owner"
    assert (worker_artifacts / "stderr.txt").exists()
    assert (worker_artifacts / "last_message.txt").exists()


def test_build_codex_exec_parallel_executor_wraps_ps1_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("core.parallel_executor.os.name", "nt")
    monkeypatch.setattr("core.parallel_executor.shutil.which", lambda name: {
        "codex": r"C:\nvm4w\nodejs\codex.ps1",
        "pwsh": r"C:\Program Files\PowerShell\7\pwsh.exe",
    }.get(name))

    executor = build_codex_exec_parallel_executor()

    assert executor is not None
    assert isinstance(executor, CodexExecParallelExecutor)
    assert executor.launcher == (
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        "-File",
        r"C:\nvm4w\nodejs\codex.ps1",
    )
