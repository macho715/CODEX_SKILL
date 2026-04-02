"""Packaged asset resolution and Codex skill installation helpers."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version as package_version
from importlib.resources.abc import Traversable
from importlib.resources import files
from pathlib import Path
import json
import shutil
import tempfile


ASSET_PACKAGE = "core._assets"
CODEX_INSTALL_PREFIX = "mstack-"
CODEX_MANIFEST = ".mstack-install.json"
CODEX_SKILL_DIR = "skills-codex"
CLASSIC_SKILL_DIR = "skills"
PRESET_DIR = "presets"


def asset_dir(name: str) -> Path:
    """Return a filesystem path for a packaged asset directory."""
    resource = files(ASSET_PACKAGE).joinpath(name)
    return _materialize_dir(resource, name)


def packaged_codex_skill_dirs() -> list[Path]:
    """Return packaged Codex skill directories."""
    root = asset_dir(CODEX_SKILL_DIR)
    return sorted(path for path in root.iterdir() if path.is_dir())


@dataclass(frozen=True)
class CodexInstallResult:
    """Summary of a Codex asset installation run."""

    target_dir: Path
    installed: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    overwritten: tuple[str, ...] = ()


def install_codex_skills(
    target_dir: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> CodexInstallResult:
    """Install packaged Codex skills into the target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    skipped: list[str] = []
    overwritten: list[str] = []
    collisions: list[str] = []

    for src in packaged_codex_skill_dirs():
        dest_name = f"{CODEX_INSTALL_PREFIX}{src.name}"
        dest = target_dir / dest_name

        if dest.exists():
            if _is_managed_codex_skill(dest):
                if force:
                    overwritten.append(dest_name)
                else:
                    skipped.append(dest_name)
                    continue
            else:
                collisions.append(dest_name)
                continue

        if dry_run:
            installed.append(dest_name)
            continue

        if dest.exists() and force:
            shutil.rmtree(dest)

        shutil.copytree(src, dest)
        manifest = {
            "managed_by": "mstack",
            "skill": src.name,
            "installed_name": dest_name,
            "version": _installed_package_version(),
        }
        (dest / CODEX_MANIFEST).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        installed.append(dest_name)

    if collisions:
        collision_text = ", ".join(sorted(collisions))
        raise FileExistsError(
            f"Target contains unmanaged collisions: {collision_text}. Use a clean target or remove them."
        )

    return CodexInstallResult(
        target_dir=target_dir,
        installed=tuple(installed),
        skipped=tuple(skipped),
        overwritten=tuple(overwritten),
    )


def _is_managed_codex_skill(path: Path) -> bool:
    """Return True when the destination looks like a managed MStack skill."""
    if not path.is_dir():
        return False
    return (path / CODEX_MANIFEST).exists()


def _materialize_dir(resource: Traversable, name: str) -> Path:
    """Return a filesystem path for a resource directory, extracting if needed."""
    if isinstance(resource, Path):
        return resource

    cache_dir = Path(tempfile.gettempdir()) / "mstack-assets" / _installed_package_version() / name
    if cache_dir.exists():
        return cache_dir

    _copy_traversable_tree(resource, cache_dir)
    return cache_dir


def _copy_traversable_tree(source: Traversable, target: Path) -> None:
    """Copy a Traversable directory tree to a filesystem path."""
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        child_target = target / child.name
        if child.is_dir():
            _copy_traversable_tree(child, child_target)
            continue
        child_target.write_bytes(child.read_bytes())


def _installed_package_version() -> str:
    """Return the installed package version for cache segregation."""
    try:
        return package_version("mstack")
    except PackageNotFoundError:
        return "dev"
