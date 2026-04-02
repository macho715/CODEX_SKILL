"""Shared fixtures for mstack tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_preset_dict() -> dict:
    """A minimal preset dictionary for testing."""
    return {
        "name": "test-preset",
        "lang": "python",
        "test_cmd": "pytest tests/",
        "lint_cmd": "flake8 src/",
        "type_cmd": "mypy src/",
        "rules": ["no bare except"],
        "permissions": {"bash_python": True},
        "hooks_level": "basic",
        "custom_skills": [],
        "domain_terms": {"PR": "Pull Request"},
        "fanr_rules": [],
    }


@pytest.fixture
def preset_json_file(tmp_path: Path, sample_preset_dict: dict) -> Path:
    """Write a preset JSON file and return its path."""
    path = tmp_path / "presets" / "test-preset.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sample_preset_dict), encoding="utf-8")
    return path


@pytest.fixture
def sample_cost_entry_dict() -> dict:
    """A minimal cost entry dictionary for testing."""
    return {
        "session_id": "sess-001",
        "timestamp": "2026-03-22T10:00:00Z",
        "model": "opus",
        "input_tokens": 1000,
        "output_tokens": 500,
        "cost_usd": 0.02,
        "duration_sec": 12.5,
        "event_type": "session",
        "details": {},
    }


@pytest.fixture
def python_project(tmp_path: Path) -> Path:
    """Create a fake Python project directory."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("# main", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("# test", encoding="utf-8")
    return tmp_path


@pytest.fixture
def ts_project(tmp_path: Path) -> Path:
    """Create a fake TypeScript project directory."""
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.ts").write_text("// index", encoding="utf-8")
    return tmp_path


@pytest.fixture
def go_project(tmp_path: Path) -> Path:
    """Create a fake Go project directory."""
    (tmp_path / "go.mod").write_text("module test", encoding="utf-8")
    (tmp_path / "cmd").mkdir()
    (tmp_path / "cmd" / "main.go").write_text("// main", encoding="utf-8")
    return tmp_path


@pytest.fixture
def rust_project(tmp_path: Path) -> Path:
    """Create a fake Rust project directory."""
    (tmp_path / "Cargo.toml").write_text("[package]\nname='test'", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.rs").write_text("// main", encoding="utf-8")
    return tmp_path


@pytest.fixture
def empty_project(tmp_path: Path) -> Path:
    """Create an empty project directory (no language markers)."""
    (tmp_path / "README.md").write_text("# test", encoding="utf-8")
    return tmp_path


# ── mstack v1.1 새 fixtures ──────────────────────────

@pytest.fixture
def project_dir(tmp_path):
    """임시 프로젝트 디렉토리 (Python 프로젝트)"""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"')
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    return tmp_path


@pytest.fixture
def hvdc_project(tmp_path):
    """HVDC 프리셋용 임시 프로젝트"""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "hvdc-test"')
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()
    return tmp_path


@pytest.fixture
def sample_cost_jsonl(tmp_path):
    """샘플 비용 JSONL (10건)"""
    path = tmp_path / "cost.jsonl"
    entries = []
    for i in range(10):
        entries.append(json.dumps({
            "session_id": f"sess-{i:03d}",
            "timestamp": f"2026-03-{10+i:02d}T10:00:00Z",
            "model": "sonnet-4" if i % 3 else "opus-4",
            "input_tokens": 10000 + i * 1000,
            "output_tokens": 5000 + i * 500,
            "cost_usd": 0.05 + i * 0.02,
            "duration_sec": 120 + i * 30,
            "event_type": "session",
        }))
    path.write_text("\n".join(entries), encoding="utf-8")
    return path
