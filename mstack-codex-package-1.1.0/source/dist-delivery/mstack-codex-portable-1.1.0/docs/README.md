# mstack

MStack is a modular Codex package for agent teams. This release presents Codex packaging as plugin-first while preserving the existing direct skill install path.

## 3-layer model

- `Skills`: workflow-specific prompts and rules packaged as reusable skill folders.
- `Plugin`: the preferred Codex distribution unit for shipping the MStack skill set together.
- `Future MCP/App layer`: reserved for later; this package does not implement a runtime MCP app or Apps SDK UI layer yet.

## What this package contains

- the `mstack` Python CLI
- classic MStack skills used by the CLI at runtime
- 10 public Codex-ready skills under `skills-codex`
- embedded coordinator reference assets bundled with `mstack-pipeline-coordinator`
- plugin packaging assets for a `mstack-codex` distribution
- docs and tests that verify the skill and packaging layout

## Recommended deployment

Use the plugin-first path when you want to distribute MStack as a Codex package:

```bash
mstack install-codex-plugin --target <parent-dir>/plugins/mstack-codex --with-marketplace
```

Use direct skill install when you only need the Codex skill tree copied into `~/.codex/skills`:

```bash
mstack install-codex --target ~/.codex/skills
```

## Direct install vs plugin install

- `install-codex` installs the packaged Codex skills directly into a Codex skills directory.
- `install-codex-plugin` packages MStack as a local Codex plugin folder, with optional marketplace entry generation.
- The plugin path is the primary distribution shape; the direct install path remains for compatibility and lightweight local use.

## Verification

After a plugin install, confirm:

- `.codex-plugin/plugin.json` exists under the plugin root
- `MSTACK_SKILL_GUIDE.md` exists under the plugin root
- the plugin `skills/` tree contains the MStack Codex skills
- the optional `.agents/plugins/marketplace.json` entry points at `./plugins/mstack-codex`

After a direct install, confirm:

- `~/.codex/skills/MSTACK_SKILL_GUIDE.md`
- `~/.codex/skills/mstack-plan/SKILL.md`
- `~/.codex/skills/mstack-plan/agents/openai.yaml`
- `~/.codex/skills/mstack-pipeline/references/usage-examples.md`
- `~/.codex/skills/mstack-pipeline-coordinator/references/coordinator-input-contract.md`

## Runtime CLI

The package still exposes the main `mstack` CLI for local workflow support:

```bash
python -m mstack --help
```

The CLI continues to support the existing install and runtime commands described in `INSTALL_CODEX.md`.

상세 skill 사용법, 선택 기준, 프롬프트 템플릿, 운영 참고는 `MSTACK_SKILL_GUIDE.md`를 참고하세요.

On Windows, heavily duplicated `PATH` values can still break Node lifecycle commands such as `npm install`, `npx eslint`, or `npx tsc` under `cmd.exe`. MStack now applies a local mitigation for Node-family subprocesses, but that is not a full system fix; keep the machine `PATH` short and deduplicated and see `INSTALL_CODEX.md` troubleshooting for the recommended checks.
