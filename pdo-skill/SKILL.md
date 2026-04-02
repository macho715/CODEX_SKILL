---
name: project-doc-orchestrator
description: Inspect a real repository and generate or refresh a managed project docs bundle from actual files. Use when users ask to create, rebuild, or update `docs/project-docs` documentation such as `README.md`, `PLAN.md`, `LAYOUT.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, or `GUIDE.md`, and also during ongoing work on the current project in the same session when the repo changes and the docs need to be refreshed in parallel from real scripts, manifests, layout, commands, and current state rather than guesses. Requires subagent support for its intended parallel workflow.
---

# Project Doc Orchestrator

Generate and refresh a 6-file managed documentation set under `<project-root>/docs/project-docs`.
Base every claim on actual inspection of the repository. Do not invent architecture, commands, status, or history.
During ongoing work on the current project in the same session, treat the active repository as the default target unless the user redirects to another repo.

## Use This Skill When
- The user wants to create, rebuild, or refresh the managed docs bundle under `docs/project-docs`.
- The current project changed during the session and the managed docs need to catch up with real code, scripts, manifests, or docs.
- The user wants repository structure, commands, architecture, layout, changelog, or working guidance documented from inspected files rather than freeform writing.

## Do Not Use This Skill When
- The user only wants freeform writing, translation, or a one-off rewrite that is not tied to inspected repository evidence.
- The target files are unmanaged and the user has not approved overwrite behavior.
- Subagents are unavailable and the user has not explicitly accepted a degraded sequential fallback.

## Required Read Order
1. Read [references/evidence-rule.md](references/evidence-rule.md) first.
2. Read [references/workflow.md](references/workflow.md) before running any script.
3. Read [references/file-contract.md](references/file-contract.md) before creating or patching docs.
4. Read [references/mermaid-guidelines.md](references/mermaid-guidelines.md) before writing diagrams.

## Hard Rules
- Require subagent support. If the active Codex surface cannot run parallel lanes, stop and say that this skill cannot be used safely there.
- When the surface supports subagents, run the documentation refresh in parallel by default using the defined lane ownership.
- Do not collapse lane work into one sequential pass unless parallel execution is unavailable and the user explicitly accepts a degraded fallback.
- Inspect the real project first. Run [scripts/project_snapshot.py](scripts/project_snapshot.py) before drafting or patching any document.
- MUST read the actual scripts, manifests, config files, and existing docs that support a claim before writing that claim.
- MUST verify the relevant real script and real document inputs again before each document write or patch pass.
- Must derive Mermaid diagrams from inspected project evidence, not a generic template.
- Must mark missing evidence explicitly instead of guessing.
- Must not overwrite unmanaged target files unless the user explicitly approves it.
- Must not delete existing materials unless the user explicitly approves it.

## Execution Model
- Use a manager-worker pattern: main thread inspects the repo and generates the snapshot, worker lanes own disjoint target files, and the main thread performs the final synthesis pass.
- Keep the orchestration testable: every write must be attributable to inspected evidence, an owned target set, and a final normalization pass.
- Treat managed docs as outputs, not primary evidence. Re-read the real repo inputs that justify each document.

## Workflow
Default execution mode is 3 parallel lanes plus one final integration pass.
1. Run [scripts/project_snapshot.py](scripts/project_snapshot.py) against the target project and keep the snapshot JSON.
2. Confirm the target docs root. Default to `<project-root>/docs/project-docs`.
3. Use parallel lanes with disjoint ownership:
   - lane 1: `README.md`, `GUIDE.md`
   - lane 2: `PLAN.md`, `CHANGELOG.md`
   - lane 3: `LAYOUT.md`, `ARCHITECTURE.md`
4. Each lane must verify the relevant inspected evidence before writing its files.
5. Use [scripts/scaffold_docs.py](scripts/scaffold_docs.py) for first-time generation or [scripts/patch_docs.py](scripts/patch_docs.py) for refreshes. Use `--targets` so each lane only writes its owned files.
6. After all lanes finish, integrate locally and run one final [scripts/patch_docs.py](scripts/patch_docs.py) pass for the full bundle to normalize wording, links, and current state.

## Validation
- Confirm all 6 managed files exist under `docs/project-docs`.
- Confirm preserve blocks remain intact after refresh.
- Confirm the managed docs reflect the current repository state, changed files, and runnable commands seen in the snapshot.
- If evidence is missing or too weak for a section, state that explicitly in the affected document instead of inferring.

## Parallel Execution Contract
- Keep snapshot generation on the main thread.
- Give each lane the same snapshot file and a disjoint `--targets` subset.
- Do not let two lanes edit the same target file.
- If any lane discovers missing evidence, fix the evidence gap first or state it plainly in the affected document.

## Commands
```bash
python scripts/project_snapshot.py <project-root> --output <project-root>/docs/project-docs/project_snapshot.json
python scripts/scaffold_docs.py <project-root> --snapshot-file <snapshot.json> --targets README.md,GUIDE.md
python scripts/patch_docs.py <project-root> --snapshot-file <snapshot.json> --targets PLAN.md,CHANGELOG.md
python scripts/patch_docs.py <project-root> --snapshot-file <snapshot.json>
```

## Approval Gates
- Use `--allow-overwrite-unmanaged` only after explicit user approval in the conversation.
- Use `--allow-delete` only after explicit user approval in the conversation.

## Outputs
- `README.md`
- `PLAN.md`
- `LAYOUT.md`
- `ARCHITECTURE.md`
- `CHANGELOG.md`
- `GUIDE.md`

All files are managed and include a preserved manual section. Refreshes rewrite managed content and keep the preserved section intact.
