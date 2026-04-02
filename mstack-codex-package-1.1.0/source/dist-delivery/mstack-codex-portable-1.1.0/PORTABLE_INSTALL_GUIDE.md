# MStack Codex Portable 설치 가이드

이 폴더는 다른 컴퓨터에서 동일한 MStack Codex skill 세트를 바로 사용할 수
있도록 만든 전달용 번들이다.

이 번들에는 다음이 포함되어 있다.

- `mstack-1.1.0-py3-none-any.whl`
  Python 패키지 설치 파일
- `codex-skills/`
  바로 복사 가능한 direct Codex skill tree
- `plugins/mstack-codex/`
  바로 복사 가능한 local Codex plugin bundle
- `.agents/plugins/marketplace.json`
  plugin-first 레이아웃에서 사용할 marketplace 예시 파일
- `docs/README.md`
- `docs/INSTALL_CODEX.md`
- `docs/MSTACK_SKILL_GUIDE.md`

## 어떤 방법을 써야 하나

가장 권장되는 방법은 wheel 설치 후 CLI로 배치하는 방식이다.

이유:
- 설치 결과가 관리형 manifest와 함께 정리된다
- 다른 경로로 다시 배포하거나 `--force` 재설치하기 쉽다
- direct install과 plugin install 둘 다 같은 wheel에서 처리할 수 있다

권장 순서:

1. wheel 설치
2. `install-codex` 또는 `install-codex-plugin` 실행
3. 설치 경로 검증

## 방법 1: wheel 설치 후 direct Codex skills 배치

이 방법은 `~/.codex/skills` 같은 Codex skills 디렉터리에 직접 설치하는 방식이다.

### 1) wheel 설치

```bash
python -m pip install mstack-1.1.0-py3-none-any.whl
```

### 2) direct install 실행

예시:

```bash
python -m mstack install-codex --target ~/.codex/skills
```

Windows 예시:

```powershell
python -m mstack install-codex --target $HOME\.codex\skills
```

### 3) 설치 확인

아래가 존재하면 정상이다.

```text
<skills-target>/MSTACK_SKILL_GUIDE.md
<skills-target>/mstack-plan/SKILL.md
<skills-target>/mstack-pipeline/SKILL.md
<skills-target>/mstack-pipeline/references/usage-examples.md
<skills-target>/mstack-pipeline-coordinator/references/coordinator-input-contract.md
```

## 방법 2: wheel 설치 후 plugin-first 배치

이 방법은 local plugin bundle로 배치하는 방식이다.

### 1) wheel 설치

```bash
python -m pip install mstack-1.1.0-py3-none-any.whl
```

### 2) plugin install 실행

예시:

```bash
python -m mstack install-codex-plugin --target <parent-dir>/plugins/mstack-codex --with-marketplace
```

명시적 marketplace path를 주려면:

```bash
python -m mstack install-codex-plugin \
  --target <parent-dir>/plugins/mstack-codex \
  --with-marketplace \
  --marketplace-path <parent-dir>/.agents/plugins/marketplace.json
```

### 3) 설치 확인

아래가 존재하면 정상이다.

```text
<plugin-root>/.codex-plugin/plugin.json
<plugin-root>/MSTACK_SKILL_GUIDE.md
<plugin-root>/skills/pipeline/SKILL.md
<plugin-root>/skills/pipeline/references/core-pipeline-integration.md
<parent-dir>/.agents/plugins/marketplace.json
```

## 방법 3: 준비된 폴더를 그대로 복사

이 번들에는 이미 설치가 끝난 형태의 폴더도 포함되어 있다.

### direct copy

`codex-skills/` 아래 내용을 대상 컴퓨터의 Codex skills 디렉터리로 복사한다.

복사 후 확인:

```text
<skills-target>/MSTACK_SKILL_GUIDE.md
<skills-target>/mstack-pipeline/SKILL.md
```

### plugin copy

아래 두 경로를 repo-local plugin layout에 맞게 복사한다.

- `plugins/mstack-codex/`
- `.agents/plugins/marketplace.json`

복사 후 확인:

```text
<repo-root>/plugins/mstack-codex/.codex-plugin/plugin.json
<repo-root>/plugins/mstack-codex/MSTACK_SKILL_GUIDE.md
<repo-root>/.agents/plugins/marketplace.json
```

## 포함된 주요 문서

### `docs/README.md`

패키지 개요와 배포 모델을 간단히 설명한다.

### `docs/INSTALL_CODEX.md`

설치/검증/문제 해결 중심 문서다.

### `docs/MSTACK_SKILL_GUIDE.md`

실제 skill 사용법, 선택 기준, 프롬프트 템플릿, Windows 운영 참고를 포함한
상세 가이드다.

## 어떤 skill들이 포함되나

포함된 public Codex skills:

- `mstack-careful`
- `mstack-dispatch`
- `mstack-investigate`
- `mstack-pipeline`
- `mstack-pipeline-coordinator`
- `mstack-plan`
- `mstack-qa`
- `mstack-retro`
- `mstack-review`
- `mstack-ship`

## Windows 사용자 참고

Windows에서는 `cmd.exe` 기반 Node toolchain 실행이 시스템 `PATH` 상태에
영향받을 수 있다.

증상 예시:
- `npm install` 실패
- `npx eslint` 실패
- `node is not recognized as an internal or external command`

확인 명령:

```powershell
cmd.exe /d /c "where node && where npm && node --version && npm --version"
```

권장 조치:

1. `PATH`의 중복 Python, Git, Node, npm user-bin 항목 제거
2. `C:\Program Files\nodejs` 유지 여부 확인
3. 터미널/IDE 재시작

자세한 내용은 `docs/INSTALL_CODEX.md`와 `docs/MSTACK_SKILL_GUIDE.md`를 보면 된다.

## 빠른 추천

가장 안정적인 방식:

```bash
python -m pip install mstack-1.1.0-py3-none-any.whl
python -m mstack install-codex-plugin --target <parent-dir>/plugins/mstack-codex --with-marketplace
```

가장 단순한 방식:

```bash
python -m pip install mstack-1.1.0-py3-none-any.whl
python -m mstack install-codex --target ~/.codex/skills
```
