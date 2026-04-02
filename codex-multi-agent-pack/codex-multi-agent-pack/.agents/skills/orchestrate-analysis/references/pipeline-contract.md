# Pipeline Contract

Use this contract when `orchestrate-analysis`, `scenario-scorer`, and `analysis-verifier` are invoked together.

## Required agents
- Coordinator agent: runs `orchestrate-analysis`
- Scoring agent: runs `scenario-scorer`
- Verifier agent: runs `analysis-verifier`

Each role must be assigned to an independent agent. Do not treat section headers as proof of independence.

## Ownership
- Coordinator owns the planner output, specialist synthesis, merged draft, and final merge.
- Scoring agent owns criteria confirmation, score calculation, ranking, and sensitivity note.
- Verifier agent owns PASS / FAIL / AMBER judgments and required patches.

## Handoffs
1. Coordinator creates the merged draft.
2. Coordinator creates the scoring handoff when there are 3 or more comparable options.
3. Coordinator sends the scoring handoff to the scoring agent.
4. Coordinator sends the merged draft to the verifier agent.
5. Scoring and verification run in parallel.
6. Coordinator merges both outputs into the final answer.

## Intermediate artifact rule
- `MERGED_DRAFT` and `SCORING_HANDOFF` are content artifacts only.
- Do not include execution-mode disclosure in intermediate artifacts.
- Do not mention `single-agent`, `fallback`, `subagent unavailable`, or equivalent wording in coordinator handoff artifacts.
- Reserve all execution-mode disclosure for the final merged answer.

## Required final disclosure
- State that independent agents were used.
- Name which role each agent owned.
- Report whether scoring and verification ran in parallel.
- If fallback occurred, disclose it only here, not in intermediate artifacts.

## Fallback rule
If no required subagent can be started, say that the pipeline requirement could not be met and do not falsely claim parallel execution.
If the coordinator, scoring agent, or verifier agent has already started successfully, do not describe the run as a fallback.
