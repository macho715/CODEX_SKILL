---
name: flow-code-validator
description: Infers and validates Flow Code 0-5 using destination, warehouse-leg, and MOSB-leg rules for HVDC logistics. Use when routing records must be checked for AGI, DAS, MIR, or SHU compliance.
metadata:
  target: codex
  version: 1.0.0
---

# Flow Code Validator

## When to use
- Use when shipment routing records must be checked against documented flow rules.
- Use for AGI, DAS, MIR, SHU, warehouse legs, and MOSB legs.
- Do not use when routing facts are unavailable.

## Inputs
Required:
- `shipments`: array containing `shipment_id`, `final_location`, `current_flow_code`

Optional:
- `pre_arrival`
- `requires_warehouse_storage`
- `mosb_leg`
- `site_assigned`

## Procedure
1. Normalize destination codes.
2. Infer expected flow code:
   - `0` pre-arrival
   - `1` port to site direct for MIR or SHU
   - `2` port to warehouse to site for MIR or SHU
   - `3` port to MOSB to AGI or DAS
   - `4` port to warehouse to MOSB to AGI or DAS
   - `5` mixed or incomplete routing
3. Compare expected and current flow codes.
4. Write validation output and summary.

## Outputs
- `out/flow_code_validator/validated_shipments.json`
- `out/flow_code_validator/flow_summary.json`

## Safety
- Unknown destinations map to `5`.
- No routing legs are invented.
- No external lookups.

## Run
```bash
python .codex/skills/flow-code-validator/scripts/run.py .codex/skills/flow-code-validator/examples/input.example.json
```
