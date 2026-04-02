from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "automation" / "run_full_workflow.py"

st.set_page_config(page_title="Codex + OpenSpace One-Click", layout="wide")
st.title("Codex + OpenSpace One-Click Workflow")

repo_root = st.text_input("Repo root", value=str(ROOT))
codex_home = st.text_input("CODEX_HOME (optional)", value=str(ROOT / ".codex-home"))
task = st.text_area("Task", height=220, placeholder="예: 기존 HVDC 물류 코스트 분석 스킬을 사용해 시나리오 3개를 만들고 OpenSpace가 필요한 부분만 위임한 뒤 검증/스코어링까지 끝내라.")

if st.button("Run full workflow", type="primary"):
    if not task.strip():
        st.error("Task is required.")
    else:
        cmd = [
            sys.executable,
            str(RUNNER),
            "--repo-root", repo_root,
            "--task", task,
        ]
        if codex_home.strip():
            cmd.extend(["--codex-home", codex_home])

        with st.spinner("Running full workflow..."):
            result = subprocess.run(cmd, text=True, capture_output=True, check=False)

        st.subheader("Launcher result")
        st.code(result.stdout or "", language="json")
        if result.stderr:
            st.subheader("stderr")
            st.code(result.stderr, language="text")

        try:
            meta = json.loads(result.stdout)
            run_dir = Path(meta["run_dir"])
            final_report = run_dir / "05_final.md"
            verification = run_dir / "03_verification.md"
            manifest = run_dir / "run_manifest.json"

            cols = st.columns(3)
            cols[0].metric("Phase1 RC", meta.get("phase1_returncode"))
            cols[1].metric("Phase2 RC", meta.get("phase2_returncode"))
            cols[2].metric("Options scored", str(meta.get("options_scored")))

            for path in [final_report, verification, manifest]:
                if path.exists():
                    st.subheader(path.name)
                    st.code(path.read_text(encoding="utf-8"), language="markdown" if path.suffix == ".md" else "json")
        except Exception as exc:
            st.warning(f"Could not parse launcher output: {exc}")
