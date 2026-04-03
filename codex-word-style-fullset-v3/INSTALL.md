# Install Guide

## 1) Local skill로 바로 쓰기
Codex는 repo/user/admin/system 위치의 `.agents/skills`를 읽습니다.

### Repo
```bash
mkdir -p .agents/skills
cp -R /path/to/codex-word-style-fullset-v3/.agents/skills/word-style-upgrade .agents/skills/
```

### User
```bash
mkdir -p "$HOME/.agents/skills"
cp -R /path/to/codex-word-style-fullset-v3/.agents/skills/word-style-upgrade "$HOME/.agents/skills/"
```

## 2) AGENTS.md 적용
repo root에 이 패키지의 `AGENTS.md`를 두거나, 기존 `AGENTS.md`에 필요한 문단만 병합합니다.

## 3) Plugin 패키지 사용
재배포가 목적이면 `plugin/word-style-codex-suite/`를 기준으로 plugin을 다룹니다.

- entry point: `.codex-plugin/plugin.json`
- bundled skill path: `skills/word-style-upgrade/`

## 3-1) Git에서 이 패키지 폴더와 zip만 받기
다른 컴퓨터에서 전체 repo를 다 받지 않고 아래 두 항목만 받으려면 sparse-checkout을 사용합니다.

대상:

- `codex-word-style-fullset-v3/`
- `codex-word-style-identical-install-20260403.zip`

브랜치:

- `codex/word-style-package-20260403`

### Windows PowerShell
```powershell
git clone --filter=blob:none --no-checkout --branch codex/word-style-package-20260403 https://github.com/macho715/CODEX_SKILL.git
cd CODEX_SKILL
git sparse-checkout init --cone
git sparse-checkout set codex-word-style-fullset-v3 codex-word-style-identical-install-20260403.zip
git checkout codex/word-style-package-20260403
```

받은 뒤에는 아래 둘만 내려옵니다.

- `.\codex-word-style-fullset-v3\`
- `.\codex-word-style-identical-install-20260403.zip`

### GitHub 웹에서 바로 보기
- package folder: `codex-word-style-fullset-v3/`
- zip file: `codex-word-style-identical-install-20260403.zip`

둘 다 `codex/word-style-package-20260403` 브랜치에서 확인합니다.

## 4) Legacy fallback
새 환경은 `.agents/skills` 기준으로 설치합니다.  
오래된 예제와 내부 관행 때문에 `.codex/skills`를 쓰는 환경이 있을 수 있으나, 새 패키지는 `.agents/skills`를 기준으로 유지합니다.
