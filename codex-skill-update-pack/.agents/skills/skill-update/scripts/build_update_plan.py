#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main() -> None:
    ap = argparse.ArgumentParser(description="Build a skill update plan from request + inventory.")
    ap.add_argument("--request", required=True)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--write", default="")
    args = ap.parse_args()

    req = load_json(args.request)
    inv = load_json(args.inventory)

    target = req.get("target_skill", "").strip()
    intent = req.get("intent", "").strip()
    internet_allowed = bool(req.get("internet_allowed", False))
    emit_optional_agents = bool(req.get("emit_optional_agents", True))

    exact = []
    similar = []
    for skill in inv.get("skills", []):
        name = skill.get("name") or skill.get("folder_name") or ""
        desc = skill.get("description", "")
        hay = f"{name} {desc}".lower()
        if target and name == target:
            exact.append(skill)
        elif target and target.lower().replace("-", " ") in hay.replace("-", " "):
            similar.append(skill)

    recommendations = []
    if exact:
        recommendations.append({
            "type": "update-existing",
            "reason": f"Exact existing skill found for '{target}'. Update in place unless approval requires a fork."
        })
    elif similar:
        recommendations.append({
            "type": "review-overlap",
            "reason": f"Found {len(similar)} overlapping skill(s). Reuse or split before creating a duplicate."
        })
    else:
        recommendations.append({
            "type": "create-new",
            "reason": f"No exact match found for '{target}'. Create a new repo-scoped skill."
        })

    lanes = [
        {"lane": "A", "name": "inventory-scout", "goal": "discover skills, AGENTS.md, scripts, overlaps"},
        {"lane": "B", "name": "official-doc-scout", "goal": "benchmark against latest official docs"} if internet_allowed else {"lane": "B", "name": "reference-scout", "goal": "use bundled official benchmark notes"},
        {"lane": "C", "name": "author-worker", "goal": "author or patch the target skill"},
        {"lane": "D", "name": "verifier", "goal": "validate outputs and downgrade if parallel support was absent"},
    ]
    target_root = f".agents/skills/{target}" if target else ".agents/skills/<target>"
    benchmark_source = "official-openai-docs" if internet_allowed else "bundled-reference"

    out = {
        "request": req,
        "inventory_summary": inv.get("summary", {}),
        "exact_matches": exact,
        "similar_matches": similar,
        "recommendations": recommendations,
        "parallel_plan": {
            "mode": "parallel-first",
            "lanes": lanes,
            "emit_optional_agents": emit_optional_agents
        },
        "authoring_rules": [
            "Reuse existing scripts where practical.",
            "Keep SKILL.md concise; move long notes to references/.",
            "Add dry-run gates before destructive steps.",
            "Prefer repo-scoped .agents/skills unless user explicitly wants global install.",
            "Mark unsupported runtime capabilities as degraded instead of pretending they ran."
        ],
        "benchmark_source": benchmark_source,
        "next_files": [
            f"{target_root}/SKILL.md",
            f"{target_root}/scripts/*",
            f"{target_root}/references/*",
            "artifacts/benchmark_notes.md",
            "artifacts/verification_report.md"
        ],
        "intent": intent,
    }

    blob = json.dumps(out, indent=2, ensure_ascii=False)
    if args.write:
        out_path = Path(args.write)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(blob, encoding="utf-8")
    else:
        print(blob)

if __name__ == "__main__":
    main()
