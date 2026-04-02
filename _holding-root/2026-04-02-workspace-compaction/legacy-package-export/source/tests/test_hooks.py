"""tests/test_hooks.py — core/hooks.py 단위 테스트"""
import pytest
import shutil
import sys
import json
import stat
from pathlib import Path
from core.hooks import (
    BASIC_HOOKS,
    EXTENDED_HOOKS,
    deploy_hooks,
    gen_hook_stop,
    gen_hook_subagent_stop,
    gen_hook_task_completed,
    gen_hook_teammate_idle,
    generate_settings_json,
)
from core.config import load_preset


@pytest.fixture
def python_preset():
    return load_preset("python")


def test_deploy_basic_hooks(tmp_path, python_preset):
    hooks = deploy_hooks(tmp_path, python_preset, level="basic")
    assert len(hooks) == 2
    assert all(h.exists() for h in hooks)


def test_deploy_extended_hooks(tmp_path, python_preset):
    hooks = deploy_hooks(tmp_path, python_preset, level="extended")
    assert len(hooks) == 6
    assert all(h.exists() for h in hooks)


@pytest.mark.skipif(sys.platform == "win32", reason="Windows does not support Unix executable bits")
def test_hook_files_executable(tmp_path, python_preset):
    hooks = deploy_hooks(tmp_path, python_preset, level="basic")
    for h in hooks:
        assert h.stat().st_mode & stat.S_IEXEC, f"{h.name} is not executable"


def test_settings_json_structure(tmp_path, python_preset):
    settings = generate_settings_json(tmp_path, python_preset, level="basic")
    assert "hooks" in settings
    assert "env" in settings
    assert "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" in settings["env"]
    assert isinstance(settings["hooks"], list)
    assert len(settings["hooks"]) == 2


def test_settings_extended_has_six_hooks(tmp_path, python_preset):
    settings = generate_settings_json(tmp_path, python_preset, level="extended")
    assert len(settings["hooks"]) == 6


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None,
    reason="bash not available or Windows environment"
)
def test_pretooluse_denies_rm_rf(tmp_path, python_preset):
    import subprocess
    hooks = deploy_hooks(tmp_path, python_preset, level="extended")
    pre_tool = next(h for h in hooks if "pre-tool-use" in h.name)

    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /"}
    })
    result = subprocess.run(
        ["bash", str(pre_tool)],
        input=payload, capture_output=True, text=True, timeout=5
    )
    output = json.loads(result.stdout.strip())
    assert output["decision"] == "deny"


def test_stop_hook_calls_cost_py(python_preset):
    """v1.2: Stop Hook 스크립트가 cost.py auto-end를 호출하는지 확인"""
    script = gen_hook_stop()
    assert "cost.py" in script
    assert "auto-end" in script
    assert "--session-id" in script


def test_task_completed_hook_appends_room_log(python_preset):
    script = gen_hook_task_completed(python_preset)
    assert "room-log append" in script
    assert "--hook-event TaskCompleted" in script


def test_idle_and_subagent_hooks_append_room_log(python_preset):
    assert "room-log append" in gen_hook_teammate_idle(python_preset)
    assert "room-log append" in gen_hook_subagent_stop()
    assert "--hook-event SubagentStop" in gen_hook_subagent_stop()


def test_stop_hook_appends_room_log(python_preset):
    script = gen_hook_stop()
    assert "room-log append" in script
    assert "--hook-event Stop" in script


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None,
    reason="bash not available or Windows environment"
)
def test_pretooluse_approves_safe_command(tmp_path, python_preset):
    import subprocess
    hooks = deploy_hooks(tmp_path, python_preset, level="extended")
    pre_tool = next(h for h in hooks if "pre-tool-use" in h.name)

    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "echo hello"}
    })
    result = subprocess.run(
        ["bash", str(pre_tool)],
        input=payload, capture_output=True, text=True, timeout=5
    )
    output = json.loads(result.stdout.strip())
    assert output["decision"] == "approve"
