"""Runtime smoke test for Codex skills.

This script temporarily installs selected skills from ``skills-codex`` into the
user's Codex skill directory, runs ``codex exec`` prompts that should trigger
those skills, validates the outputs, and then removes the temporary installs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import argparse
import json
import os
import shutil
import time
import subprocess
import sys
import tempfile
import uuid

from core.assets import asset_dir

SKILL_CASES = (
    {
        "name": "mstack-careful",
        "source_dir": "careful",
        "output_file": "careful-smoke.txt",
        "prompt": (
            "Use $mstack-careful to evaluate whether running git push --force to "
            "main is acceptable. Do not inspect repository files or run "
            "commands. Treat this prompt as the full input. Return only three "
            "labeled lines: Risk:, Blocked Action:, Safer Alternative:."
        ),
        "must_contain": ("Risk:", "Blocked Action:", "Safer Alternative:"),
    },
    {
        "name": "mstack-dispatch",
        "source_dir": "dispatch",
        "output_file": "dispatch-smoke.txt",
        "prompt": (
            "Use $mstack-dispatch to route a task that touches 6 files across UI "
            "and API modules. Do not inspect repository files or run commands. "
            "Treat this prompt as the full input. Return only four labeled "
            "lines: Mode:, Risks:, Ownership:, Validation:."
        ),
        "must_contain": ("Mode:", "Ownership:", "Validation:"),
    },
    {
        "name": "mstack-investigate",
        "source_dir": "investigate",
        "output_file": "investigate-smoke.txt",
        "prompt": (
            "Use $mstack-investigate to analyze a failure where CSV import "
            "crashes on an empty file. Do not inspect repository files or run "
            "commands. Treat this prompt as the full context. Return only four "
            "labeled sections: Hypotheses:, Root Cause:, Fix Recommendation:, "
            "Regression Test:."
        ),
        "must_contain": ("Hypotheses:", "Root Cause:", "Regression Test:"),
    },
    {
        "name": "mstack-plan",
        "source_dir": "plan",
        "output_file": "plan-smoke.txt",
        "prompt": (
            "Use $mstack-plan to produce only a two-phase section outline for "
            "adding CSV import to a todo app. Do not inspect repository files or "
            "run commands. Treat this prompt as the full input. Return only "
            "Phase 1 and Phase 2 headings with 2 bullets each."
        ),
        "must_contain": ("Phase 1", "Phase 2"),
    },
    {
        "name": "mstack-pipeline",
        "source_dir": "pipeline",
        "output_file": "pipeline-smoke.txt",
        "isolated": True,
        "prompt": (
            "Use $mstack-pipeline to handle a feature request for adding CSV "
            "import to a todo app from planning through release. Do not inspect "
            "repository files or run commands. Treat this prompt as the full "
            "input. Return only three labeled lines. The Stage Order line must "
            "use exactly this canonical order: Stage Order: careful -> dispatch "
            "-> plan -> implement -> review -> qa -> ship -> retro. Then return "
            "Stop Conditions: and Final Output:."
        ),
        "must_contain": (
            "Stage Order: careful -> dispatch -> plan -> implement -> review -> qa -> ship -> retro",
            "Stop Conditions:",
            "Final Output:",
        ),
    },
    {
        "name": "mstack-pipeline-coordinator",
        "source_dir": "pipeline-coordinator",
        "output_file": "pipeline-coordinator-smoke.txt",
        "prompt": (
            "Use $mstack-pipeline-coordinator to compare 3 rollout options for a "
            "high-risk architecture change. Do not inspect repository files or "
            "run commands. Treat this prompt as the full input. Return only five "
            "labeled lines: Agent Topology:, Recommendation:, Scoring Summary:, "
            "Verifier Verdict:, Remaining Gaps:."
        ),
        "must_contain": (
            "Agent Topology:",
            "Recommendation:",
            "Scoring Summary:",
            "Verifier Verdict:",
            "Remaining Gaps:",
        ),
    },
    {
        "name": "mstack-qa",
        "source_dir": "qa",
        "output_file": "qa-smoke.txt",
        "prompt": (
            "Use $mstack-qa to assess a hypothetical change that modified a CSV "
            "parser and added no tests yet. Do not inspect repository files or "
            "run commands. Treat this prompt as the full context. Return only "
            "three labeled lines: Mode:, Results:, Regression Tests:."
        ),
        "must_contain": ("Mode:", "Results:", "Regression Tests:"),
    },
    {
        "name": "mstack-retro",
        "source_dir": "retro",
        "output_file": "retro-smoke.txt",
        "prompt": (
            "Use $mstack-retro to summarize a completed feature that shipped "
            "late and had one QA bug. Do not inspect repository files or run "
            "commands. Treat this prompt as the full input. Return only four "
            "labeled lines: Task Summary:, Keep:, Improve:, Action Items:."
        ),
        "must_contain": ("Task Summary:", "Keep:", "Action Items:"),
    },
    {
        "name": "mstack-review",
        "source_dir": "review",
        "output_file": "review-smoke.txt",
        "prompt": (
            "Use $mstack-review to review a diff that adds a new function "
            "without tests and hardcodes an API key. Do not inspect repository "
            "files or run commands. Treat this prompt as the full diff context. "
            "Return only AUTO-FIX and SURFACE sections."
        ),
        "must_contain": ("AUTO-FIX", "SURFACE"),
    },
    {
        "name": "mstack-ship",
        "source_dir": "ship",
        "output_file": "ship-smoke.txt",
        "prompt": (
            "Use $mstack-ship to assess releasing a change to main where tests "
            "passed but the commit message is vague. Do not inspect repository "
            "files or run commands. Treat this prompt as the full input. Return "
            "only four labeled lines: Status:, Checks:, Blockers:, Push Guidance:."
        ),
        "must_contain": ("Status:", "Checks:", "Push Guidance:"),
    },
)


@dataclass
class SmokeCaseResult:
    """Result of one runtime smoke case."""

    name: str
    output_file: str
    workdir: str
    isolated: bool
    passed: bool
    checks: list[str]
    stdout_tail: str


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Run Codex runtime smoke tests.")
    parser.add_argument(
        "--repo",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root to use as Codex working directory.",
    )
    parser.add_argument(
        "--skills-source",
        default=str(asset_dir("skills-codex")),
        help="Directory containing Codex-formatted skills.",
    )
    parser.add_argument(
        "--codex-skills-dir",
        default=str(Path.home() / ".codex" / "skills"),
        help="Codex skills installation directory.",
    )
    parser.add_argument(
        "--keep-artifacts",
        action="store_true",
        help="Keep runtime output files in a persistent temp folder.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Timeout in seconds for each codex exec invocation.",
    )
    parser.add_argument(
        "--skip-git-repo-check",
        action="store_true",
        help="Pass --skip-git-repo-check to codex exec for all runtime smoke commands.",
    )
    return parser


def _cleanup_prior_smoke_dirs(codex_skills_dir: Path) -> None:
    """Remove prior smoke dirs created by this script."""
    for path in codex_skills_dir.glob("codex-runtime-smoke-*"):
        _safe_rmtree(path)


def _safe_rmtree(path: Path, attempts: int = 10, delay_sec: float = 0.5) -> None:
    """Remove a directory with retries for transient Windows locks."""
    if not path.exists():
        return

    for _ in range(attempts):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            time.sleep(delay_sec)

    shutil.rmtree(path, ignore_errors=True)


def _persist_artifacts(output_dir: Path, keep_dir: Path) -> None:
    """Copy runtime smoke artifacts, preserving both files and directories."""
    keep_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.iterdir():
        destination = keep_dir / path.name
        if path.is_dir():
            shutil.copytree(path, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(path, destination)


def _install_temp_skills(skills_source: Path, codex_skills_dir: Path, run_id: str) -> list[Path]:
    """Copy selected skills into the Codex skills directory."""
    installed: list[Path] = []
    for case in SKILL_CASES:
        src = skills_source / case["source_dir"]
        dst = codex_skills_dir / f"codex-runtime-smoke-{run_id}-{case['source_dir']}"
        shutil.copytree(src, dst)
        installed.append(dst)
    return installed


def _build_codex_command(
    repo: Path,
    output_file: Path,
    prompt: str,
    *,
    skip_git_repo_check: bool = False,
) -> list[str]:
    """Build the codex exec command."""
    command = [
        "codex",
        "-m",
        "gpt-5.4-mini",
        "-c",
        'model_reasoning_effort="low"',
        "-s",
        "read-only",
        "-a",
        "never",
        "exec",
        "--ephemeral",
    ]
    if skip_git_repo_check:
        command.append("--skip-git-repo-check")
    command.extend([
        "-C",
        str(repo),
        "-o",
        str(output_file),
        prompt,
    ])
    if os.name == "nt":
        return ["cmd.exe", "/d", "/c", *command]
    return command


def _run_case(
    repo: Path,
    output_dir: Path,
    case: dict[str, object],
    timeout: int,
    *,
    isolated_repo: Path | None = None,
    skip_git_repo_check: bool = False,
) -> SmokeCaseResult:
    """Run one codex exec case and validate the output."""
    output_file = output_dir / str(case["output_file"])
    use_isolated = bool(case.get("isolated", False))
    case_repo = isolated_repo if use_isolated and isolated_repo is not None else repo
    command = _build_codex_command(
        case_repo,
        output_file,
        str(case["prompt"]),
        skip_git_repo_check=skip_git_repo_check or use_isolated,
    )
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"codex exec failed for {case['name']} with code {completed.returncode}: "
            f"{completed.stderr.strip()}"
        )

    output_text = output_file.read_text(encoding="utf-8")
    checks: list[str] = []
    passed = True
    for needle in case["must_contain"]:
        if needle in output_text:
            checks.append(f"found:{needle}")
        else:
            checks.append(f"missing:{needle}")
            passed = False

    stdout_tail = "\n".join(completed.stdout.strip().splitlines()[-12:])
    return SmokeCaseResult(
        name=str(case["name"]),
        output_file=str(output_file),
        workdir=str(case_repo),
        isolated=use_isolated,
        passed=passed,
        checks=checks,
        stdout_tail=stdout_tail,
    )


def run_smoke(
    repo: Path,
    skills_source: Path,
    codex_skills_dir: Path,
    keep_artifacts: bool,
    timeout: int,
    skip_git_repo_check: bool,
) -> dict[str, object]:
    """Run the full runtime smoke flow with cleanup."""
    if shutil.which("codex") is None:
        raise RuntimeError("codex CLI not found in PATH")
    if not skills_source.exists():
        raise RuntimeError(f"skills source not found: {skills_source}")
    if not codex_skills_dir.exists():
        raise RuntimeError(f"codex skills dir not found: {codex_skills_dir}")

    run_id = uuid.uuid4().hex[:8]
    _cleanup_prior_smoke_dirs(codex_skills_dir)

    temp_context = tempfile.TemporaryDirectory(prefix="codex-runtime-smoke-")
    output_dir = Path(temp_context.name)
    isolated_repo = output_dir / "isolated-workdir"
    isolated_repo.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []
    results: list[SmokeCaseResult] = []
    list_output = output_dir / "skills-list.txt"

    try:
        installed = _install_temp_skills(skills_source, codex_skills_dir, run_id)

        list_command = _build_codex_command(
            repo,
            list_output,
            "List only the available skill names that start with mstack-.",
            skip_git_repo_check=skip_git_repo_check,
        )
        listed = subprocess.run(
            list_command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        if listed.returncode != 0:
            raise RuntimeError(f"codex exec failed for skills list: {listed.stderr.strip()}")

        listed_text = list_output.read_text(encoding="utf-8")
        for expected in (
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
        ):
            if expected not in listed_text:
                raise RuntimeError(f"runtime skill list missing {expected}")

        for case in SKILL_CASES:
            results.append(
                _run_case(
                    repo,
                    output_dir,
                    case,
                    timeout,
                    isolated_repo=isolated_repo,
                    skip_git_repo_check=skip_git_repo_check,
                )
            )

        if not all(result.passed for result in results):
            raise RuntimeError(
                "one or more runtime smoke cases failed validation: "
                + json.dumps([asdict(result) for result in results], ensure_ascii=False)
            )

        summary = {
            "ok": True,
            "repo": str(repo),
            "skills_source": str(skills_source),
            "results": [asdict(result) for result in results],
            "skills_list": listed_text.strip().splitlines(),
            "output_dir": str(output_dir),
        }
        if keep_artifacts:
            keep_dir = repo / "skills-workspace" / "runtime-smoke"
            _persist_artifacts(output_dir, keep_dir)
            summary["persisted_output_dir"] = str(keep_dir)
        return summary
    finally:
        for path in installed:
            _safe_rmtree(path)
        _cleanup_prior_smoke_dirs(codex_skills_dir)
        temp_context.cleanup()


def main() -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    summary = run_smoke(
        repo=Path(args.repo),
        skills_source=Path(args.skills_source),
        codex_skills_dir=Path(args.codex_skills_dir),
        keep_artifacts=args.keep_artifacts,
        timeout=args.timeout,
        skip_git_repo_check=args.skip_git_repo_check,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
