# Evidence Rule

Apply this rule before every write.

## Must
- Must inspect real manifests, scripts, config files, and existing docs before writing claims about setup, architecture, layout, commands, progress, or history.
- Must inspect the actual script files and actual documentation files relevant to the target document immediately before writing or patching that document.
- Each parallel lane must re-read the specific scripts, manifests, and docs relevant to its owned targets immediately before patching.
- Must use the current repository state, not a stock project template.
- Must prefer source files, manifests, scripts, and user-authored docs over previously generated managed docs when gathering evidence.
- Must say when evidence is missing or weak.
- Must derive Mermaid diagrams from inspected files and observed relationships.

## Must Not
- Must not invent commands that were not seen in manifests or runnable scripts.
- Must not invent components, data flows, or environments that are not supported by inspected files.
- Must not rely on another lane's earlier inspection as sufficient evidence for a write.
- Must not treat generated outputs under `docs/project-docs` as the primary source of truth for repo behavior.
- Must not convert assumptions into facts.

## Minimum Evidence Per Document
- `README.md`: inspect manifests, scripts, and any existing root/docs Markdown.
- `PLAN.md`: inspect git activity, TODO/FIXME markers, and current docs/scripts.
- `LAYOUT.md`: inspect the live directory tree and relevant top-level files.
- `ARCHITECTURE.md`: inspect manifests, source/script layout, and architecture-related docs if present.
- `CHANGELOG.md`: inspect git history and current working tree state.
- `GUIDE.md`: inspect runnable scripts, manifest commands, and existing usage docs.
