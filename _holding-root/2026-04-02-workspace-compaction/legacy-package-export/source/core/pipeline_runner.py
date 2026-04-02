"""Real stage runner backends for mstack pipeline CLI execution."""

from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from typing import Callable

from .assets import asset_dir
from .config import resolve_preset, scan_dirs
from .cost import DEFAULT_COST_LOG, aggregate, parse_jsonl
from .parallel_executor import ParallelExecutor, ParallelExecutionContext, plan_generic_parallel_tasks
from .pipeline_recipes import (
    GenericImplementBackend,
    ImplementRecipeContext,
    ParallelImplementTask,
    ParallelImplementWrite,
    detect_parallel_executor_capabilities,
    run_implement_recipe,
)
from .types import Preset, RouterDecision, RouterResult, StageResult, StageStatus


PRESETS_DIR = asset_dir("presets")
SECRET_PATTERNS = (
    r"sk-[A-Za-z0-9_-]{10,}",
    r"api[_-]?key",
    r"OPENAI_API_KEY",
    r"ghp_[A-Za-z0-9]{10,}",
)
REVIEW_IGNORE_DIR_MARKERS = (
    ".mstack-parallel-artifacts/",
    "__pycache__/",
)
REVIEW_IGNORE_SUFFIXES = (".pyc", ".pyo")


@dataclass(frozen=True)
class PipelineRunnerContext:
    """Execution context shared by stage backends."""

    project_dir: Path
    request: str
    preset: Preset
    dirs: list[str]
    dispatch_result: RouterResult | None = None
    generic_implement_backend: GenericImplementBackend | None = None
    parallel_executor: ParallelExecutor | None = None
    executor_capabilities: frozenset[RouterDecision] = frozenset({RouterDecision.SINGLE})


def build_stage_runner(
    project_dir: Path,
    request: str,
    *,
    dispatch_result: RouterResult | None = None,
    generic_implement_backend: GenericImplementBackend | None = None,
    parallel_executor: ParallelExecutor | None = None,
    executor_capabilities: frozenset[RouterDecision] | None = None,
    fail_stage: str | None = None,
    fail_until: int = 0,
) -> Callable[[str], StageResult]:
    """Build a stage runner backed by real project inspection and commands."""
    preset = resolve_preset(project_dir, None, None, PRESETS_DIR)
    recipe_context = ImplementRecipeContext(
        project_dir=project_dir,
        request=request,
        lang=preset.lang,
    )
    default_executor_capabilities = set(detect_parallel_executor_capabilities(recipe_context))
    if parallel_executor is not None:
        default_executor_capabilities.update(parallel_executor.capabilities)
    context = PipelineRunnerContext(
        project_dir=project_dir,
        request=request,
        preset=preset,
        dirs=scan_dirs(project_dir),
        dispatch_result=dispatch_result,
        generic_implement_backend=generic_implement_backend,
        parallel_executor=parallel_executor,
        executor_capabilities=executor_capabilities or frozenset(default_executor_capabilities),
    )
    call_count: dict[str, int] = {}

    def runner(stage: str) -> StageResult:
        call_count[stage] = call_count.get(stage, 0) + 1

        if fail_stage and stage == fail_stage:
            if stage == "qa" and call_count[stage] > fail_until:
                return _run_stage(stage, context)
            return StageResult(
                stage=stage,
                status=StageStatus.FAILED,
                output=f"{stage} failed by test hook",
                errors=[f"{stage} failed"],
            )

        return _run_stage(stage, context)

    return runner


def _run_stage(stage: str, context: PipelineRunnerContext) -> StageResult:
    """Dispatch to a concrete backend for one stage."""
    backend = {
        "plan": _run_plan_stage,
        "implement": _run_implement_stage,
        "review": _run_review_stage,
        "qa": _run_qa_stage,
        "ship": _run_ship_stage,
        "retro": _run_retro_stage,
        "investigate": _run_investigate_stage,
    }.get(stage)

    if backend is None:
        return StageResult(
            stage=stage,
            status=StageStatus.SKIPPED,
            output=f"no backend registered for {stage}",
        )

    start = time.perf_counter()
    result = backend(context)
    result.duration_sec = round(time.perf_counter() - start, 3)
    return result


def _run_plan_stage(context: PipelineRunnerContext) -> StageResult:
    lines = [
        "## Phase 1: Business Review",
        f"- Request: {context.request}",
        f"- Project directories: {', '.join(context.dirs) if context.dirs else 'N/A'}",
        "",
        "## Phase 2: Engineering Review",
        f"- Suggested test command: {context.preset.test_cmd or 'N/A'}",
        f"- Suggested lint command: {context.preset.lint_cmd or 'N/A'}",
    ]
    return StageResult(stage="plan", status=StageStatus.PASSED, output="\n".join(lines))


def _run_implement_stage(context: PipelineRunnerContext) -> StageResult:
    execution_mode = context.dispatch_result.decision if context.dispatch_result else None
    recipe_context = ImplementRecipeContext(
        project_dir=context.project_dir,
        request=context.request,
        lang=context.preset.lang,
    )
    result = run_implement_recipe(
        recipe_context,
        fallback_backend=None,
        execution_mode=execution_mode,
        parallel_executor=_local_parallel_implement_executor,
    )
    if result.status != StageStatus.SKIPPED:
        return result

    if (
        context.parallel_executor is not None
        and execution_mode in {RouterDecision.SUBAGENT, RouterDecision.AGENT_TEAMS}
    ):
        tasks = plan_generic_parallel_tasks(
            context.project_dir,
            context.request,
            execution_mode,
            context.dirs,
        )
        if tasks:
            return context.parallel_executor.execute(
                ParallelExecutionContext(
                    project_dir=context.project_dir,
                    request=context.request,
                    decision=execution_mode,
                    validation_command=context.preset.test_cmd or None,
                    tasks=tasks,
                    failure_excerpt=_collect_validation_excerpt(context),
                )
            )

    if context.generic_implement_backend is not None:
        fallback_result = context.generic_implement_backend(recipe_context)
        if fallback_result is not None:
            return fallback_result

    return result


def _run_review_stage(context: PipelineRunnerContext) -> StageResult:
    changed_files = _git_changed_files(context.project_dir)
    if not changed_files:
        return StageResult(
            stage="review",
            status=StageStatus.PASSED,
            output="No changed files detected for review.",
        )

    findings: list[str] = []
    non_test_changes = [path for path in changed_files if "test" not in path.lower()]
    has_test_changes = any("test" in path.lower() for path in changed_files)
    if non_test_changes and not has_test_changes:
        findings.append("Tests appear missing for changed non-test files.")

    secret_hits = _scan_changed_files_for_secrets(context.project_dir, changed_files)
    findings.extend(secret_hits)

    status = StageStatus.FAILED if findings else StageStatus.PASSED
    output_lines = [
        f"Changed files: {', '.join(changed_files)}",
        "Findings: " + (", ".join(findings) if findings else "none"),
    ]
    return StageResult(
        stage="review",
        status=status,
        output="\n".join(output_lines),
        errors=findings,
    )


def _run_qa_stage(context: PipelineRunnerContext) -> StageResult:
    return _run_command_stage("qa", context.project_dir, context.preset.test_cmd, allow_skip=False)


def _run_ship_stage(context: PipelineRunnerContext) -> StageResult:
    branch = _git_branch(context.project_dir)
    blockers: list[str] = []
    output_lines = [f"branch: {branch}"]

    if branch in {"main", "master"}:
        blockers.append("direct release from protected branch requires manual review")

    for label, command in (
        ("test", context.preset.test_cmd),
        ("lint", context.preset.lint_cmd),
        ("type", context.preset.type_cmd),
    ):
        result = _run_shell_command(context.project_dir, command, allow_skip=True)
        output_lines.append(f"{label}: {result.output}")
        blockers.extend(result.errors)

    status = StageStatus.FAILED if blockers else StageStatus.PASSED
    return StageResult(
        stage="ship",
        status=status,
        output="\n".join(output_lines),
        errors=blockers,
    )


def _run_retro_stage(context: PipelineRunnerContext) -> StageResult:
    commits = _git_recent_commits(context.project_dir, count=5)
    cost_note = "N/A"
    if DEFAULT_COST_LOG.exists():
        data = aggregate(parse_jsonl(DEFAULT_COST_LOG))
        cost_note = f"${data.total_cost:.2f} across {data.total_sessions} sessions"
    output = "\n".join([
        "## Retrospective",
        f"recent commits: {len(commits)}",
        f"cost summary: {cost_note}",
    ])
    return StageResult(stage="retro", status=StageStatus.PASSED, output=output)


def _run_investigate_stage(context: PipelineRunnerContext) -> StageResult:
    output = "\n".join([
        "Hypotheses:",
        "- input is empty or malformed",
        "- parser assumes at least one row",
        "- validation does not guard pre-parse edge cases",
        "Root cause: evidence gathering required before mutation",
        "Regression test: add repro for the reported failure path",
    ])
    return StageResult(stage="investigate", status=StageStatus.PASSED, output=output)


def _run_command_stage(
    stage: str,
    project_dir: Path,
    command: str,
    *,
    allow_skip: bool,
) -> StageResult:
    result = _run_shell_command(project_dir, command, allow_skip=allow_skip)
    status = StageStatus.PASSED
    if result.skipped:
        status = StageStatus.SKIPPED
    elif result.errors:
        status = StageStatus.FAILED

    return StageResult(
        stage=stage,
        status=status,
        output=result.output,
        errors=result.errors,
    )


@dataclass(frozen=True)
class CommandStageResult:
    output: str
    errors: list[str]
    skipped: bool = False


def _run_shell_command(project_dir: Path, command: str, *, allow_skip: bool) -> CommandStageResult:
    if not command:
        return CommandStageResult(output="command not configured", errors=[], skipped=True)

    executable = _extract_executable(command)
    if executable and shutil.which(executable) is None and allow_skip:
        return CommandStageResult(
            output=f"skipped ({executable} not installed)",
            errors=[],
            skipped=True,
        )

    completed = _execute_command(project_dir, command)
    combined = (completed.stdout or "").strip()
    if completed.returncode != 0:
        error_text = _select_error_line(completed.stderr or "", combined)
        return CommandStageResult(
            output=f"failed ({command})",
            errors=[error_text],
            skipped=False,
        )

    return CommandStageResult(
        output=f"passed ({command})" if not combined else _select_summary_line(combined),
        errors=[],
        skipped=False,
    )


def _execute_command(project_dir: Path, command: str) -> subprocess.CompletedProcess[str]:
    env = _build_command_env(project_dir)
    tokens = _split_command(command)

    if tokens and tokens[0].lower() == "pytest":
        return subprocess.run(
            [sys.executable, "-m", "pytest", *tokens[1:]],
            cwd=project_dir,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
            env=env,
        )

    return subprocess.run(
        command,
        cwd=project_dir,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
        env=env,
    )


def _build_command_env(project_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{project_dir}{os.pathsep}{existing}" if existing else str(project_dir)
    )
    existing_path = env.get("PATH")
    env["PATH"] = f"{project_dir}{os.pathsep}{existing_path}" if existing_path else str(project_dir)
    return env


def _extract_executable(command: str) -> str | None:
    tokens = _split_command(command)
    return tokens[0] if tokens else None


def _split_command(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=False)
    except ValueError:
        return []


def _select_summary_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "command completed"

    for line in reversed(lines):
        if line.startswith("# pass "):
            return f"{line.split()[-1]} passed"

    for line in reversed(lines):
        if line.startswith("# fail "):
            return f"{line.split()[-1]} failed"

    summary = lines[-1]
    match = re.fullmatch(r"=+\s*(.+?)\s*=+", summary)
    if match:
        return match.group(1).strip()
    return summary


def _select_error_line(stderr_text: str, stdout_text: str) -> str:
    stderr_lines = [line.strip() for line in stderr_text.splitlines() if line.strip()]
    stdout_lines = [line.strip() for line in stdout_text.splitlines() if line.strip()]

    for prefix in ("FAILED ", "ERROR ", "E   "):
        for line in stdout_lines:
            if line.startswith(prefix):
                return line

    for line in stderr_lines:
        lowered = line.lower()
        if "warning" not in lowered and "deprecationwarning" not in lowered:
            return line

    if stdout_lines:
        return stdout_lines[-1]
    if stderr_lines:
        return stderr_lines[0]
    return "command failed"


def _git_changed_files(project_dir: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    tracked_files = [] if completed.returncode != 0 else [
        line for line in completed.stdout.splitlines() if line.strip()
    ]
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    untracked_files = [] if untracked.returncode != 0 else [
        line for line in untracked.stdout.splitlines() if line.strip()
    ]
    candidates = sorted(set(tracked_files + untracked_files))
    return [path for path in candidates if not _should_ignore_review_path(path)]


def _should_ignore_review_path(rel_path: str) -> bool:
    """Return True when a path should be ignored for review drift output."""
    normalized = rel_path.replace("\\", "/")
    if normalized.startswith(".mstack-parallel-artifacts/"):
        return True
    if any(marker in normalized for marker in REVIEW_IGNORE_DIR_MARKERS):
        return True
    if normalized.endswith(REVIEW_IGNORE_SUFFIXES):
        return True
    return False


def _git_branch(project_dir: Path) -> str:
    completed = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _git_recent_commits(project_dir: Path, *, count: int) -> list[str]:
    completed = subprocess.run(
        ["git", "log", "--oneline", f"-{count}"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def _scan_changed_files_for_secrets(project_dir: Path, changed_files: list[str]) -> list[str]:
    findings: list[str] = []
    for rel_path in changed_files:
        path = project_dir / rel_path
        if not path.exists() or path.is_dir():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(f"possible secret found in {rel_path}")
                break
    return findings


def _collect_validation_excerpt(context: PipelineRunnerContext) -> str:
    """Collect a short failing-test excerpt to guide external workers."""
    if not context.preset.test_cmd:
        return ""
    result = _run_shell_command(context.project_dir, context.preset.test_cmd, allow_skip=False)
    if not result.errors:
        return ""
    return "\n".join(result.errors[:2])


def _local_parallel_implement_executor(
    project_dir: Path,
    tasks: tuple[ParallelImplementTask, ...],
    recipe_name: str,
) -> StageResult:
    """Execute deterministic implement tasks in parallel within the local runtime."""
    target_errors = _parallel_target_conflicts(project_dir, tasks)
    if target_errors:
        return StageResult(
            stage="implement",
            status=StageStatus.FAILED,
            output="parallel implement refused to overwrite existing protected targets",
            errors=target_errors,
        )

    with ThreadPoolExecutor(max_workers=max(1, len(tasks))) as executor:
        futures = [executor.submit(_apply_parallel_task, project_dir, task) for task in tasks]
        results = [future.result() for future in futures]

    files_changed: list[str] = []
    worker_summaries: list[str] = []
    for worker_name, writes in results:
        worker_summaries.append(f"{worker_name}: {', '.join(writes)}")
        for rel_path in writes:
            if rel_path not in files_changed:
                files_changed.append(rel_path)

    return StageResult(
        stage="implement",
        status=StageStatus.PASSED,
        output=(
            f"applied parallel {recipe_name} implementation with {len(tasks)} workers: "
            + "; ".join(worker_summaries)
        ),
        files_changed=files_changed,
    )


def _parallel_target_conflicts(project_dir: Path, tasks: tuple[ParallelImplementTask, ...]) -> list[str]:
    """Return protected target conflicts for planned parallel writes."""
    conflicts: list[str] = []
    seen: set[str] = set()
    for task in tasks:
        for write in task.writes:
            rel_path = write.relative_path
            if rel_path in seen:
                conflicts.append(f"duplicate worker ownership for {rel_path}")
                continue
            seen.add(rel_path)
            target = project_dir / rel_path
            if target.exists() and not write.allow_overwrite:
                conflicts.append(f"existing target files must be reviewed manually: {rel_path}")
    return conflicts


def _apply_parallel_task(project_dir: Path, task: ParallelImplementTask) -> tuple[str, list[str]]:
    """Apply one worker task and return owned files."""
    written: list[str] = []
    for write in task.writes:
        _write_parallel_file(project_dir, write)
        written.append(write.relative_path)
    return task.worker_name, written


def _write_parallel_file(project_dir: Path, write: ParallelImplementWrite) -> None:
    """Write one planned file for a parallel task."""
    target = project_dir / write.relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(write.content, encoding="utf-8")
