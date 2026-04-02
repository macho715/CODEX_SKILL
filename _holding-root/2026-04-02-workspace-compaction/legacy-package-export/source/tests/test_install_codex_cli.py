"""tests/test_install_codex_cli.py — install-codex CLI tests."""

from __future__ import annotations

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
    assert "Installed: 9" in result.stdout
    assert not any(tmp_path.iterdir())


def test_install_codex_installs_expected_skill_tree(tmp_path: Path) -> None:
    result = _run_cli("install-codex", "--target", str(tmp_path))
    assert result.returncode == 0, result.stderr or result.stdout
    assert (tmp_path / "mstack-plan" / "SKILL.md").exists()
    assert (tmp_path / "mstack-plan" / "agents" / "openai.yaml").exists()
    assert (tmp_path / "mstack-pipeline" / "references" / "usage-examples.md").exists()
