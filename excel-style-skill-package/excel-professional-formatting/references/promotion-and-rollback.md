# Promotion and Rollback

Use this reference whenever a validated sidecar workbook may be promoted back to the original workbook path.

## Promotion prerequisites

Promote only when all of the following are true:

1. the sidecar validation gates pass
2. `promotion_decision.md` records `PASS`
3. the original workbook has not changed since the sidecar was created
4. a fresh backup of the original workbook is available

## Promotion sequence

1. Create a fresh backup of the original workbook.
2. Copy the validated sidecar workbook to the original workbook path.
3. Reopen the workbook from the original path and confirm it is the promoted copy.
4. Recheck the critical sheets manually.
5. Record the backup path and promotion timestamp.

## Immediate rollback triggers

- repair prompt appears on open
- workbook opens read-only unexpectedly
- macro bindings, shapes, or events differ from the validated sidecar state
- named ranges, tables, formulas, or visibility differ unexpectedly
- the user reports a behavior regression after promotion

## Rollback sequence

1. Locate the backup created just before promotion.
2. Restore the backup to the original workbook path.
3. Reopen the restored workbook and confirm the key sheets.
4. Record the cause and diff evidence before retrying another formatting pass.
