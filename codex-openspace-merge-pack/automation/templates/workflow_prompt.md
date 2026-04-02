You are running inside a Codex repository that already contains AGENTS.md and repo skills.

Mandatory execution order:
1. Use `openspace-bridge` to decide local-vs-delegate routing.
2. Use `orchestrate-analysis` for planner/specialist structure.
3. Use `analysis-verifier` before finalization.
4. If there are 3 or more meaningful options, write `04_options.json` for deterministic scoring.
5. If the bridge decides delegation is required, use OpenSpace host skills (`skill-discovery`, `delegate-task`) and keep the result concise.

Rules:
- Planner-first structure is required.
- Verifier must separate PASS and FAIL.
- Maximum replan count: 1.
- Do not ask the user follow-up questions unless a critical input is missing.
- Write all outputs to the exact run directory given below.

Artifacts to create:
- {run_dir}/01_plan.md
- {run_dir}/02_draft.md
- {run_dir}/03_verification.md
- {run_dir}/04_options.json   (only if 3+ options exist)
- {run_dir}/05_final.md

User task:
{task}
