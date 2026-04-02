# AGENTS.md

## Purpose
- This repository uses a planner-specialist-verifier workflow for complex analysis and system design.
- Keep always-on rules here; keep repeatable task procedures inside skills.

## Default workflow
1. Clarify the goal, constraints, and success criteria.
2. Let the planner define workstreams and acceptance criteria.
3. Let 2-4 specialists produce scoped outputs.
4. Run the verifier before finalizing.
5. Allow at most one replan when the verifier returns FAIL.
6. Deliver a structured, reproducible final report.

## Required behaviors
- Separate facts, evidence, and assumptions.
- If evidence is missing, mark it as AMBER or ask for missing inputs instead of inventing details.
- Keep specialist roles narrow and non-overlapping.
- Prefer deterministic scoring for final recommendations when options can be quantified.
- Do not perform destructive actions without dry-run, impact summary, and explicit approval.

## Skill routing hints
- Use `pipeline-coordinator` when the user wants a fixed 4-agent topology with one coordinator and three independent execution agents.
- Use `orchestrate-analysis` for multi-perspective planning and synthesis.
- Use `analysis-verifier` after any draft analysis, workflow design, or claimed completion.
- Use `scenario-scorer` when 3 or more options need weighted scoring and a reproducible recommendation.
