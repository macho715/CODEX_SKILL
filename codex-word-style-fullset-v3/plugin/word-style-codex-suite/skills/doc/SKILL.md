---
name: "doc"
description: "Use when the task involves reading, creating, or editing `.docx` documents, especially when formatting or layout fidelity matters; prefer `python-docx` plus the bundled `scripts/render_docx.py` for visual checks."
---


# DOCX Skill

## Trigger
- Read or review DOCX content where layout matters (tables, diagrams, pagination).
- Create or edit DOCX files with professional formatting.
- Validate visual layout before delivery.

## Non-trigger
- Do not default to `python-docx` rewrite for existing complex `.docx` files that contain media, headers, footers, fields, TOC, comments, or section-dependent pagination unless package-preservation checks pass.
- Do not claim TOC/page-number refresh is complete if the saved file has not been reopened or otherwise verified.
- Do not keep retrying unstable Word COM automation without cleaning up hidden Word processes first.

## Steps
1. Prefer visual review (layout, tables, diagrams).
   - If `soffice` and `pdftoppm` are available, convert DOCX -> PDF -> PNGs.
   - Or use `scripts/render_docx.py` (requires `pdf2image` and Poppler).
   - If these tools are missing, install them or ask the user to review rendered pages locally.
2. Classify the document mutation path before editing.
   - OpenXML-safe: new docs, text-only normalization, simple structure changes, package-preservation checks available.
   - Word-engine-required: TOC update, page-number field refresh, section/page behavior, repeated header validation, actual pagination-dependent fixes.
3. For existing complex `.docx`, record pre-mutation integrity signals.
   - source hash
   - package counts for entries/media/headers/footers
   - section count
   - presence of fields/TOC when relevant
4. Use `python-docx` only when the mutation is OpenXML-safe.
   - If package counts change unexpectedly after save, discard the artifact and report failure.
5. Use Word automation for Word-engine-required operations.
   - Kill hidden `WINWORD.EXE /Automation -Embedding` processes before starting.
   - Set `BackgroundSave` off where available.
   - Save, then verify the saved file state before claiming success.
6. If Word automation is unstable, stop and hand off to a manual Word step instead of guessing.
7. After each meaningful change, re-render and inspect the pages when the toolchain is available.
8. Keep intermediate outputs organized and clean up after final approval.

## Temp and output conventions
- Use `tmp/docs/` for intermediate files; delete when done.
- Write final artifacts under `output/doc/` when working in this repo.
- Keep filenames stable and descriptive.

## Dependencies (install if missing)
Prefer `uv` for dependency management.

Python packages:
```
uv pip install python-docx pdf2image
```
If `uv` is unavailable:
```
python3 -m pip install python-docx pdf2image
```
System tools (for rendering):
```
# macOS (Homebrew)
brew install libreoffice poppler

# Ubuntu/Debian
sudo apt-get install -y libreoffice poppler-utils
```

If installation isn't possible in this environment, tell the user which dependency is missing and how to install it locally.

## Environment
No required environment variables.

## Rendering commands
DOCX -> PDF:
```
soffice -env:UserInstallation=file:///tmp/lo_profile_$$ --headless --convert-to pdf --outdir $OUTDIR $INPUT_DOCX
```

PDF -> PNGs:
```
pdftoppm -png $OUTDIR/$BASENAME.pdf $OUTDIR/$BASENAME
```

Bundled helper:
```
python3 scripts/render_docx.py /path/to/file.docx --output_dir /tmp/docx_pages
```

## Quality expectations
- Deliver a client-ready document: consistent typography, spacing, margins, and clear hierarchy.
- Avoid formatting defects: clipped/overlapping text, broken tables, unreadable characters, or default-template styling.
- Charts, tables, and visuals must be legible in rendered pages with correct alignment.
- Use ASCII hyphens only. Avoid U+2011 (non-breaking hyphen) and other Unicode dashes.
- Citations and references must be human-readable; never leave tool tokens or placeholder strings.

## Verification
- Re-render and inspect every page at 100% zoom before final delivery.
- Fix any spacing, alignment, or pagination issues and repeat the render loop.
- Confirm there are no leftovers (temp files, duplicate renders) unless the user asks to keep them.
- For existing `.docx`, compare post-save hash/package counts against the preflight record.
- If TOC/page-number/field refresh was part of the task, verify the saved file result rather than only the in-memory Word view.
- If hidden Word automation processes remain after the run, treat the run as unstable and do not report completion.
