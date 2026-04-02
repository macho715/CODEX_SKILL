---
name: analysis-verifier
description: Validate a draft analysis, workflow design, or multi-agent output against explicit acceptance criteria. Use after a draft claims completion and you need PASS/FAIL separation, gap detection, and a minimal patch list. When paired with `orchestrate-analysis` or `pipeline-coordinator`, run as an independent verifier agent rather than letting the coordinator self-certify.
---

# Analysis Verifier

## When to use
Use this skill when:
- a planner-specialist draft already exists,
- the user asks whether the draft is complete,
- a multi-agent output needs an independent skeptical review,
- the user wants verification owned by a separate agent in a pipeline.

Do not use this skill when:
- nothing has been drafted yet,
- the task is pure brainstorming without acceptance criteria.

## Inputs
- Draft output to verify
- Acceptance criteria or checklist
- Optional source files, links, or evidence references
- Draft type: planner-specialist workflow or single-draft analysis/workflow design
- Optional scoring artifact or criteria table when reproducibility depends on a separate scoring step

## Verification procedure

### 1. Extract claims
List what the draft claims to have completed.

### 2. Map claims to checks
Map each claim to a concrete verification point.

### 3. Apply the correct default checklist
When no custom checklist is supplied, choose one mode before scoring:

- Use `references/default-checklist.md` for planner-specialist-verifier workflows.
- Use `references/generic-checklist.md` for a single-draft analysis, design note, or workflow proposal.

Do not force planner/specialist checks onto a draft that never claimed to use that structure.

### 4. Produce a strict verdict
Use this exact logic:
- PASS: requirement satisfied and evidence is visible.
- FAIL: requirement missing, ambiguous, or contradicted.
- AMBER: partially satisfied but evidence is weak.

### 5. Patch guidance
If any item is FAIL or AMBER, provide only:
- failed item,
- reason,
- minimum patch needed,
- whether full rewrite is unnecessary.

### 6. Pipeline role
When used together with `orchestrate-analysis` and `scenario-scorer`:
- accept the coordinator's merged draft as input,
- read the scoring artifact as supporting evidence when scoring exists,
- stay independent from both recommendation and scoring,
- do not recalculate scores unless the draft is internally inconsistent,
- return only the verification artifact needed for the final merge.

When `pipeline-coordinator` is active, return the verification artifact to that skill for final merge.

## Output format
Return a compact table or bullet set with:
- Check
- Status (PASS / FAIL / AMBER)
- Evidence
- Required patch

Then finish with:
- Overall verdict
- Replan needed? (Yes/No)
- Safe to finalize? (Yes/No)

## Safety
- Be skeptical.
- Do not reward style when evidence is missing.
- Do not rewrite the whole draft unless the user asks.

## References
- See `references/default-checklist.md` for the default acceptance rubric.
- See `references/generic-checklist.md` for non-multi-agent draft verification.
