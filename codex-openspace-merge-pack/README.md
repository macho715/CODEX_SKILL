# Codex + OpenSpace Merge Pack

이 패키지는 기존 Codex Skill 팩에 OpenSpace를 **실행 엔진/MCP 확장**으로 병합하고,
로컬 버튼 한 번으로 전체 워크플로를 실행하는 최소 구현입니다.

## 포함 내용
- `.codex/config.toml.example` — Codex가 OpenSpace MCP 서버를 인식하도록 하는 예시 설정
- `.agents/skills/openspace-bridge/SKILL.md` — 기존 Codex Skills와 OpenSpace host skills 사이의 라우팅 브리지
- `AGENTS.merge-snippet.md` — 기존 `AGENTS.md`에 추가할 권장 규칙
- `automation/setup_merge.sh` — OpenSpace host skills 복사 + config 생성
- `automation/run_full_workflow.py` — one-shot 자동 워크플로 실행기
- `automation/one_click_app.py` — Streamlit 버튼 UI
- `automation/templates/workflow_prompt.md` — Codex에 넘길 프롬프트 템플릿

## 전제
1. 기존 Codex Skill 팩이 이미 `.agents/skills/`에 존재
2. OpenSpace가 별도 경로에 설치됨
3. Codex CLI가 설치됨
4. `OPENAI_API_KEY`가 로컬 환경에 설정됨

## 빠른 시작
```bash
bash automation/setup_merge.sh /absolute/path/to/OpenSpace /absolute/path/to/your/repo
python -m venv .venv && source .venv/bin/activate
pip install -r automation/requirements.txt
streamlit run automation/one_click_app.py
```
