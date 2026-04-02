"""core/session.py — 세션 상태 관리 (라우터 결과 지속성)

.claude/session.json에 RouterResult를 저장/복원.
CLAUDE.md 배너 생성 포함.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Mapping
from .types import RouterDecision, RouterResult

SESSION_FILE = ".claude/session.json"
ROOM_BINDING_FILE = ".claude/room-binding.json"
BANNER_START = "<!-- mstack-session-start -->"
BANNER_END = "<!-- mstack-session-end -->"

ACTION_GUIDE = MappingProxyType({
    RouterDecision.SINGLE: "작업을 바로 시작하세요.",
    RouterDecision.SUBAGENT: "서브에이전트를 사용하세요 (Task 도구).",
    RouterDecision.AGENT_TEAMS: "**Shift+Tab** 으로 위임 모드로 전환하세요.",
})


def _read_json_file(path: Path) -> dict | None:
    """JSON 파일을 읽고 dict를 반환한다."""
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def write_session(
    project_dir: Path,
    result: RouterResult,
    changed_files: list[str] | None = None,
    ttl_min: int = 30,
    room_name: str | None = None,
    room_slug: str | None = None,
) -> Path:
    """RouterResult를 .claude/session.json에 저장한다.

    Args:
        project_dir: 프로젝트 루트
        result: smart_route() 결과
        changed_files: 분석된 파일 목록
        ttl_min: 만료 시간 (분, 기본 30분)

    Returns:
        저장된 파일 경로
    """
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=ttl_min)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    existing = _read_json_file(project_dir / SESSION_FILE) or {}
    binding = read_room_binding(project_dir)
    data = {
        "decision": result.decision.value,
        "reason": result.reason,
        "file_count": result.file_count,
        "coordination_needed": result.coordination_needed,
        "estimated_cost_ratio": result.estimated_cost_ratio,
        "expires_at": expires_at,
        "changed_files": changed_files or [],
    }
    if room_name is not None:
        data["room_name"] = room_name
    elif binding is not None:
        data["room_name"] = binding[0]
    elif existing.get("room_name"):
        data["room_name"] = existing["room_name"]
    if room_slug is not None:
        data["room_slug"] = room_slug
    elif binding is not None:
        data["room_slug"] = binding[1]
    elif existing.get("room_slug"):
        data["room_slug"] = existing["room_slug"]

    session_path = project_dir / SESSION_FILE
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return session_path


def read_session_data(project_dir: Path) -> dict | None:
    """session.json 전체 payload를 읽는다."""
    data = _read_json_file(project_dir / SESSION_FILE)
    if data is None:
        return None
    if is_expired(data):
        return None
    return data


def read_session(project_dir: Path) -> RouterResult | None:
    """session.json을 읽어 RouterResult를 반환한다.

    만료됐거나 파일이 없으면 None 반환.
    """
    data = read_session_data(project_dir)
    if data is None:
        return None

    return RouterResult(
        decision=RouterDecision(data["decision"]),
        reason=data["reason"],
        file_count=data["file_count"],
        coordination_needed=data["coordination_needed"],
        estimated_cost_ratio=data["estimated_cost_ratio"],
    )


def is_expired(session: dict) -> bool:
    """세션 만료 여부를 확인한다."""
    expires_at = session.get("expires_at")
    if not expires_at:
        return True
    try:
        expiry = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        return datetime.now(timezone.utc) > expiry
    except ValueError:
        return True


def read_session_room(project_dir: Path) -> tuple[str, str] | None:
    """session.json에 저장된 활성 room binding을 읽는다."""
    data = read_session_data(project_dir)
    if data is None:
        return None
    room_name = data.get("room_name")
    room_slug = data.get("room_slug")
    if not room_name or not room_slug:
        return None
    return str(room_name), str(room_slug)


def read_room_binding_data(project_dir: Path) -> dict | None:
    """room-binding.json 전체 payload를 읽는다."""
    return _read_json_file(project_dir / ROOM_BINDING_FILE)


def read_room_binding(project_dir: Path) -> tuple[str, str] | None:
    """비만료 room binding 파일에서 활성 room binding을 읽는다."""
    data = read_room_binding_data(project_dir)
    if data is None:
        return None
    room_name = data.get("room_name")
    room_slug = data.get("room_slug")
    if not room_name or not room_slug:
        return None
    return str(room_name), str(room_slug)


def resolve_room_binding(
    project_dir: Path,
    env: Mapping[str, str] | None = None,
) -> tuple[str | None, str | None]:
    """env -> room-binding -> session fallback 순으로 활성 room binding을 결정한다."""
    env_room_name = None
    env_room_slug = None
    if env:
        env_room_name = env.get("MSTACK_ROOM_NAME")
        env_room_slug = env.get("MSTACK_ROOM_SLUG")

    binding = read_room_binding(project_dir)
    session_room = read_session_room(project_dir)
    room_name = env_room_name
    room_slug = env_room_slug

    if binding is not None:
        if room_name is None:
            room_name = binding[0]
        if room_slug is None:
            room_slug = binding[1]

    if session_room is not None:
        if room_name is None:
            room_name = session_room[0]
        if room_slug is None:
            room_slug = session_room[1]

    return room_name, room_slug


def write_room_binding(
    project_dir: Path,
    room_name: str,
    room_slug: str,
) -> Path:
    """비만료 room binding 파일을 기록한다."""
    path = project_dir / ROOM_BINDING_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "room_name": room_name,
        "room_slug": room_slug,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def set_room_binding(
    project_dir: Path,
    room_name: str,
    room_slug: str | None = None,
    ttl_min: int = 30,
) -> Path:
    """비만료 room binding 파일과 session.json에 활성 room binding을 저장한다."""
    existing = _read_json_file(project_dir / SESSION_FILE) or {}
    expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=ttl_min)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    if room_slug is None:
        from .group_logs import slugify_room_name

        room_slug = slugify_room_name(room_name)

    write_room_binding(project_dir, room_name, room_slug)

    data = {
        "decision": existing.get("decision", RouterDecision.SINGLE.value),
        "reason": existing.get("reason", "room binding updated"),
        "file_count": existing.get("file_count", 0),
        "coordination_needed": existing.get("coordination_needed", False),
        "estimated_cost_ratio": existing.get("estimated_cost_ratio", 1.0),
        "expires_at": existing.get("expires_at", expires_at),
        "changed_files": existing.get("changed_files", []),
        "room_name": room_name,
        "room_slug": room_slug,
    }

    session_path = project_dir / SESSION_FILE
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return session_path


def format_claude_md_banner(result: RouterResult) -> str:
    """CLAUDE.md 삽입용 세션 배너를 생성한다."""
    icon = {
        RouterDecision.SINGLE: "👤",
        RouterDecision.SUBAGENT: "🔀",
        RouterDecision.AGENT_TEAMS: "👥",
    }[result.decision]

    action = ACTION_GUIDE[result.decision]
    mode_label = result.decision.value.upper()

    lines = [
        BANNER_START,
        f"> {icon} **Session Mode: {mode_label}**"
        f" | {result.file_count} files"
        f" | cost {result.estimated_cost_ratio}x",
        f"> Reason: {result.reason}",
        f"> Action: {action}",
        BANNER_END,
    ]
    return "\n".join(lines)


def patch_claude_md(project_dir: Path, result: RouterResult) -> bool:
    """CLAUDE.md 상단에 세션 배너를 삽입 또는 교체한다.

    Returns:
        True if CLAUDE.md was found and patched, False otherwise
    """
    claude_path = project_dir / "CLAUDE.md"
    if not claude_path.exists():
        return False

    banner = format_claude_md_banner(result)
    content = claude_path.read_text(encoding="utf-8")

    # 기존 배너 제거
    if BANNER_START in content and BANNER_END in content:
        start_idx = content.index(BANNER_START)
        end_idx = content.index(BANNER_END) + len(BANNER_END)
        # 배너 다음 줄 개행 포함해 제거
        after = content[end_idx:].lstrip("\n")
        content = content[:start_idx] + after

    # 상단에 새 배너 삽입
    claude_path.write_text(banner + "\n" + content, encoding="utf-8")
    return True


def patch_settings_env(project_dir: Path, result: RouterResult) -> bool:
    """settings.json의 env에 MSTACK_SESSION_MODE를 기록한다.

    Returns:
        True if settings.json was found and patched, False otherwise
    """
    settings_path = project_dir / ".claude" / "settings.json"
    if not settings_path.exists():
        return False

    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    settings.setdefault("env", {})
    settings["env"]["MSTACK_SESSION_MODE"] = result.decision.value

    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False)
    )
    return True
