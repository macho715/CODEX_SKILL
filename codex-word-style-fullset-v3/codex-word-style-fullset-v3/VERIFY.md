# Verify Guide

## Discovery 확인
```bash
codex --ask-for-approval never "List available skills and confirm word-style-upgrade is loaded."
```

## Explicit invocation 확인
```bash
codex --ask-for-approval never "Use $word-style-upgrade to audit this memo and return patch-list-only."
```

## AGENTS 로딩 확인
```bash
codex --ask-for-approval never "List the instruction sources you loaded."
```

## 기대 결과
- `word-style-upgrade`가 skill selector 또는 응답 내에서 인식된다.
- `AGENTS.md`의 문서 패치 원칙이 요약된다.
- layout 미확인 항목은 `AMBER layout checks`로 분리된다.
- 명시 호출 시 bilingual font policy와 table discipline이 응답에 반영된다.
