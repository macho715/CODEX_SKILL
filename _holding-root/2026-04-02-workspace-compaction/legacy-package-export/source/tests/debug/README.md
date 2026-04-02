# tests/debug/

실험용·디버그용 테스트 디렉토리.

**pytest 수집에서 제외됨** (`pyproject.toml` → `--ignore=tests/debug`).

이 디렉토리의 파일은 글로벌 상태를 직접 변이하거나, 의도적 실패를 유발하는 등
정규 테스트 스위트에 포함하면 안 되는 코드를 담는다.

개별 실행: `python -m pytest tests/debug/test_xxx.py -v`
