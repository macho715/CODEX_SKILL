"""Unit tests for deterministic implement recipes."""

from __future__ import annotations

from pathlib import Path

from core.pipeline_recipes import ImplementRecipeContext, run_implement_recipe
from core.types import Lang, StageResult, StageStatus


def _init_python_feature_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    return tmp_path


def _init_python_bugfix_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "parser.py").write_text(
        "def first_row(text: str) -> str:\n    return text.splitlines()[1]\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    return tmp_path


def _init_typescript_repo(tmp_path: Path) -> Path:
    (tmp_path / "package.json").write_text('{"name":"demo-ts","version":"0.1.0"}\n', encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("export const version = '0.1.0';\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    return tmp_path


def test_python_csv_recipe_creates_files_and_reports_changes(tmp_path: Path) -> None:
    repo = _init_python_feature_repo(tmp_path)

    result = run_implement_recipe(
        ImplementRecipeContext(
            project_dir=repo,
            request="Add CSV import end-to-end",
            lang=Lang.PYTHON,
        )
    )

    assert result.status == StageStatus.PASSED
    assert result.files_changed == ["src/csv_import.py", "tests/test_csv_import.py"]
    assert (repo / "src" / "csv_import.py").exists()
    assert (repo / "tests" / "test_csv_import.py").exists()


def test_python_bugfix_recipe_updates_parser_and_adds_regression_test(tmp_path: Path) -> None:
    repo = _init_python_bugfix_repo(tmp_path)

    result = run_implement_recipe(
        ImplementRecipeContext(
            project_dir=repo,
            request="Fix crash in parser on empty input",
            lang=Lang.PYTHON,
        )
    )

    assert result.status == StageStatus.PASSED
    assert result.files_changed == ["src/parser.py", "tests/test_parser_regression.py"]
    assert 'return ""' in (repo / "src" / "parser.py").read_text(encoding="utf-8")
    assert (repo / "tests" / "test_parser_regression.py").exists()


def test_python_refactor_recipe_extracts_helper_module(tmp_path: Path) -> None:
    repo = _init_python_feature_repo(tmp_path)

    result = run_implement_recipe(
        ImplementRecipeContext(
            project_dir=repo,
            request="Refactor the add flow into a helper module",
            lang=Lang.PYTHON,
        )
    )

    assert result.status == StageStatus.PASSED
    assert result.files_changed == ["src/app.py", "src/math_helpers.py", "tests/test_math_helpers.py"]
    assert "add_numbers" in (repo / "src" / "app.py").read_text(encoding="utf-8")
    assert (repo / "src" / "math_helpers.py").exists()
    assert (repo / "tests" / "test_math_helpers.py").exists()


def test_typescript_csv_recipe_creates_ts_scaffold(tmp_path: Path) -> None:
    repo = _init_typescript_repo(tmp_path)

    result = run_implement_recipe(
        ImplementRecipeContext(
            project_dir=repo,
            request="Add CSV import flow",
            lang=Lang.TS,
        )
    )

    assert result.status == StageStatus.PASSED
    assert result.files_changed == ["src/csvImport.ts", "tests/csvImport.test.ts"]
    assert (repo / "src" / "csvImport.ts").exists()
    assert (repo / "tests" / "csvImport.test.ts").exists()


def test_unmatched_recipe_returns_skipped(tmp_path: Path) -> None:
    repo = _init_python_feature_repo(tmp_path)

    result = run_implement_recipe(
        ImplementRecipeContext(
            project_dir=repo,
            request="Write release notes",
            lang=Lang.PYTHON,
        )
    )

    assert result.status == StageStatus.SKIPPED
    assert result.output == "no deterministic implementation recipe matched the request"
    assert result.files_changed == []


def test_unmatched_recipe_uses_generic_fallback_backend(tmp_path: Path) -> None:
    repo = _init_python_feature_repo(tmp_path)

    def fallback(context: ImplementRecipeContext):
        notes_path = context.project_dir / "IMPLEMENTATION_NOTES.md"
        notes_path.write_text("# Manual follow-up\n", encoding="utf-8")
        return StageResult(
            stage="implement",
            status=StageStatus.PASSED,
            output="generic fallback backend created implementation notes",
            files_changed=["IMPLEMENTATION_NOTES.md"],
        )

    result = run_implement_recipe(
        ImplementRecipeContext(
            project_dir=repo,
            request="Write release notes",
            lang=Lang.PYTHON,
        ),
        fallback_backend=fallback,
    )

    assert result.status == StageStatus.PASSED
    assert result.files_changed == ["IMPLEMENTATION_NOTES.md"]
    assert (repo / "IMPLEMENTATION_NOTES.md").exists()
