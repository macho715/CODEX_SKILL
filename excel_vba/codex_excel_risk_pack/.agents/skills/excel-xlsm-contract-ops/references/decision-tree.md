# Decision Tree

## 1. Live workbook인가

- 예
  - unsaved state known?
    - 아니오 → `BLOCKED` 또는 최소 `WARN`
    - 예 → live patch 허용 범위 확인
- 아니오
  - 다음 단계 진행

## 2. non-ASCII 경로/캡션/시트명인가

- 예 → Unicode risk 활성화
- 아니오 → 일반 경로 규칙 적용

## 3. VBA reinjection이 필요한가

- 예 → compile / references / save-close-reopen / `Application.Run` 필수
- 아니오 → 일반 workbook validation 적용

## 4. Python과 VBA가 같은 workbook surface를 건드리는가

- 예 → collision review 필수
- 아니오 → 일반 충돌 검토

## 5. touched surface가 contract-sensitive인가

다음이면 contract-sensitive다.
- button
- shape
- `OnAction`
- worksheet/workbook event
- named range
- `ListObject`
- formula 위치
- macro entrypoint
- Result / Validation_Errors / LOG
- visible-session behavior

## 6. write posture 결정

- read-only analysis 가능 → 병렬 허용
- same workbook write 필요 → single-writer
- live workbook + unsaved unknown → blocked
