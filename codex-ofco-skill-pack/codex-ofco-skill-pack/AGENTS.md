# AGENTS.md

## Purpose
This repository provides Codex-only skills for OFCO and HVDC invoice, line export, grouping, cost hierarchy mapping, and flow code validation workflows.

## Always apply
- Use the closest matching skill in `.codex/skills/` before inventing a new workflow.
- Prefer deterministic local scripts over free-form reasoning when structured input JSON is available.
- Stop on missing required fields. Do not fabricate rows, mappings, routing legs, or evidence.
- Keep source files unchanged. Write outputs only under each skill's `out/` directory unless the user explicitly requests another location.
- For destructive actions, use dry-run first and present the change list before execution.

## Repo conventions
- Skill folders use kebab-case names.
- Scripts are Python and expect exactly one JSON input path argument.
- Numeric outputs use 2-decimal precision where applicable.
- Status values must remain explicit: `MATCHED`, `MISMATCH`, `UNMATCHED`, `PASS`, `FAIL`, `OK`, `FAILED`.

## Quick map
- invoice row matching -> `invoice-match-verify`
- cost hierarchy mapping -> `cost-center-mapper`
- vendor invoice grouping -> `vendor-invoice-grouping`
- fixed lines export -> `ofco-lines-export`
- routing / flow code check -> `flow-code-validator`
