# Benchmark Notes

Verification date: 2026-04-03
Sources:
- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/subagents

## Current official baseline
- Codex reads `AGENTS.md` files before work and layers project guidance from repository root down to the current working directory.
- Skills are directories with `SKILL.md`; `SKILL.md` must include `name` and `description`.
- Skills may optionally include `scripts/`, `references/`, `assets/`, `examples/`, and `agents/openai.yaml`.
- Repo-scoped skill discovery scans `.agents/skills` from the current working directory up to the repository root.
- Custom agent files live under `.codex/agents/` and must define `name`, `description`, and `developer_instructions`.
- Optional custom-agent fields include `nickname_candidates`, `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config`.

## Local package notes
- The reviewed `excel-vba` package is a standalone skill and plugin workspace, not a repo-scoped `.agents/skills` package. This is compatible with local distribution but is not the primary repo-scoped path documented in official Codex docs.
- The `excel-vba` skill now meets local workspace rules by including `trigger`, `non-trigger`, `steps`, and `verification` in addition to the official `name` and `description` frontmatter.
- The package uses optional `agents/openai.yaml`, examples, and reference documents in a way that is compatible with the official skill packaging model.
- The package also includes project-scoped `.codex/agents` and root `AGENTS.md` guidance for a guarded companion workflow; this extends the package beyond the minimum official skill shape but aligns with the official AGENTS.md and subagents documentation.
- The integrated `excel-xlsm-contract-ops` companion skill is a local packaging extension that routes high-risk existing `.xlsm` work more explicitly; this is an inference from the local package structure, not a separate official Codex requirement.

## Compatibility verdict
- Official Codex compatibility: PASS
- Local packaging posture: PASS_WITH_WARNINGS
- Warning: the repo distributes skills from package-local directories rather than the officially documented repo-scoped `.agents/skills` path, so local install and plugin distribution remain the primary supported activation routes for this package.