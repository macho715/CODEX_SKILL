---
name: ofco-lines-export
description: Exports normalized OFCO, SAFEEN, and ADP lines into a fixed Lines schema with calc checks and evidence fields. Use when structured line items must become stable CSV and JSON outputs for downstream Excel workflows.
metadata:
  target: codex
  version: 1.0.0
---

# OFCO Lines Export

## When to use
- Use when normalized lines must be exported in a fixed tabular contract.
- Use before downstream Excel load, line-level audit, or schema-locked posting.
- Do not use for raw OCR extraction.

## Inputs
Required:
- `lines`: array containing `invoice_no`, `line_no`, `tariff_id`, `description`, `rate`, `amount_excl_tax`

Optional:
- `unit1`, `unit2`, `unit3`
- `tax_rate_pct`, `tax_amount`, `total_incl_tax`
- `evidence`

## Procedure
1. Validate required fields.
2. Default blank units to `1.00` when all three are missing.
3. Default `total_incl_tax` to amount plus tax.
4. Compute `calc_check` from `unit1 × unit2 × unit3 × rate`.
5. Write CSV and JSON with fixed column order.

## Outputs
- `out/ofco_lines_export/lines.csv`
- `out/ofco_lines_export/lines.json`

## Safety
- No column order changes.
- No external lookups.
- Preserve evidence exactly.

## Run
```bash
python .codex/skills/ofco-lines-export/scripts/run.py .codex/skills/ofco-lines-export/examples/input.example.json
```
