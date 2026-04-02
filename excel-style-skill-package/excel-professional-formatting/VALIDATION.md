# Excel Professional Formatting Validation Guide

Use this guide with `scripts/run_excel_professional_formatting_validation.ps1` after any skill, plugin, or registration change.

For workbook-pass operations, use `references/operational-checklist.md` to package run artifacts and fixed validation evidence before any promotion decision.

## Validation lanes

- `Skill structure`: active skill manifest, metadata, and required references
- `Plugin/package`: plugin manifest, embedded skill tree, and source/plugin consistency
- `Install/registration`: direct install, plugin install script, marketplace, and Codex config
- `Sidecar contract`: sidecar pass, validation, promotion, and rollback guidance

## Report outputs

Each run writes:

- `summary.md`
- `summary.json`

The output directory is `validation-reports\<timestamp>\`.

## Default workflow

1. Run the validation script from this package root.
2. Review `summary.md` first.
3. Use `summary.json` for automation or gating.
4. If any lane reports `warning` or `fail`, fix the artifact and rerun.
5. Use `-Strict` when you want a non-zero exit on any non-pass overall result.
