---
name: excel-professional-formatting
description: Apply a safe Excel formatting pass to workbook copies without changing workbook logic. Use when the request is about styling, readability, accessibility, print layout, or report polish and workbook behavior must stay intact. Default to a sidecar-first workflow, escalate to `excel-vba` for any structure-sensitive change, and use explicit parallel lanes only when the user asks for delegated or parallel execution.
---

# Excel Professional Formatting

Own the visual layer only.
Preserve workbook behavior over appearance.
Run formatting passes on a sidecar workbook copy before any promotion back to the original workbook.

## Trigger

- workbook styling, readability cleanup, print-layout polish, dashboard cleanup, or accessibility cleanup
- tasks where formulas, VBA, named ranges, tables, shapes, buttons, or macro bindings must remain intact
- follow-on work after `excel-vba` has stabilized workbook logic
- requests to run a formatting pass safely on `.xlsm` or `.xlsb` workbooks

## Non-Trigger

- requests to change formulas, VBA, named ranges, table names, controls, or workbook structure
- requests to move buttons, re-anchor shapes, or rearrange control layouts
- requests to inject or repair macros or worksheet events
- requests to diagnose visible Excel sessions, COM runtime issues, or automation wrapper failures
- requests that need direct in-place edits to live production workbooks
- requests that need raw-data restructuring to achieve a style result

## Steps

1. Read the workbook directly or consume the handoff produced by `excel-vba`.
2. Read [references/sidecar-formatting-pass.md](references/sidecar-formatting-pass.md) and [references/operational-checklist.md](references/operational-checklist.md) before proposing or applying changes.
3. Confirm the sidecar path, baseline contract capture, and promotion boundary before touching the workbook.
4. Classify each sheet as one of:
   - Raw Data
   - Working Calc
   - Input Form
   - Operational Tracker
   - Executive Report
   - Dashboard
   - Print Form or Submission Sheet
5. Apply only visual-layer changes in this order:
   - workbook theme
   - title, section, header, body, note, warning, and total hierarchy
   - column width and row height
   - print setup
   - minimal conditional formatting
6. Keep Raw Data sheets conservative and keep Working Calc or System sheets out of scope unless the need is explicit and approved.
7. Read [references/validation-checklist.md](references/validation-checklist.md) and [references/promotion-and-rollback.md](references/promotion-and-rollback.md) before finalizing.
8. If the user explicitly requests parallel or delegated execution and the active surface supports it, read [references/parallel-agent-workflow.md](references/parallel-agent-workflow.md) and use manager-worker lanes.

## Safety Boundary

- Do not change workbook logic, formulas, named ranges, table names, controls, shapes, macro bindings, or event code.
- Do not save formatting changes directly into the original workbook path before sidecar validation passes.
- Do not reuse a live user Excel session for the formatting pass.
- Do not mix runtime stabilization or visible-session investigation into the formatting pass. Hand that work to `excel-vba` first.
- Do not touch hidden or veryHidden operational sheets unless the request is explicit and the risk is reviewed.
- Hand the task back to `excel-vba` when styling requires structure-sensitive edits.

## Required Formatting Rules

- Use a sidecar-first workflow for macro-enabled or compatibility-sensitive workbooks.
- Capture a baseline contract before formatting and compare it against the post-format contract before promotion.
- Prefer theme-first formatting over ad hoc cell-by-cell decoration.
- Keep Raw Data sheets conservative:
  - exactly one real header row
  - no merged cells inside data regions
  - no blank rows or columns inside the structured range
  - preserve filters and table readability
- Keep reports, forms, and dashboards readable:
  - maintain contrast and hierarchy
  - keep fills and borders restrained
  - avoid 3D or decorative clutter
  - keep print output usable at normal zoom
- Avoid `Merge & Center` inside data and report structures. Prefer `Center Across Selection` or layout blocks outside the data region.
- If the workbook path contains non-ASCII characters or there is a same-name collision risk, use an ASCII sidecar path.

## Verification

Verify all of the following before finalizing:

- the sidecar workbook opens without a repair prompt
- the sidecar path is the workbook actually being edited
- baseline and post-format contract diffs contain only formatting-safe changes
- Raw Data, accessibility, print, and macro safety gates all pass
- promotion and rollback steps are documented if the sidecar is going to be promoted

## Output

Return:

1. sheet classification summary
2. sidecar path and source workbook boundary
3. formatting plan or applied pass summary
4. validation and contract-diff results
5. promotion decision
6. rollback notes when promotion is planned
