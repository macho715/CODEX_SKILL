"""tests/test_mstack_room_log_cli.py — room-log CLI smoke tests."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "mstack.py"


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=cwd,
    )


def test_room_log_append_creates_room_dir_and_session_binding(tmp_path: Path) -> None:
    result = _run_cli(
        "room-log",
        "append",
        "--room-name",
        "Ops Review",
        "--event-type",
        "task_completed",
        "--sender",
        "system",
        "--message",
        "checks passed",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    log_path = tmp_path / ".claude" / "group-logs" / "ops-review" / "messages.jsonl"
    assert log_path.exists()
    session_path = tmp_path / ".claude" / "session.json"
    assert session_path.exists()
    data = json.loads(session_path.read_text(encoding="utf-8"))
    assert data["room_name"] == "Ops Review"
    assert data["room_slug"] == "ops-review"


def test_room_log_bind_bootstraps_room_and_session_binding(tmp_path: Path) -> None:
    result = _run_cli(
        "room-log",
        "bind",
        "--room-name",
        "Ops Review",
        "--json",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["room_name"] == "Ops Review"
    assert data["room_slug"] == "ops-review"
    assert (tmp_path / ".claude" / "group-logs" / "ops-review" / "room.json").exists()
    assert (tmp_path / ".claude" / "room-binding.json").exists()
    session_path = tmp_path / ".claude" / "session.json"
    assert session_path.exists()


def test_room_log_tail_returns_recent_entries_as_json(tmp_path: Path) -> None:
    for event_type, message in (
        ("task_completed", "checks passed"),
        ("teammate_idle", "idle"),
    ):
        result = _run_cli(
            "room-log",
            "append",
            "--room-name",
            "Ops Review",
            "--event-type",
            event_type,
            "--sender",
            "system",
            "--message",
            message,
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr or result.stdout

    tail = _run_cli("room-log", "tail", "--room-slug", "ops-review", "--json", cwd=tmp_path)
    assert tail.returncode == 0, tail.stderr or tail.stdout
    data = json.loads(tail.stdout)
    assert [item["message"] for item in data] == ["checks passed", "idle"]


def test_room_log_append_uses_bound_room_without_room_args(tmp_path: Path) -> None:
    bind = _run_cli(
        "room-log",
        "bind",
        "--room-name",
        "Ops Review",
        cwd=tmp_path,
    )
    assert bind.returncode == 0, bind.stderr or bind.stdout

    append = _run_cli(
        "room-log",
        "append",
        "--event-type",
        "task_completed",
        "--sender",
        "system",
        "--message",
        "checks passed",
        cwd=tmp_path,
    )
    assert append.returncode == 0, append.stderr or append.stdout
    log_path = tmp_path / ".claude" / "group-logs" / "ops-review" / "messages.jsonl"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_room_log_tail_accepts_room_name_without_existing_binding(tmp_path: Path) -> None:
    result = _run_cli(
        "room-log",
        "append",
        "--room-name",
        "Ops Review",
        "--event-type",
        "task_completed",
        "--sender",
        "system",
        "--message",
        "checks passed",
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    session_path = tmp_path / ".claude" / "session.json"
    session_path.unlink()

    tail = _run_cli("room-log", "tail", "--room-name", "Ops Review", "--json", cwd=tmp_path)
    assert tail.returncode == 0, tail.stderr or tail.stdout
    data = json.loads(tail.stdout)
    assert [item["message"] for item in data] == ["checks passed"]


def test_room_log_append_and_tail_work_with_binding_file_after_session_expiry(tmp_path: Path) -> None:
    bind = _run_cli(
        "room-log",
        "bind",
        "--room-name",
        "Ops Review",
        cwd=tmp_path,
    )
    assert bind.returncode == 0, bind.stderr or bind.stdout

    session_path = tmp_path / ".claude" / "session.json"
    payload = json.loads(session_path.read_text(encoding="utf-8"))
    payload["expires_at"] = "2000-01-01T00:00:00Z"
    session_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    append = _run_cli(
        "room-log",
        "append",
        "--event-type",
        "task_completed",
        "--sender",
        "system",
        "--message",
        "after expiry",
        cwd=tmp_path,
    )
    assert append.returncode == 0, append.stderr or append.stdout

    tail = _run_cli("room-log", "tail", "--json", cwd=tmp_path)
    assert tail.returncode == 0, tail.stderr or tail.stdout
    data = json.loads(tail.stdout)
    assert [item["message"] for item in data] == ["after expiry"]
