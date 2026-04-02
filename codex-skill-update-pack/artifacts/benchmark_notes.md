# Benchmark Notes

Run date: 2026-04-02
Package: `codex-skill-update-pack`

## Official sources checked

1. `https://developers.openai.com/codex/guides/agents-md`
   - Confirms `AGENTS.md` loading order and the `~/.codex` global scope.

2. `https://developers.openai.com/codex/skills`
   - Confirms that skills use `SKILL.md` with `name` and `description`, and that repo discovery scans `.agents/skills`.

3. `https://developers.openai.com/codex/subagents`
   - Confirms project and user custom-agent locations plus the required TOML fields.

## Applied package updates

- Kept the repo-scoped skill under `.agents/skills/skill-update`.
- Added validation for the promised `artifacts/benchmark_notes.md` output.
- Added compatibility scanning for `C:\Users\SAMSUNG\.codex\skills` because this runtime exposes home-level skills there.
- Kept the compatibility path separate from the official `.agents/skills` rule so the package does not overstate official behavior.
