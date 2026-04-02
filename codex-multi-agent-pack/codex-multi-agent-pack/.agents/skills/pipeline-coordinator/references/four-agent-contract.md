# Four-Agent Contract

Use this contract when `pipeline-coordinator`, `orchestrate-analysis`, `scenario-scorer`, and `analysis-verifier` are active together.

## Required roles
- Coordinator: `pipeline-coordinator`
- Analysis: `orchestrate-analysis`
- Scoring: `scenario-scorer`
- Verification: `analysis-verifier`

## Ownership
- Coordinator owns topology disclosure and final merge only.
- Analysis owns `MERGED_DRAFT` and `SCORING_HANDOFF`.
- Scoring owns the scoring artifact.
- Verification owns the verification artifact.
- When the caller is an `mstack-*` skill, MStack keeps SDLC ownership and the
  coordinator acts only as an analysis decision gate.

The coordinator may be invoked after execution has already started, as long as the three required artifacts will be provided.

## Required flow
1. Coordinator starts the topology.
2. Analysis returns `MERGED_DRAFT` and `SCORING_HANDOFF`.
3. Scoring and verification run in parallel on those artifacts.
4. Coordinator merges the three execution outputs into the final answer.

Scoring and verification must not start substantive evaluation before step 2.

## Hard rules
- Do not let the coordinator fabricate missing execution output.
- Do not let analysis, scoring, or verification claim they performed the final merge.
- Do not mention topology or fallback status inside `MERGED_DRAFT` or `SCORING_HANDOFF`.
- Disclose topology only in the coordinator's final answer.
- Do not let the coordinator overrule a topology that the caller has already started.
- Do not let the coordinator absorb `review`, `qa`, `ship`, or `retro` from an
  `mstack-*` caller.
- Return a `Decision Packet` when the caller packet comes from
  `mstack-dispatch`, `mstack-plan`, `mstack-pipeline`, or `mstack-investigate`.
