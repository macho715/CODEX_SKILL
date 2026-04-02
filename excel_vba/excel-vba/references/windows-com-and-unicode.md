# Windows COM and Unicode

Read this file when the task includes `.xlsm` generation, VBA module import or injection, Excel COM automation, PowerShell-driven Excel execution, workbook buttons, or non-ASCII paths, sheet names, captions, or filenames.

## Why this file exists
- Excel COM automation can succeed at file creation but still fail at VBA execution.
- VBA import paths, PowerShell encoding, and workbook-qualified macro calls are common failure points.
- Non-ASCII workbook paths and UI captions are fragile unless you design for them explicitly.

## Mandatory rules
- Treat `file created` and `macro runnable` as separate checks.
- If you inject or import VBA, validate the actual entry macro by running it after save and reopen.
- Prefer workbook-qualified `Application.Run`, for example `'<WorkbookName>.xlsm'!RunEntry`.
- Keep VBA source ASCII-first when practical.
- When you need Korean or other non-ASCII captions in VBA, prefer `ChrW(&HXXXX)` sequences over raw literals.
- Verify every `ChrW` hex literal uses the `&H` prefix. A missing `H` can become a hidden syntax error.
- For PowerShell-generated Korean filenames or captions, prefer explicit UTF-8 BOM handling or codepoint assembly rather than assuming console encoding is safe.
- Prefer the bundled script [../scripts/build-reopen-smoketest.ps1](../scripts/build-reopen-smoketest.ps1) when you need a repeatable `build -> reopen -> smoke-test` path.

## Import and execution sequence
1. Open the source workbook.
2. Save a macro-enabled copy with `SaveAs(..., 52)` or the required macro format.
3. Inject or import the VBA module.
4. Save the workbook.
5. Close the workbook.
6. Reopen the generated workbook.
7. Run the entry macro through workbook-qualified `Application.Run`.
8. Save again only after the smoke test passes.

Do not assume `VBComponents.AddFromString` or `VBComponents.Import` is enough by itself. The workbook can still fail at the first real macro call.

## PowerShell guidance
- Do not use Bash-style heredoc syntax in Windows PowerShell.
- Prefer one of these paths:
- a `.ps1` file
- a PowerShell here-string piped to Python
- a short `python -c` command
- If you patch VBA from PowerShell, avoid mixing quoting-heavy command strings and non-ASCII literals unless you have a reason.

## Workbook button rules
- Prefer Forms controls over ActiveX unless the user specifically needs ActiveX behavior.
- After creating buttons, verify:
- shape count
- button names
- button captions
- `OnAction` target
- a real click-equivalent macro call through `Application.Run`

## Minimum smoke test
Run these checks before declaring success:
1. workbook opens
2. entry macro runs without compile or syntax error
3. `Result`, `Validation_Errors`, and `LOG` exist and are populated as expected
4. expected conditional formatting rules exist
5. expected buttons or shapes exist
6. at least one button macro works
7. save, close, and reopen still work

## Failure interpretation
- If `Application.Run` fails immediately after injection, do not assume the business logic is wrong.
- First check syntax and encoding issues in the injected VBA module.
- Then check workbook qualification in the macro call.
- Then retry after save, close, and reopen.
- Only after those checks should you debug the business logic.
