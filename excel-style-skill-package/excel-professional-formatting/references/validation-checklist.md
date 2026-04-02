# Validation Checklist

Use this reference before finalizing any workbook formatting pass.

## Gate A: Workbook Open

Confirm all of the following:

- the sidecar workbook opens without a repair prompt
- the workbook is not unexpectedly read-only
- the actual open path matches the intended sidecar path

## Gate B: Contract Diff

Allowed diff classes:

- fill
- font
- alignment
- width or height
- print setup
- tab color

Disallowed diff classes:

- sheet name, order, or visibility change
- merged-cell increase
- named range change
- table name change
- formula change
- shape count change
- VBA component change
- worksheet code module change

## Gate C: Raw Data Gate

Confirm all of the following:

- one real header row only
- no merged cells inside the structured data range
- no blank rows or blank columns inside the structured range
- filters, table headers, and sort behavior still make sense
- decorative fills and heavy borders were not added

## Gate D: Print Gate

Confirm all of the following:

- margins, orientation, and scaling fit the intended output
- multi-page print sheets repeat top rows when persistent context is needed
- titles and headers are not clipped
- wrapped headings do not collapse readability

## Gate E: Accessibility Gate

Confirm all of the following:

- color is not the only carrier of meaning
- text and background combinations keep usable contrast
- warning, total, ready, and missing states remain visually distinct
- presentation-heavy sheets have a clear starting point
- no new merged cells were introduced into sortable or filterable regions

## Gate F: Macro Safety Gate

Even for a formatting pass, confirm all of the following:

- the workbook reopens normally
- buttons and shapes still have the expected macro paths
- worksheet events still match the expected state
- the VBA project component list is unchanged

## Approved Hook Gate

If scripting or automation is allowed, stay within these approved hooks unless `excel-vba` explicitly authorizes more:

- `RangeFormat.autofitColumns()`
- `RangeFormat.autofitRows()`
- `Table.setPredefinedTableStyle()`
- `Table.setShowBandedRows()`
- `Table.setShowFilterButton()`

## Stop and Escalate

Stop the formatting pass and hand back to `excel-vba` when any of these appear:

- the visual request requires changing headers, table names, or named ranges
- controls or shapes drift after row or column sizing
- workbook protection blocks safe formatting
- conditional formatting depends on formula logic that is still unstable
- the workbook needs structural changes in raw-data regions to satisfy the style request
