# Official benchmark notes for skill-update

Verification date: 2026-04-02
Source policy: use official OpenAI Codex docs for behavior-changing facts, then note any local-runtime compatibility observations separately.

## Official docs checked on 2026-04-02

1. **Codex AGENTS.md guide**
   - Source: `https://developers.openai.com/codex/guides/agents-md`
   - Codex reads `AGENTS.md` files before work.
   - Global scope uses `~/.codex/AGENTS.override.md` first, then `~/.codex/AGENTS.md`.
   - Project scope walks from repo root to the current directory and checks `AGENTS.override.md`, then `AGENTS.md`, then any configured fallback names.

2. **Codex skills guide**
   - Source: `https://developers.openai.com/codex/skills`
   - Skills are directories with `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`.
   - `SKILL.md` must include `name` and `description`.
   - Codex scans repository skills from `.agents/skills` from the working directory up to repo root.
   - The same guide documents `agents/openai.yaml` as optional metadata for appearance, invocation policy, and tool dependencies.

3. **Codex subagents guide**
   - Source: `https://developers.openai.com/codex/subagents`
   - Custom agent files live under `.codex/agents/` for projects and `~/.codex/agents/` for user scope.
   - Required fields are `name`, `description`, and `developer_instructions`.
   - Optional inherited config includes fields such as `model`, `sandbox_mode`, and `skills.config`.

## Local runtime compatibility note

- In this environment, built-in or installed home-level skills are also exposed from `C:\Users\SAMSUNG\.codex\skills`.
- Treat that path as runtime inventory worth scanning for reuse when present.
- Do not treat this compatibility path as a replacement for the officially documented repo path `.agents/skills`.

## How skill-update should apply these facts

- Scan repo-scoped `.agents/skills` locations and include compatible home-level skill inventories when present.
- Read `AGENTS.md` guidance before planning or patching any skill.
- Keep frontmatter minimal: only `name` and `description`.
- Treat `agents/openai.yaml` as optional metadata, not a required packaging artifact.
- Verify that any custom-agent claims point to real `.codex/agents/*.toml` files.
