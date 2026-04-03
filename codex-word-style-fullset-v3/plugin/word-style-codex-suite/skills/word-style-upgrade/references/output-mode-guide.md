# Output Mode Guide

## audit-only
- 검토 결과만 필요할 때
- 실제 문장 패치는 최소화하거나 생략
- high-stakes 문서의 1차 리뷰로 적합

## patch-list-only
- 최소 변경 보고용
- 기존 문서를 재작성하지 말고 바뀐 부분만 제시
- 계약, 보고, 상신문, 결재문에 가장 안전

## patched-document
- 사용자가 full revised text를 명시 요청할 때
- 문장 교정은 하되 구조와 사실은 보존
- QA Summary를 반드시 붙인다

## style-spec-only
- 문서 수정이 아니라 표준 서식 정의가 필요할 때
- 스타일 이름, font mapping, table rules, accessibility gate를 내놓는다
