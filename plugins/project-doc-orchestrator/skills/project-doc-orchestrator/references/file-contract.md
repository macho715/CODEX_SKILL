# Managed File Contract

## Managed Markers
- `<!-- PROJECT-DOC-ORCHESTRATOR:MANAGED -->`
- `<!-- PROJECT-DOC-ORCHESTRATOR:MANAGED-START -->`
- `<!-- PROJECT-DOC-ORCHESTRATOR:MANAGED-END -->`
- `<!-- PROJECT-DOC-ORCHESTRATOR:PRESERVE-START -->`
- `<!-- PROJECT-DOC-ORCHESTRATOR:PRESERVE-END -->`

## Rules
- Treat files with the managed marker as tool-owned.
- Rewrite only the managed region during refresh.
- Keep the preserve block intact across refreshes.
- Treat files without the managed marker as unmanaged.
- Refuse to overwrite unmanaged files unless the user explicitly approved it.
- Refuse to delete old managed files unless the user explicitly approved it.
- Do not treat managed docs as input evidence when source files, manifests, scripts, or user-authored docs are available.
- After refresh, each managed file must still contain both the managed markers and the preserve markers.
