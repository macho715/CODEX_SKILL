# Pipeline-Coordinator Integration

Use this note to connect `mstack-*` skills to `pipeline-coordinator` without
turning the coordinator into the top-level SDLC owner.

## Purpose

- Keep `mstack-dispatch` as the single routing decision point.
- Use `pipeline-coordinator` as a pre-implementation analysis gate.
- Preserve `review`, `qa`, `ship`, and `retro` as MStack-owned stages.

## When to call the coordinator

Route to `pipeline-coordinator` only when at least one of these is true:

- the task still has `3+` viable implementation or architecture options
- the user explicitly asks for trade-off scoring
- the decision is hard to reverse after coding starts
- the user explicitly asks for a fixed multi-agent topology

Do not call the coordinator for:

- simple direct implementation
- review-only work
- QA-only work
- release-only work

## Stage ownership

- `mstack-dispatch` decides whether the coordinator is needed.
- `mstack-plan` or `mstack-investigate` prepares the caller packet.
- `pipeline-coordinator` runs the fixed 4-agent topology and returns a
  `Decision Packet`.
- `mstack-pipeline` decides whether to stop, continue with assumptions, or move
  into `implement`.
- `mstack-review`, `mstack-qa`, `mstack-ship`, and `mstack-retro` consume the
  decision artifacts as downstream evidence.

## Caller packet

The coordinator-ready caller packet must contain:

- `objective`
- `non-negotiables`
- `candidate options`
- `acceptance criteria`
- `required evidence`
- `stop conditions`

## Decision Packet

The coordinator must return:

1. `Agent Topology`
2. `Recommendation`
3. `Scoring Summary`
4. `Verifier Verdict`
5. `Remaining Gaps`

Only these fields move downstream into MStack stages.

## Hand-off rules

- Stop before `implement` if the verifier verdict is `FAIL`.
- Continue on `AMBER` only with explicit assumptions and a named mitigation list.
- Turn `Remaining Gaps` into mandatory review and QA checks.
- Treat unresolved verifier `FAIL` as a release blocker.

## Hard boundaries

- Do not silently downgrade an approved fixed topology to single-agent work.
- Do not let the coordinator absorb `review`, `qa`, `ship`, or `retro`.
- Do not start implementation without a final merge result from the coordinator
  when the coordinator gate was selected.
