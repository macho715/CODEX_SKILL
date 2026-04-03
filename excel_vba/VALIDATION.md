# Excel-VBA Validation Guide

Use this guide with `scripts/run_excel_vba_validation.ps1` after skill activation, plugin packaging, or install-path changes.

## Validation lanes
- `Skill structure`: checks the skill tree, active/disabled manifests, and required reference files.
- `Plugin/package`: checks for Codex plugin packaging artifacts, manifest parsing, and source/plugin consistency.
- `Install/registration`: checks direct skill install support and local Codex/plugin registration paths.
- `QA contract`: checks that the workbook safety rules, reopen smoke guidance, and output contract are documented.
- `Contract pack`: checks that `excel-xlsm-contract-ops`, its plugin-embedded companion tree, root guardrails, runtime heartbeat rules, `.codex/agents`, and `docs/ops` are present and aligned.

## Report outputs
The runner writes two files per run:
- `summary.md`: human-readable lane status and notes
- `summary.json`: machine-readable lane status and artifact list

Template files that mirror the summary shape live under `scripts/templates/`.

The output directory is `validation-reports\<timestamp>\`.

## Default workflow
1. Run the validation script from the repo root.
2. Review the Markdown summary first.
3. Use the JSON summary if you need to script follow-up checks or CI gating.
4. If any lane reports `warning` or `fail`, fix the underlying artifact and rerun.
5. Use `-Strict` when you want the script to exit non-zero on any non-`pass` overall status.

## Operator expectations
- Direct skill install remains supported.
- Plugin-first packaging is the preferred distribution shape when plugin artifacts are present.
- The plugin package is expected at `plugins/excel-vba/.codex-plugin/plugin.json`.
- Restart Codex after install or registration changes.
- Do not treat generated docs or validation output as source-of-truth inputs for the next run.
