"""core/doctor.py — 환경 진단 (mstack doctor)"""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: Status
    message: str
    hint: str = ""


def _run_cmd(cmd: list[str]) -> tuple[bool, str]:
    """Run a command and return (success, stdout_stripped)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def check_python() -> CheckResult:
    ver = sys.version_info
    version_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    if (ver.major, ver.minor) >= (3, 11):
        return CheckResult("Python", Status.PASS, version_str)
    return CheckResult(
        "Python", Status.FAIL, version_str,
        hint="Python 3.11+ required",
    )


def check_claude_cli() -> CheckResult:
    ok, output = _run_cmd(["claude", "--version"])
    if ok and output:
        return CheckResult("Claude Code", Status.PASS, output)
    return CheckResult(
        "Claude Code", Status.FAIL, "not found",
        hint="Install: https://claude.ai/code",
    )


def check_git() -> CheckResult:
    ok, output = _run_cmd(["git", "--version"])
    if ok and output:
        version = output.replace("git version ", "")
        return CheckResult("Git", Status.PASS, version)
    return CheckResult(
        "Git", Status.FAIL, "not found",
        hint="Install: https://git-scm.com",
    )


def check_git_bash() -> CheckResult:
    if platform.system() != "Windows":
        return CheckResult("Git Bash", Status.PASS, "not required (non-Windows)")

    bash_path = shutil.which("bash")
    if bash_path:
        return CheckResult("Git Bash", Status.PASS, bash_path)
    return CheckResult(
        "Git Bash", Status.WARN, "not found",
        hint="Required for hooks on Windows. Install: https://gitforwindows.org",
    )


def check_mstack_version(version: str) -> CheckResult:
    return CheckResult("mstack", Status.PASS, version)


def check_project(cwd: Path) -> list[CheckResult]:
    results: list[CheckResult] = []

    # CLAUDE.md
    claude_md = cwd / "CLAUDE.md"
    if claude_md.exists():
        size = len(claude_md.read_text(encoding="utf-8"))
        results.append(CheckResult("CLAUDE.md", Status.PASS, f"found ({size} chars)"))
    else:
        results.append(CheckResult(
            "CLAUDE.md", Status.FAIL, "not found",
            hint="Run `mstack init` first",
        ))

    # Skills
    skills_dir = cwd / ".claude" / "skills" / "mstack"
    if skills_dir.is_dir():
        skill_files = list(skills_dir.glob("*.md"))
        count = len(skill_files)
        if count >= 7:
            results.append(CheckResult("Skills", Status.PASS, f"{count}/7 files"))
        else:
            results.append(CheckResult(
                "Skills", Status.WARN, f"{count}/7 files",
                hint="Some skills missing. Run `mstack init --force`",
            ))
    else:
        results.append(CheckResult(
            "Skills", Status.FAIL, "directory not found",
            hint="Run `mstack init` first",
        ))

    # Hooks
    hooks_dir = cwd / ".claude" / "hooks"
    if hooks_dir.is_dir():
        hook_files = [f for f in hooks_dir.iterdir() if f.is_file()]
        count = len(hook_files)
        level = "extended" if count >= 5 else "basic" if count >= 2 else "minimal"
        results.append(CheckResult("Hooks", Status.PASS, f"{count} files ({level})"))
    else:
        results.append(CheckResult(
            "Hooks", Status.WARN, "directory not found",
            hint="Run `mstack init` to set up hooks",
        ))

    # settings.json
    settings = cwd / ".claude" / "settings.json"
    if settings.exists():
        results.append(CheckResult("settings.json", Status.PASS, "found"))
    else:
        results.append(CheckResult(
            "settings.json", Status.WARN, "not found",
            hint="Run `mstack init` to generate settings.json",
        ))

    return results


def run_all_checks(cwd: Path, version: str) -> list[CheckResult]:
    env_checks = [
        check_python(),
        check_claude_cli(),
        check_git(),
        check_git_bash(),
        check_mstack_version(version),
    ]
    project_checks = check_project(cwd)
    return [*env_checks, *project_checks]


def format_results(results: list[CheckResult], cwd: Path) -> str:
    icons = {Status.PASS: "✅", Status.WARN: "⚠️", Status.FAIL: "❌"}
    lines: list[str] = []

    # Split into env and project sections
    env_names = {"Python", "Claude Code", "Git", "Git Bash", "mstack"}
    env_results = [r for r in results if r.name in env_names]
    project_results = [r for r in results if r.name not in env_names]

    lines.append("[mstack] 🔍 Environment Check")
    for r in env_results:
        lines.append(f"  {icons[r.status]} {r.name}: {r.message}")
        if r.hint:
            lines.append(f"     → {r.hint}")

    if project_results:
        lines.append(f"\n[mstack] 📁 Project Check ({cwd})")
        for r in project_results:
            lines.append(f"  {icons[r.status]} {r.name}: {r.message}")
            if r.hint:
                lines.append(f"     → {r.hint}")

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.status == Status.PASS)
    warnings = sum(1 for r in results if r.status == Status.WARN)
    failures = sum(1 for r in results if r.status == Status.FAIL)

    parts = [f"{passed}/{total} passed"]
    if warnings:
        parts.append(f"{warnings} warning{'s' if warnings > 1 else ''}")
    if failures:
        parts.append(f"{failures} failure{'s' if failures > 1 else ''}")

    lines.append(f"\n[mstack] Result: {', '.join(parts)}")
    return "\n".join(lines)


def format_results_json(results: list[CheckResult]) -> list[dict]:
    return [
        {
            "name": r.name,
            "status": r.status.value,
            "message": r.message,
            "hint": r.hint,
        }
        for r in results
    ]
