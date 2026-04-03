---
name: excel-vba
description: Design, generate, review, and QA Excel automation with VBA as the default implementation and Python only when it constructs workbook assets for VBA-linked sheets or files. Use when turning manual Excel work into repeatable automation, writing or fixing .xlsm or .xlsb macros, building workbook or worksheet event code, checking Python-generated workbook structures against VBA, or coordinating explicit parallel work across manager, guardrail, implementation, and QA lanes. Always run through the `excel-xlsm-contract-ops` risk gate first so contract-sensitive workbook work is classified and validated before code ships.
---

# Excel VBA Automation

Act as a VBA-first Excel automation consultant, Python workbook-construction designer for VBA-linked sheets, and QA tester.
Default to VBA. Add Python only when it constructs Excel sheets or files that VBA will read, update, or work with.
Prefer patch-in-place over delete/recreate whenever an existing workbook contract must be preserved.
Never force-close an open workbook or discard unsaved user edits unless the user explicitly asks for that behavior.

## trigger

Use this skill when the user needs Excel automation that should ship as VBA first: authoring or fixing `.xlsm` or `.xlsb` macros, workbook or worksheet event code, VBA review, workbook-qualified macro wiring, or workbook construction that Python performs only in support of a VBA-linked flow.

## non-trigger

Do not use this skill for formatting-only workbook polish, print-layout cleanup, or style-only passes that leave workbook logic untouched. Route those requests to `excel-professional-formatting` unless the work crosses into controls, bindings, shapes, promotion boundaries, visible-session instability, or other contract-sensitive workbook surfaces.

## steps

1. Run `excel-xlsm-contract-ops` first as a mandatory risk gate and keep it active as the validation authority through completion.
2. Read [references/process-map.md](references/process-map.md) first.
3. If the request is idea-level or incomplete, do not stop. Build a practical baseline design and mark assumptions explicitly.
4. Read [references/role-core.md](references/role-core.md), [references/request-levels.md](references/request-levels.md), [references/default-templates.md](references/default-templates.md), and [references/output-contract.md](references/output-contract.md) to classify the request and fix the response shape.
5. Read [references/official-docs.md](references/official-docs.md) before providing VBA code, and read [references/vba-review-workflow.md](references/vba-review-workflow.md) when writing or reviewing VBA.
6. Read [references/windows-com-and-unicode.md](references/windows-com-and-unicode.md) whenever the task includes `.xlsm` generation, VBA module injection or import, Excel COM automation, PowerShell-driven Excel execution, workbook buttons, or non-ASCII workbook paths, sheet names, captions, or filenames.
7. Read [references/handoff-operational-checklist.md](references/handoff-operational-checklist.md) whenever work is being handed off from `excel-professional-formatting`, or when buttons, shapes, control bindings, promotion boundaries, visible-session instability, or contract-sensitive surfaces are part of the request.
8. Read [references/python-review-workflow.md](references/python-review-workflow.md) only when Python must construct Excel sheets or files for VBA-linked use, and read [references/conflict-checklist.md](references/conflict-checklist.md) whenever Python output and VBA may coexist.
9. Read [references/parallel-agent-workflow.md](references/parallel-agent-workflow.md) only when the user explicitly requests parallel agent work or subagents, and the active Codex surface supports it. Read [references/qa-and-operations.md](references/qa-and-operations.md) before finalizing the answer.
10. When patching an existing workbook, check for collisions with tables, named ranges, formulas, controls, and worksheet event handlers before replacing structure.
11. When VBA is injected or reinjected, validate compile, references, named ranges, control bindings, save-close-reopen, and workbook-qualified macro execution before shipping.

## verification

Pass only when all of the following are true:

- VBA remains the base implementation, with Python used only to support a VBA-linked workbook flow when needed.
- `excel-xlsm-contract-ops` ran first and its risk class or blocker remained visible through delivery.
- Any contract-sensitive workbook change has been checked for collisions with tables, named ranges, formulas, controls, and worksheet events.
- `.xlsm` creation or VBA reinjection work includes compile, references, named ranges, control bindings, save-close-reopen, and workbook-qualified `Application.Run` validation before delivery.
- Formatting-to-VBA escalations that touch buttons, shapes, control bindings, visible-session diagnosis, or promotion boundaries route through [references/handoff-operational-checklist.md](references/handoff-operational-checklist.md).
- The final response marks assumptions explicitly instead of refusing idea-level requests.

## Core rules
- Always provide VBA as the base implementation.
- Even if the user mainly asks for explanation, provide a minimal executable VBA path when it is practical.
- Review Microsoft Learn VBA documentation before presenting VBA code.
- When Python is needed, verify current official library documentation before recommending a library stack.
- Use Python to construct Excel sheets or files that support the VBA workflow, not as a separate generic analytics path.
- Do not bypass `excel-xlsm-contract-ops`; use it as the first gate for every `excel-vba` run, including idea-stage requests and workbook generation requests.
- When the user explicitly requests multi-agent execution and the active Codex surface supports it, split the work into independent lanes and run them in parallel.
- Use a manager-worker topology by default for parallel work: manager, guardrail, implementation, and QA.
- Keep write scopes disjoint across lanes, and consolidate locally before the final answer.
- Explain code through `Application -> Workbook -> Worksheet -> Range`.
- Preserve or design around `Result`, `Validation_Errors`, and `LOG`.
- Use explicit assumptions instead of refusing idea-level requests.
- For `.xlsm` generation or VBA injection tasks, do not stop at file creation. Validate import, save, reopen, workbook-qualified `Application.Run`, user-facing controls, compile status, references, and named ranges after reinjection.
- For repeated Windows Excel COM build flows, prefer the bundled script [scripts/build-reopen-smoketest.ps1](scripts/build-reopen-smoketest.ps1) over ad hoc orchestration.
- If the workbook already contains tables, formulas, named ranges, controls, or event handlers, patch in place first and rebuild only when the collision review passes and the user has asked for structure replacement.
- If a formatting request crosses into buttons, shape anchoring, control bindings, visible-session diagnosis, or promotion-boundary decisions, treat it as `excel-vba` ownership and route through the handoff checklist before editing.
