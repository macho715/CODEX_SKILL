---
name: invoice-match-verify
description: Matches target invoice rows to structured OFCO reference records and verifies amount tolerance with evidence-backed scoring. Use when you have structured invoice rows and need deterministic OFCO row matching.
metadata:
  target: codex
  version: 1.0.0
---

# Invoice Match Verify

## When to use
- Use when structured target invoice rows must be matched against trusted OFCO reference lines.
- Use when the user asks for deterministic row matching, ranked candidates, or tolerance-based invoice verification.
- Do not use for raw PDF OCR or unstructured scans.

## Inputs
Required JSON fields:
- `target_rows`: array of objects containing `row_id`, `bj_amount`, `subject`
- one of `reference_records` or `reference_records_path`

Optional:
- `tolerance_pct` default `2.0`
- `invoice_no_weight` default `0.35`
- `subject_weight` default `0.35`
- `amount_weight` default `0.30`

Reference record fields supported:
- `NO.` or `NO`
- `SUBJECT`
- `INVOICE NUMBER (OFCO)` or `invoice_no`
- `Amount (AED)` or `amount_aed`
- optional `SAMSUNG REF`

## Procedure
1. Load input JSON and validate required fields.
2. Load reference data from inline JSON or file path.
3. Normalize text and numeric fields.
4. Score candidates using invoice number match, subject overlap, and amount closeness.
5. Rank candidates per target row.
6. Mark the row as `MATCHED`, `MISMATCH`, or `UNMATCHED`.
7. Write `match_results.json` and `summary.json`.

## Outputs
- `out/invoice_match_verify/match_results.json`
- `out/invoice_match_verify/summary.json`

## Safety
- Fail immediately on missing required fields.
- Do not invent candidates.
- Do not modify source files.
- Local execution only.

## Run
```bash
python .codex/skills/invoice-match-verify/scripts/run.py .codex/skills/invoice-match-verify/examples/input.example.json
```
