---
name: scenario-scorer
description: Rank 3 or more options with explicit criteria and deterministic weights. Use when strategies, scenarios, or implementation options must be scored reproducibly instead of chosen by narrative preference. When paired with `orchestrate-analysis` or `pipeline-coordinator`, run as an independent scoring agent in the pipeline rather than as an inline narrative step.
---

# Scenario Scorer

## When to use
Use this skill when:
- there are 3 or more options,
- the user wants a recommendation with explicit weights,
- the final choice should be reproducible by calculation,
- the user wants the scoring owned by a separate parallel agent.

Do not use this skill when:
- there is only one option,
- weights or criteria are unavailable and cannot be reasonably proposed,
- the user only wants qualitative brainstorming.

## Inputs
- Options list
- Criteria list
- Weight per criterion, or permission to propose defaults
- Score scale (default: 1-5)
- Optional rationale per score

## Deterministic workflow
1. Confirm options and criteria.
2. Confirm weights sum to 100.
3. If weights were not supplied, propose the default weighting from `references/weighting-guide.md` and mark it as an assumption.
4. Score each option on each criterion.
5. Keep score direction consistent: a higher score must always be better. Convert raw risk into desirability if needed.
6. Run `scripts/score_options.py` when possible.
7. Present total score, ranking, and key trade-offs.

## Total-score rule
- Keep the final total transparent and reproducible.
- Prefer a normalized `0-100` total when weights sum to 100.
- If you do not use `scripts/score_options.py`, show the exact formula used for totals.
- Do not emit weighted totals that cannot be recomputed from the displayed scores and weights.

## Pipeline role
When used together with `orchestrate-analysis` and `analysis-verifier`:
- accept the coordinator's scoring handoff as input,
- keep scoring independent from the verifier's judgment,
- do not rewrite the coordinator's merged draft,
- return only the scoring artifact needed for the final merge.

When `pipeline-coordinator` is active, return the scoring artifact to that skill for final merge.

## Default criteria
If the user did not provide criteria, propose:
- Impact: 35
- Feasibility: 25
- Risk: 20
- Time-to-value: 20

## Output format
Return:
- scoring table,
- ranked options,
- recommended option,
- criteria and weights used,
- sensitivity note if one criterion dominates the outcome.

## Safety
- Keep scoring rules visible.
- Do not hide assumptions.
- If weights are arbitrary, say so.

## References
- Example inputs and outputs live in `examples/`.
- Weighting tips live in `references/weighting-guide.md`.
