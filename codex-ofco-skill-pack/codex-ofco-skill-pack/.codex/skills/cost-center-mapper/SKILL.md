---
name: cost-center-mapper
description: Maps invoice description and tariff patterns into OFCO cost hierarchy and immutable qty and amount fields. Use when structured invoice lines must be assigned to fixed cost center outputs.
metadata:
  target: codex
  version: 1.0.0
---

# Cost Center Mapper

## When to use
- Use when line descriptions or tariff IDs must map to COST MAIN, COST CENTER A/B, PRICE CENTER, and immutable field names.
- Use after normalization and before Excel posting or summary generation.
- Do not use for unknown schemas or workflows that require external lookups.

## Inputs
Required:
- `lines`: array with `description`
- one of `cost_items` or `cost_items_path`
- one of `cost_item_fields` or `cost_item_fields_path`

Optional:
- `tariff_mapping` or `tariff_mapping_path`
- `default_cost_main`

## Procedure
1. Load cost items and immutable field names.
2. For each line, attempt tariff-first mapping.
3. If tariff-first fails, apply subject pattern rules.
4. Resolve `cost_item_code`, `qty_field`, and `amount_field`.
5. Validate immutable field existence.
6. Fail if any line cannot be mapped safely.
7. Write mapped lines and summary.

## Outputs
- `out/cost_center_mapper/mapped_lines.json`
- `out/cost_center_mapper/mapping_summary.json`

## Safety
- No guessing for unmapped lines.
- No source file edits.
- Local deterministic execution only.

## Run
```bash
python .codex/skills/cost-center-mapper/scripts/run.py .codex/skills/cost-center-mapper/examples/input.example.json
```
