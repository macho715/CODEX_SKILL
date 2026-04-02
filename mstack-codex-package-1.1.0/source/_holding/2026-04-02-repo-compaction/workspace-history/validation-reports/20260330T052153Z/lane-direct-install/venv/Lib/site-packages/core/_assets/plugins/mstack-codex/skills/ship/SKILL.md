---
name: mstack-ship
description: >
  Release gate skill for Codex. Use when review and QA evidence already exist
  and the main task is to validate tests, coverage, commit hygiene, branch
  strategy, and safe push behavior before merge or deployment; triggers include
  ship, release, push, merge, deploy, and handoff-before-merge requests.
  Prefer `mstack-plan` for design-only work, `mstack-qa` for verification-only
  work, and `mstack-pipeline` for one-shot end-to-end workflows.
---

# Release Prep

## Use This Skill When

- review and QA evidence already exist and the question is whether the change is
  ready to merge or deploy
- the user asks to commit, push, merge, ship, release, or hand off a change
- branch strategy, commit hygiene, and quality gates must be checked together

## Prefer Another Skill When

- the request is design-only or pre-coding: use `mstack-plan`
- the request is verification-only without a release decision: use `mstack-qa`
- the user wants one-shot start-to-finish execution: use `mstack-pipeline`

## Core rules

- Never force push.
- Prefer revert commits over history rewriting.
- Treat release prep as a quality gate, not a formality.

## Checklist

### 1. Confirm tests exist

- If the project has no tests, establish a minimal test harness first.
- If tests already exist, extend the relevant suite instead of inventing a new path.

### 2. Check coverage

- Verify that new functions and changed paths have tests.
- Compare coverage against the repository standard.
- If no standard exists, treat a meaningful drop as a release blocker.

### 3. Run quality checks

- Run the repository's documented test, lint, and type-check commands.
- If those commands are missing, infer the stack-specific checks from the repo
  and state the assumption.
- Stop on the first failure that indicates a correctness or hygiene issue.

### 4. Validate commit hygiene

- Prefer a Conventional Commits style message when creating a commit.
- Flag unclear, vague, or missing commit messages before pushing.
- Do not rewrite history just to polish a message unless the user explicitly asks.

### 5. Check branch strategy

- Treat `main` and `master` as protected by default.
- Prefer feature or hotfix branches for release work.
- Warn before direct commits to a protected branch.

### 6. Summarize the release

- Report branch, files changed, tests run, and whether coverage is acceptable.
- Separate passed checks from skipped or unavailable checks.
- Do not call the release ready until the blockers are cleared.

## Execution

- If the release is approved, commit only after checks pass.
- Push without force.
- Open or update the pull request if the repository uses one.
- Capture the final validation result in the handoff.
