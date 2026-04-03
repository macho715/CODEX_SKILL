#!/usr/bin/env python3
"""Create the managed documentation bundle for a project."""

from __future__ import annotations

import argparse
import json

from doc_orchestrator_lib import (
    docs_root_path,
    evaluate_parallel_execution,
    load_snapshot,
    parse_targets,
    write_docs,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create the managed documentation set for a project."
    )
    parser.add_argument("project_root", help="Project root directory")
    parser.add_argument(
        "--docs-root",
        help="Output directory for the managed docs. Defaults to <project>/docs/project-docs",
    )
    parser.add_argument(
        "--snapshot-file",
        help="Optional snapshot JSON produced by project_snapshot.py",
    )
    parser.add_argument(
        "--allow-overwrite-unmanaged",
        action="store_true",
        help="Allow overwriting unmanaged target files only after explicit user approval.",
    )
    parser.add_argument(
        "--allow-delete",
        action="store_true",
        help="Allow deleting obsolete managed files only after explicit user approval.",
    )
    parser.add_argument(
        "--targets",
        help="Optional comma-separated subset of target docs for parallel lanes.",
    )
    parser.add_argument(
        "--parallel-validated",
        action="store_true",
        help="Report this invocation as part of a validated lane-based parallel run.",
    )
    parser.add_argument(
        "--require-parallel",
        action="store_true",
        help="Fail instead of degrading when parallel execution was not validated.",
    )
    args = parser.parse_args()

    targets = parse_targets(args.targets)
    snapshot = load_snapshot(args.project_root, snapshot_file=args.snapshot_file)
    result = write_docs(
        snapshot=snapshot,
        docs_root=docs_root_path(args.project_root, args.docs_root),
        allow_overwrite_unmanaged=args.allow_overwrite_unmanaged,
        allow_delete=args.allow_delete,
        targets=targets,
    )
    result.update(
        evaluate_parallel_execution(
            parallel_validated=args.parallel_validated,
            require_parallel=args.require_parallel,
        )
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
