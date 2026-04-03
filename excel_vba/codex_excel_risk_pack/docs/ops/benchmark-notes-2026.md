# Benchmark Notes (2026)

## 목적

이 문서는 이 패키지가 어떤 최신 공식 Codex 문서 스타일과 규칙을 벤치마크했는지 기록한다.

## 반영한 공식 Codex 문서

### 1. Custom instructions with AGENTS.md – Codex
반영 내용:
- `AGENTS.override.md` 우선, 없으면 `AGENTS.md`
- project root에서 current working directory까지 계층 적용
- directory마다 최대 1개 instructions file 포함
- fallback filename은 `project_doc_fallback_filenames`로 확장 가능

문서 스타일 반영:
- 짧은 섹션 제목
- layered instruction 설명
- 예시 중심

검증일:
- 2026-04-03

### 2. Subagents – Codex
반영 내용:
- subagent는 explicit ask 기반 spawn
- project-scoped custom agent는 `.codex/agents/*.toml`
- required field는 `name`, `description`, `developer_instructions`
- optional config key는 `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, `skills.config`
- global subagent setting은 `[agents]`

문서 스타일 반영:
- narrow and opinionated agent
- role 분리
- TOML minimal schema
- example-driven formatting

검증일:
- 2026-04-03

### 3. Agent Skills – Codex
반영 내용:
- Skill은 `SKILL.md` 기반
- `name`, `description` 필수
- optional `scripts/`, `references/`, `assets/`, `agents/openai.yaml`
- implicit invocation은 description 품질에 의존
- repo-scoped skill path는 `.agents/skills`

문서 스타일 반영:
- frontmatter + concise procedure
- progressive disclosure
- compact reference split

검증일:
- 2026-04-03

### 4. Configuration Reference – Codex
반영 내용:
- `sandbox_mode = "read-only" | "workspace-write" | "danger-full-access"`
- `sandbox_workspace_write.network_access`
- `[agents] max_threads`, `max_depth`, `job_max_runtime_seconds`
- custom agent file에서 `model`, `model_reasoning_effort`, `sandbox_mode` 등 사용 가능

문서 스타일 반영:
- declarative key/value
- minimal but explicit defaults

검증일:
- 2026-04-03

### 5. Agent approvals & security / Sandboxing – Codex
반영 내용:
- `approval_policy = "untrusted"`를 기본 보수값으로 채택
- `--full-auto`는 `workspace-write + on-request`
- child workflow는 parent sandbox / approval을 상속
- fresh approval을 surface 못하면 child action은 실패하고 parent에 오류 반환

문서 스타일 반영:
- safe default
- policy를 짧게 규정
- approval failure를 explicit blocker로 다룸

검증일:
- 2026-04-03

### 6. Introducing the Codex app / Codex product page
반영 내용:
- Skills는 instructions, resources, scripts를 묶는 reusable workflow
- Codex는 multi-agent workflow와 parallel work를 계속 강화 중
- background / automation 방향성을 반영하되, 현재 repo 문서는 explicit spawn 기반으로 설계

문서 스타일 반영:
- short executive framing
- workflow capability 강조
- role separation

검증일:
- 2026-04-03

## 내부 실무 지식과의 결합

이 패키지는 내부 `excel-vba` 지침에서 다음 위험 신호를 별도 고위험 게이트로 끌어올렸다.

- `windows-com-and-unicode.md` 계열 위험: COM + VBA reinjection + non-ASCII path
- `handoff-operational-checklist.md` 계열 위험: formatting처럼 보여도 button / shape / OnAction / event / named range / table name이면 contract-sensitive
- `conflict-checklist.md` 계열 위험: Python + VBA coexistence in existing `.xlsm`
- `qa-and-operations.md` 계열 위험: open workbook, unsaved changes, force close / overwrite / reinjection

따라서 이 패키지는 **공식 Codex 최신 문서 스타일 + 내부 Excel 운영 리스크 지식**의 조합으로 설계했다.
