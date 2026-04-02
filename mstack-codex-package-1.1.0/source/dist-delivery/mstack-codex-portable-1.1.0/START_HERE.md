# MStack Codex Portable Bundle

This folder contains everything needed to use the same Codex skill set on
another machine.

If you want the full step-by-step guide, read `PORTABLE_INSTALL_GUIDE.md`
first.

## Option 1: Install from wheel

```bash
python -m pip install mstack-1.1.0-py3-none-any.whl
python -m mstack install-codex --target ~/.codex/skills
```

## Option 2: Use the ready-to-copy Codex skill tree

Copy the contents of `codex-skills/` into the target Codex skills directory.

## Option 3: Use the ready-to-copy plugin bundle

Copy:

- `plugins/mstack-codex/`
- `.agents/plugins/marketplace.json`

into the target machine's repo-local plugin layout.

## Included docs

- `PORTABLE_INSTALL_GUIDE.md`
- `docs/README.md`
- `docs/INSTALL_CODEX.md`
- `docs/MSTACK_SKILL_GUIDE.md`
