---
name: mstack-review
description: >
  Code and diff review skill for Codex. Use when code, a diff, or concrete
  implementation artifacts already exist and the main task is to classify
  findings into AUTO-FIX and SURFACE, spot missing tests, and compare the
  change against the plan; triggers include review, PR review, code review, and
  merge-readiness checks. Prefer `mstack-plan` for pre-implementation design
  and `mstack-pipeline` only when the user wants review chained with
  implementation, QA, shipping, and retro.
---

# 코드 리뷰

## Use This Skill When

- code or a diff already exists and needs quality or completeness review
- the main task is to classify findings into AUTO-FIX and SURFACE
- missing tests, plan drift, or edge-case gaps need to be surfaced before merge

## Prefer Another Skill When

- the request is pre-implementation design or approval: use `mstack-plan`
- the user wants full end-to-end execution instead of review-only: use
  `mstack-pipeline`
- the question is release readiness after QA evidence already exists: use
  `mstack-ship`

## 핵심 원칙

리뷰의 목적은 수정이 아니라 발견이다.
발견한 이슈를 두 버킷으로 나눠 후속 작업을 명확히 한다.

- `AUTO-FIX`: 기계적으로 수정 가능
- `SURFACE`: 사람의 판단이 필요

## 리뷰 절차

### Step 1 - 변경 범위 파악

```bash
git diff --stat HEAD~1
```

변경된 파일 목록과 각 파일의 `+/-` 줄 수를 확인한다.
계획이 있으면 계획 대비 실제 변경을 비교한다.

### Step 2 - 카테고리별 점검

#### 보안
- 하드코딩된 시크릿, API 키
- SQL 인젝션, XSS 취약점
- 인증/인가 바이패스
- 대부분 `SURFACE`

#### 성능
- N+1 쿼리 패턴
- 불필요한 루프 내 I/O
- 메모리 누수 가능성
- 단순 캐싱 누락은 `AUTO-FIX`, 구조 변경은 `SURFACE`

#### 품질
- 타입 힌트 누락, `any` 사용
- 에러 핸들링 미흡, bare except
- 매직 넘버, 하드코딩 문자열
- 대부분 `AUTO-FIX`

#### 완전성 갭
- 계획에 명시된 파일 중 변경되지 않은 것
- 테스트가 없는 새 함수/메서드
- 에러 경로 테스트 부재
- `SURFACE`

### Step 3 - 리뷰 리포트 생성

아래 형식으로 `review-report.md`를 작성한다.

```markdown
# Code Review Report
Date: YYYY-MM-DD
Base: <branch/commit>

## Summary
변경 파일 N개, +X/-Y 줄

## AUTO-FIX
1. [파일:줄] 이슈 설명 → 수정 방법

## SURFACE
1. [파일:줄] 이슈 설명 → 질문/제안

## Completeness Gap
- [ ] 계획 대비 누락: ...
- [ ] 테스트 미작성: ...

## Verdict
- [ ] APPROVE
- [ ] REQUEST CHANGES
- [ ] NEEDS DISCUSSION
```

### Step 4 - AUTO-FIX 적용

사용자가 동의하면 `AUTO-FIX` 항목만 적용한다.
적용 후 `git diff`를 보여주어 변경 내용을 확인하게 한다.
`SURFACE` 항목은 자동 수정하지 않는다.

## 출력

리포트에는 다음을 포함한다.
- 변경 파일 수와 핵심 리스크
- `AUTO-FIX`와 `SURFACE`의 구분
- 누락된 테스트 또는 계획 대비 누락
- 승인, 수정 요청, 추가 논의 중 하나의 판정

## Guardrails

- 리뷰 중에는 불필요한 수정을 하지 않는다.
- 계획이 있으면 계획 기준 누락을 우선 확인한다.
- 테스트가 없는데 새 코드가 추가되면 반드시 지적한다.
