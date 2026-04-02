# MStack Codex Skill Validation Report

- Generated: `2026-03-30T05:43:20.048466+00:00`
- Repo: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source`
- Overall Status: `failed`
- Automatic Patch Action: `manual-follow-up-required`

## Lanes

### lane-direct-install

- Status: `passed`
- Duration: `198.67s`
- Checks: `validated:mstack-careful, validated:mstack-dispatch, validated:mstack-investigate, validated:mstack-pipeline, validated:mstack-plan, validated:mstack-qa, validated:mstack-retro, validated:mstack-review, validated:mstack-ship`
- venv: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T052709Z\lane-direct-install\venv`
- target_dir: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T052709Z\lane-direct-install\codex-skills`
- stdout: `[mstack] Codex target: C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T052709Z\lane-direct-install\codex-skills
[mstack] Installed: 9
[mstack] Skipped: 0
[mstack] Overwritten: 0
[mstack] Installed names: mstack-careful, mstack-dispatch, mstack-investigate, mstack-pipeline, mstack-plan, mstack-qa, mstack-retro, mstack-review, mstack-ship`

### lane-plugin-install

- Status: `passed`
- Duration: `200.16s`
- Checks: `validated:plugin-manifest, validated:plugin-skill-tree, validated:plugin-managed-marker, validated:marketplace-entry`
- venv: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T052709Z\lane-plugin-install\venv`
- plugin_root: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T052709Z\lane-plugin-install\plugins\mstack-codex`
- marketplace_path: `C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\skills-workspace\validation-reports\20260330T052709Z\lane-plugin-install\.agents\plugins\marketplace.json`
- stdout: `[mstack] Plugin target: C:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/skills-workspace/validation-reports/20260330T052709Z/lane-plugin-install/plugins/mstack-codex
[mstack] Plugin manifest: C:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/skills-workspace/validation-reports/20260330T052709Z/lane-plugin-install/plugins/mstack-codex/.codex-plugin/plugin.json
[mstack] Plugin name: mstack-codex
[mstack] Installed: 9
[mstack] Skipped: 0
[mstack] Overwritten: 0
[mstack] Marketplace path: C:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/skills-workspace/validation-reports/20260330T052709Z/lane-plugin-install/.agents/plugins/marketplace.json
[mstack] Marketplace updated: 1`

### lane-runtime-smoke

- Status: `failed`
- Duration: `885.47s`
- Error:
```text
Traceback (most recent call last):
  File "C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\scripts\codex_runtime_smoke.py", line 440, in <module>
    sys.exit(main())
             ^^^^^^
  File "C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\scripts\codex_runtime_smoke.py", line 427, in main
    summary = run_smoke(
              ^^^^^^^^^^
  File "C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\scripts\codex_runtime_smoke.py", line 413, in run_smoke
    shutil.copy2(path, keep_dir / path.name)
  File "C:\Program Files\Python311\Lib\shutil.py", line 448, in copy2
    copyfile(src, dst, follow_symlinks=follow_symlinks)
  File "C:\Program Files\Python311\Lib\shutil.py", line 256, in copyfile
    with open(src, 'rb') as fsrc:
         ^^^^^^^^^^^^^^^
PermissionError: [Errno 13] Permission denied: 'C:\\Users\\SAMSUNG\\AppData\\Local\\Temp\\codex-runtime-smoke-wq2n4rfh\\isolated-workdir'

Traceback (most recent call last):
  File "C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\scripts\run_codex_skill_validation.py", line 317, in _run_lane
    return lane_fn(wheel_path, lane_root)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\scripts\run_codex_skill_validation.py", line 285, in _lane_runtime_smoke
    raise RuntimeError(smoke.stderr or smoke.stdout or "runtime smoke failed")
RuntimeError: Traceback (most recent call last):
  File "C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\scripts\codex_runtime_smoke.py", line 440, in <module>
    sys.exit(main())
             ^^^^^^
  File "C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\scripts\codex_runtime_smoke.py", line 427, in main
    summary = run_smoke(
              ^^^^^^^^^^
  File "C:\Users\SAMSUNG\Downloads\skill\mstack-codex-package-1.1.0\source\scripts\codex_runtime_smoke.py", line 413, in run_smoke
    shutil.copy2(path, keep_dir / path.name)
  File "C:\Program Files\Python311\Lib\shutil.py", line 448, in copy2
    copyfile(src, dst, follow_symlinks=follow_symlinks)
  File "C:\Program Files\Python311\Lib\shutil.py", line 256, in copyfile
    with open(src, 'rb') as fsrc:
         ^^^^^^^^^^^^^^^
PermissionError: [Errno 13] Permission denied: 'C:\\Users\\SAMSUNG\\AppData\\Local\\Temp\\codex-runtime-smoke-wq2n4rfh\\isolated-workdir'
```
