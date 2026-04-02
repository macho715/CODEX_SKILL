#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
KV_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")

def parse_frontmatter(text: str) -> dict[str, Any]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    raw = m.group(1)
    out: dict[str, Any] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        km = KV_RE.match(line)
        if km:
            key, value = km.group(1), km.group(2).strip()
            out[key] = value.strip('"').strip("'")
    return out

def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    return cur

def repo_skill_roots(start: Path) -> list[Path]:
    roots: list[Path] = []
    repo_root = find_repo_root(start)
    cur = start.resolve()
    lineage = [cur, *cur.parents]
    for p in lineage:
        candidate = p / ".agents" / "skills"
        if candidate.exists():
            roots.append(candidate)
        if p == repo_root:
            break
    return roots

def home_skill_roots() -> list[tuple[str, Path]]:
    home = Path.home()
    return [
        ("user", home / ".agents" / "skills"),
        ("compat-user", home / ".codex" / "skills"),
        ("admin", Path("/etc/codex/skills")),
    ]

def collect_skill(root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for skill_dir in sorted(root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        scripts = [str(p.relative_to(skill_dir)) for p in sorted((skill_dir / "scripts").rglob("*")) if p.is_file()] if (skill_dir / "scripts").exists() else []
        references = [str(p.relative_to(skill_dir)) for p in sorted((skill_dir / "references").rglob("*")) if p.is_file()] if (skill_dir / "references").exists() else []
        examples = [str(p.relative_to(skill_dir)) for p in sorted((skill_dir / "examples").rglob("*")) if p.is_file()] if (skill_dir / "examples").exists() else []
        items.append({
            "path": str(skill_dir),
            "folder_name": skill_dir.name,
            "name": fm.get("name", ""),
            "description": fm.get("description", ""),
            "scripts": scripts,
            "references": references,
            "examples": examples,
        })
    return items

def collect_agents_files(start: Path) -> list[str]:
    repo_root = find_repo_root(start)
    files: list[str] = []
    for p in [Path.home() / ".codex", repo_root, start.resolve(), *start.resolve().parents]:
        for name in ("AGENTS.override.md", "AGENTS.md"):
            candidate = p / name
            if candidate.exists():
                files.append(str(candidate))
    seen: list[str] = []
    for f in files:
        if f not in seen:
            seen.append(f)
    return seen

def main() -> None:
    ap = argparse.ArgumentParser(description="Scan Codex/Agent Skills and related guidance.")
    ap.add_argument("--root", default=".", help="Working directory to scan from.")
    ap.add_argument("--write", default="", help="Optional JSON output path.")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    repo_roots = repo_skill_roots(root)

    sources: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []

    for label, path in [("repo", p) for p in repo_roots] + home_skill_roots():
        entry = {"scope": label, "path": str(path), "exists": path.exists()}
        sources.append(entry)
        if path.exists() and path.is_dir():
            inventory.extend(collect_skill(path))

    result = {
        "scan_root": str(root),
        "repo_root": str(find_repo_root(root)),
        "sources": sources,
        "skills": inventory,
        "agents_md_files": collect_agents_files(root),
        "summary": {
            "skill_count": len(inventory),
            "scanned_source_count": len(sources),
        },
    }

    blob = json.dumps(result, indent=2, ensure_ascii=False)
    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(blob, encoding="utf-8")
    else:
        print(blob)

if __name__ == "__main__":
    main()
