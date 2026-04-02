---
name: mstack-pipeline-coordinator
description: >
  Fixed four-lane decision-engine skill for Codex. Use when a request needs a
  standard coordinator-led comparison across embedded analysis, scoring, and
  verification lanes instead of a single narrative answer; triggers include 3+
  options, high-risk architecture choices, rollout trade-offs, and explicit
  requests for a decision engine inside `mstack-pipeline`.
---

# Pipeline Coordinator

## Use This Skill When

- the user needs a fixed four-lane decision engine for a complex choice
- there are 3 or more credible options to compare
- architecture, rollout, release, or operating trade-offs are material
- `mstack-dispatch` or `mstack-pipeline` escalates to a nested decision analysis

## Prefer Another Skill When

- the request is a simple design note or one-path implementation plan: use
  `mstack-plan`
- the request is full start-to-finish execution without a major decision point:
  use `mstack-pipeline`
- the request is review-only or QA-only after implementation already exists: use
  `mstack-review` or `mstack-qa`

## Fixed Topology

Use exactly these roles:

- coordinator: `pipeline-coordinator`
- embedded analysis lane: `orchestrate-analysis`
- embedded scoring lane: `scenario-scorer`
- embedded verification lane: `analysis-verifier`

Only the coordinator owns the final merged recommendation.

## Required Input Contract

Expect this handoff shape before substantive comparison:

- objective
- non-negotiables
- acceptance criteria
- option set
- required evidence
- test expectations

If any required field is missing, stop and request the minimum patch needed.

## When Called From MStack

- When the caller is an `mstack-*` skill, this skill acts as a decision gate,
  not as the top-level SDLC orchestrator.
- Accept a caller packet from `mstack-dispatch`, `mstack-plan`,
  `mstack-pipeline`, or `mstack-investigate`.
- Return a `Decision Packet` with `Agent Topology`, `Recommendation`,
  `Scoring Summary`, `Verifier Verdict`, and `Remaining Gaps`.
- Do not absorb `review`, `qa`, `ship`, or `retro` responsibilities from
  MStack.
- Do not reinterpret already-approved topology availability after startup.

## Execution Rules

1. Build one `MERGED_DRAFT` and one `SCORING_HANDOFF`.
2. Keep scoring and verification independent from the coordinator merge.
3. Do not add a new stage to `core/pipeline.py`.
4. Treat this skill as a nested decision engine invoked between dispatch/plan
   and implementation.
5. Reuse the final verdict in review, QA, ship, and retro rather than
   recomputing the same decision later.

## Output

Return these sections in order:

1. Agent Topology
2. Recommendation
3. Scoring Summary
4. Verifier Verdict
5. Remaining Gaps

## References

- [`references/coordinator-input-contract.md`](references/coordinator-input-contract.md)
- [`references/embedded-orchestrate-analysis.md`](references/embedded-orchestrate-analysis.md)
- [`references/embedded-scenario-scorer.md`](references/embedded-scenario-scorer.md)
- [`references/embedded-analysis-verifier.md`](references/embedded-analysis-verifier.md)
- [`references/four-agent-contract.md`](references/four-agent-contract.md)
