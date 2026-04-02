"""Optional integration test for the real Codex runtime smoke flow."""

from __future__ import annotations

import json
from pathlib import Path
import os
import shutil
import subprocess
import sys

import pytest


RUN_RUNTIME_SMOKE = os.getenv("RUN_CODEX_RUNTIME_SMOKE") == "1"


@pytest.mark.skipif(not RUN_RUNTIME_SMOKE, reason="set RUN_CODEX_RUNTIME_SMOKE=1 to enable")
@pytest.mark.skipif(shutil.which("codex") is None, reason="codex CLI not installed")
def test_codex_runtime_smoke_script_runs_and_cleans_up() -> None:
    """Run the real runtime smoke script and verify cleanup of temp skills."""
    repo_root = Path(__file__).resolve().parent.parent
    script = repo_root / "scripts" / "codex_runtime_smoke.py"
    codex_skills_dir = Path.home() / ".codex" / "skills"

    result = subprocess.run(
        [sys.executable, str(script), "--repo", str(repo_root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["ok"] is True
    skill_names = {entry["name"] for entry in data["results"]}
    assert skill_names == {
        "mstack-careful",
        "mstack-dispatch",
        "mstack-investigate",
        "mstack-plan",
        "mstack-pipeline",
        "mstack-pipeline-coordinator",
        "mstack-qa",
        "mstack-retro",
        "mstack-review",
        "mstack-ship",
    }
    pipeline_entry = next(entry for entry in data["results"] if entry["name"] == "mstack-pipeline")
    assert pipeline_entry["isolated"] is True
    assert pipeline_entry["workdir"] != str(repo_root)
    assert (
        "found:Stage Order: careful -> dispatch -> plan -> implement -> review -> qa -> ship -> retro"
        in pipeline_entry["checks"]
    )
    assert not any(codex_skills_dir.glob("codex-runtime-smoke-*"))
