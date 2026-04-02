---
name: mstack-review
description: >
  코드 리뷰 스킬. 변경사항을 AUTO-FIX(자동 수정 가능)와 SURFACE(사람 판단 필요)로 분류하고,
  완전성 갭(누락된 테스트, 미처리 엣지 케이스)까지 점검한다.
  이 스킬은 review, 코드 리뷰, PR 리뷰, code review, diff 분석,
  "이거 봐줘", "머지 전에 확인", "뭐 빠뜨린 거 없나", 리뷰 요청, pull request,
  "코드 검토", "변경사항 확인", security review, 보안 점검 등
  코드 변경 검토가 필요한 모든 상황에서 반드시 사용해야 한다.
  사용자가 코드를 작성하고 확인을 요청하거나, PR을 올리기 전이라면 명시적 요청 없이도 이 스킬을 사용하라.
  mstack SDLC 파이프라인에서 /plan 후 실행되며, /ship으로 넘기는 중간 단계.
  구현 전 설계/승인은 mstack-plan, end-to-end 실행은 mstack-pipeline,
  QA 증거 기반 릴리스 판단은 mstack-ship 사용.
---

# /review — 코드 리뷰

> 파이프라인 위치: plan → **[review]** → ship → qa → investigate → retro

## Use This Skill When

- 코드/diff가 이미 존재하고 품질/완전성 리뷰가 주 작업일 때
- AUTO-FIX / SURFACE 분류가 필요할 때
- 누락 테스트, 계획 대비 드리프트, 에지 케이스 갭을 머지 전에 확인할 때

## Prefer Another Skill When

- 구현 전 설계/승인: `mstack-plan` 사용
- 리뷰가 아닌 end-to-end 실행: `mstack-pipeline` 사용
- QA 증거 기반 릴리스 준비도 판단: `mstack-ship` 사용

## 핵심 원칙

리뷰의 목적은 "고치는 것"이 아니라 "발견하는 것"이다.
발견한 이슈를 두 버킷으로 분류하면 리뷰 후속 작업이 명확해진다:

- **AUTO-FIX**: 기계적으로 수정 가능 (포맷, 미사용 import, 타입 어노테이션 누락 등)
- **SURFACE**: 사람의 판단이 필요 (설계 결정, 비즈니스 로직, 성능 트레이드오프 등)

---

## 리뷰 절차

### Step 1 — 변경 범위 파악

```bash
git diff --stat HEAD~1   # 또는 지정된 base branch
```

변경된 파일 목록과 각 파일의 +/- 줄 수를 확인한다.
`/plan`에서 생성된 `plan.md`가 있으면 계획 대비 실제 변경을 비교한다.

### Step 2 — 카테고리별 점검

#### 보안 (Security)
- 하드코딩된 시크릿, API 키
- SQL 인젝션, XSS 취약점
- 인증/인가 바이패스
- 분류: 대부분 **SURFACE** (컨텍스트 의존)

#### 성능 (Performance)
- N+1 쿼리 패턴
- 불필요한 루프 내 I/O
- 메모리 누수 가능성 (이벤트 리스너 미해제 등)
- 분류: 단순 캐싱 누락은 **AUTO-FIX**, 아키텍처 변경은 **SURFACE**

#### 품질 (Quality)
- 타입 힌트 누락 (Python), `any` 사용 (TypeScript)
- 에러 핸들링 미흡 (bare except, 빈 catch)
- 매직 넘버, 하드코딩된 문자열
- 분류: 대부분 **AUTO-FIX**

#### 완전성 갭 (Completeness Gap)
- 계획(plan.md)에 명시된 파일 중 변경되지 않은 것
- 테스트가 없는 새 함수/메서드
- 에러 경로에 대한 테스트 부재
- 분류: **SURFACE** (의도적 생략인지 확인 필요)

### Step 3 — 리뷰 리포트 생성

아래 형식으로 `review-report.md`를 작성한다:

```markdown
# Code Review Report
Date: YYYY-MM-DD
Base: <branch/commit>

## Summary
변경 파일 N개, +X/-Y 줄

## AUTO-FIX (자동 수정 가능)
1. [파일:줄] 이슈 설명 → 수정 방법
2. ...

## SURFACE (사람 판단 필요)
1. [파일:줄] 이슈 설명 → 질문/제안
2. ...

## Completeness Gap
- [ ] plan.md 대비 누락: ...
- [ ] 테스트 미작성: ...

## Verdict
- [ ] APPROVE — 머지 가능
- [ ] REQUEST CHANGES — AUTO-FIX 적용 후 재확인
- [ ] NEEDS DISCUSSION — SURFACE 항목 해결 필요
```

### Step 4 — AUTO-FIX 적용 (선택)

사용자가 동의하면 AUTO-FIX 항목을 일괄 적용한다.
적용 후 `git diff`를 보여주어 변경 내용을 확인할 수 있게 한다.
**SURFACE 항목은 절대 자동 수정하지 않는다.**

---

## Agent Teams 연동

Agent Teams 모드에서는 리뷰를 3명이 분담할 수 있다:
- Security Reviewer → 보안 섹션
- Performance Reviewer → 성능 섹션
- Quality Reviewer → 품질 + 완전성 갭

각 리뷰어의 결과를 리드가 통합하여 최종 리포트를 생성한다.
(`.claude-prompts/01-review.md` 참고)

## 파이프라인 연결

리뷰 완료 후:
> "리뷰 완료. AUTO-FIX N건 적용 가능, SURFACE M건 논의 필요.
> `/ship`으로 배포 준비를 하시겠습니까?"
