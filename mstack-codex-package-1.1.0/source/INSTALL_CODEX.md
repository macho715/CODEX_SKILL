# MStack Codex Packaging

This document explains how to install MStack for Codex in a plugin-first way while keeping the existing direct skill install path.

## Deployment model

MStack now maps to three layers:

- `Skills`: reusable workflow definitions, shipped under `skills-codex`
- `Plugin`: the preferred Codex distribution unit for shipping the MStack skill bundle
- `Future MCP/App layer`: reserved for a later release; this package does not implement it yet

## What gets installed

After installation, the target machine gets:

- the `mstack` Python CLI
- packaged classic skills and presets needed by the CLI at runtime
- Codex-ready skills from `skills-codex`
- plugin packaging assets for a `mstack-codex` bundle

## Supported installation paths

### 1) Direct Codex skills install

Use this when you want the Codex skill tree copied directly into a Codex skills directory:

```bash
mstack install-codex
```

Optional flags:

```bash
mstack install-codex --target C:\path\to\codex-skills
mstack install-codex --dry-run
mstack install-codex --force
```

Behavior:

- installs the 10 packaged public Codex skills
- includes embedded coordinator contracts inside `mstack-pipeline-coordinator`
- keeps unmanaged collisions safe
- overwrites only MStack-managed directories when `--force` is used

### 2) Plugin-first Codex packaging

Use this when you want MStack distributed as a local Codex plugin package:

```bash
mstack install-codex-plugin
```

Recommended plugin export:

```bash
mstack install-codex-plugin --target <parent-dir>/plugins/mstack-codex --with-marketplace
```

Supported flags:

- `--target`
- `--force`
- `--dry-run`
- `--with-marketplace`
- `--marketplace-path`

Behavior:

- creates or exports a local plugin tree for `mstack-codex`
- places the plugin manifest at `.codex-plugin/plugin.json`
- embeds the MStack Codex skills under the plugin `skills/` tree
- optionally creates or updates a local `.agents/plugins/marketplace.json` entry
- overwrites only MStack-managed plugin installs when `--force` is set

## Build the wheel

From this repository root:

```bash
python -m pip wheel . --no-deps -w dist-wheel
```

The built wheel will be created under `dist-wheel/`.

## Install on another machine

Copy the wheel to the destination machine, then run:

```bash
python -m pip install mstack-<version>-py3-none-any.whl
```

Verify the CLI is available:

```bash
python -m mstack --help
```

## Verification

### Direct install verification

After `mstack install-codex`, confirm these paths exist:

```text
~/.codex/skills/MSTACK_SKILL_GUIDE.md
~/.codex/skills/mstack-plan/SKILL.md
~/.codex/skills/mstack-plan/agents/openai.yaml
~/.codex/skills/mstack-pipeline/references/usage-examples.md
~/.codex/skills/mstack-pipeline-coordinator/references/coordinator-input-contract.md
```

### Plugin verification

After `mstack install-codex-plugin`, confirm:

```text
<target>/mstack-codex/.codex-plugin/plugin.json
<target>/mstack-codex/MSTACK_SKILL_GUIDE.md
<target>/mstack-codex/skills/
<target>/.agents/plugins/marketplace.json
```

The marketplace entry should point to `./plugins/mstack-codex` when the plugin is installed in a repo-local layout.

## Troubleshooting

For detailed skill usage, prompt templates, and MStack workflow selection guidance, see `MSTACK_SKILL_GUIDE.md`.

### `install-codex` reports unmanaged collisions

The target already contains a folder with the same MStack skill name that was not installed by MStack.

Use one of these options:

- remove the conflicting folder manually
- install into a different `--target`

### `install-codex-plugin` reports unmanaged collisions

The target already contains a plugin folder with the same MStack plugin name that was not installed by MStack.

Use one of these options:

- remove the conflicting folder manually
- install into a different `--target`

### `mstack` command not found

Try:

```bash
python -m mstack --help
```

If that works, your Python scripts path is not on `PATH`.

### Windows Node lifecycle commands fail with `node not recognized`

Symptoms may include failures from `npm install`, `npx`, or Node-based lint, test, and typecheck commands under `cmd.exe`, including errors like `node is not recognized as an internal or external command`.

On Windows, `cmd.exe` can fail when inherited `PATH` values become excessively long or heavily duplicated. npm lifecycle scripts also prepend local `.bin` directories to `PATH`, and `@npmcli/run-script` does not automatically add the Node install directory to the child `PATH`. That means critical entries such as `C:\Program Files\nodejs` can fall out of the effective search path even when top-level shells still resolve `node`.

MStack now applies a local mitigation for Node-family subprocesses, but this is only a targeted workaround, not a full machine-level correction.

Recommended remediation:

1. Remove duplicate `PATH` entries for Python, Git, Node, and the npm user bin directory.
2. Confirm that `C:\Program Files\nodejs` is still present on `PATH`.
3. Restart the terminal or IDE so new shells inherit the cleaned environment.
4. Re-check Node resolution from `cmd.exe`:

```bash
cmd.exe /d /c "where node && where npm && node --version && npm --version"
```

Reference:

- Microsoft Learn: `cmd.exe` command-line and environment string limitation
  https://learn.microsoft.com/en-us/troubleshoot/windows-client/shell-experience/command-line-string-limitation
- npm Docs: scripts and lifecycle `PATH` behavior
  https://docs.npmjs.com/cli/v11/using-npm/scripts/
- `@npmcli/run-script`: Windows shell behavior and no `prepend-node-path`
  https://github.com/npm/run-script

### Codex runtime smoke

The repository includes an optional runtime smoke test:

```bash
set RUN_CODEX_RUNTIME_SMOKE=1
python -m pytest tests/test_codex_runtime_smoke.py -v --tb=short
```

This requires a working `codex` CLI on the machine.
