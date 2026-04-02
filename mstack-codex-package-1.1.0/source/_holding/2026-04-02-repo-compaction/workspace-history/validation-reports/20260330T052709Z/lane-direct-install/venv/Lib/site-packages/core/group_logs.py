"""core/group_logs.py — 단체방 로그 append/tail 유틸리티."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1
import json
from pathlib import Path
import re

from .types import GroupMessageEntry, GroupRoomMeta


GROUP_LOG_DIR = Path(".claude/group-logs")
ROOM_META_FILE = "room.json"
ROOM_MESSAGES_FILE = "messages.jsonl"
MESSAGE_CHAR_LIMIT = 500
ROOM_TAIL_RECENT = 5
ROOM_TAIL_MAX_CHARS = 800
ALLOWED_METADATA_KEYS = ("hook_event", "tool_name", "stage", "status", "agent_id")
SECRET_PATTERNS = (
    (re.compile(r"sk-[A-Za-z0-9_-]{10,}"), "sk-***"),
    (re.compile(r"ghp_[A-Za-z0-9]{10,}", re.IGNORECASE), "ghp_***"),
    (re.compile(r"(OPENAI_API_KEY\s*[=:]\s*)(\S+)", re.IGNORECASE), r"\1***"),
)


def group_log_root(project_dir: Path) -> Path:
    """프로젝트 기준 group log 루트 경로."""
    return project_dir / GROUP_LOG_DIR


def slugify_room_name(room_name: str) -> str:
    """방 이름을 Windows-safe slug로 변환한다."""
    normalized = room_name.strip()
    parts: list[str] = []
    last_was_dash = False
    for char in normalized:
        if char in '<>:"/\\|?*':
            char = " "
        if char.isalnum():
            parts.append(char.lower())
            last_was_dash = False
            continue
        if char in {" ", "-", "_"} and not last_was_dash:
            parts.append("-")
            last_was_dash = True

    slug = "".join(parts).strip("-")
    if slug:
        return slug[:80]

    digest = sha1(room_name.encode("utf-8")).hexdigest()[:8]
    return f"room-{digest}"


def room_dir(project_dir: Path, room_slug: str) -> Path:
    """방 디렉토리 경로."""
    return group_log_root(project_dir) / room_slug


def room_meta_path(project_dir: Path, room_slug: str) -> Path:
    """방 메타데이터 파일 경로."""
    return room_dir(project_dir, room_slug) / ROOM_META_FILE


def room_messages_path(project_dir: Path, room_slug: str) -> Path:
    """방 메시지 로그 파일 경로."""
    return room_dir(project_dir, room_slug) / ROOM_MESSAGES_FILE


def ensure_room(
    project_dir: Path,
    room_name: str,
    room_slug: str | None = None,
    *,
    timestamp: str | None = None,
) -> GroupRoomMeta:
    """방 디렉토리와 메타데이터를 생성하거나 갱신한다."""
    now = timestamp or utc_now()
    slug = room_slug or _resolve_room_slug(project_dir, room_name)
    target_dir = room_dir(project_dir, slug)
    target_dir.mkdir(parents=True, exist_ok=True)
    meta_path = room_meta_path(project_dir, slug)
    existing = read_room_meta(project_dir, slug)

    if existing is None:
        meta = GroupRoomMeta(
            room_name=room_name,
            room_slug=slug,
            display_name=room_name,
            created_at=now,
            updated_at=now,
        )
    else:
        meta = GroupRoomMeta(
            room_name=room_name,
            room_slug=slug,
            display_name=room_name,
            created_at=existing.created_at,
            updated_at=now,
        )

    meta_path.write_text(meta.to_json(), encoding="utf-8")
    return meta


def read_room_meta(project_dir: Path, room_slug: str) -> GroupRoomMeta | None:
    """방 메타데이터를 읽는다."""
    path = room_meta_path(project_dir, room_slug)
    if not path.exists():
        return None
    try:
        return GroupRoomMeta.from_json(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, TypeError):
        return None


def append_group_message(
    project_dir: Path,
    entry: GroupMessageEntry,
) -> Path:
    """메시지/이벤트를 append-only JSONL로 기록한다."""
    meta = ensure_room(project_dir, entry.room_name, entry.room_slug or None, timestamp=entry.timestamp)
    sanitized = GroupMessageEntry(
        room_name=meta.display_name,
        room_slug=meta.room_slug,
        event_type=entry.event_type.strip(),
        sender=entry.sender.strip(),
        message=_sanitize_text(entry.message, MESSAGE_CHAR_LIMIT),
        timestamp=entry.timestamp or utc_now(),
        session_id=entry.session_id,
        metadata=_sanitize_metadata(entry.metadata),
    )
    path = room_messages_path(project_dir, meta.room_slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(sanitized.to_jsonl() + "\n")
    return path


def load_room_messages(project_dir: Path, room_slug: str) -> list[GroupMessageEntry]:
    """방 로그 전체를 로드한다."""
    path = room_messages_path(project_dir, room_slug)
    if not path.exists():
        return []
    entries: list[GroupMessageEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            entries.append(GroupMessageEntry.from_jsonl(stripped))
        except (json.JSONDecodeError, TypeError):
            continue
    return entries


def tail_room_messages(
    project_dir: Path,
    room_slug: str,
    *,
    limit: int = ROOM_TAIL_RECENT,
    max_chars: int = ROOM_TAIL_MAX_CHARS,
) -> list[GroupMessageEntry]:
    """최근 room 로그를 길이 예산 안에서 반환한다."""
    recent = load_room_messages(project_dir, room_slug)[-limit:]
    selected: list[GroupMessageEntry] = []
    used = 0
    for entry in reversed(recent):
        cost = len(entry.message)
        if selected and used + cost > max_chars:
            break
        selected.append(entry)
        used += cost
    selected.reverse()
    return selected


def utc_now() -> str:
    """UTC ISO timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_room_slug(project_dir: Path, room_name: str) -> str:
    base = slugify_room_name(room_name)
    existing = read_room_meta(project_dir, base)
    if existing is None or existing.display_name == room_name:
        return base

    digest = sha1(room_name.encode("utf-8")).hexdigest()[:8]
    candidate = f"{base}--{digest}"
    existing = read_room_meta(project_dir, candidate)
    if existing is None or existing.display_name == room_name:
        return candidate
    return candidate


def _sanitize_metadata(metadata: dict[str, str] | None) -> dict[str, str]:
    if not metadata:
        return {}
    sanitized: dict[str, str] = {}
    for key in ALLOWED_METADATA_KEYS:
        value = metadata.get(key)
        if not value:
            continue
        sanitized[key] = _sanitize_text(str(value), 200)
    return sanitized


def _sanitize_text(text: str, limit: int) -> str:
    masked = text.strip()
    for pattern, replacement in SECRET_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked[:limit]
