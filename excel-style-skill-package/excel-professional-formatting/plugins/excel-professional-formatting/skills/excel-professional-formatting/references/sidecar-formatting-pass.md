# Sidecar Formatting Pass

Use this reference before any non-trivial formatting work on `.xlsm`, `.xlsb`, or workbook-contract-sensitive files.

## Core policy

- Never format the original workbook first.
- Create a sidecar copy and apply every formatting action there.
- Do not write back to the source workbook until validation passes.
- Use an ASCII sidecar path when the source path is non-ASCII or same-name collisions are likely.

## Default sidecar outputs

Keep these artifacts together under one run directory:

- `sidecar_workbook.xlsm` or the matching source extension
- `baseline_contract.json`
- `post_format_contract.json`
- `validation_report.md`
- `promotion_decision.md`

## Baseline contract

Capture at least:

- workbook path
- sheet names, order, and visibility
- used range
- freeze panes
- autofilter ranges
- merged range count
- ListObject names
- named ranges
- formula presence
- shape count
- worksheet event presence
- VBA component names

## Allowed formatting changes

- theme changes
- font, fill, border, alignment, and wrapping cleanup
- column width and row height adjustments
- print setup and repeated top rows
- restrained conditional formatting
- safe table style application when the table contract is already stable

## Escalate to `excel-vba`

Stop the formatting pass and escalate when any of these appear:

- header rename
- table rename or rebuild
- named range change
- formula change
- VBA or event code change
- shape or button macro binding change
- hidden-sheet visibility change
- large row or column shifts that could move shapes or controls
