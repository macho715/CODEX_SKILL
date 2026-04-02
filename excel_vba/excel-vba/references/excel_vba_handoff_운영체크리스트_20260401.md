# excel-vba handoff 운영 체크리스트

## 목적
- visual-layer 작업을 `excel-professional-formatting`에서 끝내고, 구조 민감 작업은 `excel-vba`로 안전하게 넘긴다.
- workbook 계약, 매크로 실행 가능성, COM/Unicode 리스크를 handoff 시점에 고정한다.
- 원본 workbook보다 copy 또는 sidecar 기준으로 검증한다.

## handoff가 필요한 경우
- 버튼 또는 shape 위치 조정이 필요함
- `OnAction` 점검이나 재바인딩이 필요함
- VBA, worksheet event, named range, table name, formula를 건드려야 함
- workbook open/save는 되지만 macro run이나 COM 실행이 불안정함
- non-ASCII 경로, 한글 caption, VBA reinjection, PowerShell Excel 실행이 포함됨

## handoff 입력물
- 대상 workbook 경로와 sidecar 경로
- 현재 활성 deliverable과 promotion boundary
- 시트 분류 요약
- 최근 formatting pass 결과와 남은 시각 요구사항
- 현재 알려진 리스크
  - shape drift 여부
  - visible session 문제 여부
  - non-ASCII path 여부
  - open workbook/user edit 여부

## excel-vba가 인계받을 때 먼저 확인할 것
- source가 원본인지 sidecar인지
- workbook이 이미 열려 있는지
- unsaved user edit가 있는지
- patch-in-place가 가능한지
- 기존 tables, named ranges, formulas, controls, worksheet events 충돌이 없는지
- `Result`, `Validation_Errors`, `LOG`가 유지되는지

## 구현 기본 원칙
- VBA를 기본 구현으로 둔다.
- Python은 workbook 자산 생성 또는 VBA 지원 용도일 때만 쓴다.
- 기존 계약이 있으면 delete/recreate보다 patch-in-place를 우선한다.
- file created와 macro runnable을 별도 체크로 본다.
- workbook-qualified `Application.Run`을 기본으로 사용한다.

## COM / Unicode 규칙
- `.xlsm` 생성 또는 VBA reinjection 후에는 save, close, reopen을 반드시 거친다.
- entry macro는 reopen 후 workbook-qualified `Application.Run`으로 실행한다.
- non-ASCII 경로면 ASCII sidecar 또는 copy를 우선한다.
- VBA source는 가능하면 ASCII-first로 유지한다.
- 한글 caption이 필요하면 raw literal보다 안전한 codepoint 방식 검토가 우선이다.

## 버튼 / shape / control handoff 규칙
- Forms control 우선
- 확인 항목
  - shape count
  - button name
  - caption
  - `OnAction`
  - click-equivalent macro 실행
- row/column 조정으로 drift가 생기면 formatting lane이 아니라 `excel-vba`에서 소유한다.

## 최소 검증 게이트
- workbook open
- VBA compile 이상 없음
- broken reference 없음
- named range 유지
- table name 유지
- worksheet event 충돌 없음
- `Result`, `Validation_Errors`, `LOG` 존재
- 버튼/shape/control binding 정상
- save / close / reopen 정상
- workbook-qualified entry macro 실행 정상

## QA 순서
1. 10-row test
2. total / count validation
3. edge-case validation
4. save / close / reopen
5. workbook-qualified macro smoke
6. user-facing control 확인
7. full-run recommendation

## formatting lane이 넘기기 전에 적어둘 것
- 무엇을 건드렸는지
- 무엇을 일부러 안 건드렸는지
- 어떤 요청이 visual-only 범위를 넘었는지
- promotion 여부
- rollback 기준

## 이번 세션 기준 handoff 교훈
- 버튼 이동은 처음부터 `excel-vba` 소유로 분리하는 것이 맞았다.
- visible session hang 조사와 formatting pass는 lane을 분리했어야 했다.
- external text trace는 환경상 신뢰할 수 없으므로 `LOG` 시트와 workbook 상태 기반 검증이 우선이다.
- sidecar-first는 잘 지켰고, 원본 미승격 원칙도 유지한 점은 올바른 handoff 전제였다.

## stop 조건
- open workbook에 user unsaved edit가 있음
- worksheet event collision이 해결되지 않음
- compile 또는 `Application.Run` 실패 원인이 미확정임
- contract-sensitive surface를 formatting lane이 계속 수정하려고 함
- original path 직접 수정 요구가 sidecar 검증보다 앞섬
