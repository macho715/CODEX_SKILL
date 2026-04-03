# AGENTS.md

## Repository Working Agreement

이 저장소에서 문서 패치 작업은 기본적으로 `word-style-upgrade` skill을 사용한다.

### 문서 패치 우선 규칙
- Word형 문서, 보고서, 결재문, 계약 검토 요약, 백서, 부속서, Markdown/HTML/docx export 정리는 먼저 `word-style-upgrade`를 고려한다.
- 의미, 날짜, 숫자, 고유명사, 표 ID, 조항 번호, 부록 번호, 통화, 단위를 바꾸지 않는다.
- 사용자가 최소 수정 또는 보고용 patch를 원하면 기본 출력은 `patch-list-only`다.
- 문서 전체 재작성보다 최소 패치를 우선한다.
- 정확한 pagination, repeated header, row-split, style panel 상태를 실제로 확인하지 못하면 `AMBER layout checks`로 분리한다.

### KR/EN 글꼴 정책
- Latin/English: `Aptos`
- East Asian/Korean: `맑은 고딕`
- plain text나 Markdown만 있을 때는 run-level font 적용을 확정하지 말고 style spec에만 기록한다.

### 구조 규칙
- 스타일 기반 구조를 우선한다.
- 본문 기본 정렬은 좌측 정렬이다.
- 간격은 빈 줄이 아니라 문단 속성으로 제어한다.
- 표는 데이터용으로만 쓰고, 숫자는 우측 정렬, 설명은 좌측 정렬, 상태·짧은 코드는 중앙 정렬을 기본으로 한다.
- 표 제목은 표 위에 둔다.
- Heading 계층은 논리 순서를 지킨다.

### 안전 규칙
- 편집 가능한 텍스트가 없으면 `ZERO`로 멈추고 입력 요청을 3개 이내로 제시한다.
- layout 정확성을 가장해 추정하지 않는다.
