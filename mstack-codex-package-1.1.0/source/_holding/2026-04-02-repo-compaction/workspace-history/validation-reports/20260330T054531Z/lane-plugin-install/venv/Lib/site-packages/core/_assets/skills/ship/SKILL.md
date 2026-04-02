---
name: mstack-ship
description: >
  배포 준비 스킬. 테스트 부트스트랩, 커버리지 감사, 커밋 메시지 검증, 브랜치 전략을 점검하여
  안전한 머지/배포를 보장한다. force push 금지를 강제한다.
  이 스킬은 ship, 배포, deploy, merge, 머지, release, 릴리스, push, 커밋,
  "PR 올려줘", "배포 준비", "main에 넣어도 될까", "커밋해줘", "배포해",
  "릴리스 하자", git push, "올려줘" 등
  코드 배포/커밋/머지가 필요한 모든 상황에서 반드시 사용해야 한다.
  단순 git commit도 품질 게이트를 거쳐야 하므로 이 스킬을 사용하라.
  mstack SDLC 파이프라인에서 /review 승인 후 실행되며, /qa로 이어진다.
---

# /ship — 배포 준비

> 파이프라인 위치: plan → review → **[ship]** → qa → investigate → retro

## 핵심 규칙

**force push는 금지한다.** `--force`, `--force-with-lease` 모두 사용하지 않는다.
히스토리가 꼬였다면 revert 커밋을 만드는 것이 안전하다.
이 규칙은 Agent Teams 팀원 전체에게 적용된다.

---

## 배포 체크리스트

### 1. 테스트 부트스트랩

테스트가 아예 없는 프로젝트에서는 먼저 최소한의 테스트 인프라를 구축한다:

```
테스트 파일 존재?
  ├─ Yes → Step 2로
  └─ No → 테스트 프레임워크 설치 + 샘플 테스트 1개 생성
          (pytest / jest / go test 등 언어에 맞게)
```

### 2. 커버리지 감사

```bash
# Python 예시
python -m pytest --cov=src --cov-report=term-missing
```

- 새로 추가된 함수/메서드에 대한 테스트 존재 여부 확인
- 커버리지가 프로젝트 기준 미달이면 경고 (기준이 없으면 70% 권장)
- 커버리지 리포트를 `coverage-report.txt`로 저장

### 3. 린트 & 타입체크

CLAUDE.md의 검증 명령어를 실행한다:
```bash
# CLAUDE.md에서 읽어온 명령어
{lint_command}
{typecheck_command}
```

하나라도 실패하면 배포를 중단하고 수정 사항을 안내한다.

### 4. 커밋 메시지 검증

마지막 커밋 메시지가 Conventional Commits 형식을 따르는지 확인:
- `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `ci:`
- 형식이 맞지 않으면 제안 메시지를 생성한다 (강제 수정은 하지 않음)

### 5. 브랜치 전략 확인

```
현재 브랜치?
  ├─ main/master → ⚠️ 직접 커밋 경고. PR 생성 권유.
  ├─ feature/* → PR 생성 안내
  └─ hotfix/* → 긴급 배포 플로우 (테스트 통과 필수는 동일)
```

### 6. 변경 요약 생성

배포할 내용을 한눈에 볼 수 있는 요약:

```markdown
## Ship Summary
- Branch: feature/xxx → main
- Commits: N개
- Files changed: M개 (+X/-Y)
- Tests: ✅ passed (coverage: XX%)
- Lint: ✅ clean
- Type check: ✅ clean (또는 N/A)
```

---

## 배포 실행 (사용자 승인 후)

사용자가 "가"/"ship it"/"배포해" 등으로 승인하면:

0. **git lock 자동 해제** — `resolve_git_lock()` (pipeline.py) 호출하여 `.git/index.lock`, `.git/HEAD.lock` 자동 감지 및 rename. Cowork 환경에서 lock 잔존 시 commit 실패를 방지한다.
1. `git add` + `git commit` (필요 시)
2. `git push origin <branch>` (**절대 --force 아님**)
3. PR 생성 안내 (GitHub CLI 있으면 `gh pr create` 실행)
4. **비용 기록** — `cost.record_session()` 또는 `cost.create_entry_from_pipeline()`으로 세션 비용을 JSONL 로그에 자동 기록.

## 파이프라인 연결

배포 후:
> "배포 완료. `/qa`로 배포 후 검증을 실행하시겠습니까?"

## /careful 연동

`/careful` 활성화 시:
- Step 5에서 main/master 직접 푸시를 **완전 차단** (경고가 아닌 거부)
- 공유 모듈 변경이 포함된 PR은 추가 리뷰어 태그 권장
