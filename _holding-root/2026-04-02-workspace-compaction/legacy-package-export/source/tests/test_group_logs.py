"""tests/test_group_logs.py — core/group_logs.py 단위 테스트"""
from pathlib import Path

from core.group_logs import append_group_message, ensure_room, slugify_room_name, tail_room_messages
from core.types import GroupMessageEntry


def test_slugify_room_name_strips_windows_invalid_chars() -> None:
    slug = slugify_room_name("Ops: Review / Phase*1?")
    assert ":" not in slug
    assert "/" not in slug
    assert "*" not in slug
    assert slug.startswith("ops-review")


def test_ensure_room_updates_display_name_without_changing_slug(tmp_path: Path) -> None:
    meta = ensure_room(tmp_path, "Ops Review", "ops-review", timestamp="2026-03-25T10:00:00Z")
    updated = ensure_room(tmp_path, "Ops Review Renamed", "ops-review", timestamp="2026-03-25T10:10:00Z")
    assert meta.room_slug == updated.room_slug
    assert updated.display_name == "Ops Review Renamed"
    assert updated.created_at == "2026-03-25T10:00:00Z"


def test_append_group_message_masks_and_tails(tmp_path: Path) -> None:
    append_group_message(
        tmp_path,
        GroupMessageEntry(
            room_name="Ops Review",
            room_slug="ops-review",
            event_type="task_completed",
            sender="system",
            message="OPENAI_API_KEY=sk-secret1234567890",
            timestamp="2026-03-25T10:00:00Z",
            metadata={"hook_event": "TaskCompleted", "unexpected": "drop"},
        ),
    )
    append_group_message(
        tmp_path,
        GroupMessageEntry(
            room_name="Ops Review",
            room_slug="ops-review",
            event_type="teammate_idle",
            sender="system",
            message="idle",
            timestamp="2026-03-25T10:01:00Z",
        ),
    )

    entries = tail_room_messages(tmp_path, "ops-review", limit=5, max_chars=800)
    assert len(entries) == 2
    assert "***" in entries[0].message
    assert "unexpected" not in entries[0].metadata
    assert entries[-1].message == "idle"
