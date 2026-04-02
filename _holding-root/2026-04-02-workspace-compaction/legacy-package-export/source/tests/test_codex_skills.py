"""Validation tests for Codex-converted skill folders."""

from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parent.parent / "skills-codex"
FORBIDDEN_TERMS = (
    "CLAUDE.md",
    ".claude",
    ".claude-prompts",
    "Claude Code",
    "Shift+Tab",
    "Cowork",
    "Opus",
    "Sonnet",
    "Haiku",
)


def _skill_dirs() -> list[Path]:
    return sorted(path for path in ROOT.iterdir() if path.is_dir())


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"Missing frontmatter: {path}"
    return yaml.safe_load(match.group(1))


def test_codex_skill_count_is_expected() -> None:
    assert len(_skill_dirs()) == 9


def test_codex_skill_structure_and_frontmatter() -> None:
    for skill_dir in _skill_dirs():
        skill_md = skill_dir / "SKILL.md"
        openai_yaml = skill_dir / "agents" / "openai.yaml"
        assert skill_md.exists(), skill_md
        assert openai_yaml.exists(), openai_yaml

        frontmatter = _frontmatter(skill_md)
        assert set(frontmatter) == {"name", "description"}
        assert "Codex" in frontmatter["description"]
        assert (
            "Use when" in frontmatter["description"]
            or "사용" in frontmatter["description"]
            or "트리거" in frontmatter["description"]
        )


def test_codex_openai_metadata_is_consistent() -> None:
    for skill_dir in _skill_dirs():
        openai_yaml = skill_dir / "agents" / "openai.yaml"
        data = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
        interface = data["interface"]
        assert interface["display_name"].startswith("MStack ")
        assert interface["short_description"].strip()
        assert interface["default_prompt"].strip()


def test_codex_skill_boundary_language_is_present() -> None:
    texts = {
        skill_dir.name: (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        for skill_dir in _skill_dirs()
    }

    for text in texts.values():
        assert "## Use This Skill When" in text
        assert "## Prefer Another Skill When" in text

    assert "cross-cutting safety layer" in texts["careful"]
    assert "one-shot end-to-end execution" in texts["dispatch"]
    assert "root-cause analysis" in texts["investigate"]
    assert "simple explanation" in texts["pipeline"]
    assert "before coding" in texts["plan"]
    assert "verification" in texts["qa"]
    assert "work is complete" in texts["retro"]
    assert "code or a diff already exists" in texts["review"]
    assert "review and QA evidence already exist" in texts["ship"]


def test_codex_skill_metadata_reflects_boundaries() -> None:
    interfaces = {}
    for skill_dir in _skill_dirs():
        openai_yaml = skill_dir / "agents" / "openai.yaml"
        data = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
        interfaces[skill_dir.name] = data["interface"]

    assert "safety layer" in interfaces["careful"]["default_prompt"].lower()
    assert "prefer mstack-pipeline instead" in interfaces["dispatch"]["default_prompt"].lower()
    assert "prefer mstack-qa" in interfaces["investigate"]["default_prompt"].lower()
    assert "design-only" in interfaces["pipeline"]["default_prompt"].lower()
    assert "before coding begins" in interfaces["plan"]["default_prompt"].lower()
    assert "only for verification" in interfaces["qa"]["default_prompt"].lower()
    assert "after work is complete" in interfaces["retro"]["default_prompt"].lower()
    assert "code or a diff already exists" in interfaces["review"]["default_prompt"].lower()
    assert "review and qa evidence already exist" in interfaces["ship"]["default_prompt"].lower()


def test_codex_skills_do_not_contain_claude_specific_terms() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{term!r} found in {path}"


def test_dispatch_and_pipeline_have_distinct_roles() -> None:
    dispatch_text = (ROOT / "dispatch" / "SKILL.md").read_text(encoding="utf-8")
    pipeline_text = (ROOT / "pipeline" / "SKILL.md").read_text(encoding="utf-8")

    assert "one-shot end-to-end SDLC execution" in dispatch_text
    assert "one-shot workflow execution" in pipeline_text
    assert "careful -> dispatch -> plan -> implement -> review -> qa -> ship -> retro" in pipeline_text
    assert "files changed" in pipeline_text


def test_pipeline_references_exist_and_are_linked() -> None:
    pipeline_dir = ROOT / "pipeline"
    skill_text = (pipeline_dir / "SKILL.md").read_text(encoding="utf-8")
    usage_ref = pipeline_dir / "references" / "usage-examples.md"
    integration_ref = pipeline_dir / "references" / "core-pipeline-integration.md"
    usage_text = usage_ref.read_text(encoding="utf-8")
    integration_text = integration_ref.read_text(encoding="utf-8")

    assert usage_ref.exists()
    assert integration_ref.exists()
    assert "references/usage-examples.md" in skill_text
    assert "references/core-pipeline-integration.md" in skill_text
    assert "--generic-implement notes" in skill_text
    assert "Current Runtime-Backed Recipes" in usage_text
    assert "--generic-implement notes" in usage_text
    assert "RUN_TS_REAL_TOOLCHAIN=1" in integration_text
    assert "core/pipeline_runner.py" in integration_text
