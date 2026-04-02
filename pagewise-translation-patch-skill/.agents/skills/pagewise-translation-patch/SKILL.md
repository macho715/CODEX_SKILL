---
name: pagewise-translation-patch
description: 한국어↔영어 보고서·발표자료·Word/PDF/PPT 문서를 페이지별로 검토해 사실오류, 어색한 번역, 용어 불일치를 패치하고 변경된 문구만 출력한다. Use when asked for 한영 번역 검토, 영한 번역 수정, bilingual report cleanup, pagewise patch, slide-by-slide wording fix, or “변경 문구만”.
---

# Pagewise Translation Patch

## Purpose
이 Skill은 KR↔EN 비즈니스 문서를 처음부터 끝까지 검토한 뒤, 수정이 필요한 문구만 페이지별 패치 목록으로 반환한다.

핵심 원칙:
- 전체 재작성 금지
- 변경 없는 페이지 출력 금지
- 근거 없는 숫자, 일정, 진행률, ETA, 실적, 완료 표현 생성 금지
- 번역투와 과장 표현 제거
- 문서 문체와 도메인 용어는 유지하되, 어색한 표현만 최소 수정
- 최종 산출물은 즉시 반영 가능한 패치 목록이어야 함

## When to use
다음과 같은 요청에 사용한다.
- “한영 번역 검토”
- “영한 번역 패치”
- “페이지별 변경 문구만 정리”
- “보고서/발표자료 번역투 제거”
- “bilingual report cleanup”
- “pagewise patch only”
- “slide-by-slide wording fix”

적합한 문서:
- Word, PDF, PPT, HTML, Markdown, 이메일 초안
- 한국어↔영어 혼합 문서
- 물류, marine, transport, 프로젝트 운영, 일반 비즈니스 보고 문서

## Do not use
다음 경우에는 이 Skill을 기본 선택지로 쓰지 않는다.
- 전체 문서를 새로 번역해야 하는 경우
- 페이지 구분 없이 자유 번역만 필요한 경우
- 법무, 의료, 규제 제출용의 공인 번역이 필요한 경우
- 사용자가 “전체 재작성” 또는 “polish full document”를 명시적으로 요청한 경우

## Inputs
가능하면 다음 입력을 사용한다.
- 원본 문서 또는 텍스트
- 페이지 또는 슬라이드 경계
- source language / target language 또는 혼합 문서 여부
- 문서 유형: report / presentation / email / memo / procedure
- 대상 독자와 톤: executive / client / internal / vendor
- 도메인: general-business / logistics / marine / project
- locale: ko-KR / en-US / en-GB 등
- glossary / terminology list / do-not-translate list
- prior approved translations / previous bilingual versions
- 고정해야 하는 수치, 코드, 고유명사, 제품명, 선박명, 장소명

입력이 충분하지 않아도 바로 멈추지 않는다. 아래 우선순위로 보수적으로 진행한다.
1. 사용자 제공 지침
2. 문서 안의 명시 정보
3. 같은 저장소/같은 작업 폴더의 승인된 표현
4. 일반적인 비즈니스/물류 실무 용어
5. 위 기준으로도 확정 불가하면 의미를 확대하지 않고 보수적으로 패치 또는 보류

## Preflight
최종 패치를 쓰기 전에 아래를 먼저 수행한다.

1. 문서 전체를 처음부터 끝까지 읽는다.
2. 페이지/슬라이드 경계를 식별한다.
3. 문서의 주 언어와 번역 방향을 파악한다.
4. 아래 Context Pack을 만든다.
   - 문서 유형
   - 대상 독자
   - 보고 문체 / 발표 문체 여부
   - 도메인
   - locale
   - glossary / DNT / prior-approved phrasing
   - 반드시 유지해야 할 숫자, 날짜, 코드, 이름
5. 저장소 안에 승인된 용어집, 과거 번역본, 유사 보고서가 있으면 먼저 재사용한다.
6. 짧은 문구, 제목, 표 항목, 캡션처럼 문맥 의존도가 높은 항목은 앞뒤 문단 또는 인접 페이지를 확인한 뒤 판단한다.
7. 페이지 번호가 명확하지 않으면 추정하지 말고, 가능한 실제 page/slide marker를 따른다.

## Review priorities
아래 순서로 우선 검토한다.

1. 사실과 상충되는 표현
2. 근거 없는 수치성 표현
3. 어색한 직역, 번역투, 비문
4. 도메인 용어 불일치
5. 한국어/영어 보고서 문체 이탈
6. 중복, 장황, 과장 표현
7. locale 민감 항목의 오처리 가능성

## Patch conditions
다음 조건 중 하나라도 만족하면 패치 후보로 본다.
- 사실오류
- 내부 문맥 불일치
- 지나치게 literal한 번역
- 실제 보고서 문체에 맞지 않는 표현
- logistics / marine / transport / project 용어에서 비표준 표현
- 검증 근거 없는 정량 표현
- 중복 문장 또는 비문
- 숫자, 날짜, 통화, 직함, 호칭, 지역 표기가 locale 요구와 어긋날 가능성

## Non-negotiable rules
반드시 지킨다.

### 1) Patch only
- 원문 전체를 다시 쓰지 않는다.
- 변경이 필요한 문구만 추출한다.
- 한 페이지에 변경점이 없으면 그 페이지는 출력하지 않는다.

### 2) No invention
- 일정, ETA, ETD, 진행률, 실적, 리스크 수치, 완료 상태를 임의로 만들지 않는다.
- 수치가 불명확하면 숫자를 보강하지 말고 문장 구조만 정리한다.
- 원문 의미를 임의 확대/축소하지 않는다.

### 3) Preserve controlled items
다음은 확인 없이 바꾸지 않는다.
- 숫자, 날짜, 시간, 통화
- 제품명, 프로젝트명, 선박명, 항차, 현장명
- 법인명, 계약명, 문서 번호, 코드
- 사용자가 DNT로 지정한 용어
- 승인된 glossary 항목

### 4) Locale safety gate
다음 항목은 현지화 판단이 개입될 수 있으므로 자동 변환하지 않는다.
- currency conversion
- date/time format conversion
- personal titles / ranks
- forms of address
- language or region labels

값 변환 없이 자연화가 가능하면 표현만 다듬고, 변환이 필요한 경우는 추정하지 말고 보수적으로 유지한다.

### 5) Terminology hierarchy
용어 선택 우선순위:
1. 사용자 glossary / termbase
2. prior approved translation
3. repository 내부의 승인된 유사 문구
4. 일반적인 업계 통용 용어
5. 위 기준으로도 모호하면 가장 보수적인 일반 표현

### 6) Atomic changes
- 한 항목에는 가능한 한 하나의 변경 단위만 넣는다.
- 복합 문장을 크게 갈아엎기보다, 실제로 수정이 필요한 구간을 분리해서 제시한다.

## Language rules

### Korean
- 회사 보고서 / 발표자료 문체 유지
- 짧고 명확한 문장 사용
- 번역투, 군더더기, 직역체 제거
- 물류 / marine / 프로젝트 실무에서 통상 사용하는 용어 우선
- 과장 표현, 감정 표현, 모호한 강조 표현 금지

### English
- business English 사용
- report / presentation 문체 유지
- logistics / marine / transport / project 실무 용어 사용
- awkward wording, literal translation, inflated wording 금지
- 짧고 명확한 문장 우선

## Banned style patterns
아래 표현은 근거가 없으면 유지하거나 생성하지 않는다.
- several
- many
- some
- significant
- soon
- timely
- normal
- stable
- minor
- sufficient
- early

의미상 꼭 필요하지만 근거가 없으면 삭제하거나 구조를 바꿔 표현한다.

## Output mode selection
요청 문구에 아래 표현이 있으면 Strict Patch-Only Mode를 사용한다.
- “페이지별 변경 문구만”
- “변경 문구만”
- “full rewrite 금지”
- “Word/HTML/전체본 금지”
- “설명 장황하게 하지 말 것”

그 외에는 Standard Patch Mode를 사용한다.

## Output contract

### Standard Patch Mode
아래 3개 블록만 출력한다.

1. 검토 결과 요약
- 총 검토 페이지 수
- 변경 필요 페이지 수
- 핵심 패치 기준 3~5줄

2. 페이지별 변경 문구
[Page X]
- 기존: “문구”
- 변경: “수정문구”
- 사유: 사실오류 / 번역투 제거 / 용어 통일 / 문체 보정 / 수치 불명확 / 현지화 판단 필요

3. 자체 검증 결과
- 1차 검증: 사실관계 검토 완료
- 2차 검증: 한글 표현/문체 검토 완료
- 3차 검증: 영문 표현/용어 검토 완료
- 4차 검증: 출력 형식 및 페이지 누락 여부 검토 완료

### Strict Patch-Only Mode
아래 블록만 출력한다.
[Page X]
- 기존: “문구”
- 변경: “수정문구”
- 사유: 사실오류 / 번역투 제거 / 용어 통일 / 문체 보정 / 수치 불명확 / 현지화 판단 필요

추가 설명, 전체 재작성본, Word/HTML 생성 언급, 불필요한 서론은 금지한다.

## Self-validation
최종 출력 전 아래 4회 검증을 수행한다.

### 1차 검증: Facts
- 원문에 없는 숫자/일정/완료 표현이 추가되지 않았는가
- 기존 수치/고유명사가 임의로 변경되지 않았는가
- 문맥상 사실 충돌이 남아 있지 않은가

### 2차 검증: Korean
- 보고서/프레젠테이션체를 유지했는가
- 번역투를 제거했는가
- 일반적인 실무 용어를 사용했는가
- 장황한 문장을 줄였는가

### 3차 검증: English
- business English로 자연스러운가
- logistics / marine / transport 용어가 적절한가
- awkward / literal / inflated phrasing이 제거되었는가
- 슬라이드/보고 문체에 맞는가

### 4차 검증: Output integrity
- 변경 없는 페이지를 출력하지 않았는가
- 페이지 번호가 실제 문서와 맞는가
- 각 항목이 “기존/변경/사유”를 모두 포함하는가
- full rewrite 흔적이 없는가

## Failure handling
다음 상황에서는 추정하지 말고 보수적으로 처리한다.
- 소스 문장이 중의적이라 올바른 의미를 특정할 수 없는 경우
- 페이지 번호가 추출 과정에서 유실된 경우
- 숫자/일정이 문맥상 의심되지만 확인 근거가 없는 경우
- locale 변환이 필요한지 확정할 수 없는 경우

처리 원칙:
- 의미를 보존하는 최소 수정만 한다.
- 필요하면 “현지화 판단 필요” 또는 “수치 불명확” 사유를 사용한다.
- 사용자가 전체 재작성본을 요청하지 않는 한, 대체 문단을 길게 쓰지 않는다.

## Recommended working sequence
1. Read entire source.
2. Build Context Pack.
3. Reuse glossary / prior approved phrasing.
4. Mark only patch candidates.
5. Draft pagewise changes.
6. Run 4-step self-validation.
7. Trim output to changed pages only.

## References to load on demand
- `references/output-contract.md`: 출력 계약과 사유 라벨 상세
- `references/examples.md`: 좋은/나쁜 패치 예시
- `assets/review-request-template.md`: 요청 템플릿
- `assets/termbase-template.csv`: 용어집 템플릿
