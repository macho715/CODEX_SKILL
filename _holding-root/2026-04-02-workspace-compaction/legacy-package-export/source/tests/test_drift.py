"""tests/test_drift.py — core/drift.py 단위 테스트"""
import pytest
from pathlib import Path
from core.drift import (
    compute_hash,
    check_drift,
    smart_route,
    detect_cross_module,
    detect_api_contract,
)
from core.types import RouterDecision


def test_compute_hash_returns_12_chars(tmp_path):
    f = tmp_path / "file.txt"
    f.write_bytes(b"hello world")
    result = compute_hash(f)
    assert len(result) == 12
    assert all(c in "0123456789abcdef" for c in result)


def test_check_drift_ok(tmp_path):
    f = tmp_path / "CLAUDE.md"
    f.write_text("content", encoding="utf-8")
    expected_hash = compute_hash(f)

    results = check_drift(tmp_path, {"CLAUDE.md": expected_hash})
    assert len(results) == 1
    assert results[0].status == "ok"


def test_check_drift_modified(tmp_path):
    f = tmp_path / "CLAUDE.md"
    f.write_text("content", encoding="utf-8")

    results = check_drift(tmp_path, {"CLAUDE.md": "wronghash000"})
    assert results[0].status == "modified"
    assert results[0].actual_hash is not None


def test_check_drift_missing(tmp_path):
    results = check_drift(tmp_path, {"missing.md": "abc123"})
    assert results[0].status == "missing"
    assert results[0].actual_hash is None


def test_smart_route_single():
    result = smart_route(["file1.py", "file2.py"])
    assert result.decision == RouterDecision.SINGLE
    assert result.estimated_cost_ratio == 1.0


def test_smart_route_subagent():
    files = ["src/a.py", "src/b.py", "src/c.py", "src/d.py"]
    result = smart_route(files, has_api_contract=False, has_cross_module_deps=False)
    assert result.decision == RouterDecision.SUBAGENT
    assert result.estimated_cost_ratio == 1.5


def test_smart_route_agent_teams_api():
    # 3+ files with api_contract triggers AGENT_TEAMS (n<3 → SINGLE takes priority)
    result = smart_route(["schema.py", "main.py", "utils.py"], has_api_contract=True)
    assert result.decision == RouterDecision.AGENT_TEAMS
    assert result.coordination_needed is True


def test_smart_route_agent_teams_large():
    files = [f"file{i}.py" for i in range(6)]
    result = smart_route(files)
    assert result.decision == RouterDecision.AGENT_TEAMS


def test_smart_route_cost_note_in_reason():
    files = [f"file{i}.py" for i in range(6)]
    result = smart_route(files, cost_sensitive=True)
    assert "⚠" in result.reason or "3.5x" in result.reason


def test_detect_cross_module_true():
    files = ["src/main.py", "tests/test_main.py"]
    assert detect_cross_module(files) is True


def test_detect_cross_module_false():
    files = ["src/a.py", "src/b.py"]
    assert detect_cross_module(files) is False


def test_detect_api_contract_true():
    assert detect_api_contract(["core/types.py"]) is True
    assert detect_api_contract(["api/schema.json"]) is True


def test_detect_api_contract_false():
    assert detect_api_contract(["src/main.py", "tests/test_foo.py"]) is False
