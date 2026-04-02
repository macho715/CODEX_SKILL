## OpenSpace merge rules

- Treat existing repo skills as the primary orchestration layer.
- Before improvising on an unfamiliar or tool-heavy task, use `skill-discovery` or `openspace-bridge`.
- If a reusable local or imported skill is enough, follow it locally.
- If there is a capability gap, repeated failure, or a complex multi-step execution need, use `delegate-task` / `execute_task`.
- After drafting, always run `analysis-verifier`.
- Allow at most one replan loop after a FAIL verdict.
- If 3 or more viable options exist, write `04_options.json` and use `scenario-scorer`.
- Keep output files in the run directory provided by the launcher.
