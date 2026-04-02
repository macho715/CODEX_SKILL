"""tests/test_assets.py — packaged asset and Codex install tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.assets import asset_dir, install_codex_skills, packaged_codex_skill_dirs
from core.skills import deploy_skills, packaged_skills_dir


def _packaged_plugin_bundle() -> Path:
    """Return the packaged Codex plugin bundle root.

    The bundle may be exposed either directly as a plugin directory or nested
    under a packaged plugin root. The tests only care that the bundle contains
    a real Codex plugin manifest and a mirrored skill tree.
    """

    for asset_name in ("plugins-codex", "mstack-codex", "plugins"):
        try:
            root = asset_dir(asset_name)
        except FileNotFoundError:
            continue

        for bundle_root in (root, root / "mstack-codex"):
            manifest = bundle_root / ".codex-plugin" / "plugin.json"
            skills_dir = bundle_root / "skills"
            if manifest.exists() and skills_dir.exists():
                return bundle_root

    raise AssertionError("packaged Codex plugin bundle was not found")


def test_asset_dir_exposes_packaged_runtime_dirs() -> None:
    skills_dir = asset_dir("skills")
    codex_dir = asset_dir("skills-codex")
    presets_dir = asset_dir("presets")
    docs_dir = asset_dir("docs")

    assert (skills_dir / "plan" / "SKILL.md").exists()
    assert (codex_dir / "plan" / "SKILL.md").exists()
    assert (presets_dir / "default.json").exists()
    assert (docs_dir / "MSTACK_SKILL_GUIDE.md").exists()


def test_asset_dir_exposes_packaged_plugin_bundle() -> None:
    plugin_bundle = _packaged_plugin_bundle()
    manifest = plugin_bundle / ".codex-plugin" / "plugin.json"
    skills_dir = plugin_bundle / "skills"

    assert manifest.exists()
    assert skills_dir.exists()
    assert (plugin_bundle / "MSTACK_SKILL_GUIDE.md").exists()
    assert (skills_dir / "plan" / "SKILL.md").exists()
    assert (skills_dir / "pipeline" / "agents" / "openai.yaml").exists()
    assert (skills_dir / "pipeline-coordinator" / "references" / "coordinator-input-contract.md").exists()

    packaged_skill_names = {path.name for path in packaged_codex_skill_dirs()}
    plugin_skill_names = {path.name for path in skills_dir.iterdir() if path.is_dir()}
    assert plugin_skill_names == packaged_skill_names


def test_packaged_skills_dir_can_be_deployed(tmp_path: Path) -> None:
    created = deploy_skills(packaged_skills_dir(), tmp_path / "skills")
    assert len(created) == 8
    assert all(path.exists() for path in created)


def test_install_codex_skills_installs_expected_layout(tmp_path: Path) -> None:
    result = install_codex_skills(tmp_path / "codex-skills")
    target = tmp_path / "codex-skills"

    assert len(result.installed) == 10
    assert (target / "mstack-plan" / "SKILL.md").exists()
    assert (target / "mstack-plan" / "agents" / "openai.yaml").exists()
    assert (target / "mstack-pipeline" / "references" / "usage-examples.md").exists()
    assert (target / "mstack-pipeline-coordinator" / "references" / "coordinator-input-contract.md").exists()
    assert (target / "MSTACK_SKILL_GUIDE.md").exists()


def test_install_codex_skills_is_idempotent_without_force(tmp_path: Path) -> None:
    target = tmp_path / "codex-skills"
    first = install_codex_skills(target)
    second = install_codex_skills(target)

    assert len(first.installed) == 10
    assert len(second.installed) == 0
    assert len(second.skipped) == 10


def test_install_codex_skills_force_overwrites_managed_dirs(tmp_path: Path) -> None:
    target = tmp_path / "codex-skills"
    install_codex_skills(target)
    skill_file = target / "mstack-plan" / "SKILL.md"
    skill_file.write_text("corrupted", encoding="utf-8")

    result = install_codex_skills(target, force=True)

    assert "mstack-plan" in result.overwritten
    assert "corrupted" not in skill_file.read_text(encoding="utf-8")


def test_install_codex_skills_rejects_unmanaged_collisions(tmp_path: Path) -> None:
    target = tmp_path / "codex-skills"
    collision = target / "mstack-plan"
    collision.mkdir(parents=True)
    (collision / "SKILL.md").write_text("foreign", encoding="utf-8")

    with pytest.raises(FileExistsError, match="unmanaged collisions"):
        install_codex_skills(target)
