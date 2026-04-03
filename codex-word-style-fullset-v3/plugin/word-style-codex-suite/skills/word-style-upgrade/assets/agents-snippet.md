# AGENTS snippet for existing repos

문서 패치 요청이 들어오면 `word-style-upgrade`를 먼저 고려한다.

- mixed KR/EN 문서는 Latin=`Aptos`, East Asian=`맑은 고딕` 기준으로 style spec을 잡는다.
- 본문 정렬은 좌측 정렬이 기본이다.
- patch-list-only가 기본 안전 모드다.
- layout 확인이 불가능한 항목은 `AMBER layout checks`로 분리한다.
