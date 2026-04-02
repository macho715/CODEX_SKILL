# Windows Real Toolchain PATH Fix Plan

## Objective
- Make `tests/test_mstack_pipeline_cli.py::test_pipeline_cli_typescript_feature_flow_real_toolchain` pass on Windows without changing production pipeline behavior.

## Evidence
- Local repro: with the current Windows process environment, `cmd.exe /d /c npm install --no-fund --no-audit --legacy-peer-deps` fails during `esbuild` postinstall with `'node' is not recognized as an internal or external command`.
- Local repro: the same install succeeds when `PATH` is trimmed to a short set of required directories (`Python`, `System32`, `nodejs`, `Git`, npm user bin).
- Local probe: plain `cmd.exe /d /c where node` succeeds, which means the failure happens in npm lifecycle subprocesses rather than in the top-level shell.
- External reference 1: `@npmcli/run-script` documents that on Windows lifecycle scripts default to `env.ComSpec` or `cmd`, and that the directory containing the `node` executable is never added to `PATH`.
  Source: https://github.com/npm/run-script
- External reference 2: npm lifecycle execution prepends `node_modules/.bin` entries to `PATH`, so a bloated parent `PATH` increases the risk that critical tail entries are lost in nested script execution.
  Source: https://docs.npmjs.com/cli/v11/using-npm/scripts/

## Scope
- Modify the Windows real-toolchain install helper in [tests/test_mstack_pipeline_cli.py](c:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/tests/test_mstack_pipeline_cli.py).
- Modify the Node-command shell environment builder in [core/pipeline_runner.py](c:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/core/pipeline_runner.py) so `npm` and `npx` stages inherit the same mitigation.
- Add one focused regression test in [tests/test_pipeline_runner.py](c:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/tests/test_pipeline_runner.py).
- Keep Linux/macOS behavior unchanged.

## Proposed Change
- In `_run_npm_install()`, when `os.name == "nt"`, construct a sanitized child environment for `npm install`.
- Preserve only the directories required for the test flow:
  - current process Python executable directory
  - current process Python Scripts directory when present
  - `System32`
  - `node.exe` directory
  - `git` directory when present
  - npm user bin directory when present
- Pass that environment explicitly to `subprocess.run(...)` only for the Windows `npm install` helper.
- Mirror the same short-PATH strategy inside the Node-command path of `core/pipeline_runner.py` so `npm test`, `npx eslint .`, and `npx tsc --noEmit` do not inherit the bloated parent PATH on Windows.
- Leave non-Node commands and non-Windows behavior unchanged.

## Acceptance Criteria
- `test_pipeline_cli_typescript_feature_flow_real_toolchain` passes on Windows with `RUN_TS_REAL_TOOLCHAIN=1`.
- Existing synthetic TypeScript CLI flow still passes.
- The new `pipeline_runner` regression test passes.
- The helper remains deterministic when `node` or `npm` is missing:
  stop and surface the existing install failure rather than masking it.

## Validation Commands
- `python -m pytest tests/test_mstack_pipeline_cli.py::test_pipeline_cli_typescript_feature_flow_real_toolchain -v --tb=short -r s`
- `python -m pytest tests/test_mstack_pipeline_cli.py::test_pipeline_cli_typescript_feature_flow -v --tb=short -r s`
- `python -m pytest tests/test_pipeline_runner.py::test_build_command_env_sanitizes_windows_node_commands -v --tb=short`
- If needed for regression confidence:
  `python -m pytest tests/test_pipeline_adapter.py -v --tb=short`

## Parallel Execution Split
- Lane 1: patch [tests/test_mstack_pipeline_cli.py](c:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/tests/test_mstack_pipeline_cli.py) and [core/pipeline_runner.py](c:/Users/SAMSUNG/Downloads/skill/mstack-codex-package-1.1.0/source/core/pipeline_runner.py) with the Windows-only sanitized environment logic.
- Lane 2: run focused verification on the real-toolchain test, the existing synthetic TypeScript flow, and the new `pipeline_runner` regression test after the patch is available.

## Stop Conditions
- Stop if the sanitized environment breaks `npm install` for reasons unrelated to the original `node` lookup failure.
- Stop if the sanitized environment breaks non-Node subprocesses in `pipeline_runner`.
- Stop if external docs contradict the helper-only mitigation approach.
