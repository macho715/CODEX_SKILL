<!-- mstack-session-start -->
> 👥 **Session Mode: AGENT_TEAMS** | 15 files | cost 3.5x
> Reason: 15 files — Agent Teams recommended (⚠ ~3.5x tokens)
> Action: **Shift+Tab** 으로 위임 모드로 전환하세요.
<!-- mstack-session-end -->
# mstack (ccat) — Project Context

> Agent Teams 팀원이 독립 로드. 명확할수록 토큰 절약.

## 구조
```
├── ci/                       # 2개 파일
├── core/                     # 11개 파일 (pipeline.py, memory.py 추가)
├── docs/                     # 2개 파일
├── mstack.egg-info/          # 5개 파일
├── presets/                  # 3개 파일
├── prompts/                  # 4개 파일
├── skills/                   # 7개 파일
├── skills-workspace/         # 103개 파일
├── tests/                    # 18개 파일 (test_pipeline.py, test_memory.py 추가)
```

## 검증 명령어
```bash
python -m pytest tests/ -v --tb=short
flake8 src/ --max-line-length 120 --select=E9,F63,F7,F82
python -m mypy src/ --ignore-missing-imports
```

## 코딩 규칙
Python 3.11+ / Type hints 필수 / bare except 금지
- Module-level dicts/lists used as constants MUST use MappingProxyType or tuple (no mutable globals)
- Test files that mutate global state must use pytest fixtures with proper teardown
- 특정 Python 버전에 의존하는 테스트는 `@pytest.mark.skipif` 가드 필수
- Debug tests in `tests/debug/` are excluded from collection (`--ignore=tests/debug`)

## 커버리지 기준
- core/ 전체: ≥99%
- 신규 모듈: 100% 필수 (import guard 제외)
- 기존 모듈 수정 시: 커버리지 하락 금지

## 스킬 (SDLC 파이프라인)
`/plan` → `/review` → `/ship` → `/qa` → `/investigate` → `/retro`
- `/careful` — 전 단계 안전 가드레일
- `/dispatch` — 작업 오케스트레이터 (SINGLE/SUBAGENT/AGENT_TEAMS 자동 추천 + 실행)

### 배포 경로
- **Codex**: `.codex/commands/*.md` → `.codex/skills/mstack/*/SKILL.md`
- **Cowork**: `skills/*/SKILL.md` → `package_skill.py` → `.skill` 패키지 → `present_files`
- 스킬 소스: `skills/` (8개 디렉토리)

## 파이프라인 자동 실행 (v1.0)
- `core/pipeline.py` — dispatch 승인 후 plan→구현→review→qa→ship→retro 자동 체이닝
- qa FAIL 시 review→fix→qa 자동 재시도 (최대 3회)
- `core/memory.py` — 세션 결과를 JSONL로 저장, 다음 세션에서 자동 로드
- 메모리 경로: `.codex/memory/sessions.jsonl`, `.codex/memory/context.md`
- 자동 로테이션: 최근 100 세션만 유지

## Agent Team 규칙
- 각 팀원은 할당된 디렉토리만 수정
- src/shared/ 또는 공유 모듈 수정 시 리드 승인 필수
- 태스크 완료 전 테스트 통과 필수
- plan approval 활성화 시 구현 전 계획 먼저 제출
