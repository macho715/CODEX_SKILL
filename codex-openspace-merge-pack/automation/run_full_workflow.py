#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

TEMPLATE_PATH = Path(__file__).parent / "templates" / "workflow_prompt.md"


@dataclass
class RunManifest:
    run_id: str
    repo_root: str
    run_dir: str
    task: str
    phase1_returncode: int | None = None
    phase2_returncode: int | None = None
    options_scored: bool = False
    final_report: Optional[str] = None
    stdout_phase1: str | None = None
    stderr_phase1: str | None = None
    stdout_phase2: str | None = None
    stderr_phase2: str | None = None


def check_binary(name: str) -> None:
    from shutil import which
    if which(name) is None:
        raise RuntimeError(f"Required binary not found in PATH: {name}")


def load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def ensure_dirs(repo_root: Path) -> Path:
    runs_dir = repo_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def run_codex(repo_root: Path, prompt: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    # We intentionally keep the CLI call minimal:
    # - `codex exec` is documented in the AGENTS.md guide examples.
    # - project-scoped `.codex/config.toml` and repo `AGENTS.md` / `.agents/skills` are resolved by cwd.
    cmd = ["codex", "exec", prompt]
    return subprocess.run(
        cmd,
        cwd=str(repo_root),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def maybe_score_options(repo_root: Path, run_dir: Path) -> bool:
    options_path = run_dir / "04_options.json"
    scorer = repo_root / ".agents" / "skills" / "scenario-scorer" / "scripts" / "score_options.py"
    if not options_path.exists() or not scorer.exists():
        return False

    output_path = run_dir / "04_scored_options.json"
    result = subprocess.run(
        [sys.executable, str(scorer), str(options_path)],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        write_text(run_dir / "04_scoring_error.log", result.stderr or result.stdout)
        return False

    write_text(output_path, result.stdout)
    return True


def build_phase2_prompt(run_dir: Path) -> str:
    return f"""
Read these files and write the final refined report:
- {run_dir}/01_plan.md
- {run_dir}/02_draft.md
- {run_dir}/03_verification.md
- {run_dir}/04_scored_options.json (if it exists)

Tasks:
1. If verification contains FAIL items, patch only the failed sections once.
2. Preserve planner-first reasoning.
3. Keep PASS/FAIL separation visible.
4. Write the final answer to {run_dir}/05_final.md
5. Also write a compact machine-readable summary to {run_dir}/06_summary.json

If 04_scored_options.json does not exist, finalize using the available artifacts only.
""".strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="One-click Codex + OpenSpace workflow launcher")
    parser.add_argument("--repo-root", required=True, help="Absolute path to the target Codex repository")
    parser.add_argument("--task", required=True, help="User task to execute")
    parser.add_argument("--codex-home", default="", help="Optional isolated CODEX_HOME path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root not found: {repo_root}")

    check_binary("codex")

    run_dir = ensure_dirs(repo_root)
    template = load_template()
    phase1_prompt = template.format(run_dir=run_dir.as_posix(), task=args.task)

    env = os.environ.copy()
    if args.codex_home:
        env["CODEX_HOME"] = str(Path(args.codex_home).expanduser().resolve())

    manifest = RunManifest(
        run_id=run_dir.name,
        repo_root=str(repo_root),
        run_dir=str(run_dir),
        task=args.task,
    )

    write_text(run_dir / "00_request.txt", args.task)
    write_text(run_dir / "00_phase1_prompt.txt", phase1_prompt)

    phase1 = run_codex(repo_root, phase1_prompt, env)
    manifest.phase1_returncode = phase1.returncode
    manifest.stdout_phase1 = phase1.stdout
    manifest.stderr_phase1 = phase1.stderr
    write_text(run_dir / "phase1.stdout.log", phase1.stdout or "")
    write_text(run_dir / "phase1.stderr.log", phase1.stderr or "")

    manifest.options_scored = maybe_score_options(repo_root, run_dir)

    phase2_prompt = build_phase2_prompt(run_dir)
    write_text(run_dir / "00_phase2_prompt.txt", phase2_prompt)
    phase2 = run_codex(repo_root, phase2_prompt, env)
    manifest.phase2_returncode = phase2.returncode
    manifest.stdout_phase2 = phase2.stdout
    manifest.stderr_phase2 = phase2.stderr
    write_text(run_dir / "phase2.stdout.log", phase2.stdout or "")
    write_text(run_dir / "phase2.stderr.log", phase2.stderr or "")

    final_report_path = run_dir / "05_final.md"
    if final_report_path.exists():
        manifest.final_report = str(final_report_path)

    (run_dir / "run_manifest.json").write_text(
        json.dumps(asdict(manifest), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(
        {
            "run_dir": str(run_dir),
            "phase1_returncode": manifest.phase1_returncode,
            "phase2_returncode": manifest.phase2_returncode,
            "options_scored": manifest.options_scored,
            "final_report": manifest.final_report,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
