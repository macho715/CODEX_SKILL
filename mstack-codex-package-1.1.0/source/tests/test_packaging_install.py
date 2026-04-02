"""tests/test_packaging_install.py — wheel packaging smoke for Codex install."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import venv


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def test_wheel_install_supports_install_codex(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()

    build = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", str(wheelhouse)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=240,
    )
    assert build.returncode == 0, build.stderr or build.stdout

    wheels = sorted(wheelhouse.glob("mstack-*.whl"))
    assert wheels, "wheel was not built"

    venv_dir = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    venv_python = _venv_python(venv_dir)

    install = subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheels[-1])],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=240,
    )
    assert install.returncode == 0, install.stderr or install.stdout

    help_run = subprocess.run(
        [str(venv_python), "-m", "mstack", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )
    assert help_run.returncode == 0, help_run.stderr or help_run.stdout
    assert "install-codex" in help_run.stdout

    target = tmp_path / "installed-codex-skills"
    install_codex = subprocess.run(
        [str(venv_python), "-m", "mstack", "install-codex", "--target", str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )
    assert install_codex.returncode == 0, install_codex.stderr or install_codex.stdout
    assert (target / "MSTACK_SKILL_GUIDE.md").exists()
    assert (target / "mstack-plan" / "SKILL.md").exists()
    assert (target / "mstack-plan" / "agents" / "openai.yaml").exists()
    assert (target / "mstack-pipeline" / "references" / "core-pipeline-integration.md").exists()
    assert (target / "mstack-pipeline-coordinator" / "references" / "coordinator-input-contract.md").exists()


def test_wheel_install_supports_install_codex_plugin(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()

    build = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", str(wheelhouse)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=240,
    )
    assert build.returncode == 0, build.stderr or build.stdout

    wheels = sorted(wheelhouse.glob("mstack-*.whl"))
    assert wheels, "wheel was not built"

    venv_dir = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True).create(venv_dir)
    venv_python = _venv_python(venv_dir)

    install = subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheels[-1])],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=240,
    )
    assert install.returncode == 0, install.stderr or install.stdout

    help_run = subprocess.run(
        [str(venv_python), "-m", "mstack", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )
    assert help_run.returncode == 0, help_run.stderr or help_run.stdout
    assert "install-codex" in help_run.stdout
    assert "install-codex-plugin" in help_run.stdout

    plugin_target = tmp_path / "installed-codex-plugin"
    marketplace_path = tmp_path / ".agents" / "plugins" / "marketplace.json"
    install_plugin = subprocess.run(
        [
            str(venv_python),
            "-m",
            "mstack",
            "install-codex-plugin",
            "--target",
            str(plugin_target),
            "--with-marketplace",
            "--marketplace-path",
            str(marketplace_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )
    assert install_plugin.returncode == 0, install_plugin.stderr or install_plugin.stdout
    assert (plugin_target / ".codex-plugin" / "plugin.json").exists()
    assert (plugin_target / "MSTACK_SKILL_GUIDE.md").exists()
    assert (plugin_target / "skills" / "plan" / "SKILL.md").exists()
    assert (plugin_target / "skills" / "pipeline-coordinator" / "references" / "coordinator-input-contract.md").exists()
    assert marketplace_path.exists()
