---
name: vendor-invoice-grouping
description: Groups normalized lines by vendor invoice number, infers invoice type with tariff-first rules, and calculates per-group totals. Use when OFCO master invoices contain embedded vendor invoice lines.
metadata:
  target: codex
  version: 1.0.0
---

# Vendor Invoice Grouping

## When to use
- Use after line normalization.
- Use when one OFCO invoice contains SAFEEN, ADP, or OFCO subgroups.
- Do not use when grouping keys are unavailable and cannot be supplied.

## Inputs
Required:
- `standard_lines`: array of objects with `description` and `amount_excl_tax_aed`

Optional:
- `vendor_invoice_no`
- `tariff_id` or `tariff_code`
- `tax_amount_aed`
- `amount_excl_tax`
- `tax_amount`

## Procedure
1. Validate required numeric fields.
2. Group lines by `vendor_invoice_no`.
3. Put missing grouping keys into `unassigned_lines`.
4. Infer `invoice_type` using tariff-first rules.
5. Accumulate AED and non-AED totals.
6. Write grouped output and summary.

## Outputs
- `out/vendor_invoice_grouping/grouped_vendor_invoices.json`
- `out/vendor_invoice_grouping/group_summary.json`

## Safety
- No fabricated grouping keys.
- Unknown groups default to `OFCO`.
- Local deterministic execution only.

## Run
```bash
python .codex/skills/vendor-invoice-grouping/scripts/run.py .codex/skills/vendor-invoice-grouping/examples/input.example.json
```
