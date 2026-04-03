# Output Contract

## Core rules

- Default to Markdown output only.
- Preserve the original structure unless the user explicitly allows structural
  change.
- Do not change controlled items such as numbers, dates, names, contract
  details, units, quantities, periods, or conditions.
- Do not invent page numbers or section labels. Reuse only labels that are
  present in the source.
- If the user does not choose a mode, return `[정리본]` followed by `[검수 메모]`.

## Default format

```md
[정리본]
...cleaned full text...

[검수 메모]
- 의미 변경 가능성이 있어 원문 유지
- 오타로 보이지만 근거 없어 유지
- 숫자/고유명사/계약정보라서 손대지 않음
```

## `[패치 목록]` format

Use only changed lines or phrases.

```md
[Page X]
- 원문: ...
- 수정안: ...
- 사유: 문체 정리 / 번역투 완화 / 명사형 압축 완화 / 띄어쓰기 정리 / 원문 유지 우선
```

If the source has no page markers, replace `Page X` with a real heading or
section label from the source.

## `[나란히 비교]` format

Use either a Markdown table or repeated blocks.

```md
| 원문 | 수정문 |
| --- | --- |
| ... | ... |
```

or

```md
[항목]
- 원문: ...
- 수정문: ...
```

## `[본문만]` format

Return only the cleaned text. Do not add `[검수 메모]`, explanations, or extra
headings beyond the original document structure.

## Trimming rules

- Do not omit content in `[전체 정리]` or default mode.
- In `[패치 목록]`, include only changed items.
- In `[검수 메모]`, include only short notes about ambiguity, controlled items,
  or wording intentionally left unchanged.

## Integrity check

Before final output, confirm all of the following:
- no new facts were added
- no controlled item changed
- no page or section label was invented
- the selected output mode matches the user's request
- the text is more natural without changing the meaning
