# MStack Codex Skill Validation Report

- Generated: `2026-03-30T05:55:20.761208+00:00`
- Repo: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source`
- Overall Status: `passed`
- Automatic Patch Action: `none-required`

## Lanes

### lane-direct-install

- Status: `passed`
- Duration: `81.43s`
- Checks: `validated:mstack-careful, validated:mstack-dispatch, validated:mstack-investigate, validated:mstack-pipeline, validated:mstack-plan, validated:mstack-qa, validated:mstack-retro, validated:mstack-review, validated:mstack-ship`
- venv: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T054531Z\lane-direct-install\venv`
- target_dir: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T054531Z\lane-direct-install\codex-skills`
- stdout: `[mstack] Codex target: C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T054531Z\lane-direct-install\codex-skills
[mstack] Installed: 9
[mstack] Skipped: 0
[mstack] Overwritten: 0
[mstack] Installed names: mstack-careful, mstack-dispatch, mstack-investigate, mstack-pipeline, mstack-plan, mstack-qa, mstack-retro, mstack-review, mstack-ship`

### lane-plugin-install

- Status: `passed`
- Duration: `80.17s`
- Checks: `validated:plugin-manifest, validated:plugin-skill-tree, validated:plugin-managed-marker, validated:marketplace-entry`
- venv: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T054531Z\lane-plugin-install\venv`
- plugin_root: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T054531Z\lane-plugin-install\plugins\mstack-codex`
- marketplace_path: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T054531Z\lane-plugin-install\.agents\plugins\marketplace.json`
- stdout: `[mstack] Plugin target: C:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/skills-workspace/validation-reports/20260330T054531Z/lane-plugin-install/plugins/mstack-codex
[mstack] Plugin manifest: C:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/skills-workspace/validation-reports/20260330T054531Z/lane-plugin-install/plugins/mstack-codex/.codex-plugin/plugin.json
[mstack] Plugin name: mstack-codex
[mstack] Installed: 9
[mstack] Skipped: 0
[mstack] Overwritten: 0
[mstack] Marketplace path: C:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/skills-workspace/validation-reports/20260330T054531Z/lane-plugin-install/.agents/plugins/marketplace.json
[mstack] Marketplace updated: 1`

### lane-runtime-smoke

- Status: `passed`
- Duration: `520.25s`
- Checks: `validated:runtime-smoke-ok, validated:runtime-skill-count=9, validated:mstack-careful, validated:mstack-dispatch, validated:mstack-investigate, validated:mstack-plan, validated:mstack-pipeline, validated:mstack-qa, validated:mstack-retro, validated:mstack-review, validated:mstack-ship`
- venv: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T054531Z\lane-runtime-smoke\venv`
- summary_json: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T054531Z\lane-runtime-smoke\runtime-smoke.json`
- persisted_output_dir: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\runtime-smoke`
