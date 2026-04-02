"""Generic implement backends for requests not covered by deterministic recipes."""

from __future__ import annotations

from pathlib import Path

from .pipeline_recipes import GenericImplementBackend, ImplementRecipeContext
from .types import StageResult, StageStatus


def build_generic_implement_backend(mode: str | None) -> GenericImplementBackend | None:
    """Build a generic implement backend from a user-facing mode string."""
    if mode in (None, "none"):
        return None
    if mode == "notes":
        return _notes_backend
    raise ValueError(f"unsupported generic implement backend mode: {mode}")


def _notes_backend(context: ImplementRecipeContext) -> StageResult | None:
    notes_path = context.project_dir / "IMPLEMENTATION_NOTES.md"
    notes_path.write_text(_notes_text(context), encoding="utf-8")
    return StageResult(
        stage="implement",
        status=StageStatus.FAILED,
        output="generic notes backend created IMPLEMENTATION_NOTES.md",
        errors=["manual implementation required; implementation notes created"],
        files_changed=["IMPLEMENTATION_NOTES.md"],
    )


def _notes_text(context: ImplementRecipeContext) -> str:
    repo_shape = _repo_shape(context.project_dir)
    steps = _suggested_steps(context)
    tests = _suggested_test_checklist(context)
    return "\n".join([
        "# Implementation Notes",
        "",
        "## Original Request",
        context.request,
        "",
        "## Detected Context",
        f"- language: {context.lang.value}",
        f"- repo shape: {repo_shape}",
        "",
        "## Why No Deterministic Recipe Matched",
        "- No built-in implement recipe matched the current request text and repository shape.",
        "",
        "## Suggested Implementation Steps",
        *[f"{index}. {step}" for index, step in enumerate(steps, start=1)],
        "",
        "## Suggested Test Checklist",
        *[f"- {item}" for item in tests],
        "",
    ])


def _repo_shape(project_dir: Path) -> str:
    items = sorted(
        path.name
        for path in project_dir.iterdir()
        if not path.name.startswith(".")
    )
    return ", ".join(items) if items else "empty repository"


def _suggested_steps(context: ImplementRecipeContext) -> list[str]:
    if context.lang.value == "python":
        return [
            "Locate the target Python module and define the new behavior in a typed function.",
            "Add or update focused pytest coverage for the new behavior before release.",
            "Run review, qa, and ship stages again after the manual code change.",
        ]
    if context.lang.value == "ts":
        return [
            "Create or update the TypeScript module in src/ with explicit exported types.",
            "Add a matching .test.ts case and verify the npm test script exercises it.",
            "Re-run lint and tsc checks before release.",
        ]
    return [
        "Identify the target module and add the requested behavior in a minimal, reviewable change.",
        "Add or update tests that cover the requested behavior and expected failure modes.",
        "Re-run the pipeline after the manual implementation is complete.",
    ]


def _suggested_test_checklist(context: ImplementRecipeContext) -> list[str]:
    if context.lang.value == "python":
        return [
            "pytest tests/ -x",
            "ruff check .",
            "mypy --strict .",
        ]
    if context.lang.value == "ts":
        return [
            "npm test",
            "npx eslint .",
            "npx tsc --noEmit",
        ]
    return [
        "Unit tests for the changed behavior",
        "Lint and static analysis for the target language",
        "One end-to-end or integration check covering the user request",
    ]
