# Output Contract

## Required order

1. Risk class
2. Downstream owner
3. Touched surfaces
4. Write posture
5. Validation gates
6. Heartbeat recommendation
7. Blocker or next action

## Minimum validation summary

```text
Risk: HIGH
Downstream owner: excel-vba
Write posture: SERIAL SINGLE-WRITER
Touched:
- button/OnAction
- event handler
- named range
Validation:
- compile: PASS
- references: PASS
- save: PASS
- reopen: PASS
- Application.Run: PASS
- output integrity: PASS
Heartbeat: HEARTBEAT_DONE
Next: user verification
```

## Done is forbidden when any of these are unverified

- compile
- references
- reopen
- `Application.Run`
- output integrity
- unsaved-edits preservation
