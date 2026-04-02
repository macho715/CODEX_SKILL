#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")

def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def parse_frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out

def check_section(text: str, heading: str) -> bool:
    return heading.lower() in text.lower()

def main() -> None:
    ap = argparse.ArgumentParser(description="Validate a generated skill package.")
    ap.add_argument("--skill-root", required=True)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--benchmark", default="")
    ap.add_argument("--write", default="")
    args = ap.parse_args()

    skill_root = Path(args.skill_root)
    inv = read_json(args.inventory)
    plan = read_json(args.plan)

    issues: list[str] = []
    warnings: list[str] = []

    skill_md = skill_root / "SKILL.md"
    if not skill_md.exists():
        issues.append("Missing SKILL.md")
        text = ""
        fm = {}
    else:
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        if not fm:
            issues.append("Missing or invalid YAML frontmatter")
        if fm.get("name", "") != skill_root.name:
            issues.append("Frontmatter name does not match folder name")
        if not NAME_RE.match(fm.get("name", "")):
            issues.append("Skill name violates Codex skill naming constraints")
        if len(fm.get("description", "")) < 30:
            warnings.append("Description is short; routing reliability may be weak")

    if not (skill_root / "scripts").exists():
        warnings.append("No scripts/ directory present")
    if not (skill_root / "references").exists():
        warnings.append("No references/ directory present")
    if not (skill_root / "examples").exists():
        warnings.append("No examples/ directory present")

    if inv.get("summary", {}).get("skill_count", 0) == 0:
        warnings.append("Inventory is empty; reuse detection may be incomplete")

    if plan.get("parallel_plan", {}).get("mode") != "parallel-first":
        warnings.append("Plan is not marked parallel-first")
    if any("<target>" in item for item in plan.get("next_files", [])):
        warnings.append("Plan still contains unresolved <target> placeholders")

    for heading in ["## trigger", "## non-trigger", "## steps", "## verification"]:
        if text and not check_section(text, heading):
            issues.append(f"Missing required section: {heading}")

    benchmark_text = ""
    if args.benchmark:
        benchmark_path = Path(args.benchmark)
        if not benchmark_path.exists():
            issues.append("Missing benchmark notes artifact")
        else:
            benchmark_text = benchmark_path.read_text(encoding="utf-8", errors="ignore")
            if not DATE_RE.search(benchmark_text):
                warnings.append("Benchmark notes do not contain an absolute date")

    if plan.get("parallel_plan", {}).get("emit_optional_agents") and not (skill_root.parents[2] / ".codex" / "agents").exists():
        warnings.append("Plan requests optional custom agents, but .codex/agents is missing")

    status = "PASS"
    if issues:
        status = "VALIDATION_FAILED"
    elif warnings:
        status = "PASS_WITH_WARNINGS"

    lines = [
        "# Verification Report",
        "",
        f"- Status: **{status}**",
        f"- Skill root: `{skill_root}`",
        "",
        "## Errors",
    ]
    if issues:
        lines.extend([f"- {x}" for x in issues])
    else:
        lines.append("- None")
    lines.extend(["", "## Warnings"])
    if warnings:
        lines.extend([f"- {x}" for x in warnings])
    else:
        lines.append("- None")
    lines.extend(["", "## Inventory Summary", "```json", json.dumps(inv.get("summary", {}), indent=2, ensure_ascii=False), "```"])
    if benchmark_text:
        lines.extend(["", "## Benchmark Artifact", f"- Path: `{args.benchmark}`"])

    report = "\n".join(lines)
    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
    else:
        print(report)

if __name__ == "__main__":
    main()
