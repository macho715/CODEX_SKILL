---
name: mstack-investigate
description: >
  Failure diagnosis skill for Codex. Use when the main task is to reproduce a
  bug, form hypotheses, gather evidence, and identify the root cause before
  editing production code; triggers include crash, failure, regression, root
  cause, and "왜 안 돼" requests. Prefer `mstack-qa` for verification-only work,
  `mstack-plan` for pre-implementation design, and `mstack-pipeline` only when
  the user wants the full fix-through-release workflow.
---

# Investigate

## Use This Skill When

- the main goal is root-cause analysis before changing production code
- the user asks why something failed, how to reproduce it, or what caused a
  crash or regression
- evidence gathering matters more than immediate implementation

## Prefer Another Skill When

- the main task is verification or test execution: use `mstack-qa`
- the main task is pre-implementation design: use `mstack-plan`
- the user wants a full fix-through-release chain: use `mstack-pipeline`

Use this skill to diagnose a problem before making a fix.

## Core rule

Do not modify production code until the evidence supports a specific fix.
Read production files, run focused repros, and write temporary debug tests when needed. If the user
explicitly asks to fix the issue now, leave freeze mode only after the request is clear.

## Investigation flow

1. Capture the symptom.
   - Record the exact error, failing test, or unexpected behavior.
   - Note reproduction steps and the smallest affected input.
   - Check recent history with `git log --oneline -10` or a narrower range.

2. Form three hypotheses.
   - Write exactly three plausible root-cause hypotheses.
   - Make each hypothesis specific enough to falsify.
   - Avoid vague claims like "the code is wrong".

3. Verify each hypothesis.
   - Reproduce the failure with a focused test or script.
   - Trace the relevant code path.
   - Compare expected vs actual behavior.
   - Record evidence that confirms or rejects each hypothesis.

4. Report the result.
   - Summarize the symptom, hypothesis results, and the most likely root cause.
   - List the fix direction and the regression test that should be added.
   - If no fix was applied, say that explicitly.

## Working rules

- Treat `src/`, `lib/`, and other production directories as read-only during investigation.
- Use `tests/debug/` or another temporary test location for repros when helpful.
- Prefer small, evidence-driven changes over broad rewrites.
- If multiple agents are available, assign one hypothesis per agent and merge the evidence.

## Output shape

Produce a concise investigation report with:

- symptom
- reproduction
- three hypotheses
- evidence for each hypothesis
- root cause
- fix recommendation
- regression test recommendation
