# Parallel Agent Workflow

Use this file only when the user explicitly asks for delegated agents, subagents, or parallel execution, and the active Codex surface supports that workflow.

## Permission rule

- Do not assume delegation is allowed by default.
- Use parallel lanes only when the user explicitly requests parallel or delegated work.
- If delegation is not allowed, keep the same workflow locally.

## Recommended lanes

- `Manager lane`: hold the workbook contract, sidecar boundary, and final decision.
- `Baseline lane`: capture the pre-format contract and classify sheets.
- `Formatting lane`: propose or apply the visual pass on the sidecar workbook only.
- `QA lane`: run gate checks, contract diff review, promotion, and rollback readiness.

## Ownership rule

- Keep write scopes disjoint whenever code or workbook edits are involved.
- Do not let two lanes edit the same workbook copy at the same time.
- Keep promotion decisions with the manager lane.

## Integration rule

- Merge lane results locally.
- Re-run the validation checklist after integration.
- Summarize only the lanes that materially affected the result.
