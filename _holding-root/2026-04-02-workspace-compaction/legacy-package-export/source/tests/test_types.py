"""tests/test_types.py — core/types.py 직렬화 함수 단위 테스트"""
import json
import pytest
from pathlib import Path
from core.types import (
    CostEntry,
    GroupMessageEntry,
    GroupRoomMeta,
    HookConfig,
    HookEvent,
    Lang,
    Preset,
)


# ── Preset.from_json ──────────────────────────────────

class TestPresetFromJson:
    """Preset.from_json 정상/에러 경로 테스트"""

    @pytest.fixture()
    def preset_json(self, tmp_path: Path) -> Path:
        data = {
            "name": "test-project",
            "lang": "python",
            "test_cmd": "pytest",
            "lint_cmd": "flake8",
            "type_cmd": "mypy",
            "rules": ["no bare except"],
        }
        p = tmp_path / "preset.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_from_json_returns_preset(self, preset_json: Path) -> None:
        result = Preset.from_json(preset_json)
        assert isinstance(result, Preset)
        assert result.name == "test-project"
        assert result.lang == Lang.PYTHON
        assert result.test_cmd == "pytest"

    def test_from_json_lang_enum(self, preset_json: Path) -> None:
        result = Preset.from_json(preset_json)
        assert result.lang is Lang.PYTHON

    def test_from_json_default_lang_fallback(self, tmp_path: Path) -> None:
        """lang 키 생략 시 data.get("lang", "unknown") fallback 경로 검증"""
        data = {
            "name": "no-lang",
            "test_cmd": "",
            "lint_cmd": "",
            "type_cmd": "",
        }
        p = tmp_path / "preset.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        result = Preset.from_json(p)
        assert result.lang == Lang.UNKNOWN

    def test_from_json_optional_fields_default(self, tmp_path: Path) -> None:
        data = {
            "name": "minimal",
            "lang": "ts",
            "test_cmd": "jest",
            "lint_cmd": "eslint",
            "type_cmd": "tsc",
        }
        p = tmp_path / "preset.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        result = Preset.from_json(p)
        assert result.rules == []
        assert result.permissions == {}
        assert result.hooks_level == "basic"
        assert result.custom_skills == []

    def test_from_json_invalid_json_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{broken", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            Preset.from_json(p)

    def test_from_json_missing_required_field_raises(self, tmp_path: Path) -> None:
        data = {"name": "partial"}  # missing test_cmd, lint_cmd, type_cmd, lang
        p = tmp_path / "missing.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(TypeError):
            Preset.from_json(p)

    def test_from_json_extra_field_ignored(self, tmp_path: Path) -> None:
        """JSON에 정의되지 않은 필드가 있어도 무시하고 Preset을 생성한다."""
        p = tmp_path / "extra.json"
        p.write_text(json.dumps({
            "name": "test",
            "lang": "python",
            "test_cmd": "pytest",
            "lint_cmd": "flake8",
            "type_cmd": "mypy",
            "unknown_field": "should be ignored",
            "another_extra": 42
        }))
        preset = Preset.from_json(p)
        assert preset.name == "test"
        assert preset.lang == Lang.PYTHON


# ── CostEntry.to_jsonl / from_jsonl ──────────────────

class TestCostEntrySerialization:
    """CostEntry 직렬화 왕복(round-trip) 테스트"""

    @pytest.fixture()
    def sample_entry(self) -> CostEntry:
        return CostEntry(
            session_id="sess-001",
            timestamp="2026-03-22T10:00:00Z",
            model="opus",
            input_tokens=1500,
            output_tokens=800,
            cost_usd=0.045,
            duration_sec=3.2,
            event_type="session",
            details={"skill": "dispatch"},
        )

    def test_to_jsonl_returns_valid_json(self, sample_entry: CostEntry) -> None:
        line = sample_entry.to_jsonl()
        parsed = json.loads(line)
        assert isinstance(parsed, dict)

    def test_to_jsonl_contains_all_fields(self, sample_entry: CostEntry) -> None:
        parsed = json.loads(sample_entry.to_jsonl())
        assert parsed["session_id"] == "sess-001"
        assert parsed["model"] == "opus"
        assert parsed["input_tokens"] == 1500
        assert parsed["cost_usd"] == 0.045
        assert parsed["details"] == {"skill": "dispatch"}

    def test_from_jsonl_returns_cost_entry(self, sample_entry: CostEntry) -> None:
        line = sample_entry.to_jsonl()
        restored = CostEntry.from_jsonl(line)
        assert isinstance(restored, CostEntry)

    def test_roundtrip_preserves_data(self, sample_entry: CostEntry) -> None:
        line = sample_entry.to_jsonl()
        restored = CostEntry.from_jsonl(line)
        assert restored == sample_entry  # dataclass __eq__
        assert restored.details == {"skill": "dispatch"}  # nested dict 확인

    def test_from_jsonl_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            CostEntry.from_jsonl("{bad json")

    def test_from_jsonl_missing_field_raises(self) -> None:
        incomplete = json.dumps({"session_id": "x", "timestamp": "t"})
        with pytest.raises(TypeError):
            CostEntry.from_jsonl(incomplete)

    def test_to_jsonl_unicode_preserved(self) -> None:
        entry = CostEntry(
            session_id="유니코드",
            timestamp="2026-03-22",
            model="sonnet",
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            duration_sec=0.0,
            details={"note": "한글 테스트"},
        )
        line = entry.to_jsonl()
        assert "유니코드" in line
        assert "한글 테스트" in line
        restored = CostEntry.from_jsonl(line)
        assert restored.session_id == "유니코드"


# ── HookConfig.to_settings_entry ──────────────────────

class TestHookConfigToSettingsEntry:
    """HookConfig.to_settings_entry 출력 구조 검증"""

    def test_returns_dict_with_matcher_and_hooks(self) -> None:
        cfg = HookConfig(
            event=HookEvent.STOP,
            hooks=[{"type": "command", "command": "echo done"}],
        )
        entry = cfg.to_settings_entry()
        assert "matcher" in entry
        assert "hooks" in entry
        assert entry["matcher"]["event"] == "Stop"

    def test_hooks_list_preserved(self) -> None:
        hooks_data = [
            {"type": "command", "command": "cmd1"},
            {"type": "command", "command": "cmd2"},
        ]
        cfg = HookConfig(event=HookEvent.PRE_TOOL_USE, hooks=hooks_data)
        entry = cfg.to_settings_entry()
        assert len(entry["hooks"]) == 2
        assert entry["hooks"][0]["command"] == "cmd1"

    def test_all_hook_events_produce_valid_matcher(self) -> None:
        for event in HookEvent:
            cfg = HookConfig(event=event, hooks=[])
            entry = cfg.to_settings_entry()
            assert entry["matcher"]["event"] == event.value


class TestGroupRoomMetaSerialization:
    def test_roundtrip(self) -> None:
        meta = GroupRoomMeta(
            room_name="Ops Review",
            room_slug="ops-review",
            display_name="Ops Review",
            created_at="2026-03-25T10:00:00Z",
            updated_at="2026-03-25T10:01:00Z",
        )
        restored = GroupRoomMeta.from_json(meta.to_json())
        assert restored == meta


class TestGroupMessageEntrySerialization:
    def test_roundtrip(self) -> None:
        entry = GroupMessageEntry(
            room_name="Ops Review",
            room_slug="ops-review",
            event_type="task_completed",
            sender="system",
            message="checks passed",
            timestamp="2026-03-25T10:00:00Z",
            session_id="sess-001",
            metadata={"hook_event": "TaskCompleted"},
        )
        restored = GroupMessageEntry.from_jsonl(entry.to_jsonl())
        assert restored == entry
