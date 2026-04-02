"""tests/test_claude_md.py — core/claude_md.py 단위 테스트"""
import pytest
from core.claude_md import generate_claude_md, measure_token_count
from core.config import load_preset


def test_lazy_md_contains_skill_table():
    preset = load_preset("python")
    md = generate_claude_md("test-project", ["src", "tests"], preset, lazy_skills=True)
    assert "## Available Skills (Lazy Index)" in md
    assert "/plan" in md


def test_inline_md_contains_skill_details():
    preset = load_preset("python")
    md = generate_claude_md("test-project", ["src", "tests"], preset, lazy_skills=False)
    assert "## Skills (Full Index)" in md
    assert "/plan" in md


def test_compaction_rules_present():
    preset = load_preset("python")
    md = generate_claude_md("test-project", ["src"], preset, lazy_skills=True)
    assert "## Compaction Rules" in md
    assert "ALWAYS preserve" in md


def test_hvdc_domain_terms_appear(hvdc_project):
    from core.config import resolve_preset
    import sys
    from pathlib import Path
    presets_dir = Path(__file__).parent.parent / "presets"
    preset = load_preset("hvdc", presets_dir)
    md = generate_claude_md("hvdc-project", ["src", "docs"], preset, lazy_skills=True)
    assert "## Domain Terms" in md
    assert "FANR" in md
    assert "MOIAT" in md


def test_project_name_in_header():
    preset = load_preset("python")
    md = generate_claude_md("my-cool-project", ["src"], preset)
    assert "# my-cool-project" in md


def test_rules_appear_when_set():
    preset = load_preset("python")
    md = generate_claude_md("test", ["src"], preset)
    assert "## Rules" in md
    assert "type hints" in md


def test_extended_hooks_description():
    preset = load_preset("python")
    md = generate_claude_md("test", ["src"], preset, hooks_level="extended")
    assert "PreToolUse" in md
    assert "security gate" in md
    assert "group-logs" in md
