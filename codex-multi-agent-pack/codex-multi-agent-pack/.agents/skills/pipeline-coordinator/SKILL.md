---
name: pipeline-coordinator
description: Coordinate a fixed 4-agent topology with one coordinator plus independent `orchestrate-analysis`, `scenario-scorer`, and `analysis-verifier` agents. Use when the user wants a standard parallel pipeline with explicit ownership, artifact handoffs, final merge, and topology disclosure instead of letting one skill coordinate everything.
---

# Pipeline Coordinator

## When to use
Use this skill when:
- the user wants a fixed 4-agent topology,
- one agent should coordinate while three other agents execute,
- `orchestrate-analysis`, `scenario-scorer`, and `analysis-verifier` should stay independent,
- the final answer must disclose the topology used and merge artifacts from separate agents.

Do not use this skill when:
- the task is simple enough for one skill,
- subagents are unavailable and the user did not ask for strict topology,
- there are fewer than three execution lanes.

## Inputs
- Goal or decision to make
- Constraints and non-negotiables
- Required options or specialist lanes
- Required final output format
- Any policy on fallback behavior
- Or, in merge-only mode, completed artifacts from `orchestrate-analysis`, `scenario-scorer`, and `analysis-verifier`
- Optionally, a caller packet from `mstack-dispatch`, `mstack-plan`,
  `mstack-pipeline`, or `mstack-investigate`

## Fixed topology
Use exactly these roles:
- `pipeline-coordinator`: final merge only
- `orchestrate-analysis`: merged analysis artifacts
- `scenario-scorer`: scoring artifact
- `analysis-verifier`: verification artifact

Do not let the coordinator rewrite the execution agents' roles.

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

## Procedure

### 1. Topology setup
Before any substantive analysis:
- spawn one coordinator agent,
- spawn one `orchestrate-analysis` agent,
- spawn one `scenario-scorer` agent,
- spawn one `analysis-verifier` agent,
- define ownership and required artifacts.

Do not send substantive scoring or verification work yet.
The scoring agent and verifier agent may be spawned early, but their real task input must wait until the analysis artifact exists.

### 2. Analysis artifact
Ask `orchestrate-analysis` to return only:
- `MERGED_DRAFT`
- `SCORING_HANDOFF`

Do not let `orchestrate-analysis` produce the final merged answer when this skill is active.

### 3. Parallel execution
After the analysis artifact is ready:
- send `SCORING_HANDOFF` to `scenario-scorer`,
- send `MERGED_DRAFT` to `analysis-verifier`,
- include the scoring criteria or scoring artifact in the verifier input when reproducibility depends on a separate scoring step,
- run scoring and verification in parallel.

### 4. Final merge
The coordinator merges only completed artifacts from the three execution agents.
This skill may run in merge-only mode when the caller already started the execution agents and only needs artifact merge.

The coordinator must:
- name the topology used,
- summarize the recommendation,
- summarize the scoring result,
- summarize the verifier verdict,
- list remaining gaps or required patches.

The coordinator must not invent missing artifacts or pretend a failed agent completed.
The coordinator must not self-assess tool availability, subagent availability, or session limits after the topology has already been started by the caller.
Treat execution agents as already started unless the caller explicitly reports a startup failure artifact.
Do not reject merge-only mode just because a fresh business topic was not restated.

### 5. Fallback handling
If the fixed topology cannot be started:
- say which role could not start,
- stop or explicitly downgrade only if the user allows it,
- do not falsely claim a 4-agent run.

Only the caller or an explicit startup-failure artifact may declare topology startup failure.

## Output contract
Return these sections in order:
1. Agent Topology
2. Recommendation
3. Scoring Summary
4. Verifier Verdict
5. Remaining Gaps

## Safety
- Keep coordinator and execution roles separate.
- Do not collapse independent scoring or verification back into the coordinator.
- Do not disclose execution-mode details inside intermediate artifacts; only the final merged answer may disclose topology or fallback status.

## References
- See `references/four-agent-contract.md` for the fixed topology contract.
- See `references/external-docs.md` for the external OpenAI and GitHub documentation used to shape this workflow.
