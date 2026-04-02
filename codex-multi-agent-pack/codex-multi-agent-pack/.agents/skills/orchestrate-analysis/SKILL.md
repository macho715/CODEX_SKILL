---
name: orchestrate-analysis
description: Break a complex task into a planner plus 2-4 specialist workstreams and produce the analysis artifacts for a multi-agent pipeline. Use when the user asks for multi-perspective analysis, system design, strategy options, or decision support that must be structured, checkable, reproducible, and processed by real independent agents in parallel. When this skill is paired with `pipeline-coordinator`, it owns merged analysis artifacts, not the final merge.
---

# Orchestrate Analysis

## When to use
Use this skill when:
- the user wants a planner + specialist + verifier workflow,
- multiple viewpoints must be covered before a recommendation,
- a draft answer needs stronger structure and traceability,
- the user explicitly wants real parallel subagents instead of one agent simulating multiple roles,
- the user invokes this skill together with `scenario-scorer` and `analysis-verifier`,
- the user invokes this skill together with `pipeline-coordinator`.

Do not use this skill when:
- the task is a one-shot factual lookup,
- there is only one narrow perspective,
- the user only wants a short chat reply with no structure.

## Inputs
- Goal or decision to make
- Constraints, risks, and non-negotiables
- Required specialist lanes (if the user specified them)
- Available evidence, data, links, or files
- Output format required by the user
- Candidate options if the task ends in a recommendation

## Specialist lane defaults
If the user did not define lanes, start with:
- Cost / ROI
- Risk / Compliance
- Operations / Logistics / Execution

You may swap these for other lanes if the task clearly calls for different expertise.

## Procedure

### 0. Execution mode
When the user asks for actual multi-agent processing, do not simulate the workflow in one agent.

- Spawn independent agents with explicit ownership.
- Keep `orchestrate-analysis` responsible for planning, lane synthesis, and merged analysis artifacts.
- Use `scenario-scorer` as a separate agent for scoring.
- Use `analysis-verifier` as a separate agent for independent verification.
- Only use fallback wording if no required subagent could be started.
- Decide fallback status before emitting the coordinator draft.
- If any required downstream agent was started successfully, do not describe the run as a single-agent fallback.
- If the task does not justify subagents or subagents are unavailable, say so explicitly before falling back to a single-agent workflow.

### 1. Planner phase
Create a compact execution plan with:
- objective,
- success criteria,
- lane definitions,
- what can run in parallel,
- what the verifier must check.

If real subagents are being used, define:
- which agent owns the merged draft,
- which agent owns scoring,
- which agent owns verification,
- which agent owns the final merge,
- which artifact is handed from one stage to the next.

### 2. Specialist phase
Ask each lane to produce only:
- its scope,
- key findings,
- assumptions,
- evidence gaps,
- 1-3 concrete recommendations.

Keep the lanes independent. Do not let one lane rewrite another lane.

### 3. Merge phase
Build one merged draft that contains:
- common facts,
- lane-specific findings,
- contradictions,
- open questions,
- candidate options.

When the user provides explicit budget, timeline, or user scale constraints, also include compact feasibility anchors in `MERGED_DRAFT`:
- a simple budget shape or cost buckets,
- a phased rollout outline,
- sizing or operational assumptions tied to user count.

Prefer minimally quantified anchors over generic prose:
- budget: at least `one-time setup`, `monthly run cost`, and `reserve` ranges,
- rollout: phase order plus at least one critical dependency or slip risk,
- operations: at least one concurrency or throughput assumption and one support ownership assumption.

When user count, ticket volume, editor count, or approval volume can be inferred, include at least one numeric operating assumption instead of only words like `modest` or `small`.

Treat `MERGED_DRAFT` as a content artifact only.
- Do not describe execution mode inside `MERGED_DRAFT`.
- Do not mention whether the run is parallel, single-agent, fallback, or blocked on subagents.
- Do not use phrases such as `single-agent`, `fallback`, `subagent unavailable`, or equivalent wording inside the coordinator draft.

If the draft contains 3 or more comparable options, also prepare a scoring handoff with:
- option names,
- criteria,
- weights,
- score scale,
- any assumptions needed for scoring.

Treat `SCORING_HANDOFF` as a scoring artifact only.
- Do not include execution-mode narration.
- Do not mention agent availability, fallback status, or pipeline status inside the handoff.

### 4. Pipeline handoff
When `pipeline-coordinator` is not active and all three skills are active, use this pipeline:
1. `orchestrate-analysis` agent creates the merged draft and the scoring handoff.
2. Send the scoring handoff to a separate `scenario-scorer` agent.
3. Send the merged draft to a separate `analysis-verifier` agent.
4. Run steps 2 and 3 in parallel whenever both inputs are ready.
5. Merge the scorer and verifier outputs into the final answer.

Do not collapse scoring or verification back into the coordinator unless subagents are unavailable.
Only the final merged answer may disclose whether the workflow used actual parallel agents or a fallback mode.

When `pipeline-coordinator` is active:
1. `orchestrate-analysis` produces only `MERGED_DRAFT` and `SCORING_HANDOFF`.
2. `pipeline-coordinator` owns final topology disclosure and final merge.
3. Do not emit the final merged answer from this skill.

### 5. Verifier requirement
The verifier must test all required acceptance criteria before the final answer is emitted.

### 6. Replan gate
If the verifier returns FAIL:
- replan once,
- patch only failed sections,
- do not restart the whole workflow unless the user explicitly asks.

Maximum replan count: 1.

### 7. Final output contract
Return a structured final answer with these sections in order:
1. Executive summary
2. Planner summary
3. Specialist findings
4. Verifier verdict
5. Final recommendation
6. Assumptions and evidence gaps

## Output rules
- Mark unsupported statements as assumptions.
- Keep the final answer reproducible: show criteria, not only conclusions.
- When 3 or more options are comparable, call `scenario-scorer` as a separate agent or package the exact scoring inputs for it.
- If `analysis-verifier` is active, keep verification independent from the coordinator's recommendations.
- `MERGED_DRAFT` and `SCORING_HANDOFF` must not mention execution mode.
- State whether the workflow used actual parallel agents or a single-agent fallback only in the final merged answer.
- If the scoring agent or verifier agent ran, the final merged answer must say independent agents were used and must not claim fallback.
- If `pipeline-coordinator` is active, return only the analysis artifacts it needs and let that skill handle the final merge.

## Safety
- No destructive actions without dry-run, change list, and approval.
- No fabricated evidence.
- If critical inputs are missing, stop and request the minimum missing inputs.

## References
- See `references/output-contract.md` for the default section layout and pass criteria.
- See `references/pipeline-contract.md` for the required three-skill pipeline handoff.
- See `../pipeline-coordinator/references/four-agent-contract.md` when the 4-agent topology is active.
