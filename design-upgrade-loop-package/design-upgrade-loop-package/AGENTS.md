# AGENTS.md

## Design task routing for Codex

When the user asks for design benchmarking, dashboard polish, webpage cleanup, report-page refinement, or visual QA:

1. Prefer the `design-upgrade-loop` skill.
2. Require at least one current screenshot or render and editable source paths before editing.
3. Search current external references before proposing a redesign.
4. Use at least 3 external references and at least 2 different source families.
5. Do not clone a single reference.
6. Produce a patch map before wide-impact edits.
7. After patching, create a scorecard JSON and run the validator script.
8. If the task is binary-only and not editable, switch to patch-plan-only mode and say so explicitly.
9. Keep design edits reversible and scoped.
10. For browser-verifiable surfaces, inspect the result at multiple breakpoints when tooling is available.
