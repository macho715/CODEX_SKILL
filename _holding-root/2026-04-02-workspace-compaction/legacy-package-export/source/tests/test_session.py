"""tests/test_session.py — core/session.py 단위 테스트"""
import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from core.session import (
    write_session,
    read_session,
    read_session_data,
    read_room_binding,
    read_room_binding_data,
    read_session_room,
    resolve_room_binding,
    set_room_binding,
    write_room_binding,
    is_expired,
    format_claude_md_banner,
    patch_claude_md,
    patch_settings_env,
    BANNER_START,
    BANNER_END,
)
from core.types import RouterDecision, RouterResult


@pytest.fixture
def single_result():
    return RouterResult(
        decision=RouterDecision.SINGLE,
        reason="Only 2 files — single session sufficient",
        file_count=2,
        coordination_needed=False,
        estimated_cost_ratio=1.0,
    )


@pytest.fixture
def agent_teams_result():
    return RouterResult(
        decision=RouterDecision.AGENT_TEAMS,
        reason="Cross-module coordination needed",
        file_count=5,
        coordination_needed=True,
        estimated_cost_ratio=3.5,
    )


def test_write_session_creates_file(tmp_path, single_result):
    path = write_session(tmp_path, single_result, ["src/a.py", "src/b.py"])
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["decision"] == "single"
    assert data["file_count"] == 2
    assert data["changed_files"] == ["src/a.py", "src/b.py"]
    assert "expires_at" in data


def test_read_session_returns_result(tmp_path, agent_teams_result):
    write_session(tmp_path, agent_teams_result)
    result = read_session(tmp_path)
    assert result is not None
    assert result.decision == RouterDecision.AGENT_TEAMS
    assert result.estimated_cost_ratio == 3.5


def test_read_session_returns_none_if_missing(tmp_path):
    assert read_session(tmp_path) is None


def test_is_expired_future():
    future = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    assert is_expired({"expires_at": future}) is False


def test_is_expired_past():
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    assert is_expired({"expires_at": past}) is True


def test_is_expired_missing_key():
    assert is_expired({}) is True


def test_format_banner_contains_decision(agent_teams_result):
    banner = format_claude_md_banner(agent_teams_result)
    assert BANNER_START in banner
    assert BANNER_END in banner
    assert "AGENT_TEAMS" in banner
    assert "Shift+Tab" in banner
    assert "3.5x" in banner


def test_format_banner_single(single_result):
    banner = format_claude_md_banner(single_result)
    assert "SINGLE" in banner
    assert "👤" in banner


def test_patch_claude_md_inserts_banner(tmp_path, agent_teams_result):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# MyProject\n\nSome content", encoding="utf-8")

    result = patch_claude_md(tmp_path, agent_teams_result)
    assert result is True

    content = claude_md.read_text(encoding="utf-8")
    assert BANNER_START in content
    assert "AGENT_TEAMS" in content
    assert "# MyProject" in content  # 기존 내용 보존


def test_patch_claude_md_replaces_existing_banner(tmp_path, single_result, agent_teams_result):
    claude_md = tmp_path / "CLAUDE.md"
    initial = f"{BANNER_START}\n> 👤 SINGLE\n{BANNER_END}\n# MyProject"
    claude_md.write_text(initial, encoding="utf-8")

    patch_claude_md(tmp_path, agent_teams_result)
    content = claude_md.read_text(encoding="utf-8")

    assert content.count(BANNER_START) == 1  # 중복 없음
    assert "AGENT_TEAMS" in content
    assert "SINGLE" not in content or "SINGLE" in "AGENT_TEAMS"  # 이전 배너 사라짐


def test_patch_claude_md_returns_false_if_missing(tmp_path, single_result):
    assert patch_claude_md(tmp_path, single_result) is False


def test_patch_settings_env(tmp_path, agent_teams_result):
    settings_dir = tmp_path / ".claude"
    settings_dir.mkdir()
    settings_path = settings_dir / "settings.json"
    settings_path.write_text(
        json.dumps({"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}}),
        encoding="utf-8",
    )

    result = patch_settings_env(tmp_path, agent_teams_result)
    assert result is True

    data = json.loads(settings_path.read_text())
    assert data["env"]["MSTACK_SESSION_MODE"] == "agent_teams"
    assert data["env"]["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] == "1"  # 기존 값 보존


def test_patch_settings_env_returns_false_if_missing(tmp_path, single_result):
    assert patch_settings_env(tmp_path, single_result) is False


# ── 미커버 라인 보강 (v1.3) ──────────────────────────────


def test_read_session_corrupt_json(tmp_path, single_result):
    """session.json이 깨진 JSON이면 None 반환 (L72-73)."""
    write_session(tmp_path, single_result)
    session_path = tmp_path / ".claude" / "session.json"
    session_path.write_text("NOT VALID JSON {{{", encoding="utf-8")
    assert read_session(tmp_path) is None


def test_read_session_expired_returns_none(tmp_path, single_result):
    """만료된 세션이면 None 반환 (L76)."""
    write_session(tmp_path, single_result, ttl_min=0)
    # ttl_min=0이면 즉시 만료 — 약간의 시간 지연으로 expired
    import time
    time.sleep(0.1)
    assert read_session(tmp_path) is None


def test_is_expired_invalid_format():
    """expires_at 형식이 잘못되면 True 반환 (L97-98)."""
    assert is_expired({"expires_at": "not-a-date"}) is True
    assert is_expired({"expires_at": "2025/01/01"}) is True


def test_patch_settings_env_corrupt_json(tmp_path, single_result):
    """settings.json이 깨진 JSON이면 False 반환 (L162-163)."""
    settings_dir = tmp_path / ".claude"
    settings_dir.mkdir()
    settings_path = settings_dir / "settings.json"
    settings_path.write_text("{broken json!!!", encoding="utf-8")
    assert patch_settings_env(tmp_path, single_result) is False


def test_set_room_binding_creates_session_payload(tmp_path):
    path = set_room_binding(tmp_path, "Ops Review", "ops-review")
    assert path.exists()
    data = read_session_data(tmp_path)
    assert data is not None
    assert data["room_name"] == "Ops Review"
    assert data["room_slug"] == "ops-review"
    binding = read_room_binding_data(tmp_path)
    assert binding is not None
    assert binding["room_name"] == "Ops Review"
    assert binding["room_slug"] == "ops-review"


def test_write_session_preserves_existing_room_binding(tmp_path, agent_teams_result):
    set_room_binding(tmp_path, "Ops Review", "ops-review")
    write_session(tmp_path, agent_teams_result, ["core/types.py"])
    assert read_session_room(tmp_path) == ("Ops Review", "ops-review")


def test_resolve_room_binding_prefers_env(tmp_path):
    set_room_binding(tmp_path, "Ops Review", "ops-review")
    room_name, room_slug = resolve_room_binding(
        tmp_path,
        {"MSTACK_ROOM_NAME": "War Room", "MSTACK_ROOM_SLUG": "war-room"},
    )
    assert room_name == "War Room"
    assert room_slug == "war-room"


def test_write_room_binding_roundtrip(tmp_path):
    path = write_room_binding(tmp_path, "Ops Review", "ops-review")
    assert path.exists()
    assert read_room_binding(tmp_path) == ("Ops Review", "ops-review")


def test_resolve_room_binding_prefers_binding_file_over_session_fallback(tmp_path, agent_teams_result):
    write_room_binding(tmp_path, "Bound Room", "bound-room")
    write_session(
        tmp_path,
        agent_teams_result,
        ["core/session.py"],
        room_name="Session Room",
        room_slug="session-room",
    )
    room_name, room_slug = resolve_room_binding(tmp_path, {})
    assert room_name == "Bound Room"
    assert room_slug == "bound-room"


def test_resolve_room_binding_uses_binding_file_when_session_is_expired(tmp_path, single_result):
    set_room_binding(tmp_path, "Ops Review", "ops-review")
    write_session(tmp_path, single_result, ["core/session.py"], ttl_min=0)

    session_path = tmp_path / ".claude" / "session.json"
    data = json.loads(session_path.read_text(encoding="utf-8"))
    data["expires_at"] = "2000-01-01T00:00:00Z"
    session_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    room_name, room_slug = resolve_room_binding(tmp_path, {})
    assert room_name == "Ops Review"
    assert room_slug == "ops-review"
