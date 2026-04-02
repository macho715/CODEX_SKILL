# Output Contract

## Core rule
최종 산출물은 “수정이 필요한 문구만” 페이지 단위로 정리한 패치 목록이다.
전체 재작성본, 문단 통째 대체, 파일 생성 언급은 기본적으로 금지한다.

## Page unit
- PDF/Word의 page를 우선 사용한다.
- PPT는 기본적으로 slide를 page처럼 취급한다.
- 사용자가 `Slide X` 표기를 명시하면 그 형식에 맞춘다.
- 페이지 번호를 추정하지 않는다.

## Allowed reason labels
아래 라벨 중 하나 이상을 사용한다.
- 사실오류
- 번역투 제거
- 용어 통일
- 문체 보정
- 수치 불명확
- 현지화 판단 필요

## Standard Patch Mode
```text
1. 검토 결과 요약
- 총 검토 페이지 수
- 변경 필요 페이지 수
- 핵심 패치 기준 3~5줄

2. 페이지별 변경 문구
[Page 3]
- 기존: “The cargo inward to site is pending.”
- 변경: “Site delivery of the cargo is pending.”
- 사유: 번역투 제거 / 문체 보정

[Page 7]
- 기존: “선적 서류 준비를 진행 중입니다.”
- 변경: “선적 서류를 준비하고 있습니다.”
- 사유: 번역투 제거 / 문체 보정

3. 자체 검증 결과
- 1차 검증: 사실관계 검토 완료
- 2차 검증: 한글 표현/문체 검토 완료
- 3차 검증: 영문 표현/용어 검토 완료
- 4차 검증: 출력 형식 및 페이지 누락 여부 검토 완료
```

## Strict Patch-Only Mode
아래 형식만 허용한다.
```text
[Page 3]
- 기존: “The cargo inward to site is pending.”
- 변경: “Site delivery of the cargo is pending.”
- 사유: 번역투 제거 / 문체 보정
```

## Trimming rules
- 변경 없는 페이지는 출력하지 않는다.
- 한 페이지에 변경점이 많아도 “변경이 필요한 구문”만 나눈다.
- 장문 설명 대신 바로 반영 가능한 수정문구를 우선한다.

## Integrity check
최종 제출 직전 아래를 다시 확인한다.
- `기존` 문구가 실제 원문에 존재하는가
- `변경` 문구가 의미를 과도하게 바꾸지 않는가
- `사유`가 실제 변경 이유와 맞는가
- 페이지가 잘못 매핑되지 않았는가
