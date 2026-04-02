---
name: mstack-careful
description: >
  안전 가드레일 스킬. 모든 파이프라인 단계에서 위험한 동작을 감지하고 차단한다.
  force push 금지, 공유 모듈 변경 경고, 프로덕션 직접 수정 차단(freeze),
  시크릿 노출 방지, 위험 명령어 감지를 하나로 통합한 크로스커팅 안전 레이어.
  이 스킬은 careful, 안전, safety, guard, freeze, 가드레일, protection,
  "조심해서", "위험한 거 아냐", "실수 방지", "안전하게", "force push 하지 마",
  main branch 작업, 대규모 변경, 시크릿 관리 등
  안전/보호/주의가 필요한 모든 상황에서 반드시 사용해야 한다.
  다른 mstack 스킬과 함께 활성화되어 전 단계에 안전 규칙을 주입하는 크로스커팅 레이어다.
  main/master 브랜치 작업이나 50+ 파일 변경 시 자동 활성화하라.
---

# /careful — 안전 가드레일

> 파이프라인 위치: 모든 단계에 적용되는 **크로스커팅 레이어**

```
/plan → /review → /ship → /qa → /investigate → /retro
  │        │        │       │        │            │
  └────────┴────────┴───────┴────────┴────────────┘
                    /careful (전 단계 감시)
```

## 왜 별도 스킬인가

안전 규칙을 각 스킬에 분산하면 일관성이 깨지고 유지보수가 어렵다.
하나의 스킬로 모아두면 규칙 추가/변경이 한 곳에서 이루어지고,
Agent Teams의 모든 팀원에게 동일하게 적용된다.

---

## 안전 규칙

### Rule 1 — Force Push 금지

```
감지: git push --force, git push --force-with-lease, git push -f
동작: 즉시 차단 + "revert 커밋을 사용하세요" 안내
적용: /ship, 그리고 git push를 사용하는 모든 컨텍스트
```

### Rule 2 — 공유 모듈 변경 경고

```
감지 경로: src/shared/, lib/common/, utils/, types/ (프로젝트에 맞게 조정)
동작: ⚠️ 경고 + "리드 승인 필요" 메시지
적용: /plan(Phase 2), /review, /ship
```

프로젝트의 CLAUDE.md에 공유 모듈 경로가 정의되어 있으면 그것을 사용한다.
정의가 없으면 위의 기본 경로를 적용한다.

### Rule 3 — 프로덕션 직접 수정 차단 (Freeze 모드)

```
활성화 조건: /investigate 실행 중
차단 범위: src/, lib/, app/ (테스트/디버그 파일 제외)
해제 조건: 사용자의 명시적 승인 ("수정해", "fix", "go ahead")
```

### Rule 4 — 시크릿 노출 방지

```
감지 패턴:
  - 하드코딩된 API 키 (AWS, GCP, Azure, GitHub 토큰 등)
  - .env 파일의 git add
  - 비밀번호 문자열 (password=, secret=, token= 뒤의 값)
동작: 커밋 전 경고 + 해당 줄 표시
적용: /ship, /review
```

### Rule 5 — 위험한 명령어 감지

```
감지:
  - rm -rf / (루트 삭제)
  - DROP TABLE, TRUNCATE (데이터베이스)
  - chmod 777 (과도한 권한)
  - git reset --hard (히스토리 손실)
  - git clean -fd (추적 안 되는 파일 삭제)
동작: 실행 전 확인 요청 + 대안 제시
```

---

## Agent Teams 전파

Agent Teams 모드에서 `/careful`이 활성화되면:

1. CLAUDE.md의 Agent Team 규칙 섹션에 가드레일이 추가됨
2. 모든 팀원의 프롬프트에 안전 규칙이 주입됨
3. `on-task-completed.sh` 훅이 Rule 1, 4를 검증

전파 메커니즘:
```
/careful 활성화
  → CLAUDE.md 임시 규칙 추가 (세션 내)
  → 각 팀원 프롬프트에 "[CAREFUL MODE] 활성화" 헤더 추가
  → 훅에서 최종 검증
```

## 사용법

### 명시적 활성화
사용자가 `/careful` 또는 "조심해서 해" 등으로 호출하면
현재 세션의 모든 후속 작업에 가드레일을 적용한다.

### 자동 활성화
다음 상황에서 자동으로 활성화된다:
- `/investigate` 실행 시 (Rule 3 자동 적용)
- main/master 브랜치에서 작업 시 (Rule 1, 2 강화)
- 대규모 변경 (50+ 파일) 감지 시

### 비활성화
"careful 해제", "가드레일 끄기" 등으로 비활성화할 수 있다.
단, Rule 1(force push 금지)과 Rule 4(시크릿 방지)는 해제되지 않는다.
이 두 규칙은 항상 활성 상태를 유지한다.

---

## 위반 로그

가드레일이 동작을 차단하면 로그를 남긴다:

```markdown
# Careful Log
| 시각 | 규칙 | 동작 | 결과 |
|------|------|------|------|
| HH:MM | Rule 1 | git push --force | 차단 |
| HH:MM | Rule 4 | .env staged | 경고 |
```

이 로그는 `/retro`에서 회고 시 참조된다.
