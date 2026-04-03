---
name: pagewise-translation-patch
description: Refine Korean business and approval documents into a natural standard internal style without changing facts, numbers, dates, proper nouns, contracts, conditions, tables, or structure. Use for whole-document cleanup, patch lists, side-by-side comparison, or pagewise wording fixes.
---

# Pagewise Translation Patch

## trigger

Use this skill when the user wants Korean business text cleaned up for approval, reporting, or internal communication while preserving the original facts and structure.

Typical requests:
- 표준 사내 문체로 다듬기
- 결재/보고 문서 톤으로 정리하기
- 오래된 상신문 표현 줄이기
- 번역투나 비문만 고치기
- 패치 목록만 출력하기
- 원문과 수정문을 나란히 비교하기
- pagewise patch
- slide-by-slide wording fix

When page or slide markers exist, preserve them and group edits by that unit if the user asks for pagewise or patch-style output.

## non-trigger

Do not use this skill when the user wants:
- a full translation into another language
- new facts, background, interpretation, or conclusions
- a summary instead of a cleanup
- structural reorganization without explicit permission
- certified legal wording or regulatory filing language
- table data rewritten, condensed, or recalculated

## defaults

Unless the user says otherwise, use these defaults:
- whole document
- structure preserved
- tables preserved
- numbers, dates, proper nouns, contract information, units, and conditions preserved
- only Korean prose is adjusted
- output format: `[정리본]` then `[검수 메모]`
- Markdown output only unless the user explicitly asks for another file format

## controlled items

Treat the following as controlled items and do not change them without explicit evidence in the source:
- numbers, dates, time, currency, units, rates, quantities, and periods
- contract names, contract numbers, amendment numbers, and document numbers
- company names, site names, project names, product names, and codes
- item names, table headers, and attachment names
- contractual or commercial conditions

If something looks like a typo but cannot be proven from the source, keep it and mention it in `[검수 메모]`.

## style target

Target style:
- polite but not overly ceremonial internal report tone
- short and clear sentences
- fact-first, non-emotional wording
- language that helps a decision-maker scan quickly
- no hype, decoration, or promotional phrasing
- no unnecessary legal stiffness

Preferred moves when they fit the context:
- split long sentences so one sentence carries one main point
- replace dated approval-language with natural modern business wording
- unpack noun stacks so the actor and action are clear
- normalize spacing and notation without changing the underlying values
- reduce translationese and awkward literal phrasing

Examples of preferred normalization:
- `검토후` -> `검토 후`
- `현시점` -> `현 시점`
- `변경전 / 변경후` -> `변경 전 / 변경 후`
- `운영중` -> `운영 중`
- `현장내` -> `현장 내`
- `불가피 함` -> `불가피함`
- `추진코자 하오니` -> `추진하고자 하오니`
- `승인하여 주시기 바랍니다` -> `승인 부탁드립니다`
- `~로 인하여` -> `~로`, `~때문에`, `~에 따라`
- `~함에 따라서` -> `~에 따라`, `~로 인해`

Do not apply these mechanically. Preserve the original meaning.

## steps

1. Read the full source once before rewriting anything.
2. Mark the document structure: title, headings, numbering, bullets, tables, attachments, and page or slide markers.
3. Extract controlled items that must not change.
4. Rewrite only the Korean sentences.
   - remove archaic approval-language and translationese
   - split long sentences naturally
   - keep one core judgment per sentence when possible
   - keep the tone formal enough for approval and reporting
5. Clean spacing and notation only when the underlying value or name stays the same.
6. Run the final self-check.
   - no new information added
   - no controlled item changed
   - no structure damaged
   - tone is natural, concise, and still formal
7. Emit the requested output mode. If the user did not specify a mode, emit `[정리본]` and `[검수 메모]`.

## output modes

### `[전체 정리]`

Return the full cleaned document with the original structure preserved, followed by `[검수 메모]`.

### `[패치 목록]`

Return only changed sentences or phrases. Use this format:

```md
[Page X]
- 원문: ...
- 수정안: ...
- 사유: 문체 정리 / 번역투 완화 / 명사형 압축 완화 / 띄어쓰기 정리 / 원문 유지 우선
```

If the source has no real page markers, use the closest stable section label instead of inventing a page number.

### `[나란히 비교]`

Return a two-column Markdown table or a repeated block format with `원문` and `수정문`. Preserve the original order and structure.

### `[본문만]`

Return only the cleaned final text. Do not add `[검수 메모]`.

## mandatory rules

### 1) No information outside the source

Do not add facts, explanations, evaluations, conclusions, or missing context.

### 2) Preserve controlled items

Do not change numbers, dates, currency, units, names, codes, contract information, quantities, periods, or conditions.

### 3) Preserve structure

Do not change the title hierarchy, numbering, bullets, table titles, table structure, or attachment list structure unless the user explicitly allows structural changes.

### 4) Hallucination guard

If uncertain, keep the original wording. Conservative retention is better than speculative cleanup.

### 5) Separate inspection note

Create `[검수 메모]` after the cleaned text when the mode requires it. Only note items that were intentionally preserved because of ambiguity, controlled data, or possible meaning-shift risk.

## verification

Pass only when all of the following are true:
- the output adds no information that was not in the source
- all numbers, dates, proper nouns, contract data, units, quantities, periods, and conditions are unchanged
- the document structure is preserved
- the wording is more natural and readable for internal approval and report use
- the tone stays formal, factual, and not overly stiff or casual
- the selected output mode is followed exactly
- `[검수 메모]` contains only short risk notes, not new content

## references to load on demand

- `references/output-contract.md`
- `references/examples.md`
- `assets/review-request-template.md`
- `assets/termbase-template.csv`
