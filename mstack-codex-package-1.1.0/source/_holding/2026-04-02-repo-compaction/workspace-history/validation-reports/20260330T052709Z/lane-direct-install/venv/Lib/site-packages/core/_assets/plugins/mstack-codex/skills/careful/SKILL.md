---
name: mstack-careful
description: >
  Cross-cutting safety guardrail skill for Codex. Use when work could be
  destructive, expose secrets, touch shared modules, rewrite history,
  investigate failures under freeze, or change protected branches; triggers
  include "조심해서", safety, protection, secrets, rollback risk, and
  main-branch work. Prefer the task-specific mstack skill for planning, review,
  QA, shipping, or investigation after the safety posture is set.
---

# Safety Rules

Use this skill as a cross-cutting safety layer before any risky stage.

## Use This Skill When

- the request could destroy data, expose secrets, rewrite shared history, or
  make rollback expensive
- the work touches shared modules, protected branches, production paths, or
  freeze-mode investigation flows
- the user asks for careful handling such as `조심해서`, safety, protection, or
  mistake prevention

## Prefer Another Skill When

- the main task is planning: use `mstack-plan`
- the main task is routing or ownership: use `mstack-dispatch`
- the main task is review, QA, shipping, or investigation: use that stage skill
  with `mstack-careful` as the safety layer

## Default posture

Pause when a request could destroy data, expose secrets, rewrite shared code, or
make rollback expensive. Prefer a short confirmation prompt over silent action.

## Hard stops

- Block `git push --force`, `git push --force-with-lease`, and `git push -f`.
- Block `rm -rf /`, destructive database commands, `git reset --hard`, and
  `git clean -fd` unless the user explicitly confirms the risk.
- Block adding secrets, tokens, passwords, or `.env` files to version control.
- Block direct edits to production code while investigating a failure unless the
  user explicitly lifts freeze mode.

## Shared code

- Treat shared modules and utility layers as high risk.
- Call out the impacted paths before editing them.
- Ask for lead approval if the change can affect multiple modules or teams.

## Investigation freeze

- During investigation, read production code first.
- Add or run a reproducible test before proposing a fix.
- Keep edits out of production paths until the root cause is clear or the user
  approves a change.

## Response shape

- State the risk first.
- Name the blocked action.
- Give the safest alternative.
- If the request is safe, proceed normally and keep the guardrail in mind.
