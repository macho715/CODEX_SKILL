# Formatting Handoff

Use this reference only after workbook logic is stable and the user also wants visual polish.

## Boundary

Hand off to `excel-professional-formatting` only after verifying:

- the workbook opens cleanly
- macros compile when applicable
- formulas, named ranges, and ListObjects still resolve
- buttons, shapes, and assigned macros still work

Keep `excel-vba` responsible for:

- workbook structure
- VBA modules
- event code
- formula safety
- named ranges
- ListObject names and header contracts
- protection and compatibility constraints

Keep `excel-professional-formatting` responsible for:

- theme and typography
- cell style hierarchy
- table appearance
- number and date formatting cleanup
- readability, accessibility, and print polish

## Handoff Contract

Return a compact handoff with these fields:

```json
{
  "safe_to_format": ["Report", "Dashboard"],
  "keep_conservative": ["RawData", "Lookup"],
  "do_not_touch": [
    "Named range Input_Start",
    "Buttons on Control sheet",
    "Merged title block on Print_Form"
  ],
  "table_rules": {
    "single_header_row_required": true,
    "preserve_filters": true,
    "preserve_table_names": true
  },
  "print_rules": {
    "repeat_top_rows": {
      "Print_Form": "$1:$2"
    },
    "fit_to_page": ["Print_Form"]
  },
  "formatting_notes": [
    "Avoid merged cells inside sortable/filterable ranges",
    "Preserve button and shape placement",
    "Use theme-based styles where possible"
  ]
}
```

## Stop Conditions

Do not hand off broad styling changes when any of these remain unresolved:

- workbook opens in repair mode
- event code is still unstable
- named range or table references are broken
- control placement is already drifting
- the requested style change requires structural edits to raw-data regions
