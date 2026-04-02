#!/usr/bin/env python3
"""Inspect a project and emit a normalized snapshot for document generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from doc_orchestrator_lib import build_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a project and emit a normalized snapshot as JSON."
    )
    parser.add_argument("project_root", help="Project root directory to inspect")
    parser.add_argument(
        "--output",
        help="Optional JSON file path. When omitted, print to stdout.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level when printing or writing output",
    )
    args = parser.parse_args()

    snapshot = build_snapshot(args.project_root)
    rendered = json.dumps(snapshot, indent=args.indent, ensure_ascii=False) + "\n"
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
