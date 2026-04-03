# First Response Prompt Set

Assumption: this capture uses independent Codex subagents with `fork_context=false` as the closest available proxy for a fresh session first response.

## Acceptance Contract

- `excel-xlsm-contract-ops` appears as the first gate
- the first response states a `risk class` or equivalent risk decision
- the first response states a downstream owner: `excel-vba`, `excel-professional-formatting`, or `blocked`
- the next stage is explicit
- contract-sensitive work is not routed to formatting-only
- live workbook and unsaved-edit risk are not glossed over

## Prompt 1: High-Risk Reinjection

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-vba](C:\Users\SAMSUNG\.codex\skills\excel-vba\SKILL.md)

Existing `.xlsm`. VBA reinjection required. Workbook path contains Korean characters. Delivery is not complete until save-close-reopen and workbook-qualified `Application.Run` pass on the actual target path. Return only the first response you would give before implementation details.
```

Expected owner: `excel-vba`

## Prompt 2: Formatting-Only Release

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-professional-formatting](C:\Users\SAMSUNG\.codex\skills\excel-professional-formatting\SKILL.md)

This is an existing macro-enabled workbook. The request is only to improve readability, print layout, and professional formatting. Do not touch formulas, named ranges, controls, or VBA. Return only the first response you would give before implementation details.
```

Expected owner: `excel-professional-formatting`

## Prompt 3: Formatting Escalation To VBA

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-vba](C:\Users\SAMSUNG\.codex\skills\excel-vba\SKILL.md)
[$excel-professional-formatting](C:\Users\SAMSUNG\.codex\skills\excel-professional-formatting\SKILL.md)

The workbook was visually cleaned already, but now the request includes button placement fixes, shape drift, and `OnAction` rebinding. Return only the first response you would give before implementation details.
```

Expected owner: `excel-vba`

## Prompt 4: Python Plus VBA Collision Risk

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-vba](C:\Users\SAMSUNG\.codex\skills\excel-vba\SKILL.md)

Python generated part of this workbook, and now VBA changes will touch named ranges, `ListObject` names, and macro entrypoints in the same file. Return only the first response you would give before implementation details.
```

Expected owner: `excel-vba`

## Prompt 5: Live Workbook With Unsaved Risk

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-professional-formatting](C:\Users\SAMSUNG\.codex\skills\excel-professional-formatting\SKILL.md)
[$excel-vba](C:\Users\SAMSUNG\.codex\skills\excel-vba\SKILL.md)

The user wants the print layout polished, but the workbook may already be open in Excel and the unsaved state is unclear. Return only the first response you would give before implementation details.
```

Expected owner: `blocked` or `excel-professional-formatting` only after explicit live-state handling
