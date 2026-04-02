---
name: mstack-pipeline
description: >
  End-to-end SDLC orchestration skill for Codex. Use when one request should be
  carried from start to finish across multiple mstack stages such as careful,
  dispatch, plan or investigate, implement, review, QA, ship, and retro;
  triggers include "한 번에", "end-to-end", "pipeline", and "자동으로 끝까지".
  When invoked in the middle of ongoing work, first reconstruct the current
  project state, then resume from the furthest incomplete stage instead of
  restarting at plan-only. Prefer `mstack-plan` for design-only work,
  `mstack-review` for review-only work, `mstack-qa` for verification-only work,
  and no mstack skill for simple explanations or meta analysis.
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
  [`core/pipeline.py`](C:/Users/jichu/Downloads/ccat/core/pipeline.py), read
  [`references/core-pipeline-integration.md`](references/core-pipeline-integration.md)
  before changing runtime or automation behavior.

## 1. Classify the work

- `feature` or `refactor`: use the planning path
- `bugfix`: use the investigation path
- `deploy` or `release`: use the release path
- `test` or `validate`: use the QA-only path
- `retro`: use the retrospective-only path

## 2. Reconstruct current state first

- Inspect the current repo or workspace state before choosing the starting
  stage.
- Read existing plans, review notes, QA results, generated artifacts, recent
  test failures, and modified files when they exist.
- Treat explicit `file targets`, `resume point`, and approved scope in `plan.md`
  or equivalent notes as authoritative for the current run unless the user
  changes scope or a new checkpoint explicitly re-approves a reduced scope.
- Identify which stages are already complete enough to skip safely.
- If the user says `implement`, `continue`, `execute`, `fix now`, or otherwise
  asks to proceed, do not fall back to plan-only unless a true blocker is found.

## 3. Apply global guardrails

- Start with `mstack-careful`.
- Use `mstack-dispatch` to choose direct execution, subagents, or a team.
- Stop immediately for destructive actions, secret exposure, protected-branch
  risk, or missing context that blocks safe execution.

## 4. Execute the dispatch result, not just the recommendation

- If `mstack-dispatch` chooses direct execution, continue locally.
- If it chooses subagents or parallel teams and the user asked to proceed,
  actually start the delegated work instead of only summarizing the split.
- If delegation is blocked by tool availability, policy, or coupling, say so
  immediately and downgrade the execution mode explicitly.
- If `dispatch` says `parallel required` or `subagents required` and actual
  delegation does not start, stop with `blocked` unless the user explicitly
  approves a single-agent fallback.
- Do not reinterpret an approved 5+ file plan as a 1 to 2 file direct-execution
  task only because the currently reproduced failure lands in fewer files.

## 5. Run the stage chain

| Work type | Stage order |
|---|---|
| `feature` | careful -> dispatch -> plan -> implement -> review -> qa -> ship -> retro |
| `refactor` | careful -> dispatch -> plan -> implement -> review -> qa -> ship -> retro |
| `bugfix` | careful -> dispatch -> investigate -> implement -> qa -> ship -> retro |
| `deploy` | careful -> dispatch -> ship -> qa -> retro |
| `test` | careful -> dispatch -> qa |
| `retro` | retro |

Resume from the furthest incomplete stage:

- If plan already exists and is still valid, continue at `implement`.
- If implementation exists and only findings remain, continue at `review` or
  `qa` based on the latest evidence.
- If review and QA are already complete, continue at `ship`.
- Only restart from `plan` or `investigate` when the current state is missing,
  stale, or contradicted by new evidence.

## 6. Retry and stop rules

- If `qa` fails, run `review -> fix -> qa` with a maximum of 3 retries.
- Do not continue to `ship` while `qa` is failing.
- Stop on unresolved security, secret, or protected-branch blockers.
- If the user explicitly asks for a checkpoint, stop after the current stage and
  report status instead of auto-continuing.
- If the user did not ask for a checkpoint, continue automatically until the
  last safe applicable stage.
- Do not report `DONE` when `parallel required` or `subagents required` was not
  actually executed.
- In that case report `blocked` or `partial` with the delegation gap called out
  before any success summary.

## 7. Output

Return a concise orchestration summary with:

- work type
- execution mode
- required execution mode
- resumed from stage
- stage order
- current-state evidence used
- planned scope evidence used
- delegation status
- files changed
- blockers or stop conditions
- retries used
- final status
- next action

## 8. Defaults

- Do not pause after `plan` unless the user asked for approval gates.
- Keep intermediate stage notes short.
- Record assumptions explicitly whenever execution continues with inferred context.
- When runtime integration is available, prefer the engine summary fields from
  `PipelineResult`, including `files_changed`.
- In CLI flows, use `mstack pipeline --generic-implement notes` when the user
  wants a safe fallback for requests that do not match a deterministic
  implementation recipe.
