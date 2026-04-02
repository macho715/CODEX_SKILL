---
name: skill-update
description: Update or create Codex skills with a parallel-first workflow. Use when you need to benchmark a skill against the latest official docs, detect related existing skills and processes, reuse compatible assets, and produce validated skill patches or a new skill package.
---

# Skill Update

## trigger

Use this skill when Codex needs to create a new skill or refresh an existing skill package with reuse detection, source-backed benchmark notes, deterministic helper scripts, or parallel-capable authoring and verification.

## non-trigger

Do not use this skill for one-off prompt rewrites, destructive repo-wide cleanup, speculative platform claims without a source, or workflow changes that require human approval before touching CI, permissions, auth, billing, deployment, or secrets.

## inputs

Minimum useful input:
- target skill name
- `create` or `update` intent
- working directory or repo root
- internet allowed or blocked
- destructive actions allowed or not

Recommended request shape:

```json
{
  "mode": "create|update",
  "target_skill": "skill-name",
  "repo_root": ".",
  "intent": "one sentence goal",
  "internet_allowed": true,
  "allow_destructive": false,
  "emit_optional_agents": true,
  "notes": "optional constraints"
}
```

## steps

1. Read active `AGENTS.md` guidance before editing anything.
2. Load [references/official-benchmark-2026.md](references/official-benchmark-2026.md) first so the local fallback and current packaging rules are visible before any web lookup.
3. Confirm whether internet access and destructive actions are allowed. Require dry-run plus explicit approval before any destructive change.
4. Scan the current repo and available home-level skill locations:

   ```powershell
   python .agents/skills/skill-update/scripts/scan_skill_graph.py --root . --write artifacts/skill_inventory.json
   ```

5. Reuse an existing compatible skill, script, or reference instead of creating a duplicate when the inventory shows overlap.
6. If web access is allowed, benchmark the current package against official OpenAI Codex docs for `AGENTS.md`, skills, and subagents. Write absolute dates and source-backed behavior changes to `artifacts/benchmark_notes.md`. If web access is blocked, copy forward the bundled benchmark notes and mark the run `WEB_BLOCKED`.
7. Build the integration plan:

   ```powershell
   python .agents/skills/skill-update/scripts/build_update_plan.py --request .agents/skills/skill-update/examples/request.example.json --inventory artifacts/skill_inventory.json --write artifacts/update_plan.json
   ```

8. Author or patch the target skill package. Keep `SKILL.md` concise, move long notes into `references/`, keep deterministic logic in `scripts/`, and preserve working files unless the plan explicitly replaces them.
9. Use parallel lanes when the runtime actually supports them. Prefer custom agents when available, otherwise built-in subagents. If parallel execution is not available, continue sequentially and report `PARALLEL_DEGRADED` instead of overstating what happened.
10. Validate the package:

   ```powershell
   python .agents/skills/skill-update/scripts/validate_outputs.py --skill-root <target-skill-root> --inventory artifacts/skill_inventory.json --plan artifacts/update_plan.json --benchmark artifacts/benchmark_notes.md --write artifacts/verification_report.md
   ```

11. Deliver the changed skill, `artifacts/skill_inventory.json`, `artifacts/update_plan.json`, `artifacts/benchmark_notes.md`, and `artifacts/verification_report.md`.

## verification

Pass only when all of the following are true:
- `SKILL.md` frontmatter exists, uses `name` and `description`, and `name` matches the folder name.
- The skill body includes `trigger`, `non-trigger`, `steps`, and `verification`.
- `artifacts/skill_inventory.json`, `artifacts/update_plan.json`, `artifacts/benchmark_notes.md`, and `artifacts/verification_report.md` all exist for the run.
- Reuse or overlap claims point to real files, or are explicitly marked as assumptions.
- Destructive actions are either absent or gated by dry-run plus approval.
- Parallel execution claims are downgraded honestly when the runtime did not support the requested topology.

Use these status labels exactly when needed:
- `PASS`
- `PASS_WITH_WARNINGS`
- `PARALLEL_DEGRADED`
- `WEB_BLOCKED`
- `INVENTORY_INCOMPLETE`
- `VALIDATION_FAILED`
- `APPROVAL_REQUIRED`

## safety

- Never expose secrets, tokens, private URLs, or internal identifiers in benchmark notes or example artifacts.
- Never claim a feature exists without either an official OpenAI source or a real local file.
- Never delete or overwrite an existing skill without dry-run plus explicit approval.
- When evidence is incomplete, preserve the current files and emit a plan or warning instead of forcing a rewrite.
