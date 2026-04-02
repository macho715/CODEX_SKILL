# Mermaid Guidelines

Generate one Mermaid block per managed file.

## Required Diagram Shape
- `README.md`: high-level flowchart from repo inspection to document set generation.
- `PLAN.md`: evidence-to-plan flowchart.
- `LAYOUT.md`: repository structure flowchart.
- `ARCHITECTURE.md`: observed component/config relationship flowchart.
- `CHANGELOG.md`: timeline of observed commits or refresh events.
- `GUIDE.md`: sequence diagram for the documentation workflow.

## Diagram Rules
- Use inspected project paths, commands, and observed entities as labels.
- Keep labels short and derived from real files.
- If evidence is too weak for a detailed diagram, emit a smaller truthful diagram rather than a fabricated one.
