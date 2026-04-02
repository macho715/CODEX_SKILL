# excel-professional-formatting 운영 체크리스트

## 목적
- 시각 개선만 수행한다.
- workbook 동작 보존이 외형 개선보다 우선이다.
- 원본이 아니라 sidecar에서만 작업한다.

## 시작 전
- source workbook 경로를 확인한다.
- sidecar 경로를 먼저 만든다.
- non-ASCII 경로면 ASCII sidecar를 쓴다.
- promotion boundary를 먼저 정한다.
- 필요 시 `excel-vba` handoff 여부를 먼저 판단한다.

## 이 스킬로 해도 되는 일
- theme 정리
- 제목, 섹션, 헤더, 본문 계층 정리
- 열 너비, 행 높이, 정렬, 줄바꿈 정리
- print setup 정리
- 최소한의 conditional formatting
- report, dashboard, tracker 시트의 가독성 개선

## 이 스킬로 하면 안 되는 일
- 수식 변경
- VBA, event code 변경
- named range 변경
- table name 변경
- hidden 또는 veryHidden sheet 조작
- 버튼, shape, macro binding 변경
- raw-data 구조 변경
- live user Excel session 재사용

## 시트 분류
- Raw Data: 가장 보수적으로 처리한다.
- Working Calc: 명시 승인 없으면 제외한다.
- Input Form: 입력 동선과 대비를 우선한다.
- Operational Tracker: 헤더 계층, 상태 가독성, 필터 사용성을 우선한다.
- Executive Report / Dashboard: 시각 계층과 print 품질을 우선한다.

## 적용 순서
1. workbook theme
2. title / section / header / body hierarchy
3. width / height 조정
4. print setup
5. minimal conditional formatting

## Raw Data 규칙
- 실제 헤더는 1행만 유지한다.
- 데이터 영역 안에 merged cell을 만들지 않는다.
- 데이터 영역 안에 blank row/column을 만들지 않는다.
- filters와 table readability를 유지한다.
- 과한 fill, border, decoration을 넣지 않는다.

## 검증 게이트
- sidecar가 repair prompt 없이 열려야 한다.
- 실제 편집 파일이 sidecar 경로여야 한다.
- sheet name/order/visibility가 바뀌지 않아야 한다.
- merged range count가 늘지 않아야 한다.
- named range와 ListObject name이 바뀌지 않아야 한다.
- shape count와 macro path가 유지되어야 한다.
- VBA component list가 같아야 한다.
- save/close/reopen이 정상이어야 한다.

## 필수 산출물
- `sidecar_workbook.xlsm`
- `baseline_contract.json`
- `post_format_contract.json`
- `validation_report.md`
- `promotion_decision.md`

## 이번 세션 기준 교훈
- 잘한 점: sidecar-first, ASCII sidecar 사용, 원본 미승격, hidden sheet 보수 처리
- 아쉬운 점: 버튼 이동은 `excel-vba`로 넘겼어야 함
- 아쉬운 점: baseline/post-format contract 산출물 패키징이 약했음
- 아쉬운 점: visible-session 조사와 formatting 작업이 섞였음

## promotion 조건
- validation gate 전부 통과
- 원본이 sidecar 생성 후 바뀌지 않음
- 직전 backup 확보
- promotion 후 원본 경로에서 reopen 확인

## stop 조건
- 버튼/shape drift가 보이면 중단
- 구조 변경이 필요하면 `excel-vba`로 전환
- workbook protection이나 repair prompt가 보이면 중단
- contract diff에 formatting-safe 범위 밖 변경이 나오면 중단
