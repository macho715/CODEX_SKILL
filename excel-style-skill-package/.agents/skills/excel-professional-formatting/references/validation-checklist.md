# Validation Checklist

Use this reference before finalizing any workbook formatting pass.

## Raw Data Gate

Confirm all of the following:

- one real header row only
- no merged cells inside the structured data range
- no blank rows or blank columns inside the structured range
- similar data remains in the same column
- filters, table headers, and sort behavior still make sense
- decorative fills and heavy borders were not added

## Report and Dashboard Gate

Confirm all of the following:

- title, section headers, headers, and body text form a clear hierarchy
- contrast is sufficient for text against fills
- tables remain readable at normal zoom
- borders and fills are restrained
- KPI or exception styling adds signal instead of noise
- chart or dashboard visuals avoid clutter and 3D decoration

## Print Gate

Confirm all of the following:

- margins, orientation, and scaling fit the intended output
- multi-page print sheets repeat top rows when persistent context is needed
- titles and headers are not clipped
- wrapped headings do not collapse readability
- grayscale printing still preserves meaning where practical

## Accessibility Gate

Confirm all of the following:

- color is not the only carrier of meaning
- text and background combinations keep usable contrast
- presentation-heavy sheets have a clear starting point
- tables remain simple and navigable
- no new merged cells were introduced into sortable or filterable regions

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
