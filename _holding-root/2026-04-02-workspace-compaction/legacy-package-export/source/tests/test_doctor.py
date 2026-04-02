"""tests/test_doctor.py — mstack doctor 진단 테스트"""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from core.doctor import (
    CheckResult,
    Status,
    _run_cmd,
    check_claude_cli,
    check_git,
    check_git_bash,
    check_mstack_version,
    check_project,
    check_python,
    format_results,
    format_results_json,
    run_all_checks,
)


# ── check_python ──────────────────────────────────────

@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires Python 3.11+")
def test_check_python_pass():
    result = check_python()
    # We're running on Python 3.11+, so this should pass
    assert result.status == Status.PASS
    assert result.name == "Python"


def test_check_python_fail():
    with patch("core.doctor.sys") as mock_sys:
        mock_sys.version_info = type("VersionInfo", (), {
            "major": 3, "minor": 10, "micro": 0,
        })()
        result = check_python()
        assert result.status == Status.FAIL
        assert "3.11" in result.hint


# ── check_git ─────────────────────────────────────────

def test_check_git_pass():
    result = check_git()
    assert result.status == Status.PASS
    assert result.name == "Git"


def test_check_git_fail():
    with patch("core.doctor._run_cmd", return_value=(False, "")):
        result = check_git()
        assert result.status == Status.FAIL
        assert "git-scm.com" in result.hint


# ── check_git_bash ────────────────────────────────────

def test_check_git_bash_non_windows():
    with patch("core.doctor.platform") as mock_platform:
        mock_platform.system.return_value = "Linux"
        result = check_git_bash()
        assert result.status == Status.PASS
        assert "non-Windows" in result.message


def test_check_git_bash_windows_found():
    with patch("core.doctor.platform") as mock_platform, \
         patch("core.doctor.shutil") as mock_shutil:
        mock_platform.system.return_value = "Windows"
        mock_shutil.which.return_value = "C:\\Program Files\\Git\\bin\\bash.exe"
        result = check_git_bash()
        assert result.status == Status.PASS


def test_check_git_bash_windows_not_found():
    with patch("core.doctor.platform") as mock_platform, \
         patch("core.doctor.shutil") as mock_shutil:
        mock_platform.system.return_value = "Windows"
        mock_shutil.which.return_value = None
        result = check_git_bash()
        assert result.status == Status.WARN
        assert "gitforwindows.org" in result.hint


# ── check_mstack_version ─────────────────────────────

def test_check_mstack_version():
    result = check_mstack_version("1.1.0")
    assert result.status == Status.PASS
    assert result.message == "1.1.0"


# ── check_project ────────────────────────────────────

def test_check_project_full(tmp_path: Path):
    """Fully initialized project passes all checks."""
    (tmp_path / "CLAUDE.md").write_text("# Test", encoding="utf-8")
    skills = tmp_path / ".claude" / "skills" / "mstack"
    skills.mkdir(parents=True)
    for name in ["plan", "review", "ship", "qa", "investigate", "retro", "careful"]:
        (skills / f"{name}.md").write_text(f"# {name}", encoding="utf-8")
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "on-task-completed.sh").write_text("#!/bin/bash", encoding="utf-8")
    (hooks / "on-teammate-idle.sh").write_text("#!/bin/bash", encoding="utf-8")
    (tmp_path / ".claude" / "settings.json").write_text("{}", encoding="utf-8")

    results = check_project(tmp_path)
    assert all(r.status == Status.PASS for r in results)
    assert len(results) == 4


def test_check_project_empty(tmp_path: Path):
    """Empty directory fails CLAUDE.md and skills, warns on hooks and settings."""
    results = check_project(tmp_path)
    statuses = {r.name: r.status for r in results}
    assert statuses["CLAUDE.md"] == Status.FAIL
    assert statuses["Skills"] == Status.FAIL
    assert statuses["Hooks"] == Status.WARN
    assert statuses["settings.json"] == Status.WARN


def test_check_project_partial_skills(tmp_path: Path):
    """Partial skills directory triggers warning."""
    (tmp_path / "CLAUDE.md").write_text("# Test", encoding="utf-8")
    skills = tmp_path / ".claude" / "skills" / "mstack"
    skills.mkdir(parents=True)
    for name in ["plan", "review"]:
        (skills / f"{name}.md").write_text(f"# {name}", encoding="utf-8")

    results = check_project(tmp_path)
    skills_result = next(r for r in results if r.name == "Skills")
    assert skills_result.status == Status.WARN
    assert "2/7" in skills_result.message


# ── run_all_checks ────────────────────────────────────

def test_run_all_checks_returns_all(tmp_path: Path):
    results = run_all_checks(tmp_path, "1.1.0")
    names = [r.name for r in results]
    assert "Python" in names
    assert "Git" in names
    assert "Git Bash" in names
    assert "mstack" in names
    assert "CLAUDE.md" in names
    assert "Skills" in names
    assert "Hooks" in names
    assert "settings.json" in names


# ── format_results ────────────────────────────────────

def test_format_results_contains_sections(tmp_path: Path):
    results = [
        CheckResult("Python", Status.PASS, "3.12.4"),
        CheckResult("Git", Status.FAIL, "not found", hint="Install git"),
        CheckResult("CLAUDE.md", Status.PASS, "found (100 chars)"),
    ]
    output = format_results(results, tmp_path)
    assert "Environment Check" in output
    assert "Project Check" in output
    assert "✅ Python" in output
    assert "❌ Git" in output
    assert "→ Install git" in output
    assert "2/3 passed" in output
    assert "1 failure" in output


# ── format_results_json ──────────────────────────────

def test_format_results_json():
    results = [
        CheckResult("Python", Status.PASS, "3.12.4"),
        CheckResult("Git", Status.FAIL, "not found", hint="Install git"),
    ]
    data = format_results_json(results)
    assert len(data) == 2
    assert data[0]["status"] == "pass"
    assert data[1]["hint"] == "Install git"


# ── 미커버 라인 보강 (v1.3) ──────────────────────────────


def test_run_cmd_file_not_found():
    """존재하지 않는 명령어 실행 시 (False, '') 반환 (L34-35)."""
    ok, output = _run_cmd(["__nonexistent_command_xyz__"])
    assert ok is False
    assert output == ""


def test_run_cmd_timeout():
    """타임아웃 시 (False, '') 반환 (L34-35)."""
    with patch(
        "core.doctor.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="slow", timeout=10),
    ):
        ok, output = _run_cmd(["slow"])
        assert ok is False
        assert output == ""


def test_check_python_pass_mocked():
    """Python 3.11+ 환경을 mock으로 검증 (L42)."""
    with patch("core.doctor.sys") as mock_sys:
        mock_sys.version_info = type("VersionInfo", (), {
            "major": 3, "minor": 12, "micro": 0,
        })()
        result = check_python()
        assert result.status == Status.PASS
        assert "3.12.0" in result.message


def test_check_claude_cli_fail():
    """claude CLI 미설치 시 FAIL 반환 (L53)."""
    with patch("core.doctor._run_cmd", return_value=(False, "")):
        result = check_claude_cli()
        assert result.status == Status.FAIL
        assert "claude.ai/code" in result.hint


def test_format_results_project_hint(tmp_path: Path):
    """프로젝트 결과에 hint가 있을 때 표시 (L177)."""
    results = [
        CheckResult("Python", Status.PASS, "3.12.4"),
        CheckResult("CLAUDE.md", Status.FAIL, "not found", hint="Run mstack init"),
    ]
    output = format_results(results, tmp_path)
    assert "Project Check" in output
    assert "→ Run mstack init" in output


def test_format_results_warnings_plural(tmp_path: Path):
    """경고가 2건 이상이면 's'가 붙는지 확인 (L187)."""
    results = [
        CheckResult("Python", Status.PASS, "3.12.4"),
        CheckResult("Hooks", Status.WARN, "not found", hint="a"),
        CheckResult("settings.json", Status.WARN, "not found", hint="b"),
    ]
    output = format_results(results, tmp_path)
    assert "2 warnings" in output
