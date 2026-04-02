# MStack Codex Installation

This document explains how to move the packaged MStack bundle to another computer and install the Codex-ready skills there.

## Recommended package

If you already built the deliverable bundle, copy this zip to the destination machine:

- `dist-package/mstack-codex-package-1.1.0.zip`

After extracting it, the wheel will be here:

- `wheel/mstack-1.1.0-py3-none-any.whl`

The extracted package also includes:

- `source/skills-codex/`
- `source/core/_assets/`
- `source/tests/`
- `source/INSTALL_CODEX.md`
- `PACKAGE_CONTENTS.txt`

## What gets installed

After installation, the target machine gets:

- the `mstack` Python CLI
- packaged Codex skills from `skills-codex`
- packaged classic skills and presets needed by the CLI at runtime

The Codex skills are installed into:

- default: `~/.codex/skills`
- installed names:
  - `mstack-careful`
  - `mstack-dispatch`
  - `mstack-investigate`
  - `mstack-pipeline`
  - `mstack-plan`
  - `mstack-qa`
  - `mstack-retro`
  - `mstack-review`
  - `mstack-ship`

## Requirements

- Python 3.11+
- `pip`
- Codex installed on the destination machine

## Build the wheel

From this repository root:

```bash
python -m pip wheel . --no-deps -w dist-wheel
```

The built wheel will be created under `dist-wheel/`.

## Install from the package zip

On the destination Codex computer:

1. Extract `mstack-codex-package-1.1.0.zip`
2. Open a terminal in the extracted `wheel/` directory
3. Install the wheel
4. Run `mstack install-codex`

Windows example:

```bash
cd <extracted-package>\wheel
python -m pip install mstack-1.1.0-py3-none-any.whl
mstack install-codex
```

If `mstack` is not on `PATH`, run:

```bash
python -m mstack install-codex
```

## Install on another Codex computer

Copy the wheel to the destination machine, then run:

```bash
python -m pip install mstack-<version>-py3-none-any.whl
```

Verify the CLI is available:

```bash
python -m mstack --help
```

For a quick safety check without copying files yet:

```bash
mstack install-codex --dry-run
```

## Install Codex skills

Install the packaged Codex skills into the default Codex skills directory:

```bash
mstack install-codex
```

Or install into a custom directory:

```bash
mstack install-codex --target C:\path\to\codex-skills
```

## Useful options

Dry run:

```bash
mstack install-codex --dry-run
```

Overwrite existing MStack-managed Codex skill directories:

```bash
mstack install-codex --force
```

Notes:

- `--force` only overwrites directories previously installed by MStack
- unmanaged collisions fail safely instead of overwriting foreign skill folders

## Verify installation

After `mstack install-codex`, confirm these paths exist:

```text
~/.codex/skills/mstack-plan/SKILL.md
~/.codex/skills/mstack-plan/agents/openai.yaml
~/.codex/skills/mstack-pipeline/references/usage-examples.md
```

## Troubleshooting

### `install-codex` reports unmanaged collisions

The target already contains a folder with the same MStack skill name that was not installed by MStack.

Use one of these options:

- remove the conflicting folder manually
- install into a different `--target`

### `mstack` command not found

Try:

```bash
python -m mstack --help
```

If that works, your Python scripts path is not on `PATH`.

### Codex runtime smoke

The repository includes an optional runtime smoke test:

```bash
set RUN_CODEX_RUNTIME_SMOKE=1
python -m pytest tests/test_codex_runtime_smoke.py -v --tb=short
```

This requires a working `codex` CLI on the machine.
