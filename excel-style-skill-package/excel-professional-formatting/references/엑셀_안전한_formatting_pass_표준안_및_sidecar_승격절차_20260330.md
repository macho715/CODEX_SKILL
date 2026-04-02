# 엑셀 안전한 Formatting Pass 표준안 및 Sidecar 승격절차

기준일: `2026-03-30`  
대상: 매크로 포함 workbook (`.xlsm`, `.xlsb`) 의 시각 포맷 작업

## 1. 목적

- workbook 로직, VBA, named range, 표 구조, 버튼 바인딩을 보존한 상태로 시각 포맷만 적용한다.
- live 원본을 직접 건드리지 않고 sidecar copy 에서 작업한 뒤, 검증 통과 시에만 원본으로 승격한다.
- 한글 경로, 동일 파일명, COM 오동작, hidden sheet 회귀를 운영 절차로 차단한다.

## 2. 기본 원칙

1. 포맷 작업은 항상 원본이 아니라 sidecar copy 에서 수행한다.
2. 포맷 작업은 시각 레이어만 다룬다.
3. Raw Data 성격 시트는 가장 보수적으로 다룬다.
4. hidden / veryHidden 운영 시트는 기본적으로 포맷 대상에서 제외한다.
5. COM 자동화는 최소화하고, 창 선택, 활성화, FreezePanes 같은 UI 의존 조작은 예외 상황에서만 쓴다.
6. 승격 전 검증이 끝나기 전까지 원본 경로에 저장하지 않는다.

## 3. 절대 금지

- 원본 workbook 을 잡은 상태에서 직접 저장
- 이미 열려 있는 사용자 Excel 세션을 재사용해서 포맷 적용
- header 이름 변경
- table name 변경
- named range 변경
- formula 변경
- VBA module / event / shape macro binding 변경
- Raw Data 영역에 merged cell 추가
- hidden 운영 시트에 장식성 포맷 일괄 적용
- 검증 없이 sidecar 를 원본에 덮어쓰기

## 4. 시트 분류 기준

- `Input Form`
  - 예: `Package_Intake`
- `Operational Tracker`
  - 예: `Package_Checklist`, `LIST_REV`
- `Print Form / Submission Sheet`
  - 예: `User_Guide`
- `Executive Report`
  - 예: `SUMMARY`
- `Raw Data / Output`
  - 예: `Evidence_Index`
- `Working Calc / System`
  - 예: `Config`, `Result`, `Validation_Errors`, `LOG`

원칙:

- `Input Form`, `Operational Tracker`, `Print Form`, `Executive Report` 만 기본 포맷 대상
- `Raw Data / Output` 은 최소 포맷만 허용
- `Working Calc / System` 은 필요가 명확할 때만 별도 승인 후 작업

## 5. 허용 작업

- workbook theme 통일
- 제목 / 섹션 / 헤더 / 본문 / note / warning / total 계층 정리
- 컬럼 폭 조정
- 행 높이 조정
- 폰트, 정렬, wrap, border, fill 정리
- 인쇄 여백, 방향, 반복행 설정
- 의미가 분명한 조건부서식
- 표 형태가 이미 안전하게 잡혀 있을 때 table style 적용

## 6. 제한 작업

아래는 `excel-vba` 검토 없이는 하지 않는다.

- 시트 구조 변경
- ListObject 생성 / 삭제 / 재구성
- print area 재정의가 수식 범위와 얽힌 경우
- shape 위치가 바뀔 수 있는 큰 폭의 row/column 재조정
- workbook 창 상태에 의존하는 FreezePanes 수정
- hidden / veryHidden 시트 가시성 변경

## 7. Sidecar Copy 작업 표준 경로

작업 폴더 예시:

- `tmp/formatting_pass/20260330_01/`

필수 산출물:

- `sidecar_workbook.xlsm`
- `baseline_contract.json`
- `post_format_contract.json`
- `validation_report.md`
- `promotion_decision.md`

권장 원본 복제 경로:

- 원본이 한글 경로이거나 동일 파일명 충돌 이력이 있으면 ASCII 경로로 복제
- 예: `C:\HVDC_TMP\formatting_pass\sidecar_master.xlsm`

## 8. 실행 절차

### Step 1. 원본 고정

- 대상 원본 절대경로를 먼저 확정한다.
- 동일 이름 backup, Documents 사본, 임시 파일 `~$*` 는 제외한다.
- 사용자가 원본을 열어두고 있으면 포맷 pass 는 원본이 아니라 복제본으로만 진행한다.

### Step 2. Sidecar 생성

- 원본을 sidecar 경로로 `copy2` 한다.
- 이후 모든 COM / 포맷 조작은 sidecar 에만 수행한다.
- 원본 경로에는 쓰기 금지다.

### Step 3. Baseline Contract 캡처

최소한 아래를 저장한다.

- workbook path
- sheet names / order / visibility
- used range
- freeze panes
- autofilter ranges
- merged ranges count
- ListObject names
- named ranges
- formula 존재 여부
- shape count
- sheet event 존재 여부
- VB component names

이 단계는 승격 전후 diff 기준이다.

### Step 4. 시트 분류

각 시트를 아래 중 하나로 분류한다.

- Input Form
- Operational Tracker
- Print Form
- Executive Report
- Raw Data
- Working Calc

분류 결과에 따라 포맷 강도를 다르게 적용한다.

### Step 5. 포맷 적용

우선순서:

1. theme
2. title / section / header hierarchy
3. column width / row height
4. print setup
5. 필요한 최소 조건부서식

적용 규칙:

- `User_Guide`: print-first, 1 page readable
- `Package_Intake`: 입력 영역과 action 영역만 명확화
- `Package_Checklist`: status column 가독성 우선
- `LIST_REV`: header, 숫자열, 날짜열, package 확장열 위주
- `SUMMARY`: 상단 KPI / 하단 matrix 만 정리
- `Evidence_Index`: 헤더와 폭만 최소 정리

## 9. 검증 절차

### Gate A. Workbook Open

- sidecar 가 repair prompt 없이 열린다
- read-only 로 잘못 열리지 않는다
- 실제 열린 경로가 sidecar 절대경로와 일치한다

### Gate B. Contract Diff

승격 가능한 diff:

- fill
- font
- alignment
- width / height
- print setup
- tab color

승격 불가 diff:

- sheet name / order / visibility 변경
- merged cell 증가
- named range 변경
- table name 변경
- formula 변경
- shape count 변경
- VBA component 변경
- sheet code module 변경

### Gate C. Raw Data Gate

- 실제 header row 는 여전히 1개
- data region 내부에 merged cell 없음
- filter range 정상
- blank column / blank row 유입 없음
- decorative heavy border 없음

### Gate D. Print Gate

- 제목과 헤더가 잘리지 않음
- 반복행이 의도대로 설정됨
- landscape / portrait 가 시트 목적과 맞음
- 정상 zoom 에서 읽힘

### Gate E. Accessibility Gate

- 색만으로 상태를 전달하지 않음
- 텍스트 대비가 충분함
- warning / total / ready / missing 상태가 명확함

### Gate F. Macro Safety Gate

포맷 작업이라도 아래는 다시 확인한다.

- workbook reopen 정상
- button / shape 클릭 경로가 그대로 존재
- sheet event 가 예상과 동일
- VBA project component 목록 변화 없음

## 10. 승격 절차

승격 조건:

1. sidecar 검증 전 항목 통과
2. promotion_decision.md 에 `PASS` 기록
3. 최신 원본이 sidecar 생성 시점 이후 변경되지 않음

승격 순서:

1. 원본 현재 백업 생성
2. sidecar 최종본을 원본 경로로 복사
3. 원본 경로에서 다시 open 검증
4. 핵심 시트 3~5개 수동 확인
5. 작업 보고서에 backup 경로와 승격 시각 기록

## 11. 롤백 절차

즉시 롤백 조건:

- repair prompt 발생
- VBA compile 문제
- 이벤트 미동작
- named range / table diff 발생
- 사용자가 시각 결과보다 동작 회귀를 우려하는 경우

롤백 방법:

1. 승격 직전 백업본 경로 확인
2. 해당 백업을 원본 경로로 복원
3. 원본 reopen 검증
4. 회귀 원인과 diff 를 문서화

## 12. 이번 세션 기준 개선 포인트

- 원본 workbook 직접 포맷 저장 금지
- active Excel 세션 재사용 금지
- 한글 경로와 동일 파일명 조합은 sidecar 를 ASCII temp 경로로 강제
- `LIST_REV` 같은 운영 시트의 freeze / window 상태는 포맷 대상이 아니라 별도 검토 항목으로 분리
- `Config`, `Result`, `Validation_Errors`, `LOG` 는 기본 포맷 대상에서 제외
- 포맷 스크립트는 validation report 없이 `PASS` 를 주장하지 않음

## 13. 권장 운영 문구

포맷 작업 요청 시 아래 문구를 기본으로 사용한다.

`원본은 건드리지 않고 sidecar copy 에서 formatting pass 를 수행한 뒤, contract diff 와 reopen 검증이 끝나면 승격하겠습니다.`

## 14. 최종 결론

안전한 formatting pass 의 핵심은 “예쁘게 만드는 것”이 아니라 “원본 동작 계약을 건드리지 않은 채 sidecar 에서 검증하고 승격하는 것”이다.  
향후 모든 `.xlsm` 포맷 작업은 이 문서를 기준 절차로 삼는다.
