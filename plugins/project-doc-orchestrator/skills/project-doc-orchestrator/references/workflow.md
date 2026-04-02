# Workflow

## Execution Order
1. Run `scripts/project_snapshot.py`.
2. Review the snapshot and the inspected file list.
3. By default, split the work into three parallel lanes.
4. Generate or patch lane-owned docs with `--targets`.
5. Run one final full-bundle patch to align wording and links.

## Orchestration Pattern
- Use a manager-worker topology.
- Main thread responsibilities: choose `project_root`, generate the snapshot, launch the 3 lanes, integrate results, and run the final full-bundle patch.
- Worker lane responsibilities: re-check owned evidence, patch only owned targets, and surface evidence gaps instead of guessing.

## Current Project Reuse
- If the current project is already established in the session, reuse that repository as `project_root` unless the user redirects to another repo.
- When the current project changes during the session, refresh the managed docs bundle from the updated repository state rather than starting from a generic template.

## Lane Ownership
- Lane 1 owns `README.md`, `GUIDE.md`
- Lane 2 owns `PLAN.md`, `CHANGELOG.md`
- Lane 3 owns `LAYOUT.md`, `ARCHITECTURE.md`

## Stop Conditions
- Stop if subagents are unavailable.
- Stop if parallel lanes are unavailable, unless the user explicitly approves a degraded sequential fallback.
- Stop if a target file is unmanaged and overwrite approval has not been given.
- Stop if deletion would be required and delete approval has not been given.

## Validation Gates
- After the lanes finish, run one final full-bundle patch before concluding.
- Verify that preserve blocks survived, managed markers remain intact, and each target file was owned by exactly one lane before the final integration pass.
- Verify that the snapshot and final docs reflect the current repo rather than stale generated outputs.
