**Findings**

1. High: `Package_Intake`, `Evidence_Index`, `Package_Checklist` 를 “보존 후 패치”가 아니라 “전행 삭제 후 재생성”으로 처리했습니다. 이 방식은 ListObject, data validation, named range anchor, 기존 수식, 시트 수준 서식/도형 기준점을 같이 날릴 수 있어서 `excel-vba` 스킬의 핵심 보존 규칙을 정면으로 위반합니다. [apply_invoice_package_automation.py#L125](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L125) [apply_invoice_package_automation.py#L128](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L128)

2. High: 시트 이벤트 주입이 marker 기반 치환만 가정하고 있어서, 기존 `Worksheet_BeforeDoubleClick` 이 marker 없이 이미 존재하면 기존 핸들러를 제거하지 못한 채 새 핸들러를 추가합니다. 그 경우 VBA는 중복 프로시저로 바로 compile failure 위험이 납니다. 세션에서 “기존 이벤트와 충돌 없는지”를 사전 점검한 흔적도 없습니다. [apply_invoice_package_automation.py#L231](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L231) [apply_invoice_package_automation.py#L266](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L266) [simplify_workbook_ui.py#L148](C:/HVDC_WORK/REPORTS/기성/scripts/simplify_workbook_ui.py#L148)

3. High: 한글 UI 텍스트를 다루는 경로가 Unicode-safe 하지 않았고, 실제로 mojibake 문자열이 스크립트에 박혀 있었습니다. 이 문제는 workbook 사용자 가이드 시트에 그대로 반영됐고, 세션 후반에 별도 복구 절차가 필요했습니다. 즉 “실제 workbook 계약을 먼저 지킨다”는 VBA 스킬 관점에서, 문자열 입력 경로 검증이 빠져 있었습니다. [simplify_workbook_ui.py#L60](C:/HVDC_WORK/REPORTS/기성/scripts/simplify_workbook_ui.py#L60) [simplify_workbook_ui.py#L85](C:/HVDC_WORK/REPORTS/기성/scripts/simplify_workbook_ui.py#L85) [scenario_runtime_patch_report_20260330.md#L45](C:/HVDC_WORK/REPORTS/기성/output/doc/scenario_runtime_patch_report_20260330.md#L45)

4. Medium: VBA 모듈을 제거 후 재주입하면서도 compile, broken reference, named range resolution, control binding 검증이 없습니다. 저장은 하지만 “컴파일 가능 여부”를 확인하지 않기 때문에, 런타임 전에 잡을 수 있는 손상을 그대로 남길 수 있습니다. `excel-vba` 스킬의 필수 validation 항목이 빠져 있습니다. [apply_invoice_package_automation.py#L251](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L251) [apply_invoice_package_automation.py#L283](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L283)

5. Medium: 세션에서 이미 “Excel COM + 한글 경로 + 동일 파일명” 오동작이 확인됐는데, 자동화 스크립트는 여전히 원본을 그대로 `Workbooks.Open(fullpath)` 합니다. 즉 실제로 드러난 경로 해석 리스크가 툴링에 반영되지 않았습니다. 이번 세션의 핵심 장애 원인이 재발 가능한 상태로 남아 있습니다. [apply_invoice_package_automation.py#L247](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L247) [simplify_workbook_ui.py#L146](C:/HVDC_WORK/REPORTS/기성/scripts/simplify_workbook_ui.py#L146) [scenario_runtime_patch_report_20260330.md#L47](C:/HVDC_WORK/REPORTS/기성/output/doc/scenario_runtime_patch_report_20260330.md#L47)

6. Medium: 자동화 시작 전에 열린 workbook 을 강제로 닫으면서 `SaveChanges=False` 를 사용했습니다. 사용자가 workbook 을 열어두고 수동 수정 중이었다면 세션 스크립트가 그 변경을 조용히 버릴 수 있습니다. live `.xlsm` 작업에서 이건 운영 리스크가 큽니다. [apply_invoice_package_automation.py#L94](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L94) [apply_invoice_package_automation.py#L106](C:/HVDC_WORK/REPORTS/기성/scripts/apply_invoice_package_automation.py#L106)

**Open Questions**

- `Package_*` 시트에 원래 ListObject, validation, named range 가 있었는지 별도 감사가 필요합니다. 지금 스크립트 구조상 있었다면 손실 가능성을 배제할 수 없습니다.
- VBA 프로젝트의 `Compile VBAProject`, 참조 라이브러리 이상 여부, 버튼/도형 매크로 연결 상태는 세션 중 “열린다” 수준만 확인했고, 스킬 기준의 정식 검증은 아닙니다.

**Summary**

이번 세션의 부족한 점은 “VBA 코드를 수정한 것”보다 “live macro workbook 을 다루는 방식”에 더 컸습니다. `excel-vba` 관점에서 빠진 핵심은 1) 파괴적 시트 재생성 회피, 2) 이벤트 충돌 검증, 3) Unicode-safe 경로/문자열 처리, 4) compile/reference/named-range 검증, 5) 열린 workbook 의 무손실 처리입니다.

원하면 다음 턴에 이 5개를 기준으로 `세션 후속 개선 체크리스트`와 `자동 검증 스크립트`까지 바로 만들겠습니다.