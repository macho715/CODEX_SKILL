---
name: word-style-upgrade
description: Audit and patch Korean or bilingual Word-style business documents into a professional standard with English in Aptos, Korean in 맑은 고딕, left-aligned body text, controlled spacing, clear heading hierarchy, disciplined tables, and patch-list-only or full-document outputs without changing facts.
---

# Word Style Upgrade

## Purpose
이 skill은 한글 문서 또는 KR/EN 혼합 문서를 **프로 Word 문서 표준**으로 정규화하기 위한 것이다.

핵심 목적은 다음 4가지다.
1. 사실을 바꾸지 않고 문서 구조를 정돈한다.
2. 스타일·문단·표·접근성 규칙을 일관되게 적용한다.
3. layout 확인이 불가능한 항목은 `AMBER`로 분리한다.
4. 사용자가 원하는 경우 patch-list-only, audit-only, patched-document, style-spec-only 중 하나로 결과를 낸다.

## Trigger
다음 요청에서 사용한다.
- “워드 문서처럼 다시 다듬어”
- “표/단락/스타일 다시 정리해”
- “patch-list-only로 달라”
- “결재문/보고서 문체만 정리해”
- “한글 문서 서식 표준으로 맞춰”
- “영문은 Aptos, 한글은 맑은 고딕으로 기준 잡아”
- “KR/EN Word 스타일 가이드로 패치해”

## Non-trigger
다음 작업이 중심이면 이 skill만으로 처리하지 않는다.
- 법률 해석, 규정 판단, 계약 리스크 판정이 주업무일 때
- OCR 자체가 불가능한 이미지 전용 원본만 있을 때
- PowerPoint 또는 spreadsheet formatting이 본업무일 때
- 새로운 전략 보고서를 0부터 작성해야 할 때

## Trusted source selection
기존 `.docx`를 실제로 수정하려면 먼저 mutable source path를 1개만 고른다.

- 같은 파일명이 `Downloads`, `Desktop`, `OneDrive` 등에 여러 개 있으면 size, hash, package counts를 먼저 비교한다.
- 작업 복사본이 로컬 workspace에 있으면 그 파일을 source of truth로 우선한다.
- `Desktop/OneDrive`는 배포본일 수 있으므로, 로컬 작업 복사본이 따로 있으면 mutation source로 쓰지 않는다.
- source가 갈라져 있거나 partial artifact가 섞여 있으면 수정 전에 멈추고 기준 파일을 다시 정한다.

## Document class split
기존 Word 문서를 수정할 때는 먼저 어떤 엔진이 필요한지 분류한다.

### OpenXML-safe
- patch-list-only
- style-spec-only
- text-only normalization
- 단순 heading/caption/table wording 수정
- package-preservation check가 가능한 제한적 구조 수정

### Word-engine-required
- TOC update
- page-number field refresh
- section/page behavior 확인
- repeated header / orphan-header 검증
- 실제 pagination 결과에 의존하는 수정
- footer/header field 결과 업데이트

Word-engine-required 작업은 Word field/layout engine이 필요하므로, 결과를 OpenXML만으로 확정하지 않는다.

## Inputs
허용 입력:
- `.docx`에서 추출한 텍스트
- `.md`, `.txt`, `.html`
- pasted text
- 기존 사내 템플릿 규칙
- 사용자 지정 스타일 세트

선택 입력:
- output mode: `audit-only`, `patch-list-only`, `patched-document`, `style-spec-only`
- preset: `bilingual-kr-en-standard`, `kr-corporate-standard`, `kr-executive-report`, `kr-contract-review`, `table-heavy-annex`
- preserve markers: heading 번호, clause 번호, annex ID, table ID, ref ID
- template priority: `strict-template`, `template-preferred`, `guide-preferred`

## Mandatory references
작업 시작 전에 아래 중 해당 파일을 먼저 읽는다.

- KR 또는 KR/EN 혼합 문서: `assets/kr-pro-style-set.md`
- profile 선택이 필요한 경우: `assets/style-profiles.md`
- 출력 형식이 필요한 경우: `assets/output-templates.md`
- 표가 많은 문서: `references/table-and-accessibility-policy.md`
- 기본 원칙과 QA 근거가 필요할 때: `references/word-style-reference.md`
- existing `.docx`를 실제로 수정하거나 pagination/field를 다룰 때: installed `doc` skill

## Output modes
정확히 1개만 선택한다.

| Mode | Use when | Output |
|---|---|---|
| `audit-only` | 검토 결과와 권고만 필요 | Findings table + QA gate |
| `patch-list-only` | 최소 수정만 원함 / 고위험 문서 | Before/After patch table only |
| `patched-document` | 전체 교정본이 필요 | corrected full text + QA summary |
| `style-spec-only` | 문장 수정 없이 스타일 기준만 필요 | preset + style map + table rules |

기본 선택 규칙:
1. 사용자가 patch, diff, pagewise fix, 최소 수정이라고 말하면 `patch-list-only`
2. 사용자가 “전체 다시 써”, “전체 패치본”이라고 말하면 `patched-document`
3. 검토/점검/리뷰만 원하면 `audit-only`
4. 표준안/서식안/스타일 가이드만 원하면 `style-spec-only`

## Preset selection
아래 preset 중 하나를 고른다.

| Preset | Use when | Summary |
|---|---|---|
| `bilingual-kr-en-standard` | KR/EN 혼합 문서, 기본값 | Latin=Aptos / East Asian=맑은 고딕 / body 10.50 / line 1.30 |
| `kr-corporate-standard` | 일반 사내 보고서형 | 제목1 16.00 / 제목2 13.00 / 본문 10.50 |
| `kr-executive-report` | 임원 보고형 | 제목1 15.00 / 제목2 12.50 / 표 본문 10.00 |
| `kr-contract-review` | 계약/정산 검토형 | 숫자열 우측 정렬 엄격 / 표 규율 강화 |
| `table-heavy-annex` | 부속서, schedule, 데이터 다량 | 표 구조·헤더 반복·행 분할 리스크 중심 |

선택 규칙:
- mixed-language 문서거나 사용자가 `Aptos + 맑은 고딕`을 지정하면 `bilingual-kr-en-standard`
- 일반 내부 보고서는 `kr-corporate-standard`
- 임원 보고서는 `kr-executive-report`
- 계약/정산 검토 문서는 `kr-contract-review`
- 표 중심 부속서는 `table-heavy-annex`

## Non-negotiables
1. 날짜, 숫자, 금액, 이름, 고유 ID, 조항 번호, 표 의미를 바꾸지 않는다.
2. 직접 서식처럼 보이는 표현을 텍스트로 꾸미지 말고 style intent로 정리한다.
3. 의미보다 레이아웃을 우선하지 않는다.
4. 빈 줄 여러 개로 간격을 만드는 방식을 승인하지 않는다.
5. 문단 하나에는 메시지 하나를 원칙으로 한다.
6. 표는 데이터용으로만 다룬다.
7. layout을 실제로 검증할 수 없으면 `AMBER`로 남긴다.
8. editable text가 없으면 `ZERO`로 중단한다.

## Font policy
문서의 기본 글꼴 정책은 다음과 같다.

- Latin / English: `Aptos`
- East Asian / Korean: `맑은 고딕`

실제 Word 스타일에서 가능하면 **Latin font와 East Asian font를 분리 설정**하는 방식으로 이해한다.

중요:
- plain text, Markdown, HTML export만 있는 경우에는 run-level font 적용을 확정하지 않는다.
- 이 경우 출력에는 font mapping을 style spec으로 기록하고, 실제 적용 여부는 `AMBER layout checks`에 남긴다.
- 사용자가 한글 Word 문서만 요구하면 한글 기준은 `맑은 고딕`을 우선한다.

## Gate policy

### GREEN
다음이면 일반 처리:
- editable text가 있다
- 구조가 보인다
- 문체/스타일/표 수정이 주목적이다

### AMBER
다음이면 진행하되 layout 의존 항목을 별도 표기:
- plain text만 있어 repeated header, row split, style panel 상태를 확인할 수 없다
- Word 원본의 section/page behavior를 직접 볼 수 없다
- mixed KR/EN run-level font 적용을 실제 문서에서 검증할 수 없다
- Word engine 작업이 필요하지만 automation 또는 저장 상태가 불안정하다

AMBER 규칙:
- content-level normalization은 진행한다
- 아래 항목은 `AMBER layout checks`로 분리한다:
  - repeated header
  - allow row to break across pages
  - section/page break behavior
  - Word style pane 설정값
  - run-level font 적용 여부

### ZERO
다음이면 중단:
- 이미지 전용이어서 텍스트를 신뢰성 있게 추출할 수 없다
- 사용자가 layout-accurate Word styling을 요구하지만 editable text가 없다
- 원문이 너무 부족해서 사실 보존 패치가 불가능하다

ZERO 출력:
- blocked item
- why blocked
- input required 3개 이내

## Procedure

### 1) Preflight
- 입력 형식을 식별한다.
- mutable source path를 1개만 고정한다.
- 동일 파일명 복사본이 여러 개면 size/hash/package counts를 비교한다.
- editable text 여부를 판단한다.
- OpenXML-safe인지 Word-engine-required인지 문서 class를 고른다.
- output mode를 고른다.
- preset을 고른다.
- 기존 corporate template 존재 여부를 확인한다.
- 필요한 asset/reference만 읽는다.

기존 `.docx` mutation 전 체크:
- source hash
- package counts(entries/media/headers/footers)
- section 개수
- field/TOC 존재 여부

### 2) Audit order
항상 아래 순서로 본다.
1. title / heading hierarchy
2. paragraph logic
3. alignment / spacing / line height
4. numbering / notation / punctuation
5. font policy / emphasis
6. table caption / header / alignment / complexity
7. accessibility and scanability
8. Korean business-document notation

### 3) Apply structure rules
- 제목/본문/표/캡션을 스타일 단위로 본다.
- Heading level을 건너뛰지 않는다.
- 본문 기본 정렬은 좌측 정렬이다.
- 줄간격과 문단 간격은 paragraph property로 통제된다고 가정한다.
- 양쪽 정렬은 한글 문서에서 신중하게만 허용한다.
- 강조는 Bold 우선이고 밑줄/색상 남용을 제거한다.

### 4) Apply paragraph rules
- 한 문단에는 한 메시지.
- 3~4줄 이상 장문이 되면 의미 단위로 분리 검토.
- 번역투, 명사형 과밀, 중복 표현을 줄인다.
- 어조는 직접적이고 사무형으로 유지한다.

### 5) Apply table rules
- 표 제목은 표 위.
- 헤더 행은 필수.
- 표 헤더는 bold + 중앙 정렬을 기본.
- 텍스트는 좌측 정렬.
- 숫자/금액/%는 우측 정렬.
- 날짜는 중앙 또는 우측 정렬.
- 셀 병합과 중첩 표는 최소화.
- 열이 너무 넓으면 글자 크기를 급히 줄이지 말고 열 구조 재설계를 먼저 검토.
- repeated header 및 row split 제어는 plain text 환경이면 `AMBER layout checks`로 남긴다.

orphan-header 방지 규칙:
- heading/body paragraph 자체에 `pageBreakBefore`를 직접 걸지 않는다.
- table 바로 앞 blank paragraph가 있으면 그 문단만 pagination anchor로 사용한다.
- blank paragraph가 없으면 새 empty paragraph를 table 직전에 삽입하는 방식을 우선 검토한다.
- table를 다음 페이지로 넘겨야 할 때도 heading/body text를 통째로 밀어내는 fallback은 마지막 수단이다.

### 6) Apply preset rules
정확한 수치가 필요하면 `assets/kr-pro-style-set.md`와 `assets/style-profiles.md`를 따른다.

### 7) Produce output
반드시 선택한 output mode의 형식을 따른다.
형식은 `assets/output-templates.md`를 그대로 따른다.

### 8) Saved-file verification gate
기존 `.docx`를 실제로 수정했으면 결과 파일을 저장한 뒤 아래를 다시 확인한다.

- output hash
- output package counts(entries/media/headers/footers)
- source 대비 text/table content 보존 여부
- field result가 필요한 작업이면 저장된 파일 기준 evidence

package counts가 예기치 않게 줄거나 늘면 partial artifact로 보고 그 출력은 버린다.

## Output contract

### audit-only
- Executive Summary
- Findings table
- AMBER layout checks
- QA Gate

### patch-list-only
- Patch List table
- AMBER layout checks
- QA Summary
- 변경되지 않은 문장은 반복하지 않는다

### patched-document
- Revised Document
- QA Summary
- 남은 가정/미확인 layout 항목

### style-spec-only
- Recommended preset
- style map
- font mapping
- table rules
- accessibility gate

## Failure modes
- layout을 확정처럼 말하면 안 된다
- 표 구조를 임의로 새로 해석하면 안 된다
- 숫자열 정렬 규칙을 놓치면 안 된다
- style spec을 요구했는데 문장을 과도하게 다시 쓰면 안 된다
- patch-list-only에서 unchanged text를 장황하게 반복하면 안 된다
- trusted source가 아닌 복사본을 mutation source로 잡으면 안 된다
- TOC/page-number/section behavior를 OpenXML 결과만으로 완료라고 말하면 안 된다
- Word COM이 unstable한데 저장 결과를 검증하지 않고 다음 단계로 가면 안 된다
- hidden `WINWORD.EXE /Automation -Embedding`가 남아 있으면 run을 정상 완료로 간주하면 안 된다

## Verification
결과 제출 전 아래를 확인한다.
- 제목/본문/표/캡션이 스타일 단위로 설명되는가
- Heading 1~3 논리가 살아 있는가
- 본문이 좌측 정렬 기준으로 정리되었는가
- 줄간격/문단간격을 빈 줄이 아니라 속성 개념으로 다루었는가
- 표 헤더, 정렬, 단위 표기가 통일되었는가
- 숫자/통화/날짜/고유명사가 보존되었는가
- KR/EN font policy가 반영되었는가
- layout 미확인 항목은 `AMBER layout checks`로 분리되었는가
- saved-file hash와 package counts를 다시 확인했는가
- TOC/page-number 같은 field 결과는 저장된 파일 기준으로 검증했는가
