---
name: design-upgrade-loop
description: Review design-heavy content such as webpages, dashboards, and document-style screens. Use when you want Codex to web-search current references, propose at least 3 transferable design elements, patch concrete files or sections, and verify the upgrade with a scored review loop.
---

# Design Upgrade Loop

## Purpose
Turn a rough or outdated design into a reviewable upgrade loop:
1. inspect the current state,
2. web-search current references,
3. synthesize at least 3 design elements that fit the target,
4. map them to exact patch points,
5. apply the changes,
6. verify the result with artifacts and a scorecard.

Keep the work original. Do not clone any single reference.

## When to use
Use this skill when the user asks for any of the following:
- improve the design of a webpage, dashboard, admin screen, landing page, report page, or document-style UI
- benchmark current design references and propose design direction
- polish spacing, hierarchy, typography, cards, tables, filters, KPI areas, status colors, or executive-readability
- patch the implementation and then review whether the design actually improved

## When not to use
Do not use this skill when:
- the task is logo creation, illustration generation, or brand identity from scratch
- there is no editable source and no screenshot or export to inspect
- the user only wants abstract inspiration with no review or patch intent

If the target is a binary-only artifact (for example, a locked `.docx`, exported PDF, or image-only deck) and there is no editable source, switch to **patch-plan-only mode** and clearly mark the limitation.

## Required inputs
Collect these before changing anything:
- target surface type: `webpage` | `dashboard` | `document-surface`
- editable source paths, component paths, or document source files
- at least one screenshot, render, or export of the current state
- constraints: brand, audience, tone, accessibility, device priorities, no-go items
- optional: design system, token files, component library, Figma selection, MCP tools, Playwright/browser access

## Required outputs
Always produce all of the following:
1. **Baseline diagnosis**
2. **Reference set** with at least 3 current external references
3. **Transferable element set** with at least 3 design elements
4. **Patch map** with exact files, components, pages, or sections to change
5. **Applied change summary** (or patch-plan-only summary if editing is blocked)
6. **Validation scorecard** in JSON and a human-readable markdown summary

## Core rules
- Read `AGENTS.md` before doing the task.
- Reuse the repo’s existing design system and components before creating new primitives.
- Search the web before proposing a redesign. Use current references, not stale memory.
- Never copy one source literally. Synthesize patterns across multiple references.
- Prefer the smallest high-leverage patch set first.
- If the task includes file edits, create a git checkpoint or equivalent reversible state before broad changes.
- For large redesigns, patch one layer at a time: hierarchy -> typography/spacing -> components -> polish.
- For any risky or wide-impact change, present the patch map before large edits.

## Reference routing
Use `references/source-routing.md` to decide where to search first.

Default routing:
- **Webpage / landing / showcase UI**: start with Awwwards, then DesignRush, then Web Design Awards
- **Dashboard / control tower / data-heavy UI**: start with DesignRush and Web Design Awards, then use Awwwards selectively for restraint-safe visual ideas
- **Document-surface / report-like UI / word-style content**: use DesignRush and conservative enterprise examples first; prioritize layout rhythm, typography, tables, section cadence, whitespace, and executive scannability over motion
- **Conservative enterprise review**: use WebAward criteria as a scoring backstop

## Workflow

### Step 0. Preflight
1. Read `AGENTS.md` and local design rules.
2. Identify the target surface type.
3. Locate editable files.
4. Confirm how the result will be inspected:
   - browser / Playwright / screenshot render for web surfaces
   - source diff + exported preview for document surfaces
5. If no editable source exists, switch to patch-plan-only mode.

### Step 1. Baseline diagnosis
Create a short baseline review covering:
- hierarchy
- typography scale
- spacing and alignment
- component consistency
- data density / readability
- navigation and filter ergonomics
- responsiveness or page cadence
- brand fit / tone

Do not jump into solutions yet. Name the current problems first.

### Step 2. External benchmark search
Search the web and collect at least 3 references that fit the task.
For each reference, log:
- URL
- why it is relevant
- which specific pattern is worth transferring
- what **not** to copy

Prefer references that match the user’s actual target:
- enterprise vs premium showcase
- dashboard vs editorial report
- dense operations UI vs light marketing site
- mobile-first vs desktop-first

### Step 3. Transferable design elements
Extract at least 3 design elements that fit the target. Use categories like:
- layout and hierarchy
- typography and spacing
- card/table/filter system
- color and surface treatment
- interaction feedback and state clarity
- executive readability / section pacing

For each element, state:
- reason
- expected benefit
- exact patch target
- implementation risk

### Step 4. Patch map
Before editing, build a concrete patch map.
Use the markdown template in `assets/design-upgrade-report-template.md`.

Minimum patch map fields:
- file or section
- current problem
- proposed change
- reference anchor
- estimated impact
- risk

### Step 5. Apply
1. Make the smallest high-leverage edits first.
2. Reuse existing components, tokens, and spacing scales.
3. Keep copy changes minimal unless copy hierarchy is part of the design issue.
4. After each meaningful round, capture a preview artifact.

### Step 6. Validate
Create `design-scorecard.json` using `assets/design-scorecard.template.json`.
Then run:

```bash
python scripts/validate_design_scorecard.py path/to/design-scorecard.json
```

Validation rules:
- all 7 metrics must be present
- each metric must be from `0.0` to `5.0`
- average score must be at least `4.0`
- no metric may be below `3.5`
- `blocking_issues` must be empty for PASS

For web surfaces, also inspect the result at multiple breakpoints if browser automation is available.
For document surfaces, inspect page rhythm, heading cadence, table readability, and export legibility.

### Step 7. Iterate if needed
If validation fails:
1. identify the weakest metric,
2. make one focused improvement,
3. regenerate artifacts,
4. rerun the validator.

Do not stop at “acceptable” if the weakest metric is still below threshold.

## Output contract
Create a reviewable artifact bundle like this:

```text
artifacts/design-upgrade/<timestamp>/
  design-upgrade-report.md
  design-scorecard.json
  before.png                # if available
  after.png                 # if available
  refs.md
```

The final response must include:
- 1-paragraph summary
- 3+ references used
- 3+ design elements proposed
- exact files/sections patched
- validation result
- remaining risks

## Browser and MCP guidance
If available, prefer these tools in this order:
1. browser automation or Playwright for screenshot comparison and breakpoint checks
2. Figma MCP when the task starts from a Figma selection or needs design-context extraction
3. browser-only screenshot capture when full automation is unavailable

If no browser tooling is available, continue with static artifact review and mark the limitation.

## Patch-plan-only mode
Use this mode when editing is blocked.
In this mode, still deliver:
- baseline diagnosis
- 3+ current references
- 3+ transferable elements
- exact patch map
- validation plan

Do **not** claim the redesign was applied.

## Safety
- Never remove large sections, rewrite design systems, or replace the visual language wholesale without a reviewable patch map.
- Keep changes reversible.
- Avoid introducing licensed assets, copied illustrations, or brand-conflicting motifs.
- For external references, cite URLs in the artifact report.
- Do not expose secrets, tokens, private URLs, or internal-only screenshots in the reference log.

## Completion criteria
The task is complete only when all of the following are true:
- at least 3 external references were logged
- at least 3 transferable design elements were proposed
- exact patch points were named
- changes were applied or patch-plan-only mode was declared
- the validation scorecard exists
- the validator passes, or the response clearly states why it does not
