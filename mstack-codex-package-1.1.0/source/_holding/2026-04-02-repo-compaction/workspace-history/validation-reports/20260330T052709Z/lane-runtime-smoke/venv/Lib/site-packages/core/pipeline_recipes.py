"""Deterministic implement-stage recipes for the pipeline runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .types import Lang, StageResult, StageStatus


CSV_PATTERNS = (
    "csv import",
    "import csv",
    "csv importer",
    "csv ingestion",
)
BUGFIX_PATTERNS = (
    "fix crash",
    "bugfix",
    "fix bug",
    "crash",
    "empty input",
    "blank input",
    "parser bug",
)
REFACTOR_PATTERNS = (
    "refactor",
    "cleanup",
    "restructure",
    "extract helper",
)


@dataclass(frozen=True)
class ImplementRecipeContext:
    """Minimal context required for deterministic implement recipes."""

    project_dir: Path
    request: str
    lang: Lang


@dataclass(frozen=True)
class ImplementRecipe:
    """Recipe matcher and applicator pair."""

    name: str
    match: Callable[[ImplementRecipeContext], bool]
    apply: Callable[[ImplementRecipeContext], StageResult]


GenericImplementBackend = Callable[[ImplementRecipeContext], StageResult | None]


def run_implement_recipe(
    context: ImplementRecipeContext,
    *,
    fallback_backend: GenericImplementBackend | None = None,
) -> StageResult:
    """Select and run the first deterministic recipe that matches the request."""
    for recipe in _IMPLEMENT_RECIPES:
        if recipe.match(context):
            return recipe.apply(context)

    if fallback_backend is not None:
        fallback_result = fallback_backend(context)
        if fallback_result is not None:
            return fallback_result

    return StageResult(
        stage="implement",
        status=StageStatus.SKIPPED,
        output="no deterministic implementation recipe matched the request",
    )


def _match_python_csv_feature(context: ImplementRecipeContext) -> bool:
    lowered = context.request.lower()
    return context.lang == Lang.PYTHON and any(pattern in lowered for pattern in CSV_PATTERNS)


def _apply_python_csv_feature(context: ImplementRecipeContext) -> StageResult:
    code_dir = _code_dir(context.project_dir)
    tests_dir = context.project_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    module_path = code_dir / "csv_import.py"
    test_path = tests_dir / "test_csv_import.py"
    existing_error = _existing_target_error(context.project_dir, (module_path, test_path))
    if existing_error is not None:
        return existing_error

    import_target = _module_import_path(code_dir, "csv_import")
    module_path.write_text(_python_csv_import_module_text(), encoding="utf-8")
    test_path.write_text(_python_csv_import_test_text(import_target), encoding="utf-8")
    return _recipe_success(context.project_dir, "applied python csv import scaffold", module_path, test_path)


def _match_python_parser_bugfix(context: ImplementRecipeContext) -> bool:
    lowered = context.request.lower()
    return (
        context.lang == Lang.PYTHON
        and any(pattern in lowered for pattern in BUGFIX_PATTERNS)
        and _find_existing_module(context.project_dir, "parser.py") is not None
    )


def _apply_python_parser_bugfix(context: ImplementRecipeContext) -> StageResult:
    parser_path = _find_existing_module(context.project_dir, "parser.py")
    if parser_path is None:
        return StageResult(
            stage="implement",
            status=StageStatus.SKIPPED,
            output="no parser module available for the python bugfix recipe",
        )

    tests_dir = context.project_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    regression_path = tests_dir / "test_parser_regression.py"
    existing_error = _existing_target_error(context.project_dir, (regression_path,))
    if existing_error is not None:
        return existing_error

    import_target = _module_import_path(parser_path.parent, "parser")
    parser_path.write_text(_python_parser_bugfix_module_text(), encoding="utf-8")
    regression_path.write_text(_python_parser_bugfix_test_text(import_target), encoding="utf-8")
    return _recipe_success(
        context.project_dir,
        "applied python parser bugfix scaffold",
        parser_path,
        regression_path,
    )


def _match_python_refactor(context: ImplementRecipeContext) -> bool:
    lowered = context.request.lower()
    return (
        context.lang == Lang.PYTHON
        and any(pattern in lowered for pattern in REFACTOR_PATTERNS)
        and _find_existing_module(context.project_dir, "app.py") is not None
    )


def _apply_python_refactor(context: ImplementRecipeContext) -> StageResult:
    app_path = _find_existing_module(context.project_dir, "app.py")
    if app_path is None:
        return StageResult(
            stage="implement",
            status=StageStatus.SKIPPED,
            output="no app module available for the python refactor recipe",
        )

    helper_path = app_path.parent / "math_helpers.py"
    tests_dir = context.project_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    helper_test_path = tests_dir / "test_math_helpers.py"
    existing_error = _existing_target_error(context.project_dir, (helper_path, helper_test_path))
    if existing_error is not None:
        return existing_error

    helper_import = _module_import_path(app_path.parent, "math_helpers")
    app_path.write_text(_python_refactor_app_text(helper_import), encoding="utf-8")
    helper_path.write_text(_python_refactor_helper_text(), encoding="utf-8")
    helper_test_path.write_text(_python_refactor_test_text(helper_import), encoding="utf-8")
    return _recipe_success(
        context.project_dir,
        "applied python refactor scaffold",
        app_path,
        helper_path,
        helper_test_path,
    )


def _match_typescript_csv_feature(context: ImplementRecipeContext) -> bool:
    lowered = context.request.lower()
    return context.lang == Lang.TS and any(pattern in lowered for pattern in CSV_PATTERNS)


def _apply_typescript_csv_feature(context: ImplementRecipeContext) -> StageResult:
    code_dir = _code_dir(context.project_dir)
    tests_dir = context.project_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    module_path = code_dir / "csvImport.ts"
    test_path = tests_dir / "csvImport.test.ts"
    existing_error = _existing_target_error(context.project_dir, (module_path, test_path))
    if existing_error is not None:
        return existing_error

    module_path.write_text(_typescript_csv_import_module_text(), encoding="utf-8")
    test_path.write_text(_typescript_csv_import_test_text(), encoding="utf-8")
    return _recipe_success(context.project_dir, "applied typescript csv import scaffold", module_path, test_path)


def _code_dir(project_dir: Path) -> Path:
    src_dir = project_dir / "src"
    if src_dir.exists():
        return src_dir
    return project_dir


def _find_existing_module(project_dir: Path, filename: str) -> Path | None:
    for candidate in (project_dir / "src" / filename, project_dir / filename):
        if candidate.exists():
            return candidate
    return None


def _module_import_path(module_dir: Path, module_name: str) -> str:
    if module_dir.name == "src":
        return f"src.{module_name}"
    return module_name


def _existing_target_error(project_dir: Path, paths: tuple[Path, ...]) -> StageResult | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None

    existing_list = ", ".join(_to_posix(path.relative_to(project_dir)) for path in existing)
    return StageResult(
        stage="implement",
        status=StageStatus.FAILED,
        output="deterministic recipe refused to overwrite existing files",
        errors=[f"existing target files must be reviewed manually: {existing_list}"],
    )


def _recipe_success(project_dir: Path, message: str, *paths: Path) -> StageResult:
    files_changed = [_to_posix(path.relative_to(project_dir)) for path in paths]
    return StageResult(
        stage="implement",
        status=StageStatus.PASSED,
        output=f"{message}: {', '.join(files_changed)}",
        files_changed=files_changed,
    )


def _to_posix(path: Path) -> str:
    return path.as_posix()


def _python_csv_import_module_text() -> str:
    return "\n".join([
        "from __future__ import annotations",
        "",
        "import csv",
        "from io import StringIO",
        "from pathlib import Path",
        "",
        "",
        "def parse_csv_rows(text: str) -> list[dict[str, str]]:",
        '    """Parse CSV text into dictionaries with normalized string keys and values."""',
        '    reader = csv.DictReader(StringIO(text.strip()))',
        "    rows: list[dict[str, str]] = []",
        "    for raw_row in reader:",
        "        row = {",
        '            str(key): value if value is not None else ""',
        "            for key, value in raw_row.items()",
        "        }",
        "        rows.append(row)",
        "    return rows",
        "",
        "",
        "def load_csv_rows(path: str | Path) -> list[dict[str, str]]:",
        '    """Load CSV rows from a filesystem path."""',
        "    csv_path = Path(path)",
        "    return parse_csv_rows(csv_path.read_text(encoding='utf-8'))",
        "",
    ])


def _python_csv_import_test_text(import_target: str) -> str:
    return "\n".join([
        "from __future__ import annotations",
        "",
        "from pathlib import Path",
        "",
        f"from {import_target} import load_csv_rows, parse_csv_rows",
        "",
        "",
        "def test_parse_csv_rows() -> None:",
        '    rows = parse_csv_rows("name,age\\nAda,36\\nGrace,47\\n")',
        '    assert rows == [{"name": "Ada", "age": "36"}, {"name": "Grace", "age": "47"}]',
        "",
        "",
        "def test_load_csv_rows(tmp_path: Path) -> None:",
        '    csv_path = tmp_path / "sample.csv"',
        '    csv_path.write_text("city,country\\nDubai,UAE\\nSeoul,Korea\\n", encoding="utf-8")',
        "    assert load_csv_rows(csv_path) == [",
        '        {"city": "Dubai", "country": "UAE"},',
        '        {"city": "Seoul", "country": "Korea"},',
        "    ]",
        "",
    ])


def _python_parser_bugfix_module_text() -> str:
    return "\n".join([
        "from __future__ import annotations",
        "",
        "",
        "def first_row(text: str) -> str:",
        '    """Return the first data row from a CSV-like string without crashing on empty input."""',
        "    lines = [line.strip() for line in text.splitlines() if line.strip()]",
        "    if len(lines) < 2:",
        '        return ""',
        "    return lines[1]",
        "",
    ])


def _python_parser_bugfix_test_text(import_target: str) -> str:
    return "\n".join([
        "from __future__ import annotations",
        "",
        f"from {import_target} import first_row",
        "",
        "",
        "def test_first_row_returns_blank_for_empty_input() -> None:",
        '    assert first_row("") == ""',
        "",
        "",
        "def test_first_row_returns_first_data_line() -> None:",
        '    assert first_row("name\\nAda\\nGrace\\n") == "Ada"',
        "",
    ])


def _python_refactor_app_text(helper_import: str) -> str:
    return "\n".join([
        "from __future__ import annotations",
        "",
        f"from {helper_import} import add_numbers",
        "",
        "",
        "def add(a: int, b: int) -> int:",
        '    """Delegate integer addition to the extracted helper module."""',
        "    return add_numbers(a, b)",
        "",
    ])


def _python_refactor_helper_text() -> str:
    return "\n".join([
        "from __future__ import annotations",
        "",
        "",
        "def add_numbers(left: int, right: int) -> int:",
        '    """Add two integers in a dedicated helper module."""',
        "    return left + right",
        "",
    ])


def _python_refactor_test_text(helper_import: str) -> str:
    return "\n".join([
        "from __future__ import annotations",
        "",
        f"from {helper_import} import add_numbers",
        "",
        "",
        "def test_add_numbers() -> None:",
        "    assert add_numbers(2, 3) == 5",
        "",
    ])


def _typescript_csv_import_module_text() -> str:
    return "\n".join([
        "export type CsvRow = Record<string, string>;",
        "",
        "export function parseCsvRows(text: string): CsvRow[] {",
        "  const lines = text.trim().split(/\\r?\\n/);",
        "  if (lines.length < 2) {",
        "    return [];",
        "  }",
        "  const headers = lines[0].split(',').map((header) => header.trim());",
        "  return lines.slice(1).map((line) => {",
        "    const values = line.split(',').map((value) => value.trim());",
        "    return headers.reduce<CsvRow>((row, header, index) => {",
        "      row[header] = values[index] ?? '';",
        "      return row;",
        "    }, {});",
        "  });",
        "}",
        "",
    ])


def _typescript_csv_import_test_text() -> str:
    return "\n".join([
        "// @ts-nocheck",
        "import { strict as assert } from 'node:assert';",
        "import test from 'node:test';",
        "",
        "import { parseCsvRows } from '../src/csvImport';",
        "",
        "test('parseCsvRows returns row dictionaries', () => {",
        "  assert.deepEqual(parseCsvRows('name,age\\nAda,36\\nGrace,47\\n'), [",
        "    { name: 'Ada', age: '36' },",
        "    { name: 'Grace', age: '47' },",
        "  ]);",
        "});",
        "",
    ])


_IMPLEMENT_RECIPES = (
    ImplementRecipe(
        name="python-csv-feature",
        match=_match_python_csv_feature,
        apply=_apply_python_csv_feature,
    ),
    ImplementRecipe(
        name="python-parser-bugfix",
        match=_match_python_parser_bugfix,
        apply=_apply_python_parser_bugfix,
    ),
    ImplementRecipe(
        name="python-refactor",
        match=_match_python_refactor,
        apply=_apply_python_refactor,
    ),
    ImplementRecipe(
        name="typescript-csv-feature",
        match=_match_typescript_csv_feature,
        apply=_apply_typescript_csv_feature,
    ),
)
