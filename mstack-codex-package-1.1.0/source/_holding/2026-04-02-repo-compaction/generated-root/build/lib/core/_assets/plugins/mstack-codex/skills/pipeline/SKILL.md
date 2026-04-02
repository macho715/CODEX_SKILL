---
name: mstack-pipeline
description: >
  End-to-end SDLC orchestration skill for Codex. Use when one request should be
  carried from start to finish across multiple mstack stages such as careful,
  dispatch, plan or investigate, implement, review, QA, ship, and retro;
  triggers include "한 번에", "end-to-end", "pipeline", and "자동으로 끝까지".
  Prefer `mstack-plan` for design-only work, `mstack-review` for review-only
  work, `mstack-qa` for verification-only work, and no mstack skill for simple
  explanations or meta analysis.
---

# Pipeline Orchestrator

Use this skill when the user wants one-shot workflow execution rather than a
single stage.

## Use This Skill When

- the user wants one request carried across multiple stages from start to finish
- the work spans planning or investigation, implementation, review, QA, ship,
  and retro
- the user asks for end-to-end automation rather than a single stage

## Prefer Another Skill When

- the request is design-only or approval-only: use `mstack-plan`
- the request is review-only or diff-only: use `mstack-review`
- the request is verification-only: use `mstack-qa`
- the request is a simple explanation, status summary, or meta evaluation: do
  not force `mstack-pipeline`

## References

- For concrete user prompts and expected summaries, read
  [`references/usage-examples.md`](references/usage-examples.md).
- For the design that connects this skill to
  `core/pipeline.py`, read
  [`references/core-pipeline-integration.md`](references/core-pipeline-integration.md)
  before changing runtime or automation behavior.
- For Windows Node toolchain behavior in CLI-backed runs, use the same
  reference note before diagnosing `npm`, `npx`, or TypeScript runtime failures.

## 1. Classify the work

- `feature` or `refactor`: use the planning path
- `bugfix`: use the investigation path
- `deploy` or `release`: use the release path
- `test` or `validate`: use the QA-only path
- `retro`: use the retrospective-only path

## 2. Apply global guardrails

- Start with `mstack-careful`.
- Use `mstack-dispatch` to choose direct execution, subagents, or a team.
- Stop immediately for destructive actions, secret exposure, protected-branch
  risk, or missing context that blocks safe execution.

## 3. Run the stage chain

| Work type | Stage order |
|---|---|
| `feature` | careful -> dispatch -> plan -> implement -> review -> qa -> ship -> retro |
| `refactor` | careful -> dispatch -> plan -> implement -> review -> qa -> ship -> retro |
| `bugfix` | careful -> dispatch -> investigate -> implement -> qa -> ship -> retro |
| `deploy` | careful -> dispatch -> ship -> qa -> retro |
| `test` | careful -> dispatch -> qa |
| `retro` | retro |

## Optional Coordinator Gate

- Before `implement`, check whether a coordinator-backed decision gate is
  required.
- If `dispatch` selected `pipeline-coordinator`, insert this subflow after
  `plan` or `investigate` and before `implement`:
  `pipeline-coordinator -> orchestrate-analysis -> scenario-scorer + analysis-verifier -> coordinator final merge`
- Carry forward only the `recommendation`, `scoring summary`,
  `verifier verdict`, and `remaining gaps`.
- If the verifier verdict is `FAIL`, stop before `implement`.
- If the verifier verdict is `AMBER`, continue only with explicit assumptions
  and a named mitigation list.

## 4. Retry and stop rules

- If `qa` fails, run `review -> fix -> qa` with a maximum of 3 retries.
- Do not continue to `ship` while `qa` is failing.
- Stop on unresolved security, secret, or protected-branch blockers.
- If the user explicitly asks for a checkpoint, stop after the current stage and
  report status instead of auto-continuing.

## 5. Output

Return a concise orchestration summary with:

- work type
- execution mode
- stage order
- files changed
- decision engine when nested analysis is required
- verifier verdict and remaining gaps when coordinator artifacts exist
- blockers or stop conditions
- retries used
- final status
- next action

## 6. Defaults

- Do not pause after `plan` unless the user asked for approval gates.
- Keep intermediate stage notes short.
- Record assumptions explicitly whenever execution continues with inferred context.
- When runtime integration is available, prefer the engine summary fields from
  `PipelineResult`, including `files_changed`.
- Keep `pipeline-coordinator` outside the canonical `core/pipeline.py` stage
  order. It is a nested decision engine, not a new pipeline stage.
- In CLI flows, use `mstack pipeline --generic-implement notes` when the user
  wants a safe fallback for requests that do not match a deterministic
  implementation recipe.
- On Windows, remember that MStack only applies a local mitigation for
  Node-family subprocesses. If `npm` or `npx` fails under `cmd.exe`, surface
  the PATH deduplication guidance instead of implying the machine is fully
  repaired.
