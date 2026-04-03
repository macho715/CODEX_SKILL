# Codex Word Style Full Set v3.0

한글/영문 Word 문서 패치 업무를 위한 OpenAI Codex 전용 풀세트입니다.

## 포함 범위
- repo용 `AGENTS.md`
- local discovery용 `.agents/skills/word-style-upgrade/`
- Codex app/IDE용 `agents/openai.yaml`
- 배포용 plugin skeleton: `plugin/word-style-codex-suite/`
- 예제 프롬프트, 출력 템플릿, QA 체크리스트, KR/EN 스타일 세트

## 핵심 정책
- 영문 라틴 글꼴: `Aptos`
- 한글/East Asian 글꼴: `맑은 고딕`
- 본문 기본 정렬: 좌측 정렬
- 스타일 기반 제어 우선, 직접 서식 남용 금지
- 의미·날짜·숫자·고유명사·표 의도 보존
- layout을 실제로 확인할 수 없으면 `AMBER layout checks`로 분리
- 수정 범위가 고위험이면 기본 출력은 `patch-list-only`

## 빠른 설치
### Repo scope
```bash
mkdir -p .agents/skills
cp -R .agents/skills/word-style-upgrade .agents/skills/
```

### User scope
```bash
mkdir -p "$HOME/.agents/skills"
cp -R .agents/skills/word-style-upgrade "$HOME/.agents/skills/"
```

## 빠른 사용
```text
Use $word-style-upgrade to audit this document and return patch-list-only.
```

```text
Use $word-style-upgrade with the bilingual-kr-en-standard preset and preserve all facts.
```

```text
Use $word-style-upgrade in style-spec-only mode for a Korean internal report.
```

## Plugin 배포
로컬 authoring은 `.agents/skills`가 적합하고, 재배포는 plugin이 적합합니다.  
`plugin/word-style-codex-suite/`에 최소 plugin manifest와 동일 skill 복사본을 넣어 두었습니다.
