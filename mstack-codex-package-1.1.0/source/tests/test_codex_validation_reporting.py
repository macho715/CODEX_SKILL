"""Tests for plugin validation reporting and runtime smoke artifact persistence."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parent.parent


def _load_script_module(name: str, relative_path: str):
    script_path = ROOT / relative_path
    spec = spec_from_file_location(name, script_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_persist_artifacts_copies_files_and_directories(tmp_path: Path) -> None:
    smoke = _load_script_module("codex_runtime_smoke_test", "scripts/codex_runtime_smoke.py")
    output_dir = tmp_path / "output"
    keep_dir = tmp_path / "keep"
    nested_dir = output_dir / "isolated-workdir"
    nested_dir.mkdir(parents=True)
    (output_dir / "summary.json").write_text('{"ok": true}', encoding="utf-8")
    (nested_dir / "notes.txt").write_text("runtime notes", encoding="utf-8")

    smoke._persist_artifacts(output_dir, keep_dir)

    assert (keep_dir / "summary.json").read_text(encoding="utf-8") == '{"ok": true}'
    assert (keep_dir / "isolated-workdir" / "notes.txt").read_text(encoding="utf-8") == "runtime notes"


def test_validate_plugin_install_accepts_expected_layout(tmp_path: Path) -> None:
    runner = _load_script_module("codex_validation_runner_test", "scripts/run_codex_skill_validation.py")
    plugin_root = tmp_path / "plugins" / "mstack-codex"
    skills_root = plugin_root / "skills"
    for name in ("careful", "dispatch", "investigate", "pipeline", "pipeline-coordinator", "plan", "qa", "retro", "review", "ship"):
        (skills_root / name).mkdir(parents=True)
    (plugin_root / ".codex-plugin").mkdir(parents=True)
    (plugin_root / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"name": "mstack-codex", "skills": "./skills"}),
        encoding="utf-8",
    )
    (plugin_root / ".mstack-plugin-install.json").write_text("{}", encoding="utf-8")

    marketplace_path = tmp_path / ".agents" / "plugins" / "marketplace.json"
    marketplace_path.parent.mkdir(parents=True)
    marketplace_path.write_text(
        json.dumps(
            {
                "name": "local-marketplace",
                "plugins": [
                    {
                        "name": "mstack-codex",
                        "source": {"source": "local", "path": "./plugins/mstack-codex"},
                        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                        "category": "Productivity",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    checks = runner._validate_plugin_install(plugin_root, marketplace_path)

    assert checks == [
        "validated:plugin-manifest",
        "validated:plugin-skill-tree",
        "validated:plugin-managed-marker",
        "validated:marketplace-entry",
    ]


def test_render_report_includes_lane_details_and_error_blocks() -> None:
    runner = _load_script_module("codex_validation_runner_render_test", "scripts/run_codex_skill_validation.py")
    summary = {
        "generated_at": "2026-03-30T00:00:00+00:00",
        "repo_root": "C:/repo",
        "overall_status": "failed",
        "automatic_patch_action": "manual-follow-up-required",
        "lanes": [
            {
                "name": "lane-plugin-install",
                "status": "passed",
                "duration_sec": 12.34,
                "details": ["validated:plugin-manifest"],
                "artifacts": {"report": "C:/repo/report.json"},
                "error": None,
            },
            {
                "name": "lane-runtime-smoke",
                "status": "failed",
                "duration_sec": 56.78,
                "details": [],
                "artifacts": {},
                "error": "runtime smoke failed",
            },
        ],
    }

    rendered = runner._render_report(summary)

    assert "# MStack Codex Skill Validation Report" in rendered
    assert "- Overall Status: `failed`" in rendered
    assert "### lane-plugin-install" in rendered
    assert "validated:plugin-manifest" in rendered
    assert "### lane-runtime-smoke" in rendered
    assert "```text" in rendered
    assert "runtime smoke failed" in rendered
