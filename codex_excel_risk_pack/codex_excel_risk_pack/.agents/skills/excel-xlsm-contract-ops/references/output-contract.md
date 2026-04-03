# Output Contract

## 필수 출력

1. Risk class
2. Touched surfaces
3. Write posture
4. Validation gates
5. Heartbeat recommendation
6. Blocker or next action

## 최소 검증 요약 형식

```text
Risk: HIGH
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
Next: 사용자 검토
```

## DONE 금지 조건

다음 중 하나라도 미확인 상태면 DONE 금지:
- compile
- references
- reopen
- `Application.Run`
- output integrity
- unsaved edits preservation
