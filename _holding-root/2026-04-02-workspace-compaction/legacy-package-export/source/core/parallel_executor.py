"""External parallel executor abstractions and a Codex-backed skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Protocol
import json
import os
import re
import shutil
import subprocess
import tempfile

from .pipeline_recipes import ParallelImplementTask
from .types import RouterDecision, StageResult, StageStatus


@dataclass(frozen=True)
class ParallelExecutionContext:
    """Execution context passed to external executors."""

    project_dir: Path
    request: str
    decision: RouterDecision
    validation_command: str | None
    tasks: tuple[ParallelImplementTask, ...]
    failure_excerpt: str = ""


@dataclass(frozen=True)
class WorkerExecutionResult:
    """One external worker run result."""

    task: ParallelImplementTask
    worker_dir: Path
    output_tail: str
    artifact_dir: Path
    changed_paths: tuple[str, ...] = ()


class ParallelExecutor(Protocol):
    """Protocol for pluggable external parallel implement executors."""

    @property
    def capabilities(self) -> frozenset[RouterDecision]:
        """Return execution modes supported by this executor."""

    def execute(self, context: ParallelExecutionContext) -> StageResult:
        """Execute one parallel implement run."""


@dataclass(frozen=True)
class CodexExecParallelExecutor:
    """Codex CLI backed external executor skeleton for generic parallel work."""

    launcher: tuple[str, ...]
    model: str = "gpt-5.4-mini"

    @property
    def capabilities(self) -> frozenset[RouterDecision]:
        return frozenset({RouterDecision.SUBAGENT, RouterDecision.AGENT_TEAMS})

    def execute(self, context: ParallelExecutionContext) -> StageResult:
        temp_root = Path(tempfile.mkdtemp(prefix="mstack-parallel-exec-"))
        artifact_root = _prepare_artifact_root(context.project_dir)
        try:
            worker_dirs = _prepare_worker_dirs(context.project_dir, temp_root, context.tasks)
            with ThreadPoolExecutor(max_workers=max(1, len(context.tasks))) as pool:
                futures = [
                    pool.submit(
                        self._run_worker,
                        context,
                        task,
                        worker_dirs[task.worker_name],
                        artifact_root / task.worker_name,
                    )
                    for task in context.tasks
                ]
                worker_results = [future.result() for future in futures]

            conflicts = _find_copyback_conflicts(worker_results)
            if conflicts:
                return StageResult(
                    stage="implement",
                    status=StageStatus.FAILED,
                    output="external parallel executor detected ownership conflicts",
                    errors=[*conflicts, f"artifacts: {artifact_root}"],
                )

            files_changed = _copy_back_changes(context.project_dir, worker_results)
            if not files_changed:
                return StageResult(
                    stage="implement",
                    status=StageStatus.FAILED,
                    output="external parallel executor produced no copy-back changes",
                    errors=[
                        "external executor completed without modifying owned paths",
                        *[
                            f"{result.task.worker_name}: {result.output_tail or 'no worker summary emitted'} | artifacts={result.artifact_dir}"
                            for result in worker_results
                        ],
                        f"artifacts: {artifact_root}",
                    ],
                )
            return StageResult(
                stage="implement",
                status=StageStatus.PASSED,
                output=(
                    f"applied external {context.decision.value} implementation with "
                    f"{len(context.tasks)} workers: "
                    + "; ".join(
                        f"{result.task.worker_name}: {result.output_tail or 'ok'}"
                        for result in worker_results
                    )
                ),
                files_changed=files_changed,
            )
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)

    def _run_worker(
        self,
        context: ParallelExecutionContext,
        task: ParallelImplementTask,
        worker_dir: Path,
        artifact_dir: Path,
    ) -> WorkerExecutionResult:
        output_file = worker_dir / "codex-output.txt"
        prompt = build_worker_prompt(
            context.request,
            task,
            validation_command=context.validation_command,
            failure_excerpt=context.failure_excerpt,
        )
        artifact_dir.mkdir(parents=True, exist_ok=True)
        before_snapshot = _snapshot_owned_paths(worker_dir, task)
        command = [
            *self.launcher,
            "exec",
            "-m",
            self.model,
            "-c",
            'model_reasoning_effort="low"',
            "-s",
            "workspace-write",
            "--ephemeral",
            "--skip-git-repo-check",
            "-C",
            str(worker_dir),
            "-o",
            str(output_file),
            "-",
        ]
        (artifact_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        (artifact_dir / "command.json").write_text(
            json.dumps({"command": command}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        completed = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=300,
        )
        (artifact_dir / "stdout.txt").write_text(completed.stdout or "", encoding="utf-8")
        (artifact_dir / "stderr.txt").write_text(completed.stderr or "", encoding="utf-8")
        if completed.returncode != 0:
            raise RuntimeError(
                f"external executor worker {task.worker_name} failed: "
                f"{completed.stderr.strip() or completed.stdout.strip()}"
            )
        output_tail = output_file.read_text(encoding="utf-8", errors="replace").strip()
        output_tail = "\n".join(output_tail.splitlines()[-6:])
        (artifact_dir / "last_message.txt").write_text(output_tail + ("\n" if output_tail else ""), encoding="utf-8")
        after_snapshot = _snapshot_owned_paths(worker_dir, task)
        changed_paths = _changed_snapshot_paths(before_snapshot, after_snapshot)
        _write_snapshot_artifacts(artifact_dir, before_snapshot, after_snapshot, changed_paths)
        return WorkerExecutionResult(
            task=task,
            worker_dir=worker_dir,
            output_tail=output_tail,
            artifact_dir=artifact_dir,
            changed_paths=tuple(changed_paths),
        )


def build_worker_prompt(
    request: str,
    task: ParallelImplementTask,
    *,
    validation_command: str | None = None,
    failure_excerpt: str = "",
) -> str:
    """Build a bounded worker prompt for external execution."""
    owned_paths = task.owned_paths or tuple(write.relative_path for write in task.writes)
    lines = [
        "Work only on the owned paths listed below.",
        "Workspace note: this worker runs in a writable temporary copy of the project.",
        f"Task request: {request}",
        f"Worker summary: {task.summary}",
        "Owned paths (exact files or approved directories):",
        *[f"- {path}" for path in owned_paths],
        "Goal:",
        "- Inspect the existing code and tests in the owned paths.",
        "- Make concrete code changes, not just analysis, so the feature actually advances.",
        "- Prefer changes that help the project pass its validation command.",
        "- Edit the owned files directly and save the changes before finishing.",
        "Rules:",
        "- Do not modify files outside the owned paths.",
        "- Do not revert or overwrite another worker's area.",
        "- Keep the change minimal and runnable.",
        "- Do not use sys.path.insert, PYTHONPATH hacks, or ad-hoc import path workarounds.",
        "- Keep imports package-safe and consistent with the existing project layout.",
    ]
    if owned_paths and all(path.startswith("tests/") for path in owned_paths):
        lines.append("- Do not rewrite tests to compensate for broken source behavior; only make minimal validation-safe test updates.")
    if failure_excerpt:
        lines.extend([
            "Current failing evidence:",
            failure_excerpt,
        ])
    if validation_command:
        lines.append(f"- Preferred validation command: {validation_command}")
    lines.append("Return a concise summary after editing.")
    return "\n".join(lines)


def plan_generic_parallel_tasks(
    project_dir: Path,
    request: str,
    decision: RouterDecision,
    dirs: list[str],
) -> tuple[ParallelImplementTask, ...] | None:
    """Create a generic ownership split for free-form parallel implementation."""
    file_targets = _planned_file_targets(project_dir)
    if file_targets:
        planned_tasks = _plan_tasks_from_file_targets(request, decision, file_targets)
        if planned_tasks is not None:
            return planned_tasks

    available_dirs = {name.lower() for name in dirs}
    fallback_tasks: list[ParallelImplementTask] = []

    if decision == RouterDecision.SUBAGENT:
        if "src" in available_dirs:
            fallback_tasks.append(
                ParallelImplementTask(
                    worker_name="code-owner",
                    summary=f"Handle the main code change for: {request}",
                    writes=(),
                    owned_paths=("src",),
                )
            )
        elif "tests" in available_dirs:
            fallback_tasks.append(
                ParallelImplementTask(
                    worker_name="tests-owner",
                    summary=f"Handle the test-side change for: {request}",
                    writes=(),
                    owned_paths=("tests",),
                )
            )
        return tuple(fallback_tasks) or None

    if decision == RouterDecision.AGENT_TEAMS:
        if "src" in available_dirs:
            fallback_tasks.append(
                ParallelImplementTask(
                    worker_name="code-owner",
                    summary=f"Own application code changes for: {request}",
                    writes=(),
                    owned_paths=("src", "tests"),
                )
            )
        if "docs" in available_dirs:
            fallback_tasks.append(
                ParallelImplementTask(
                    worker_name="docs-owner",
                    summary=f"Own documentation updates for: {request}",
                    writes=(),
                    owned_paths=("docs",),
                )
            )
        if len(fallback_tasks) >= 2:
            return tuple(fallback_tasks)

    return None


def _planned_file_targets(project_dir: Path) -> tuple[str, ...]:
    """Read approved file targets from plan.md when available."""
    plan_path = project_dir / "plan.md"
    if not plan_path.exists():
        return ()

    lines = plan_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_file_targets = False
    targets: list[str] = []
    for line in lines:
        lowered = line.strip().lower()
        if lowered.startswith("- file targets:") or lowered == "file targets:":
            in_file_targets = True
            continue
        if in_file_targets and line.startswith("#"):
            break
        if in_file_targets and line.strip().startswith("-"):
            matches = re.findall(r"`([^`]+)`", line)
            if matches:
                targets.extend(match.replace("\\", "/") for match in matches)
                continue
        if in_file_targets and line.strip() and not line.strip().startswith("-"):
            break
    return tuple(dict.fromkeys(targets))


def _plan_tasks_from_file_targets(
    request: str,
    decision: RouterDecision,
    file_targets: tuple[str, ...],
) -> tuple[ParallelImplementTask, ...] | None:
    """Create a generic worker split from approved exact file targets."""
    groups: dict[str, list[str]] = {
        "code-owner": [],
        "tests-owner": [],
        "docs-owner": [],
        "meta-owner": [],
    }
    for path in file_targets:
        normalized = path.replace("\\", "/")
        if normalized.startswith("tests/"):
            groups["tests-owner"].append(normalized)
        elif normalized.startswith("docs/"):
            groups["docs-owner"].append(normalized)
        elif normalized.startswith("src/"):
            groups["code-owner"].append(normalized)
        else:
            groups["meta-owner"].append(normalized)

    if decision == RouterDecision.SUBAGENT:
        all_targets = tuple(file_targets)
        if all_targets:
            return (
                ParallelImplementTask(
                    worker_name="subagent-owner",
                    summary=f"Handle all approved files for: {request}",
                    writes=(),
                    owned_paths=all_targets,
                ),
            )
        return None

    code_paths_list = list(groups["code-owner"] + groups["tests-owner"])
    if groups["meta-owner"] and _request_needs_meta_paths(request):
        code_paths_list.extend(groups["meta-owner"])
    code_paths = tuple(code_paths_list)
    docs_paths = tuple(groups["docs-owner"])

    # Keep behavior-coupled source and tests with one owner.
    # Only split out clearly decoupled documentation work in the generic 2-worker path.
    if decision == RouterDecision.AGENT_TEAMS and code_paths and docs_paths:
        return (
            ParallelImplementTask(
                worker_name="code-owner",
                summary=f"Own approved implementation and validation files for: {request}",
                writes=(),
                owned_paths=code_paths,
            ),
            ParallelImplementTask(
                worker_name="docs-owner",
                summary=f"Own approved documentation files for: {request}",
                writes=(),
                owned_paths=docs_paths,
            ),
        )

    tasks: list[ParallelImplementTask] = []
    if code_paths:
        tasks.append(
            ParallelImplementTask(
                worker_name="code-owner",
                summary=f"Own approved implementation and validation files for: {request}",
                writes=(),
                owned_paths=code_paths,
            )
        )
    if docs_paths:
        tasks.append(
            ParallelImplementTask(
                worker_name="docs-owner",
                summary=f"Own approved documentation files for: {request}",
                writes=(),
                owned_paths=docs_paths,
            )
        )
    return tuple(tasks) if len(tasks) >= 2 else None


def _request_needs_meta_paths(request: str) -> bool:
    """Return True when the request explicitly suggests config/package edits."""
    lowered = request.lower()
    keywords = (
        "pyproject",
        "package",
        "packaging",
        "import path",
        "module path",
        "config",
        "configuration",
        "mypy",
        "pytest config",
        "lint config",
        "build config",
    )
    return any(keyword in lowered for keyword in keywords)


def build_codex_exec_parallel_executor() -> ParallelExecutor | None:
    """Build a Codex-backed external executor when the CLI is available."""
    codex = shutil.which("codex")
    if codex is None:
        return None
    codex_path = Path(codex)
    if codex_path.suffix.lower() == ".ps1" and os.name == "nt":
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if pwsh is None:
            return None
        return CodexExecParallelExecutor(launcher=(pwsh, "-File", str(codex_path)))
    return CodexExecParallelExecutor(launcher=(str(codex_path),))


def _prepare_worker_dirs(
    project_dir: Path,
    temp_root: Path,
    tasks: tuple[ParallelImplementTask, ...],
) -> dict[str, Path]:
    worker_dirs: dict[str, Path] = {}
    ignore = shutil.ignore_patterns(".git", "__pycache__", ".venv", "node_modules", "dist", "build")
    for task in tasks:
        worker_dir = temp_root / task.worker_name
        shutil.copytree(project_dir, worker_dir, ignore=ignore)
        worker_dirs[task.worker_name] = worker_dir
    return worker_dirs


def _find_copyback_conflicts(worker_results: list[WorkerExecutionResult]) -> list[str]:
    conflicts: list[str] = []
    seen: set[str] = set()
    for result in worker_results:
        task = result.task
        owned_paths = task.owned_paths or tuple(write.relative_path for write in task.writes)
        for path in owned_paths:
            normalized = path.replace("\\", "/")
            if normalized in seen:
                conflicts.append(f"duplicate ownership for {normalized}")
                continue
            seen.add(normalized)
    return conflicts


def _copy_back_changes(
    project_dir: Path,
    worker_results: list[WorkerExecutionResult],
) -> list[str]:
    files_changed: list[str] = []
    for result in worker_results:
        task = result.task
        worker_dir = result.worker_dir
        for rel in result.changed_paths:
            source = worker_dir / rel
            dest = project_dir / rel
            if source.is_dir():
                for file in sorted(source.rglob("*")):
                    if not file.is_file():
                        continue
                    rel_file = file.relative_to(worker_dir).as_posix()
                    _copy_if_changed(project_dir / rel_file, file, rel_file, files_changed)
                continue
            if source.exists():
                _copy_if_changed(dest, source, rel, files_changed)
    return files_changed


def _copy_if_changed(dest: Path, source: Path, rel_path: str, files_changed: list[str]) -> None:
    dest_exists = dest.exists()
    source_bytes = source.read_bytes()
    if dest_exists and dest.read_bytes() == source_bytes:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    if rel_path not in files_changed:
        files_changed.append(rel_path)


def _prepare_artifact_root(project_dir: Path) -> Path:
    """Create a persistent artifact directory for one external executor run."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact_root = project_dir / ".mstack-parallel-artifacts" / run_id
    artifact_root.mkdir(parents=True, exist_ok=True)
    return artifact_root


def _snapshot_owned_paths(worker_dir: Path, task: ParallelImplementTask) -> dict[str, str]:
    """Capture text snapshots of owned paths before or after a worker run."""
    snapshots: dict[str, str] = {}
    owned_paths = task.owned_paths or tuple(write.relative_path for write in task.writes)
    for owned_path in owned_paths:
        rel = owned_path.replace("\\", "/")
        source = worker_dir / rel
        if source.is_dir():
            for file in sorted(source.rglob("*")):
                if not file.is_file():
                    continue
                rel_file = file.relative_to(worker_dir).as_posix()
                snapshots[rel_file] = file.read_text(encoding="utf-8", errors="replace")
            continue
        if source.exists():
            snapshots[rel] = source.read_text(encoding="utf-8", errors="replace")
    return snapshots


def _changed_snapshot_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return changed path list from before/after snapshots."""
    changed: list[str] = []
    for rel in sorted(set(before) | set(after)):
        if before.get(rel) != after.get(rel):
            changed.append(rel)
    return changed


def _write_snapshot_artifacts(
    artifact_dir: Path,
    before: dict[str, str],
    after: dict[str, str],
    changed_paths: list[str],
) -> None:
    """Write before/after snapshots and diffs for owned paths."""
    (artifact_dir / "changed_paths.json").write_text(
        json.dumps({"changed_paths": changed_paths}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    snapshot_dir = artifact_dir / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for rel in sorted(set(before) | set(after)):
        safe_name = rel.replace("/", "__")
        before_text = before.get(rel, "")
        after_text = after.get(rel, "")
        (snapshot_dir / f"{safe_name}.before.txt").write_text(before_text, encoding="utf-8")
        (snapshot_dir / f"{safe_name}.after.txt").write_text(after_text, encoding="utf-8")
        diff_text = "".join(
            unified_diff(
                before_text.splitlines(keepends=True),
                after_text.splitlines(keepends=True),
                fromfile=f"{rel}:before",
                tofile=f"{rel}:after",
            )
        )
        (snapshot_dir / f"{safe_name}.diff.txt").write_text(diff_text, encoding="utf-8")
