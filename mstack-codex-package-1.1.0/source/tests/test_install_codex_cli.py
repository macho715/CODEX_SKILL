"""tests/test_install_codex_cli.py — install-codex CLI tests."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "mstack.py"


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


def test_install_codex_dry_run_reports_expected_count(tmp_path: Path) -> None:
    result = _run_cli("install-codex", "--target", str(tmp_path), "--dry-run")
    assert result.returncode == 0, result.stderr or result.stdout
    assert "Installed: 10" in result.stdout
    assert not any(tmp_path.iterdir())


def test_install_codex_installs_expected_skill_tree(tmp_path: Path) -> None:
    result = _run_cli("install-codex", "--target", str(tmp_path))
    assert result.returncode == 0, result.stderr or result.stdout
    assert (tmp_path / "MSTACK_SKILL_GUIDE.md").exists()
    assert (tmp_path / "mstack-plan" / "SKILL.md").exists()
    assert (tmp_path / "mstack-plan" / "agents" / "openai.yaml").exists()
    assert (tmp_path / "mstack-pipeline" / "references" / "usage-examples.md").exists()
    assert (tmp_path / "mstack-pipeline-coordinator" / "references" / "coordinator-input-contract.md").exists()


def test_install_codex_plugin_dry_run_reports_expected_bundle(tmp_path: Path) -> None:
    plugin_target = tmp_path / "plugins" / "mstack-codex"
    marketplace_path = tmp_path / ".agents" / "plugins" / "marketplace.json"

    result = _run_cli(
        "install-codex-plugin",
        "--target",
        str(plugin_target),
        "--with-marketplace",
        "--marketplace-path",
        str(marketplace_path),
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "Installed: 10" in result.stdout
    assert "mstack-codex" in result.stdout
    assert ".codex-plugin/plugin.json" in result.stdout
    assert ".agents/plugins/marketplace.json" in result.stdout
    assert not any(tmp_path.iterdir())


def test_install_codex_plugin_installs_expected_plugin_tree(tmp_path: Path) -> None:
    plugin_target = tmp_path / "plugins" / "mstack-codex"
    marketplace_path = tmp_path / ".agents" / "plugins" / "marketplace.json"

    result = _run_cli(
        "install-codex-plugin",
        "--target",
        str(plugin_target),
        "--with-marketplace",
        "--marketplace-path",
        str(marketplace_path),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert (plugin_target / ".codex-plugin" / "plugin.json").exists()
    assert (plugin_target / "MSTACK_SKILL_GUIDE.md").exists()
    assert (plugin_target / "skills" / "plan" / "SKILL.md").exists()
    assert (plugin_target / "skills" / "pipeline" / "agents" / "openai.yaml").exists()
    assert (plugin_target / "skills" / "pipeline-coordinator" / "references" / "coordinator-input-contract.md").exists()
    assert marketplace_path.exists()

    manifest = json.loads((plugin_target / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "mstack-codex"
    assert manifest["skills"] in {"./skills", "./skills/"}
    assert "./plugins/mstack-codex" in marketplace_path.read_text(encoding="utf-8")


def test_install_codex_plugin_force_overwrites_managed_tree(tmp_path: Path) -> None:
    plugin_target = tmp_path / "plugins" / "mstack-codex"

    first = _run_cli("install-codex-plugin", "--target", str(plugin_target))
    assert first.returncode == 0, first.stderr or first.stdout

    skill_file = plugin_target / "skills" / "plan" / "SKILL.md"
    skill_file.write_text("corrupted", encoding="utf-8")

    result = _run_cli("install-codex-plugin", "--target", str(plugin_target), "--force")
    assert result.returncode == 0, result.stderr or result.stdout
    assert "corrupted" not in skill_file.read_text(encoding="utf-8")


def test_install_codex_plugin_rejects_unmanaged_collisions(tmp_path: Path) -> None:
    plugin_target = tmp_path / "plugins" / "mstack-codex"
    collision = plugin_target / "skills" / "plan"
    collision.mkdir(parents=True)
    (collision / "SKILL.md").write_text("foreign", encoding="utf-8")

    result = _run_cli("install-codex-plugin", "--target", str(plugin_target))

    assert result.returncode != 0
    assert "unmanaged collisions" in (result.stderr or result.stdout)
