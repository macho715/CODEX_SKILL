"""End-to-end CLI tests for the mstack pipeline command."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "mstack.py"
RUN_TS_REAL_TOOLCHAIN = os.getenv("RUN_TS_REAL_TOOLCHAIN") == "1"


def _run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=cwd or ROOT,
    )


def _build_windows_npm_install_env() -> dict[str, str]:
    env = os.environ.copy()
    path_entries: list[str] = []
    seen: set[str] = set()

    def add_path(entry: str | None) -> None:
        if not entry:
            return
        normalized = os.path.normcase(os.path.normpath(entry))
        if normalized in seen:
            return
        seen.add(normalized)
        path_entries.append(entry)

    python_dir = Path(sys.executable).resolve().parent
    add_path(str(python_dir))
    add_path(str(python_dir / "Scripts"))

    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    add_path(str(Path(system_root) / "System32"))

    node_path = shutil.which("node")
    if node_path:
        add_path(str(Path(node_path).resolve().parent))

    git_path = shutil.which("git")
    if git_path:
        add_path(str(Path(git_path).resolve().parent))

    appdata = os.environ.get("APPDATA")
    if appdata:
        add_path(str(Path(appdata) / "npm"))

    # npm lifecycle scripts prepend extra .bin directories to PATH on Windows.
    # Keep the parent PATH short so nested cmd.exe steps still resolve node.exe.
    env["PATH"] = os.pathsep.join(path_entries)
    return env


def _run_npm_install(cwd: Path) -> subprocess.CompletedProcess[str]:
    command = ["npm", "install", "--no-fund", "--no-audit", "--legacy-peer-deps"]
    env: dict[str, str] | None = None
    if os.name == "nt":
        # npm lifecycle scripts on Windows can lose the node.exe lookup when a
        # heavily duplicated parent PATH is combined with added .bin entries.
        command = ["cmd.exe", "/d", "/c", *command]
        env = _build_windows_npm_install_env()
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=240,
    )


def _init_python_repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text(
        "from src.app import add\n\n\ndef test_add() -> None:\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "feature/pipeline"], cwd=tmp_path, check=True, capture_output=True, text=True)
    return tmp_path


def _init_python_bugfix_repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo-bugfix'\nversion='0.1.0'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "parser.py").write_text(
        "def first_row(text: str) -> str:\n    return text.splitlines()[1]\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_parser.py").write_text(
        (
            "from src.parser import first_row\n\n\n"
            "def test_first_row_returns_blank_for_empty_input() -> None:\n"
            '    assert first_row("") == ""\n\n\n'
            "def test_first_row_returns_first_data_line() -> None:\n"
            '    assert first_row("name\\nAda\\nGrace\\n") == "Ada"\n'
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "feature/bugfix"], cwd=tmp_path, check=True, capture_output=True, text=True)
    return tmp_path


def _init_typescript_repo(tmp_path: Path) -> Path:
    (tmp_path / "package.json").write_text(
        '{"name":"demo-ts","version":"0.1.0","type":"module"}\n',
        encoding="utf-8",
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("export const version = '0.1.0';\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "npm.cmd").write_text(
        "@echo off\r\n"
        "if \"%1\"==\"test\" (\r\n"
        "  echo 1 passed\r\n"
        "  exit /b 0\r\n"
        ")\r\n"
        "echo unsupported npm command %*\r\n"
        "exit /b 1\r\n",
        encoding="utf-8",
    )
    (tmp_path / "npx.cmd").write_text(
        "@echo off\r\n"
        "if \"%1\"==\"eslint\" (\r\n"
        "  echo All checks passed!\r\n"
        "  exit /b 0\r\n"
        ")\r\n"
        "if \"%1\"==\"tsc\" (\r\n"
        "  echo Success: no issues found in 2 source files\r\n"
        "  exit /b 0\r\n"
        ")\r\n"
        "echo unsupported npx command %*\r\n"
        "exit /b 1\r\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "feature/typescript"], cwd=tmp_path, check=True, capture_output=True, text=True)
    return tmp_path


def _init_typescript_real_repo(tmp_path: Path) -> Path:
    (tmp_path / "package.json").write_text(
        "\n".join([
            "{",
            '  "name": "demo-ts-real",',
            '  "version": "0.1.0",',
            '  "private": true,',
            '  "scripts": {',
            '    "test": "tsx --test tests/**/*.test.ts"',
            "  },",
            '  "devDependencies": {',
            '    "typescript": "6.0.2",',
            '    "eslint": "10.1.0",',
            '    "@typescript-eslint/parser": "8.57.2",',
            '    "tsx": "4.21.0"',
            "  }",
            "}",
            "",
        ]),
        encoding="utf-8",
    )
    (tmp_path / "tsconfig.json").write_text(
        "\n".join([
            "{",
            '  "compilerOptions": {',
            '    "target": "ES2022",',
            '    "module": "commonjs",',
            '    "moduleResolution": "node",',
            '    "strict": true,',
            '    "noEmit": true,',
            '    "ignoreDeprecations": "6.0"',
            "  },",
            '  "include": ["src", "tests"]',
            "}",
            "",
        ]),
        encoding="utf-8",
    )
    (tmp_path / "eslint.config.mjs").write_text(
        "\n".join([
            "import tsParser from '@typescript-eslint/parser';",
            "",
            "export default [",
            "  {",
            "    files: ['**/*.ts'],",
            "    languageOptions: {",
            "      parser: tsParser,",
            "      parserOptions: {",
            "        ecmaVersion: 'latest',",
            "        sourceType: 'module'",
            "      }",
            "    },",
            "    rules: {}",
            "  }",
            "];",
            "",
        ]),
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("export const version = '0.1.0';\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "bootstrap.test.ts").write_text(
        "\n".join([
            "// @ts-nocheck",
            "import { strict as assert } from 'node:assert';",
            "import test from 'node:test';",
            "",
            "test('bootstrap', () => {",
            "  assert.equal(1, 1);",
            "});",
            "",
        ]),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "checkout", "-b", "feature/typescript-real"], cwd=tmp_path, check=True, capture_output=True, text=True)
    return tmp_path


def _commit_repo_state(repo: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True, text=True)


def test_pipeline_cli_feature_json(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli("pipeline", "Add CSV import end-to-end", "--json", cwd=repo)
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["work_type"] == "feature"
    assert data["classification"]["stage_order"] == [
        "plan", "implement", "review", "qa", "ship", "retro"
    ]
    assert data["summary"]["execution_mode"] == "direct"
    assert data["summary"]["final_status"] == "passed"
    assert data["summary"]["files_changed"] == ["src/csv_import.py", "tests/test_csv_import.py"]
    assert data["pipeline_result"]["files_changed"] == ["src/csv_import.py", "tests/test_csv_import.py"]
    stages = {stage["stage"]: stage for stage in data["pipeline_result"]["stages"]}
    assert "Phase 1" in stages["plan"]["output"]
    assert stages["plan"]["errors"] == []
    assert stages["implement"]["status"] == "passed"
    assert "applied python csv import scaffold" in stages["implement"]["output"]
    assert stages["implement"]["files_changed"] == ["src/csv_import.py", "tests/test_csv_import.py"]
    assert (repo / "src" / "csv_import.py").exists()
    assert (repo / "tests" / "test_csv_import.py").exists()
    assert "src/csv_import.py" in stages["review"]["output"]
    assert "tests/test_csv_import.py" in stages["review"]["output"]
    assert stages["review"]["errors"] == []
    assert "3 passed" in stages["qa"]["output"]
    assert stages["qa"]["errors"] == []
    assert "test: 3 passed" in stages["ship"]["output"]
    assert stages["ship"]["errors"] == []


def test_pipeline_cli_respects_mode_override(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli(
        "pipeline",
        "Add CSV import end-to-end",
        "--mode",
        "agent_teams",
        "--json",
        cwd=repo,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["execution_mode"] == "agent_teams"
    assert data["summary"]["execution_mode"] == "agent_teams"


def test_pipeline_cli_marks_nested_decision_engine_for_complex_choice(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli(
        "pipeline",
        "Add CSV import end-to-end and compare 3 rollout options for the architecture",
        "--mode",
        "agent_teams",
        "--json",
        cwd=repo,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["requires_parallel_decision"] is True
    assert data["classification"]["decision_engine"] == "pipeline-coordinator"
    assert data["classification"]["coordinator_input_ready"] is True
    assert data["summary"]["decision_engine"] == "pipeline-coordinator"


def test_pipeline_cli_bugfix_recipe_flow(tmp_path: Path) -> None:
    repo = _init_python_bugfix_repo(tmp_path)
    result = _run_cli("pipeline", "Fix crash in parser on empty input", "--json", cwd=repo)

    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["work_type"] == "bugfix"
    assert data["summary"]["final_status"] == "passed"
    assert data["summary"]["files_changed"] == ["src/parser.py", "tests/test_parser_regression.py"]
    stages = {stage["stage"]: stage for stage in data["pipeline_result"]["stages"]}
    assert stages["implement"]["status"] == "passed"
    assert "parser bugfix scaffold" in stages["implement"]["output"]
    assert "4 passed" in stages["qa"]["output"]
    assert "test: 4 passed" in stages["ship"]["output"]


def test_pipeline_cli_refactor_recipe_flow(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli("pipeline", "Refactor the add flow into a helper module", "--json", cwd=repo)

    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["work_type"] == "refactor"
    assert data["summary"]["final_status"] == "passed"
    assert data["summary"]["files_changed"] == [
        "src/app.py",
        "src/math_helpers.py",
        "tests/test_math_helpers.py",
    ]
    stages = {stage["stage"]: stage for stage in data["pipeline_result"]["stages"]}
    assert stages["implement"]["status"] == "passed"
    assert "python refactor scaffold" in stages["implement"]["output"]
    assert "src/math_helpers.py" in stages["review"]["output"]
    assert "2 passed" in stages["qa"]["output"]


def test_pipeline_cli_typescript_feature_flow(tmp_path: Path) -> None:
    repo = _init_typescript_repo(tmp_path)
    result = _run_cli("pipeline", "Add CSV import end-to-end", "--json", cwd=repo)

    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["work_type"] == "feature"
    assert data["summary"]["final_status"] == "passed"
    assert data["summary"]["files_changed"] == ["src/csvImport.ts", "tests/csvImport.test.ts"]
    stages = {stage["stage"]: stage for stage in data["pipeline_result"]["stages"]}
    assert stages["implement"]["status"] == "passed"
    assert "typescript csv import scaffold" in stages["implement"]["output"]
    assert "src/csvImport.ts" in stages["review"]["output"]
    assert "tests/csvImport.test.ts" in stages["review"]["output"]
    assert "1 passed" in stages["qa"]["output"]
    assert "lint: All checks passed!" in stages["ship"]["output"]
    assert "type: Success: no issues found in 2 source files" in stages["ship"]["output"]


@pytest.mark.skipif(not RUN_TS_REAL_TOOLCHAIN, reason="set RUN_TS_REAL_TOOLCHAIN=1 to enable")
@pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed")
def test_pipeline_cli_typescript_feature_flow_real_toolchain(tmp_path: Path) -> None:
    repo = _init_typescript_real_repo(tmp_path)
    install = _run_npm_install(repo)
    assert install.returncode == 0, install.stderr or install.stdout
    _commit_repo_state(repo, "install toolchain")

    result = _run_cli("pipeline", "Add CSV import end-to-end", "--json", cwd=repo)

    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["work_type"] == "feature"
    assert data["summary"]["final_status"] == "passed"
    assert data["summary"]["files_changed"] == ["src/csvImport.ts", "tests/csvImport.test.ts"]
    stages = {stage["stage"]: stage for stage in data["pipeline_result"]["stages"]}
    assert stages["implement"]["status"] == "passed"
    assert "typescript csv import scaffold" in stages["implement"]["output"]
    assert "src/csvImport.ts" in stages["review"]["output"]
    assert "tests/csvImport.test.ts" in stages["review"]["output"]
    assert stages["qa"]["status"] == "passed"
    assert "passed" in stages["qa"]["output"]
    assert stages["ship"]["status"] == "passed"
    assert "lint: passed (npx eslint .)" in stages["ship"]["output"]
    assert "type: passed (npx tsc --noEmit)" in stages["ship"]["output"]


def test_pipeline_cli_stop_after_stage_skips_trailing_stages(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli(
        "pipeline",
        "Plan this feature and stop after qa with approval",
        "--json",
        cwd=repo,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["stop_after_stage"] == "qa"
    skipped = [
        stage["stage"]
        for stage in data["pipeline_result"]["stages"]
        if stage["status"] == "skipped"
    ]
    assert skipped == ["implement", "ship", "retro"]


def test_pipeline_cli_qa_retry_flow(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli(
        "pipeline",
        "Validate this parser change",
        "--mock-fail-stage",
        "qa",
        "--mock-fail-until",
        "1",
        "--json",
        cwd=repo,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["pipeline_result"]["final_status"] == "passed"
    assert data["pipeline_result"]["total_retries"] == 1


def test_pipeline_cli_failure_returns_nonzero(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli(
        "pipeline",
        "Add CSV import end-to-end",
        "--mock-fail-stage",
        "implement",
        "--json",
        cwd=repo,
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["pipeline_result"]["final_status"] == "failed"
    assert data["summary"]["blockers"] == ["implement: implement failed"]
    stages = {stage["stage"]: stage for stage in data["pipeline_result"]["stages"]}
    assert stages["implement"]["output"] == "implement failed by test hook"
    assert stages["implement"]["errors"] == ["implement failed"]


def test_pipeline_cli_generic_notes_backend_returns_nonzero_and_writes_notes(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli(
        "pipeline",
        "Create admin dashboard skeleton",
        "--generic-implement",
        "notes",
        "--json",
        cwd=repo,
    )

    assert result.returncode == 1, result.stderr or result.stdout
    data = json.loads(result.stdout)
    notes_path = repo / "IMPLEMENTATION_NOTES.md"
    assert notes_path.exists()
    assert data["pipeline_result"]["final_status"] == "failed"
    assert data["summary"]["files_changed"] == ["IMPLEMENTATION_NOTES.md"]
    assert data["summary"]["blockers"] == [
        "implement: manual implementation required; implementation notes created"
    ]
    stages = data["pipeline_result"]["stages"]
    assert [stage["stage"] for stage in stages] == ["plan", "implement"]
    assert stages[1]["output"] == "generic notes backend created IMPLEMENTATION_NOTES.md"
    assert stages[1]["errors"] == ["manual implementation required; implementation notes created"]
    notes_text = notes_path.read_text(encoding="utf-8")
    assert "## Original Request" in notes_text
    assert "## Detected Context" in notes_text
    assert "## Why No Deterministic Recipe Matched" in notes_text
    assert "## Suggested Implementation Steps" in notes_text
    assert "## Suggested Test Checklist" in notes_text


def test_pipeline_cli_require_approval_and_next_action_override(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli(
        "pipeline",
        "Add CSV import end-to-end",
        "--require-approval",
        "--next-action",
        "Hand off to release lead",
        "--json",
        cwd=repo,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["classification"]["approval_gate"] == "plan"
    assert data["pipeline_result"]["final_status"] == "pending"
    assert [stage["status"] for stage in data["pipeline_result"]["stages"]] == [
        "passed",
        "skipped",
        "skipped",
        "skipped",
        "skipped",
        "skipped",
    ]
    assert data["summary"]["next_action"] == "Hand off to release lead"


def test_pipeline_cli_renders_text_summary_without_json(tmp_path: Path) -> None:
    repo = _init_python_repo(tmp_path)
    result = _run_cli("pipeline", "Add CSV import end-to-end", cwd=repo)

    assert result.returncode == 0, result.stderr or result.stdout
    assert "## MStack Pipeline Summary" in result.stdout
    assert "- final status: passed" in result.stdout
