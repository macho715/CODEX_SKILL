# Handoff Operational Checklist

Use this file when work is escalating from `excel-professional-formatting` into `excel-vba`, or when a formatting request crosses into contract-sensitive workbook surfaces.

## Purpose

- keep visual-only work in `excel-professional-formatting`
- move structure-sensitive work into `excel-vba` before controls, bindings, or workbook contracts drift
- freeze the sidecar boundary, macro-runnability checks, and COM or Unicode risk at handoff time

## Escalate into `excel-vba` when any of these appear

- button or shape repositioning
- `OnAction` review, repair, or rebinding
- VBA, worksheet events, named ranges, table names, or formulas must change
- workbook open or save works, but macro execution or COM behavior is unstable
- non-ASCII paths, Korean captions, VBA reinjection, or PowerShell-driven Excel execution are involved

## Required handoff inputs

- source workbook path and sidecar path
- current deliverable and promotion boundary
- sheet classification summary
- latest formatting-pass result and remaining visual asks
- known risks:
  - shape drift
  - visible-session instability
  - non-ASCII path exposure
  - open workbook or unsaved user edits

## Check first on takeover

- whether the source of truth is the original workbook or the sidecar
- whether the workbook is already open
- whether unsaved user edits are present
- whether patch-in-place is possible
- whether tables, named ranges, formulas, controls, and worksheet events collide
- whether `Result`, `Validation_Errors`, and `LOG` remain intact

## Implementation defaults

- keep VBA as the base implementation
- use Python only to build workbook assets or support the VBA path
- prefer patch-in-place over delete or recreate when a workbook contract already exists
- treat `file created` and `macro runnable` as separate checks
- use workbook-qualified `Application.Run` by default

## COM and Unicode rules

- after `.xlsm` creation or VBA reinjection, save, close, and reopen before shipping
- run the entry macro only after reopen and through workbook-qualified `Application.Run`
- when the path is non-ASCII, prefer an ASCII sidecar or copy
- keep VBA source ASCII-first when practical
- when Korean captions are required, prefer a safe codepoint-based approach over raw literals

## Button, shape, and control rules

- prefer Forms controls unless the user explicitly needs ActiveX
- verify:
  - shape count
  - button names
  - captions
  - `OnAction`
  - a click-equivalent macro run
- if row or column resizing causes drift, keep ownership in `excel-vba` rather than sending the issue back to a formatting-only lane

## Minimum validation gate

- workbook opens cleanly
- VBA compiles without error
- references are not broken
- named ranges remain intact
- table names remain intact
- worksheet events do not collide
- `Result`, `Validation_Errors`, and `LOG` exist
- button, shape, and control bindings still work
- save, close, and reopen succeed
- the workbook-qualified entry macro runs

## QA sequence

1. 10-row test
2. total or count validation
3. edge-case validation
4. save, close, and reopen
5. workbook-qualified macro smoke test
6. validate user-facing controls
7. full-run recommendation

## What the formatting lane should record before handoff

- what it changed
- what it intentionally did not change
- which request crossed beyond visual-only scope
- whether promotion is allowed
- what the rollback baseline is

## Stop conditions

- the workbook is open with unsaved user edits
- a worksheet-event collision is unresolved
- compile or `Application.Run` failures still have an unknown cause
- a formatting-only lane is still trying to edit a contract-sensitive surface
- direct edits to the original path are being requested before sidecar validation
