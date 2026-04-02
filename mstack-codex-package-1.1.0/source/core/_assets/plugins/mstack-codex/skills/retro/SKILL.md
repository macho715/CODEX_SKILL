---
name: mstack-retro
description: >
  Completed-work retrospective skill for Codex. Use when feature delivery, bug
  fixes, refactors, or release validation are already complete and the main
  task is to summarize outcomes, lessons, metrics, and follow-up actions;
  triggers include retro, retrospective, postmortem, and lessons-learned
  requests. Prefer
  `mstack-review` for pre-merge code findings and `mstack-pipeline` when the
  work is still in progress.
---

# Retrospective

## Use This Skill When

- the work is complete and needs lessons learned, metrics, and follow-up actions
- the user asks for a retrospective, postmortem, or completed-work summary
- evidence from git history, QA results, or cost logs should drive the wrap-up

## Prefer Another Skill When

- the main task is code review before merge: use `mstack-review`
- the work is still in progress and not ready for wrap-up: use `mstack-pipeline`
- the request is only for test execution: use `mstack-qa`

Use this skill after a task is complete or when the user asks for a review of completed work.

## Core rule

Base the retrospective on evidence, not memory.
If cost logs, git history, test output, or project notes exist, use them. If a metric is unavailable,
mark it as `N/A` instead of estimating.

## Collection steps

1. Gather context.
   - Review the completed changes and the relevant commit range.
   - Read any plan, review, QA, or investigation notes that exist in the workspace.
   - Identify the concrete scope of work before writing conclusions.

2. Collect metrics.
   - Use `git log` for commit count and time span.
   - Use `git diff --stat` for file-change volume.
   - Use `python cost.py report` when a cost log is available.
   - If a metric cannot be measured, record `N/A`.

3. Write the retrospective.
   - Summarize what went well.
   - Call out what should change next time.
   - Capture one or more actionable follow-ups.
   - Include cost efficiency only when actual data exists.

## Coordinator outcome review

- Record whether the final implementation followed the coordinator
  recommendation.
- If the team chose a lower-ranked option, state why and whether the deviation
  paid off.

## Report shape

Write a concise retrospective with these sections:

- task summary
- keep
- improve
- learn
- metrics
- action items

## Writing rules

- Use concrete facts, not generalized praise.
- Keep recommendations actionable and assignable.
- Separate observed data from interpretation.
- If the work was incomplete, say so and explain what blocked completion.

## Coordinator-driven retro

- Reuse scorer criteria and verifier failures as retrospective evidence.
- If the team chose a lower-ranked option, state why and whether the deviation
  paid off.
