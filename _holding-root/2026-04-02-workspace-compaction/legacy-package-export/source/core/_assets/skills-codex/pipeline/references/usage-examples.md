# MStack Pipeline Usage Examples

Use these examples when a user wants one-shot execution across multiple mstack
stages.

## Example 1: Feature Request

Prompt:
`Use $mstack-pipeline to handle adding CSV import to a todo app end-to-end.`

Expected routing:
- `careful`
- `dispatch`
- `plan`
- `implement`
- `review`
- `qa`
- `ship`
- `retro`

Expected summary shape:
- `work type: feature`
- `execution mode: direct | subagents | parallel team`
- `stage order: careful -> dispatch -> plan -> implement -> review -> qa -> ship -> retro`
- `files changed: ...`
- `blockers: ...`
- `retries used: N`
- `final status: ...`
- `next action: ...`

Expected execution rule:
- if `dispatch` chooses `subagents` or `parallel team`, the orchestration should
  actually start delegated work instead of stopping at a routing summary
- if planned scope is `5+ files` or `cross-module`, treat parallel execution as
  required unless the user explicitly accepts a direct-execution fallback
- do not shrink approved scope to a smaller direct-execution task only because
  the first reproduced failure lands in fewer files

## Example 2: Bugfix

Prompt:
`Use $mstack-pipeline to fix a crash in CSV import and carry it through QA and release.`

Expected routing:
- `careful`
- `dispatch`
- `investigate`
- `implement`
- `qa`
- `ship`
- `retro`

Expected summary emphasis:
- root cause confirmed before code changes
- files changed called out when the implementation stage mutated code
- QA retries if needed
- release blockers called out clearly

## Example 3: Mid-Project Continue

Prompt:
`Use $mstack-pipeline to continue from the current state and finish this feature.`

Expected behavior:
- reconstruct state from existing plans, review notes, generated files, tests,
  and modified files
- resume from the furthest incomplete stage
- do not regress to plan-only if the request is clearly asking to continue
- continue automatically until the last safe applicable stage unless the user
  asked for a checkpoint
- if `dispatch` says parallel execution is required and delegation does not
  actually start, stop as blocked instead of reporting success
- keep approved file targets authoritative for that run unless the user or a
  new checkpoint explicitly narrows the scope

## Example 4: Deploy Check

Prompt:
`Use $mstack-pipeline to take this release candidate through ship and qa.`

Expected routing:
- `careful`
- `dispatch`
- `ship`
- `qa`
- `retro`

Expected summary emphasis:
- branch strategy
- quality checks run
- blockers before push or merge

## Example 5: Validation Only

Prompt:
`Use $mstack-pipeline to validate this parser change end-to-end but stop before release.`

Expected behavior:
- classify as `test` or feature-with-checkpoint depending on the request
- run `careful -> dispatch -> qa`
- stop after validation if the prompt explicitly asks for a checkpoint

## Example 6: Cross-Module Parallel Work

Prompt:
`Use $mstack-pipeline to update the CLI, config loader, and tests in parallel and finish the project.`

Expected behavior:
- `dispatch` should classify this as `subagents` or `parallel team`
- delegated workers should actually be started when the environment allows it
- if delegation is blocked, the summary must say the run is blocked or partial
  and why the required mode was not executed

## Current Runtime-Backed Recipes

- Python feature: CSV import scaffold
- Python bugfix: parser empty-input/crash fix scaffold
- Python refactor: helper extraction scaffold
- TypeScript feature: CSV import scaffold

If a request does not match a deterministic recipe, the runtime may skip
`implement` or use a separately injected generic implement backend.

## When Not To Use Pipeline

- Use `mstack-plan` when the user only wants design, scope, or approval
  decisions before coding.
- Use `mstack-review` when code or a diff already exists and the user only wants
  findings.
- Use `mstack-qa` when the user only wants verification, smoke checks, or test
  results.
- Do not use `mstack-pipeline` for simple explanations, status summaries, or
  meta evaluation of how skills were used.

## CLI Fallback

- Use `mstack pipeline --generic-implement notes` when the user wants a
  safe, fail-closed fallback instead of silently skipping `implement`.
- The `notes` backend writes `IMPLEMENTATION_NOTES.md`, marks `implement`
  as failed, and stops the pipeline before `review`, `qa`, or `ship`.

## When Not To Use

- Use `mstack-dispatch` instead when the user only wants routing or ownership.
- Use `mstack-plan` instead when the user only wants a plan.
- Use `mstack-review` instead when the user only wants review findings.
