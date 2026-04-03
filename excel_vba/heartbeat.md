# heartbeat.md
# Codex Excel Runtime Heartbeat

Use this document for short, explicit status reporting during high-risk Excel runs.

## When to use
- Excel COM automation
- `.xlsm` patching or VBA reinjection
- Python and Excel bridge work
- non-ASCII path, filename, sheet name, or caption handling
- button, shape, `OnAction`, event, named range, or table binding changes
- live workbook work
- unsaved changes risk
- explicit subagent workflows
- any run where file creation succeeded but runtime integrity is still unverified

## Allowed states
- `HEARTBEAT_OK`
- `HEARTBEAT_WARN`
- `HEARTBEAT_BLOCKED`
- `HEARTBEAT_DONE`

## Allowed stages
- `PRECHECK`
- `OPEN`
- `PATCH`
- `INJECT`
- `SAVE`
- `REOPEN`
- `RUN`
- `VERIFY`
- `MERGE`
- `DONE`

## Format
```text
Status: <HEARTBEAT_OK | HEARTBEAT_WARN | HEARTBEAT_BLOCKED | HEARTBEAT_DONE>
Stage: <PRECHECK | OPEN | PATCH | INJECT | SAVE | REOPEN | RUN | VERIFY | MERGE | DONE>
Done:
- <item 1>
- <item 2>
- <item 3>
Blocker: <NONE or blocker>
Next: <one immediate next action>
```

If the state is `HEARTBEAT_BLOCKED`, add:

```text
Input Required:
1. <required input 1>
2. <required input 2>
3. <required input 3>
```

## Escalation rules
- Use at least `HEARTBEAT_WARN` if save passed but reopen is unverified.
- Use at least `HEARTBEAT_WARN` if reopen passed but `Application.Run` is unverified.
- Use at least `HEARTBEAT_WARN` if compile or references are unverified after VBA change.
- Use at least `HEARTBEAT_WARN` if Unicode-sensitive paths or captions are involved.
- Use at least `HEARTBEAT_WARN` if Python/VBA collision review is incomplete.
- Use `HEARTBEAT_BLOCKED` if live workbook unsaved state is unknown, overwrite would touch a live session, COM attach fails, reinjection fails, compile fails, references are broken, workbook-qualified `Application.Run` fails, or same-workbook write collision is unresolved.
