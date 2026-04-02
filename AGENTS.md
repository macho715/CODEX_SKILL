# AGENTS.md

## Purpose
- This repository is a workspace for authoring and maintaining Codex-oriented skills, plugins, and multi-agent guidance.
- Treat this repo as a guidance and automation-management workspace, not as a production application runtime.
- Keep durable repo-wide rules here. Put tool-specific differences in `CLAUDE.md` or `GEMINI.md` only when behavior must differ.

## Commands
- Before running anything, inspect the repo manifests and workflow files: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `justfile`, `Taskfile.yml`, `scripts/`, and `.github/workflows/`.
- Do not invent `install`, `dev`, `build`, `test`, `lint`, or `format` commands.
- Prefer the smallest relevant verification command first (file-scoped or package-scoped before full-repo checks).
- If the canonical command is unclear, stop and ask instead of guessing.

# [ASSUMPTION] Canonical commands are not confirmed from the current repo evidence.
# Verify with: package manager files, script folders, and CI workflow definitions.

## Source of Truth
- Repo manifests and CI/workflow files are authoritative for commands and verification order.
- Plugin manifests are authoritative for packaging and integration shape.
- `SKILL.md` is authoritative for reusable workflow behavior.
- Scripts, hooks, and CI are authoritative for deterministic enforcement. Do not rely on prose alone for mandatory checks.

## Workspace Layout
- `docs/` holds long-form reference, design notes, and examples.
- `.agents/` holds agent-specific material when tool-specific or persona-specific files are needed.
- `plugins/` holds plugin bundles and related packaging files.
- `source/` holds implementation or supporting code.
- Add `skills/` only when the repo standardizes reusable workflow bundles there.
- Add a nested `AGENTS.md` only when a subproject has materially different commands, boundaries, or verification rules.

## File Separation Rules
- `AGENTS.md` = durable repo-wide rules and non-inferable context.
- `SKILL.md` = repeated workflow with a clear trigger, non-trigger, steps, and pass/fail verification.
- `CLAUDE.md` / `GEMINI.md` = tool-specific overrides only.
- `scripts/`, hooks, and CI = deterministic enforcement.
- Do not store long procedural checklists in root `AGENTS.md` if they can live in a skill.

## What Good Changes Look Like
- Use concrete commands, real paths, and explicit boundaries.
- Prefer minimal, reviewable diffs.
- Follow the local style of the touched area instead of introducing new conventions.
- Keep generated guidance concise and operational.
- Document only what a coding agent cannot safely infer from reading code alone.

## Skill Rules
Create or update a skill only when all of the following are true:
- The workflow repeats regularly.
- The start condition can be stated in one sentence.
- Completion can be verified with pass/fail evidence.

Every `SKILL.md` must include:
- `name`
- `description`
- `trigger`
- `non-trigger`
- `steps`
- `verification`

Use `description` to make routing conditions explicit. Avoid vague descriptions.

## Plugin Rules
- Keep plugin scope minimal.
- Declare external integrations explicitly.
- Never embed secrets, tokens, or private endpoints in plugin files.
- If plugin behavior depends on MCP or external services, document the dependency and approval boundary.
- Update plugin docs when manifest behavior changes.

## Multi-Agent Rules
- Default orchestration pattern: Plan -> Execute -> Verify.
- Keep role boundaries explicit: planner, worker, verifier.
- Do not collapse verification into implementation for risky changes.
- Require a human decision point for high-risk or irreversible actions.

## Boundaries
### Always
- Read existing local patterns before editing.
- Prefer small diffs over broad refactors.
- Keep root guidance broad and subproject guidance local.
- Report assumptions explicitly.

### Ask first
- Adding or upgrading dependencies.
- Editing CI/CD, workflow automation, or release logic.
- Expanding plugin permissions or external network access.
- Renaming or deleting top-level folders.
- Changing auth, billing, deployment, or production-facing configuration.

### Never
- Commit secrets, API keys, tokens, or private URLs.
- Claim checks passed if you did not run them.
- Invent commands, paths, versions, or policies.
- Edit generated artifacts, lockfiles, or environment files unless the task explicitly requires it.

## Verification
- Run the smallest relevant checks first, then broader checks only if needed.
- For guidance-file changes, verify headings, paths, and references are correct.
- For skill changes, verify required fields exist and the verification step is measurable.
- For plugin changes, verify referenced paths exist and manifest references resolve.
- Report exactly which commands were run and their results.
- If verification could not be run, state that clearly and explain why.

## Change Reporting
Every substantial change report should include:
1. What changed
2. Files touched
3. Commands run and pass/fail results
4. Assumptions or unknowns
5. Remaining risks

## When to Stop
Stop and request human input if:
- Required commands or paths cannot be confirmed.
- The task touches secrets, production deployment, auth, billing, or destructive operations.
- A plugin permission change or external integration is unclear.
- Verification cannot be defined in a pass/fail way.

## Maintenance Rule
Update this file when a repeated agent mistake becomes clear or when a high-risk boundary changes.
Keep it short, concrete, and scannable.
