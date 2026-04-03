# Codex OFCO Skill Pack

Codex-ready skill package for deterministic OFCO/HVDC invoice and logistics validation workflows.

## Included skills
- `invoice-match-verify`
- `cost-center-mapper`
- `vendor-invoice-grouping`
- `ofco-lines-export`
- `flow-code-validator`

## Install
Copy `.codex/skills/` and `AGENTS.md` into your repository root.

## Run examples
```bash
python .codex/skills/invoice-match-verify/scripts/run.py .codex/skills/invoice-match-verify/examples/input.example.json
python .codex/skills/cost-center-mapper/scripts/run.py .codex/skills/cost-center-mapper/examples/input.example.json
python .codex/skills/vendor-invoice-grouping/scripts/run.py .codex/skills/vendor-invoice-grouping/examples/input.example.json
python .codex/skills/ofco-lines-export/scripts/run.py .codex/skills/ofco-lines-export/examples/input.example.json
python .codex/skills/flow-code-validator/scripts/run.py .codex/skills/flow-code-validator/examples/input.example.json
```
