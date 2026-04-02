# Four-Agent Contract

The fixed topology is:

- `pipeline-coordinator`
- `orchestrate-analysis`
- `scenario-scorer`
- `analysis-verifier`

When the caller is an `mstack-*` skill, MStack keeps SDLC ownership and the
coordinator acts only as an analysis decision gate.

Hard rules:

- the coordinator owns final merge only
- scoring and verification do not start before analysis artifacts exist
- intermediate artifacts must not claim final merge ownership
- missing execution output must not be fabricated
- the coordinator must not absorb `review`, `qa`, `ship`, or `retro`
- the coordinator returns a `Decision Packet` for downstream MStack stages
