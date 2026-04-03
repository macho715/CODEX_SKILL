# Benchmark Notes 2026

Verification date: 2026-04-03

## Purpose

This note records the current Codex guidance that matters for high-risk Excel work and why the risk-pack style companion workflow exists.

## Relevant Codex Guidance

### AGENTS.md

- Codex reads project instructions before work.
- Project guidance should be layered from the repository root down to the current working directory.
- Instruction files should be concise and operational.

### Skills

- Skills are directories with `SKILL.md`.
- `SKILL.md` must include `name` and `description`.
- Optional assets include `scripts/`, `references/`, `examples/`, and `agents/openai.yaml`.
- Skills are intended for reusable workflows, not one-off prompts.

### Subagents

- Custom agents live under `.codex/agents/`.
- Required fields include `name`, `description`, and `developer_instructions`.
- A guarded, role-separated workflow is appropriate when the task has clear planner, guardrail, implementer, and verifier phases.

### Security and approvals

- Approval policy and sandbox mode should be explicit.
- Sensitive workbook actions should not rely on file creation alone.
- Hidden failure is a real risk after save or reinjection.

## Risk Summary

The highest-risk Excel cases are still:

- existing `.xlsm`
- Python and VBA mixed mutation
- COM automation or VBA reinjection
- `Application.Run`
- non-ASCII path, filename, sheet name, or caption
- button, shape, `OnAction`, event, named range, `ListObject`, or formula-bearing contract surface
- open workbook with possible unsaved changes

## Conclusion

The companion skill exists to make these high-risk cases explicit, serial, and verifiable instead of treating them as ordinary workbook editing.

