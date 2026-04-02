# Operational Checklist

Use this one-page checklist before each workbook formatting run.

## 1. Split the lane before touching Excel

Keep the task in `excel-professional-formatting` only when it is a visual-only pass:

- theme, font, fill, border, alignment, wrapping
- column width or row height
- print setup
- restrained table styling

Stop and hand off to `excel-vba` when the request includes any control-sensitive or runtime-sensitive work:

- moving buttons
- re-anchoring or repositioning shapes
- rearranging ribbons, controls, or macro launch surfaces
- diagnosing visible Excel session, COM, queue, or wrapper instability

## 2. Isolate the formatting session

- create a fresh sidecar workbook copy
- keep the source workbook read-only from the formatting lane
- use an ASCII sidecar path when the source path is non-ASCII or collision-prone
- do not reuse a live user Excel session for the formatting pass
- keep runtime investigation and formatting in separate sessions

## 3. Package the minimum run artifacts

Each run directory should contain all of the following:

- `sidecar_workbook.xlsm` or the matching source extension
- `baseline_contract.json`
- `post_format_contract.json`
- `validation_report.md`
- `promotion_decision.md`

## 4. Run the fixed validation set

Confirm and record at least:

- workbook reopens without a repair prompt
- shape count
- button and shape macro paths
- sheet names, order, and visibility
- named ranges
- ListObject names
- merged range count
- freeze panes
- VBA component list
- worksheet event presence

## 5. Stop conditions

Stop the formatting pass immediately and escalate when any of these appear:

- a button must move into or across a table region
- row or column sizing causes control or shape drift
- the visual request requires header, formula, table-name, or named-range edits
- hidden or veryHidden operational sheets must change visibility
- Excel runtime stability is still under investigation
