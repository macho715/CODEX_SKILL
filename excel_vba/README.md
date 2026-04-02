# excel-vba Skill Repo

This repository packages the `excel-vba` Codex skill and its validation/docs helpers for Windows Excel automation work.

## What is here
- `excel-vba/`: the skill source tree
- `install_excel_vba_skill.ps1`: direct-install helper for a local Codex skills folder
- `scripts/run_excel_vba_validation.ps1`: parallel validation runner that writes Markdown and JSON summaries
- `scripts/templates/validation-summary.md` and `scripts/templates/validation-summary.json`: report templates for the validation summary shape
- `VALIDATION.md`: operator guide for the validation lanes and report layout

## Install paths
Direct skill install stays supported for local use:

```powershell
.\install_excel_vba_skill.ps1
```

If your checkout or package also includes Codex plugin artifacts, install and register the plugin bundle first:

```powershell
.\install_excel_vba_plugin.ps1 -Register
```

The plugin bundle source lives under `plugins/excel-vba/`. The installer copies it to `$env:USERPROFILE\plugins\excel-vba`, updates `$env:USERPROFILE\.agents\plugins\marketplace.json`, enables `excel-vba` in `$env:USERPROFILE\.codex\config.toml`, and then you should restart Codex so the new skill/plugin set is discovered in a fresh session.

## Validation
Run the repository validation before publishing or after a non-trivial skill/package change:

```powershell
.\scripts\run_excel_vba_validation.ps1
```

The runner executes four lanes in parallel:
- skill structure
- plugin/package structure
- install/registration checks
- QA contract checks

Outputs are written under `validation-reports\<timestamp>\` as both `summary.md` and `summary.json`.

## GitHub install
If you are consuming this repo from GitHub-based Codex skill installation, use the bundled installer path inside the repo:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo <owner>/<repo> --path excel-vba
```

## Operator notes
- Restart Codex or open a fresh session after skill or plugin installation.
- Use the validation report as the final source of truth for lane status.
- Keep direct skill install and plugin registration aligned; do not treat them as separate content sources.
