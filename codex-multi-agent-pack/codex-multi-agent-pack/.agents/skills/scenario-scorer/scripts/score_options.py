#!/usr/bin/env python3
"""Deterministic weighted scenario scorer.

Usage:
  python scripts/score_options.py examples/input.example.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def validate_payload(data: dict[str, Any]) -> None:
    if "criteria" not in data or "options" not in data:
        raise ValueError("Payload must include 'criteria' and 'options'.")

    criteria = data["criteria"]
    options = data["options"]

    if not isinstance(criteria, list) or not criteria:
        raise ValueError("'criteria' must be a non-empty list.")
    if not isinstance(options, list) or len(options) < 3:
        raise ValueError("'options' must contain at least 3 options.")

    weight_total = sum(float(c["weight"]) for c in criteria)
    if round(weight_total, 2) != 100.00:
        raise ValueError(f"Criteria weights must sum to 100.00. Got {weight_total:.2f}.")

    required_criteria_names = {c["name"] for c in criteria}
    for option in options:
        if "name" not in option or "scores" not in option:
            raise ValueError("Each option must include 'name' and 'scores'.")
        score_names = set(option["scores"].keys())
        if score_names != required_criteria_names:
            missing = required_criteria_names - score_names
            extra = score_names - required_criteria_names
            raise ValueError(
                f"Option {option.get('name', '<unknown>')} score keys mismatch. "
                f"Missing={sorted(missing)}, Extra={sorted(extra)}"
            )


def compute_scores(data: dict[str, Any]) -> dict[str, Any]:
    criteria = data["criteria"]
    options = data["options"]
    max_score = float(data.get("scale_max", 5))

    weight_map = {c["name"]: float(c["weight"]) for c in criteria}
    option_results: list[dict[str, Any]] = []

    for option in options:
        weighted_total = 0.0
        breakdown = []
        for criterion_name, raw_score in option["scores"].items():
            raw_score_f = float(raw_score)
            normalized = raw_score_f / max_score
            weighted = normalized * weight_map[criterion_name]
            weighted_total += weighted
            breakdown.append(
                {
                    "criterion": criterion_name,
                    "raw_score": round(raw_score_f, 2),
                    "weight": round(weight_map[criterion_name], 2),
                    "weighted_points": round(weighted, 2),
                }
            )
        option_results.append(
            {
                "name": option["name"],
                "total_score": round(weighted_total, 2),
                "breakdown": breakdown,
            }
        )

    ranked = sorted(option_results, key=lambda x: x["total_score"], reverse=True)
    winner = ranked[0]

    return {
        "criteria": criteria,
        "ranked_options": ranked,
        "recommended_option": winner["name"],
        "recommended_score": winner["total_score"],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/score_options.py <input.json>", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    data = json.loads(input_path.read_text(encoding="utf-8"))
    validate_payload(data)
    result = compute_scores(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
