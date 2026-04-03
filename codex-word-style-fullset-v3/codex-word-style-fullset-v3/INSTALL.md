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

## 4) Legacy fallback
새 환경은 `.agents/skills` 기준으로 설치합니다.  
오래된 예제와 내부 관행 때문에 `.codex/skills`를 쓰는 환경이 있을 수 있으나, 새 패키지는 `.agents/skills`를 기준으로 유지합니다.
