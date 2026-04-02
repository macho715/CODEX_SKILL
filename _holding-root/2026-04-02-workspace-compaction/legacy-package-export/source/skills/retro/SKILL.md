---
name: mstack-retro
description: >
  회고 스킬. 완료된 작업(기능 구현, 버그 수정 등)에 대해 잘된 점, 개선점, 액션 아이템을 정리한다.
  cost.py의 비용 데이터를 자동 포함하여 비용 효율성도 분석한다. 이 스킬은 retro, 회고,
  retrospective, lessons learned, postmortem, 사후 분석, wrap up, "뭘 배웠지",
  "이번 작업 마무리", "정리해줘", "비용 분석", "작업 회고", "이번 주 리뷰", "반성",
  KPT, keep/improve 등 작업 완료 후 돌아보기/교훈 정리/비용 분석이 필요한 모든 상황에서
  반드시 사용해야 한다. 기능 구현이나 버그 수정이 끝나면 사용자가 요청하지 않아도 회고를
  제안하라. mstack SDLC 파이프라인의 마지막 단계. /qa 통과 후 또는 /investigate 완료 후 실행.
  머지 전 코드 리뷰는 mstack-review, 작업 진행 중이면 mstack-pipeline,
  테스트 실행만은 mstack-qa 사용.
---

# /retro — 회고

> 파이프라인 위치: plan → review → ship → qa → investigate → **[retro]**

## Use This Skill When

- 작업이 완료되어 교훈, 메트릭, 후속 조치 정리가 필요할 때
- 사용자가 retrospective, postmortem, 완료 작업 요약을 요청할 때
- git 히스토리, QA 결과, 비용 로그 기반의 데이터 중심 마무리가 필요할 때

## Prefer Another Skill When

- 머지 전 코드 리뷰: `mstack-review` 사용
- 작업이 아직 진행 중이고 마무리 단계 아님: `mstack-pipeline` 사용
- 테스트 실행만 필요: `mstack-qa` 사용

## 왜 회고를 하는가

같은 실수를 반복하지 않고, 잘한 패턴을 강화하기 위해서다.
형식적인 회고가 되지 않도록, 구체적이고 실행 가능한 내용에 집중한다.

---

## 회고 절차

### Step 1 — 컨텍스트 수집

자동으로 수집 가능한 데이터:
```bash
# 작업 범위
git log --oneline --since="1 week ago"  # 또는 관련 브랜치의 커밋
git diff --stat main..HEAD

# 작업 시간 (커밋 타임스탬프 기반 추정)
git log --format="%ai" --reverse | head -1  # 시작
git log --format="%ai" -1                    # 종료
```

파이프라인에서 생성된 문서가 있으면 참조:
- `plan.md` — 원래 계획
- `review-report.md` — 리뷰 결과
- `qa-report.md` (또는 테스트 결과)
- `investigation-report.md` (있으면)

### Step 2 — 비용 데이터 수집 (필수 실행)

비용 분석 없는 회고는 "느낌"에 의존하게 된다.
추정치가 아닌 실제 데이터를 기반으로 분석해야 다음 세션의 팀 구성과 모델 선택을 최적화할 수 있다.

#### 2a. cost.py 실행 (반드시 실행할 것)

```bash
# 1단계: cost.py 존재 확인
ls -la cost.py 2>/dev/null && echo "FOUND" || echo "NOT_FOUND"

# 2단계: 비용 리포트 실행 — 이 출력을 그대로 회고에 인용한다
python cost.py report

# 3단계: 원시 로그가 있으면 세션 수 카운트
LOGFILE="$HOME/.claude/cost-logs/sessions.jsonl"
[ -f "$LOGFILE" ] && wc -l "$LOGFILE" && tail -5 "$LOGFILE"
```

cost.py가 없거나 로그가 비어 있으면 **"비용 데이터 없음 — cost.py 미설정"**이라고 명시한다.
절대로 비용을 추정하거나 가정하지 않는다. 실제 데이터가 없으면 "N/A"로 표기한다.

#### 2b. git 메트릭 수집 (비용 효율 계산용)

```bash
# 커밋 수 (실제 카운트 — 추정 금지)
git log --oneline HEAD~50..HEAD 2>/dev/null | wc -l

# 변경 파일 수
git diff --stat HEAD~10..HEAD 2>/dev/null | tail -1

# 작업 기간 (첫 커밋 ~ 마지막 커밋)
echo "시작: $(git log --format='%ai' --reverse HEAD~10..HEAD 2>/dev/null | head -1)"
echo "종료: $(git log --format='%ai' -1 2>/dev/null)"
```

#### 2c. 효율 지표 계산

cost.py 출력과 git 메트릭이 모두 있을 때만 계산한다:
- **비용/커밋** = 총 비용 ÷ 커밋 수
- **비용/파일변경** = 총 비용 ÷ 변경 파일 수
- **일일 비용** = 총 비용 ÷ 작업 일수

하나라도 데이터가 없으면 해당 지표를 "N/A (데이터 부족)"으로 표기한다.
**절대 가공된 숫자를 만들어내지 않는다.**

### Step 3 — 회고 작성

```markdown
# Retrospective
Date: YYYY-MM-DD
Task: [작업 한줄 설명]

## 타임라인
- 계획: X일
- 구현: Y일
- 리뷰/QA: Z일
- 총: N일 (계획 대비: +/-M일)

## 잘된 점 (Keep)
1. [구체적 사례] — 왜 잘되었는지
2. ...

## 개선점 (Improve)
1. [구체적 사례] — 어떻게 개선할 수 있는지
2. ...

## 배운 점 (Learn)
1. [기술적/프로세스적 인사이트]
2. ...

## 비용 분석 (Agent Teams)

> ⚠️ 아래 표의 모든 값은 `python cost.py report` 실행 결과에서 인용한다.
> 실행 결과가 없으면 "N/A — cost.py 미설정" 으로 기입한다.

| 항목 | 값 | 출처 |
|------|------|------|
| 총 비용 | $X.XX | cost.py report |
| 세션 수 | N | sessions.jsonl wc -l |
| 평균 비용/세션 | $X.XX | 총 비용 ÷ 세션 수 |
| 모델 믹스 | Opus X% / Sonnet Y% | cost.py report |
| 커밋 수 | N | git log --oneline \| wc -l |
| 비용/커밋 | $X.XX | 총 비용 ÷ 커밋 수 |
| 변경 파일 수 | N | git diff --stat |
| 비용/파일변경 | $X.XX | 총 비용 ÷ 변경 파일 수 |

## 액션 아이템
- [ ] [실행 가능한 개선 사항] — 담당: [누구] — 기한: [언제]
- [ ] ...
```

### Step 4 — CLAUDE.md 업데이트 제안

회고에서 발견된 패턴이 CLAUDE.md의 규칙에 반영되어야 하면 제안한다:

> "이번 회고에서 발견된 패턴:
> - bare except가 3곳에서 발견됨 → 코딩 규칙에 이미 있지만 강화 필요
> - 테스트 커버리지 기준이 없음 → 70% 최소 기준 추가 제안
>
> CLAUDE.md에 반영하시겠습니까?"

---

## 독립 실행

파이프라인 없이도 사용할 수 있다:
- "이번 주 작업 회고해줘" → git log 기반으로 회고 작성
- "이 PR 회고" → 특정 PR의 커밋/리뷰 기반 회고

## 자기 검증 체크리스트

회고를 저장하기 전에 아래를 확인한다:

- [ ] `python cost.py report`를 실행했는가? (실행 불가 시 "N/A" 명시했는가?)
- [ ] 비용 표의 모든 숫자에 출처(cost.py / git log / sessions.jsonl)가 있는가?
- [ ] 추정치("약", "~", "추정")가 비용 표에 포함되어 있지 않은가?
- [ ] `git log`에서 실제 커밋 수를 카운트했는가?
- [ ] CLAUDE.md 업데이트 제안에 구체적 diff(추가할 줄)가 있는가?

하나라도 "아니오"면 해당 섹션을 수정한 뒤 저장한다.

## 출력

`retro.md`로 저장한다 (이전 회고가 있으면 날짜 접미사 추가).

## 파이프라인 자동 실행 연동

`core/pipeline.py`의 `execute_pipeline()`에서 마지막 스테이지로 호출될 때:
- 파이프라인 전체 결과(PipelineResult)를 기반으로 자동 회고 생성
- `core/memory.py`로 세션 결과를 JSONL에 자동 저장
- `memory.generate_context()`로 다음 세션 컨텍스트 업데이트

## mstack 파이프라인 스킬 참조
- mstack-plan → mstack-review → mstack-ship → mstack-qa → mstack-investigate → mstack-retro (현재)
- mstack-careful: 모든 단계에 적용 가능한 안전 가드레일
