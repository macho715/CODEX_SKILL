# AGENTS.override.md (sample)

## Temporary strict patch mode
- 문서 패치 작업은 항상 `patch-list-only`로 시작한다.
- full rewrite는 사용자가 명시적으로 요청할 때만 한다.
- 계약/정산/대외 공문 성격 문서는 `audit-only -> patch-list-only -> patched-document` 순서를 강제한다.
- layout 검증 불가 항목은 무조건 `AMBER layout checks`로 남긴다.
