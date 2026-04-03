# Prompt Recipes

## 1) 최소 수정 패치
```text
Use $word-style-upgrade to patch this document.
Mode: patch-list-only
Preset: bilingual-kr-en-standard
Preserve all dates, figures, IDs, and table meaning.
```

## 2) 전체 교정본
```text
Use $word-style-upgrade to revise the full document.
Mode: patched-document
Preset: kr-corporate-standard
Do not change facts.
```

## 3) 계약 검토형
```text
Use $word-style-upgrade in kr-contract-review preset.
Return audit-only first.
Flag numeric alignment and any AMBER layout checks.
```

## 4) 임원 보고형
```text
Use $word-style-upgrade in kr-executive-report preset.
Return patch-list-only.
Keep sentences compact and executive-ready.
```

## 5) 스타일 가이드만 추출
```text
Use $word-style-upgrade in style-spec-only mode.
Target: Korean internal Word standard with English in Aptos and Korean in 맑은 고딕.
```
