# excel-professional-formatting Skill Package

This package ships the `excel-professional-formatting` Codex skill, a local Codex plugin bundle, and validation helpers for sidecar-first Excel formatting passes.

## What is here

- `SKILL.md`: active skill manifest
- `references/`: sidecar pass, operational checklist, validation, promotion, rollback, and parallel workflow guidance
- `install_excel_professional_formatting_skill.ps1`: direct skill installer
- `install_excel_professional_formatting_plugin.ps1`: local plugin installer and registrar
- `scripts/run_excel_professional_formatting_validation.ps1`: parallel validation runner
- `plugins/excel-professional-formatting/`: self-contained Codex plugin bundle
- `.agents/plugins/marketplace.json`: repo-local marketplace template

## Install

Direct skill install:

```powershell
.\install_excel_professional_formatting_skill.ps1
```

Plugin install and registration:

```powershell
.\install_excel_professional_formatting_plugin.ps1 -Register
```

The plugin installer copies the plugin bundle to `$env:USERPROFILE\plugins\excel-professional-formatting`, updates `$env:USERPROFILE\.agents\plugins\marketplace.json`, enables the plugin in `$env:USERPROFILE\.codex\config.toml`, and then you should restart Codex.

## Validation

Start workbook-pass work with `references/operational-checklist.md`, then run the package validation after changing the skill, plugin, install paths, or sidecar rules.

Run package validation with:

```powershell
.\scripts\run_excel_professional_formatting_validation.ps1 -Strict
```

The runner executes four lanes in parallel:

- skill structure
- plugin/package
- install/registration
- sidecar/validation contract

Outputs are written under `validation-reports\<timestamp>\` as both `summary.md` and `summary.json`.
