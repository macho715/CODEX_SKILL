#!/usr/bin/env python3
"""Shared helpers for the project-doc-orchestrator skill."""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


DOC_ORDER = [
    "README.md",
    "PLAN.md",
    "LAYOUT.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "GUIDE.md",
]

DOC_DESCRIPTIONS = {
    "README.md": "High-level project summary based on inspected files.",
    "PLAN.md": "Evidence-backed plan derived from repository state, TODOs, and recent changes.",
    "LAYOUT.md": "Observed repository structure and important files.",
    "ARCHITECTURE.md": "Observed component and dependency relationships from manifests and source layout.",
    "CHANGELOG.md": "Recent project activity based on git history and documentation refreshes.",
    "GUIDE.md": "How to work with the project using inspected commands and scripts.",
}

MANAGED_MARKER = "<!-- PROJECT-DOC-ORCHESTRATOR:MANAGED -->"
MANAGED_START = "<!-- PROJECT-DOC-ORCHESTRATOR:MANAGED-START -->"
MANAGED_END = "<!-- PROJECT-DOC-ORCHESTRATOR:MANAGED-END -->"
PRESERVE_START = "<!-- PROJECT-DOC-ORCHESTRATOR:PRESERVE-START -->"
PRESERVE_END = "<!-- PROJECT-DOC-ORCHESTRATOR:PRESERVE-END -->"

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".next",
    ".nuxt",
    ".turbo",
    ".idea",
    ".vscode",
    "out",
    "target",
    "bin",
    "obj",
}

MANAGED_DOCS_RELATIVE_ROOT = "docs/project-docs"
SNAPSHOT_ARTIFACT_RELATIVE_PATHS = {
    "snapshot.json",
    "project_snapshot.json",
    f"{MANAGED_DOCS_RELATIVE_ROOT}/project_snapshot.json",
}
EVIDENCE_EXCLUDED_TOP_LEVEL_DIRS = {
    "_holding-root",
}
EVIDENCE_EXCLUDED_PATH_PARTS = {
    "_holding",
    "_holding-root",
    "artifacts",
    "validation-reports",
}

MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
    "Makefile",
    "Gemfile",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def safe_read_text(path: Path, limit: int = 120_000) -> str:
    data = path.read_bytes()[:limit]
    return data.decode("utf-8-sig", errors="replace")


def first_lines(text: str, limit: int = 3) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("#", "//", "/*", "*", "--")):
            continue
        lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def sanitize_node_id(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", value)
    token = token.strip("_")
    return token or "node"


def sanitize_label(value: str, limit: int = 40) -> str:
    cleaned = value.replace('"', "'").replace("\n", " ").strip()
    return cleaned[: limit - 3] + "..." if len(cleaned) > limit else cleaned


def collect_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_root, dir_names, file_names in os.walk(root):
        dir_names[:] = [name for name in dir_names if name not in IGNORE_DIRS]
        current = Path(current_root)
        for file_name in file_names:
            files.append(current / file_name)
    return files


def is_generated_output(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/").strip("/")
    if normalized in SNAPSHOT_ARTIFACT_RELATIVE_PATHS:
        return True
    return normalized == MANAGED_DOCS_RELATIVE_ROOT or normalized.startswith(f"{MANAGED_DOCS_RELATIVE_ROOT}/")


def is_excluded_evidence_path(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/").strip("/")
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        return False
    if parts[0] in EVIDENCE_EXCLUDED_TOP_LEVEL_DIRS:
        return True
    return any(part in EVIDENCE_EXCLUDED_PATH_PARTS for part in parts)


def should_skip_evidence_path(relative_path: str) -> bool:
    return is_generated_output(relative_path) or is_excluded_evidence_path(relative_path)


def has_visible_layout_content(path: Path, root: Path) -> bool:
    if not path.is_dir():
        return not should_skip_evidence_path(rel_path(path, root))
    for current_root, dir_names, file_names in os.walk(path):
        dir_names[:] = [
            name
            for name in dir_names
            if name not in IGNORE_DIRS
            and not should_skip_evidence_path(rel_path(Path(current_root) / name, root))
        ]
        current = Path(current_root)
        for file_name in file_names:
            if not should_skip_evidence_path(rel_path(current / file_name, root)):
                return True
    return False


def summarize_package_json(path: Path, text: str) -> dict[str, Any]:
    data = json.loads(text)
    scripts = sorted((data.get("scripts") or {}).keys())
    return {
        "kind": "package.json",
        "name": data.get("name") or path.parent.name,
        "version": data.get("version"),
        "summary": f"npm package with {len(scripts)} script(s)",
        "commands": [f"npm run {name}" for name in scripts[:8]],
        "script_names": scripts,
    }


def summarize_pyproject(path: Path, text: str) -> dict[str, Any]:
    if tomllib is None:
        return {
            "kind": "pyproject.toml",
            "name": path.parent.name,
            "summary": "Python project manifest",
            "commands": [],
        }
    data = tomllib.loads(text)
    project = data.get("project") or {}
    scripts = sorted((project.get("scripts") or {}).keys())
    return {
        "kind": "pyproject.toml",
        "name": project.get("name") or path.parent.name,
        "version": project.get("version"),
        "summary": f"Python project manifest with {len(scripts)} script entrypoint(s)",
        "commands": [f"python -m {entry}" for entry in scripts[:8]],
        "script_names": scripts,
    }


def summarize_requirements(path: Path, text: str) -> dict[str, Any]:
    deps = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return {
        "kind": "requirements.txt",
        "name": path.parent.name,
        "summary": f"Python requirements list with {len(deps)} package(s)",
        "commands": ["python -m pip install -r requirements.txt"],
        "dependencies": deps[:20],
    }


def summarize_makefile(path: Path, text: str) -> dict[str, Any]:
    targets = []
    for line in text.splitlines():
        if line.startswith(("\t", "#", ".")):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+):", line)
        if match:
            targets.append(match.group(1))
    return {
        "kind": "Makefile",
        "name": path.parent.name,
        "summary": f"Makefile with {len(targets)} target(s)",
        "commands": [f"make {target}" for target in targets[:8]],
        "targets": targets[:20],
    }


def summarize_generic_manifest(path: Path, text: str) -> dict[str, Any]:
    return {
        "kind": path.name,
        "name": path.parent.name,
        "summary": f"Manifest/config file: {path.name}",
        "commands": [],
        "preview": first_lines(text, limit=2),
    }


def summarize_manifest(path: Path, text: str) -> dict[str, Any]:
    if path.name == "package.json":
        return summarize_package_json(path, text)
    if path.name == "pyproject.toml":
        return summarize_pyproject(path, text)
    if path.name == "requirements.txt":
        return summarize_requirements(path, text)
    if path.name == "Makefile":
        return summarize_makefile(path, text)
    return summarize_generic_manifest(path, text)


def summarize_script(path: Path, text: str) -> dict[str, Any]:
    commands = []
    suffix = path.suffix.lower()
    relative = path.as_posix()
    if suffix == ".py":
        commands.append(f"python {relative}")
    elif suffix == ".ps1":
        commands.append(f"powershell -ExecutionPolicy Bypass -File {relative}")
    elif suffix == ".sh":
        commands.append(f"bash {relative}")
    elif suffix in {".bat", ".cmd"}:
        commands.append(relative)
    return {
        "path": relative,
        "kind": suffix.lstrip("."),
        "summary": "; ".join(first_lines(text, limit=2)) or "Script inspected",
        "commands": commands,
    }


def summarize_doc(path: Path, text: str) -> dict[str, Any]:
    title = None
    headings: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                headings.append(heading)
                if title is None:
                    title = heading
        if len(headings) >= 5:
            break
    title = title or path.stem
    summary = headings[1] if len(headings) > 1 else (first_lines(text, limit=1) or [title])[0]
    return {
        "path": path.as_posix(),
        "title": title,
        "summary": summary,
        "headings": headings,
    }


def detect_root_readme_name(root: Path) -> str | None:
    for candidate in ("README.md", "README.MD", "readme.md"):
        path = root / candidate
        if not path.exists():
            continue
        try:
            text = safe_read_text(path)
        except OSError:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip()
                if heading:
                    return heading
    return None


def build_layout_tree(root: Path, max_depth: int = 3, max_entries: int = 80) -> list[str]:
    lines = [f"{root.name}/"]
    count = 0

    def walk(current: Path, prefix: str, depth: int) -> None:
        nonlocal count
        if depth > max_depth or count >= max_entries:
            return
        entries = [
            entry
            for entry in sorted(current.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
            if entry.name not in IGNORE_DIRS
            and not should_skip_evidence_path(rel_path(entry, root))
            and (not entry.is_dir() or has_visible_layout_content(entry, root))
        ]
        for index, entry in enumerate(entries):
            if count >= max_entries:
                break
            connector = "\\-- " if index == len(entries) - 1 else "|-- "
            label = f"{entry.name}/" if entry.is_dir() else entry.name
            lines.append(prefix + connector + label)
            count += 1
            if entry.is_dir():
                extension = "    " if index == len(entries) - 1 else "|   "
                walk(entry, prefix + extension, depth + 1)

    walk(root, "", 1)
    return lines


def gather_git_info(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "is_git_repo": False,
        "branch": None,
        "recent_commits": [],
        "changed_files": [],
    }
    try:
        probe = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode != 0 or probe.stdout.strip() != "true":
            return result
        result["is_git_repo"] = True
        branch = subprocess.run(
            ["git", "-C", str(root), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=False,
        )
        result["branch"] = branch.stdout.strip() or None
        commits = subprocess.run(
            ["git", "-C", str(root), "log", "--date=short", "--pretty=format:%h|%ad|%s", "-n", "6"],
            capture_output=True,
            text=True,
            check=False,
        )
        if commits.returncode == 0:
            result["recent_commits"] = [
                {"hash": parts[0], "date": parts[1], "subject": parts[2]}
                for line in commits.stdout.splitlines()
                if (parts := line.split("|", 2)) and len(parts) == 3
            ]
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--short"],
            capture_output=True,
            text=True,
            check=False,
        )
        if status.returncode == 0:
            result["changed_files"] = status.stdout.splitlines()[:40]
    except FileNotFoundError:
        return result
    return result


def gather_todos(files: list[Path], root: Path, limit: int = 20) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    todo_pattern = re.compile(r"\b(TODO|FIXME|BUG|HACK)\b", re.IGNORECASE)
    allowed_suffixes = {
        ".py",
        ".ps1",
        ".sh",
        ".bat",
        ".cmd",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".md",
        ".toml",
        ".json",
        ".yml",
        ".yaml",
    }
    for path in files:
        if path.suffix.lower() not in allowed_suffixes:
            continue
        try:
            text = safe_read_text(path, limit=60_000)
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if todo_pattern.search(line):
                hits.append(
                    {
                        "path": rel_path(path, root),
                        "line": line_number,
                        "text": line.strip()[:180],
                    }
                )
                if len(hits) >= limit:
                    return hits
    return hits


def build_snapshot(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {root}")

    files = collect_files(root)
    manifests: list[dict[str, Any]] = []
    scripts: list[dict[str, Any]] = []
    docs: list[dict[str, Any]] = []
    inspected_files: list[str] = []
    counts = Counter()
    key_dirs = Counter()

    for path in files:
        counts[path.suffix.lower() or "<no_ext>"] += 1
        relative = rel_path(path, root)
        if should_skip_evidence_path(relative):
            continue
        top_level = relative.split("/", 1)[0]
        key_dirs[top_level] += 1
        name = path.name
        suffix = path.suffix.lower()
        is_manifest = name in MANIFEST_NAMES
        is_script = suffix in {".py", ".ps1", ".sh", ".bat", ".cmd"} and ("script" in relative.lower() or path.parent == root)
        is_doc = suffix in {".md", ".mdx", ".rst", ".txt"} and (
            "docs/" in relative.lower()
            or name.upper().startswith(("README", "CHANGELOG", "GUIDE", "ARCHITECTURE", "PLAN", "LAYOUT"))
        )
        if not (is_manifest or is_script or is_doc):
            continue
        try:
            text = safe_read_text(path)
        except OSError:
            continue
        inspected_files.append(relative)
        if is_manifest:
            info = summarize_manifest(path, text)
            info["path"] = relative
            manifests.append(info)
        if is_script:
            info = summarize_script(path, text)
            info["path"] = relative
            scripts.append(info)
        if is_doc:
            info = summarize_doc(path, text)
            info["path"] = relative
            docs.append(info)

    git_info = gather_git_info(root)
    evidence_files = [
        path
        for path in files
        if not should_skip_evidence_path(rel_path(path, root))
    ]
    todos = gather_todos(evidence_files, root)
    manifest_commands = []
    for manifest in manifests:
        manifest_commands.extend(manifest.get("commands", []))
    script_commands = []
    for script in scripts:
        script_commands.extend(script.get("commands", []))

    project_name = root.name
    root_readme_name = detect_root_readme_name(root)
    if root_readme_name:
        project_name = root_readme_name
    for manifest in manifests:
        manifest_path = manifest.get("path", "")
        if "/" in manifest_path:
            continue
        if manifest.get("name"):
            project_name = manifest["name"]
            break

    observations = []
    if manifests:
        observations.append(f"Detected {len(manifests)} manifest/config file(s).")
    else:
        observations.append("No known project manifest was detected.")
    if scripts:
        observations.append(f"Inspected {len(scripts)} runnable script file(s).")
    else:
        observations.append("No runnable script files were detected in the root or script directories.")
    if docs:
        observations.append(f"Inspected {len(docs)} existing documentation file(s).")
    else:
        observations.append("No existing Markdown/text documentation was detected in standard locations.")
    if git_info["is_git_repo"]:
        observations.append(
            f"Git repository detected on branch {git_info['branch'] or 'detached HEAD'} with {len(git_info['recent_commits'])} recent commit(s)."
        )
    else:
        observations.append("Git metadata was not available.")
    if todos:
        observations.append(f"Found {len(todos)} TODO/FIXME-style marker(s) in inspected text files.")

    return {
        "generated_at": now_iso(),
        "project_root": str(root),
        "project_name": project_name,
        "docs_root_default": str(root / "docs" / "project-docs"),
        "inspected_files": sorted(set(inspected_files)),
        "manifests": manifests,
        "scripts": scripts,
        "docs": docs,
        "source_summary": {
            "total_files": len(files),
            "counts_by_extension": dict(counts.most_common(20)),
            "top_level_entries": dict(key_dirs.most_common(12)),
        },
        "layout_tree": build_layout_tree(root),
        "git": git_info,
        "todos": todos,
        "commands": {
            "from_manifests": sorted(dict.fromkeys(manifest_commands))[:20],
            "from_scripts": sorted(dict.fromkeys(script_commands))[:20],
        },
        "observations": observations,
    }


def evaluate_parallel_execution(
    *,
    parallel_validated: bool,
    require_parallel: bool,
) -> dict[str, Any]:
    if parallel_validated:
        return {
            "execution_status": "PARALLEL_VALIDATED",
            "execution_detail": "Caller validated lane-based parallel execution for this run.",
        }
    if require_parallel:
        raise RuntimeError(
            "Parallel execution was required but not validated. "
            "Re-run with --parallel-validated only after the lane-based run is confirmed."
        )
    return {
        "execution_status": "PARALLEL_DEGRADED",
        "execution_detail": (
            "Parallel lane execution was not validated by the caller. "
            "This result should be treated as a degraded sequential fallback."
        ),
    }


def load_snapshot(project_root: str | Path, snapshot_file: str | None = None) -> dict[str, Any]:
    if snapshot_file:
        return json.loads(Path(snapshot_file).read_text(encoding="utf-8"))
    return build_snapshot(project_root)


def docs_root_path(project_root: str | Path, docs_root: str | None = None) -> Path:
    root = Path(project_root).resolve()
    if docs_root:
        return Path(docs_root).resolve()
    return root / "docs" / "project-docs"


def expected_doc_paths(docs_root: Path) -> dict[str, Path]:
    return {name: docs_root / name for name in DOC_ORDER}


def render_markdown_list(items: list[str], empty_text: str, limit: int = 8) -> str:
    if not items:
        return f"- {empty_text}"
    return "\n".join(f"- `{item}`" for item in items[:limit])


def render_inspected_file_list(snapshot: dict[str, Any], limit: int = 12) -> str:
    return render_markdown_list(
        snapshot.get("inspected_files", []),
        "No relevant scripts or docs were inspected.",
        limit=limit,
    )


def render_mermaid_readme(snapshot: dict[str, Any]) -> str:
    doc_nodes = [(sanitize_node_id(name), name.replace(".md", "")) for name in DOC_ORDER]
    lines = ["```mermaid", "flowchart LR"]
    lines.append(f'    root["{sanitize_label(snapshot["project_name"])}"]')
    lines.append('    inspect["Inspect real files"]')
    lines.append('    snapshot_node["Normalize snapshot"]')
    lines.append('    docs["Managed docs set"]')
    lines.append("    root --> inspect --> snapshot_node --> docs")
    for node_id, label in doc_nodes:
        lines.append(f'    {node_id}["{sanitize_label(label)}"]')
        lines.append(f"    docs --> {node_id}")
    lines.append("```")
    return "\n".join(lines)


def render_mermaid_plan(snapshot: dict[str, Any]) -> str:
    todo_count = len(snapshot.get("todos", []))
    changed_count = len(snapshot.get("git", {}).get("changed_files", []))
    docs_count = len(snapshot.get("docs", []))
    return "\n".join(
        [
            "```mermaid",
            "flowchart TD",
            '    evidence["Inspect current repo state"]',
            f'    changes["Changed files observed: {changed_count}"]',
            f'    todos["TODO/FIXME markers: {todo_count}"]',
            f'    docs["Existing docs inspected: {docs_count}"]',
            '    plan["Refresh PLAN.md with evidence-backed next steps"]',
            "    evidence --> changes",
            "    evidence --> todos",
            "    evidence --> docs",
            "    changes --> plan",
            "    todos --> plan",
            "    docs --> plan",
            "```",
        ]
    )


def render_mermaid_layout(snapshot: dict[str, Any]) -> str:
    lines = ["```mermaid", "flowchart TD", f'    repo["{sanitize_label(snapshot["project_name"])}"]']
    top_entries = list(snapshot.get("source_summary", {}).get("top_level_entries", {}).keys())[:8]
    for name in top_entries:
        node_id = sanitize_node_id(name)
        lines.append(f'    {node_id}["{sanitize_label(name)}"]')
        lines.append(f"    repo --> {node_id}")
    lines.append("```")
    return "\n".join(lines)


def render_mermaid_architecture(snapshot: dict[str, Any]) -> str:
    manifest_nodes = snapshot.get("manifests", [])[:6]
    script_nodes = snapshot.get("scripts", [])[:6]
    lines = ["```mermaid", "flowchart LR", '    repo["Project root"]']
    for manifest in manifest_nodes:
        node_id = sanitize_node_id(manifest["path"])
        lines.append(f'    {node_id}["{sanitize_label(manifest["path"])}"]')
        lines.append(f"    repo --> {node_id}")
    for script in script_nodes:
        node_id = sanitize_node_id(script["path"])
        lines.append(f'    {node_id}["{sanitize_label(script["path"])}"]')
        lines.append(f"    repo --> {node_id}")
    lines.append("```")
    return "\n".join(lines)


def render_mermaid_changelog(snapshot: dict[str, Any]) -> str:
    commits = snapshot.get("git", {}).get("recent_commits", [])[:5]
    lines = ["```mermaid", "timeline", "    title Observed Repository Activity"]
    if commits:
        for commit in commits:
            lines.append(f'    {commit["date"]} : {sanitize_label(commit["subject"], limit=60)}')
    else:
        lines.append(f'    {snapshot["generated_at"][:10]} : Documentation refresh without git history')
    lines.append("```")
    return "\n".join(lines)


def render_mermaid_guide() -> str:
    return "\n".join(
        [
            "```mermaid",
            "sequenceDiagram",
            "    participant User",
            "    participant Skill as project-doc-orchestrator",
            "    participant Repo as Project repo",
            "    User->>Skill: Invoke documentation refresh",
            "    Skill->>Repo: Inspect actual scripts, manifests, and docs",
            "    Skill->>Skill: Build normalized snapshot",
            "    Skill->>Repo: Patch managed docs",
            "    Skill-->>User: Return updated evidence-backed docs",
            "```",
        ]
    )


def manifest_summary_lines(snapshot: dict[str, Any]) -> str:
    manifests = snapshot.get("manifests", [])
    if not manifests:
        return "- No known project manifest was detected."
    return "\n".join(
        f"- `{item['path']}`: {item.get('summary', 'Manifest inspected.')}"
        for item in manifests[:8]
    )


def script_summary_lines(snapshot: dict[str, Any]) -> str:
    scripts = snapshot.get("scripts", [])
    if not scripts:
        return "- No runnable scripts were detected in the root or script directories."
    return "\n".join(
        f"- `{item['path']}`: {item.get('summary', 'Script inspected.')}"
        for item in scripts[:10]
    )


def doc_summary_lines(snapshot: dict[str, Any]) -> str:
    docs = snapshot.get("docs", [])
    if not docs:
        return "- No existing documentation files were found in standard locations."
    return "\n".join(
        f"- `{item['path']}`: {item.get('title', item['path'])}"
        for item in docs[:10]
    )


def render_commands(snapshot: dict[str, Any]) -> str:
    commands = snapshot.get("commands", {})
    merged = list(dict.fromkeys(commands.get("from_manifests", []) + commands.get("from_scripts", [])))
    return render_markdown_list(merged, "No executable command could be derived from inspected files.", limit=12)


def render_layout_tree(snapshot: dict[str, Any]) -> str:
    return "```text\n" + "\n".join(snapshot.get("layout_tree", [])) + "\n```"


def render_todos(snapshot: dict[str, Any]) -> str:
    todos = snapshot.get("todos", [])
    if not todos:
        return "- No TODO/FIXME markers were found in inspected text files."
    return "\n".join(
        f"- `{item['path']}:{item['line']}` {item['text']}" for item in todos[:12]
    )


def render_git_activity(snapshot: dict[str, Any]) -> str:
    commits = snapshot.get("git", {}).get("recent_commits", [])
    if not commits:
        return "- No git commit history was available."
    return "\n".join(
        f"- `{item['date']}` `{item['hash']}` {item['subject']}" for item in commits
    )


def plan_actions(snapshot: dict[str, Any]) -> list[str]:
    actions = []
    git_info = snapshot.get("git", {})
    if git_info.get("changed_files"):
        actions.append(f"Review and document the {len(git_info['changed_files'])} changed file(s) already visible in git status.")
    if snapshot.get("todos"):
        actions.append("Triaging TODO/FIXME markers is evidence-backed work that can be planned immediately.")
    if snapshot.get("scripts"):
        actions.append("Validate the inspected runnable scripts and keep GUIDE.md aligned with their real invocation shape.")
    if snapshot.get("manifests"):
        actions.append("Keep setup and architecture documentation synchronized with the inspected manifest files.")
    if not actions:
        actions.append("Keep the managed docs current until more executable project evidence appears.")
    return actions[:6]


def architecture_observations(snapshot: dict[str, Any]) -> list[str]:
    observations = []
    manifests = snapshot.get("manifests", [])
    scripts = snapshot.get("scripts", [])
    docs = snapshot.get("docs", [])
    if manifests:
        observations.append(f"The project exposes {len(manifests)} inspected manifest/config file(s) that define its tooling surface.")
    if scripts:
        observations.append(f"The project exposes {len(scripts)} inspected runnable script file(s) in root/script locations.")
    if docs:
        observations.append(f"There are {len(docs)} inspected documentation file(s) that may describe or duplicate current behavior.")
    if not observations:
        observations.append("Architecture insight is currently limited because the repository exposes little structured metadata.")
    return observations[:6]


def generate_doc_body(doc_name: str, snapshot: dict[str, Any]) -> str:
    generated_at = snapshot["generated_at"]
    project_name = snapshot["project_name"]
    if doc_name == "README.md":
        return f"""# {project_name}

> Managed by `project-doc-orchestrator`. This file is regenerated from inspected repository evidence.

## Purpose
{DOC_DESCRIPTIONS[doc_name]}

## Evidence Rule
This document was generated only after reading real manifests, scripts, and docs from the project. Missing evidence is called out instead of guessed.

## Overview Diagram
{render_mermaid_readme(snapshot)}

## Observations
{chr(10).join(f"- {item}" for item in snapshot.get("observations", []))}

## Inspected Manifests
{manifest_summary_lines(snapshot)}

## Inspected Scripts
{script_summary_lines(snapshot)}

## Existing Docs
{doc_summary_lines(snapshot)}

## Commands Derived From Inspected Files
{render_commands(snapshot)}

## Evidence Files
{render_inspected_file_list(snapshot)}

## Refresh Metadata
- Generated at: `{generated_at}`
- Project root: `{snapshot["project_root"]}`
"""
    if doc_name == "PLAN.md":
        actions = "\n".join(f"- {item}" for item in plan_actions(snapshot))
        return f"""# Current Plan For {project_name}

## Planning Rule
This plan only uses observed repository state, TODO markers, git activity, and inspected scripts/docs. It does not invent backlog items.

## Plan Diagram
{render_mermaid_plan(snapshot)}

## Evidence-Backed Next Actions
{actions}

## TODO And FIXME Evidence
{render_todos(snapshot)}

## Recent Activity Considered
{render_git_activity(snapshot)}

## Evidence Files
{render_inspected_file_list(snapshot)}

## Refresh Metadata
- Generated at: `{generated_at}`
"""
    if doc_name == "LAYOUT.md":
        top_level = snapshot.get("source_summary", {}).get("top_level_entries", {})
        top_level_lines = "\n".join(f"- `{name}`: {count} item(s)" for name, count in list(top_level.items())[:10])
        if not top_level_lines:
            top_level_lines = "- No top-level entries were counted."
        return f"""# Repository Layout For {project_name}

## Layout Rule
This layout reflects the current filesystem inspection, not an assumed project template.

## Layout Diagram
{render_mermaid_layout(snapshot)}

## Tree Snapshot
{render_layout_tree(snapshot)}

## Top-Level Entry Counts
{top_level_lines}

## Files Used To Infer Layout
{render_inspected_file_list(snapshot)}

## Refresh Metadata
- Generated at: `{generated_at}`
"""
    if doc_name == "ARCHITECTURE.md":
        observations = "\n".join(f"- {item}" for item in architecture_observations(snapshot))
        return f"""# Observed Architecture For {project_name}

## Architecture Rule
This architecture view is derived from inspected manifests, scripts, source layout, and docs. If there is not enough evidence, the gaps are stated plainly.

## Architecture Diagram
{render_mermaid_architecture(snapshot)}

## Observed Architecture Notes
{observations}

## Manifest Surface
{manifest_summary_lines(snapshot)}

## Automation Surface
{script_summary_lines(snapshot)}

## Evidence Files
{render_inspected_file_list(snapshot)}

## Refresh Metadata
- Generated at: `{generated_at}`
"""
    if doc_name == "CHANGELOG.md":
        changed_files = snapshot.get("git", {}).get("changed_files", [])
        changed_lines = render_markdown_list(changed_files, "No changed files were reported by git status.", limit=12)
        return f"""# Observed Changelog For {project_name}

## Changelog Rule
This file records observable project history from git metadata and documentation refresh events. It does not manufacture release notes.

## Activity Diagram
{render_mermaid_changelog(snapshot)}

## Recent Commits
{render_git_activity(snapshot)}

## Current Working Tree Signals
{changed_lines}

## Documentation Refresh
- `{generated_at[:10]}` Managed docs refreshed from current repository inspection.

## Evidence Files
{render_inspected_file_list(snapshot)}
"""
    if doc_name == "GUIDE.md":
        return f"""# Working Guide For {project_name}

## Guide Rule
Only commands and workflows verified from inspected manifests, scripts, and docs are included below.

## Guide Diagram
{render_mermaid_guide()}

## Commands You Can Run
{render_commands(snapshot)}

## Script Entry Points
{script_summary_lines(snapshot)}

## Documentation Inputs
{doc_summary_lines(snapshot)}

## Evidence Files
{render_inspected_file_list(snapshot)}

## Refresh Metadata
- Generated at: `{generated_at}`
"""
    raise KeyError(f"Unsupported document name: {doc_name}")


def compose_managed_file(body: str, preserved: str) -> str:
    preserved_text = preserved.strip("\n")
    if not preserved_text:
        preserved_text = (
            "Add notes here if you need human-authored content preserved across refreshes.\n"
            "Do not remove the preserve markers."
        )
    return (
        f"{MANAGED_MARKER}\n"
        f"{MANAGED_START}\n"
        f"{body.rstrip()}\n"
        f"{MANAGED_END}\n\n"
        f"{PRESERVE_START}\n"
        f"{preserved_text}\n"
        f"{PRESERVE_END}\n"
    )


def is_managed_file(text: str) -> bool:
    return MANAGED_MARKER in text


def extract_preserved_text(text: str) -> str:
    pattern = re.compile(
        re.escape(PRESERVE_START) + r"\n(.*?)\n" + re.escape(PRESERVE_END),
        re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1) if match else ""


def ensure_write_allowed(path: Path, allow_overwrite_unmanaged: bool) -> None:
    if not path.exists():
        return
    text = safe_read_text(path)
    if is_managed_file(text):
        return
    if allow_overwrite_unmanaged:
        return
    raise RuntimeError(f"Refusing to overwrite unmanaged file without approval: {path}")


def find_obsolete_managed_files(docs_root: Path) -> list[Path]:
    expected = set(expected_doc_paths(docs_root).values())
    obsolete = []
    if not docs_root.exists():
        return obsolete
    for candidate in docs_root.glob("*.md"):
        if candidate in expected:
            continue
        try:
            text = safe_read_text(candidate)
        except OSError:
            continue
        if is_managed_file(text):
            obsolete.append(candidate)
    return obsolete


def write_docs(
    snapshot: dict[str, Any],
    docs_root: Path,
    allow_overwrite_unmanaged: bool = False,
    allow_delete: bool = False,
    targets: list[str] | None = None,
) -> dict[str, Any]:
    docs_root.mkdir(parents=True, exist_ok=True)
    target_names = targets or DOC_ORDER
    written: list[str] = []
    preserved: list[str] = []
    for doc_name in target_names:
        path = docs_root / doc_name
        ensure_write_allowed(path, allow_overwrite_unmanaged=allow_overwrite_unmanaged)
        previous_text = safe_read_text(path) if path.exists() else ""
        preserved_text = extract_preserved_text(previous_text) if previous_text else ""
        if preserved_text:
            preserved.append(doc_name)
        content = compose_managed_file(generate_doc_body(doc_name, snapshot), preserved_text)
        path.write_text(content, encoding="utf-8", newline="\n")
        written.append(str(path))

    deleted: list[str] = []
    obsolete = find_obsolete_managed_files(docs_root)
    if obsolete and not allow_delete:
        raise RuntimeError(
            "Managed obsolete files are present but deletion is not allowed. "
            "Re-run with --allow-delete only after explicit user approval."
        )
    if allow_delete:
        for path in obsolete:
            path.unlink()
            deleted.append(str(path))

    return {
        "docs_root": str(docs_root),
        "written_files": written,
        "preserved_files": preserved,
        "deleted_files": deleted,
    }


def parse_targets(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    targets = [item.strip() for item in raw.split(",") if item.strip()]
    invalid = [item for item in targets if item not in DOC_ORDER]
    if invalid:
        raise ValueError(
            "Unsupported target file(s): " + ", ".join(invalid) + ". "
            "Valid targets: " + ", ".join(DOC_ORDER)
        )
    return targets
