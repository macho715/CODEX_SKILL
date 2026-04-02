#!/usr/bin/env python3
"""Validate a design-upgrade scorecard and print a PASS/FAIL summary.

Usage:
  python scripts/validate_design_scorecard.py path/to/design-scorecard.json
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REQUIRED_METRICS = [
    "visual_hierarchy",
    "readability",
    "spacing_alignment",
    "component_consistency",
    "information_clarity",
    "usability",
    "brand_fit",
]
MIN_EACH = 3.5
MIN_AVG = 4.0


def fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("expected exactly one argument: path to design-scorecard.json")

    path = Path(sys.argv[1])
    if not path.exists():
        return fail(f"file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"invalid JSON: {exc}")

    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return fail("missing object: metrics")

    missing = [name for name in REQUIRED_METRICS if name not in metrics]
    if missing:
        return fail(f"missing metrics: {', '.join(missing)}")

    values: list[float] = []
    for name in REQUIRED_METRICS:
        value = metrics[name]
        if not isinstance(value, (int, float)):
            return fail(f"metric '{name}' must be numeric")
        value = float(value)
        if not 0.0 <= value <= 5.0:
            return fail(f"metric '{name}' must be between 0.0 and 5.0")
        values.append(value)

    average = statistics.fmean(values)
    weakest = min(values)
    blockers = data.get("blocking_issues", [])
    if not isinstance(blockers, list):
        return fail("blocking_issues must be a list")

    if blockers:
        print(json.dumps({
            "verdict": "FAIL",
            "reason": "blocking issues present",
            "average": round(average, 2),
            "weakest_metric": round(weakest, 2),
            "blocking_issues": blockers,
        }, ensure_ascii=False, indent=2))
        return 1

    if weakest < MIN_EACH:
        print(json.dumps({
            "verdict": "FAIL",
            "reason": f"a metric is below {MIN_EACH}",
            "average": round(average, 2),
            "weakest_metric": round(weakest, 2),
        }, ensure_ascii=False, indent=2))
        return 1

    if average < MIN_AVG:
        print(json.dumps({
            "verdict": "FAIL",
            "reason": f"average is below {MIN_AVG}",
            "average": round(average, 2),
            "weakest_metric": round(weakest, 2),
        }, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps({
        "verdict": "PASS",
        "average": round(average, 2),
        "weakest_metric": round(weakest, 2),
        "metrics_checked": REQUIRED_METRICS,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
