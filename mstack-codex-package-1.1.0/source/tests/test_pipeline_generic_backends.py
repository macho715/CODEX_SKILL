"""Tests for generic implement backends exposed to users."""

from __future__ import annotations

from pathlib import Path

from core.pipeline_generic_backends import build_generic_implement_backend
from core.pipeline_recipes import ImplementRecipeContext
from core.types import Lang, StageStatus


def test_build_generic_implement_backend_none_returns_none() -> None:
    assert build_generic_implement_backend(None) is None
    assert build_generic_implement_backend("none") is None


def test_notes_backend_creates_notes_and_returns_expected_stage_result(tmp_path: Path) -> None:
    backend = build_generic_implement_backend("notes")
    assert backend is not None

    result = backend(
        ImplementRecipeContext(
            project_dir=tmp_path,
            request="Write release notes for this project",
            lang=Lang.PYTHON,
        )
    )

    notes_path = tmp_path / "IMPLEMENTATION_NOTES.md"
    assert notes_path.exists()
    assert result is not None
    assert result.stage == "implement"
    assert result.status == StageStatus.FAILED
    assert result.output == "generic notes backend created IMPLEMENTATION_NOTES.md"
    assert result.errors == ["manual implementation required; implementation notes created"]
    assert result.files_changed == ["IMPLEMENTATION_NOTES.md"]
    notes_text = notes_path.read_text(encoding="utf-8")
    assert "## Original Request" in notes_text
    assert "## Detected Context" in notes_text
    assert "## Suggested Implementation Steps" in notes_text
    assert "## Suggested Test Checklist" in notes_text
