#!/usr/bin/env python3
"""H1 검증: P 딕셔너리의 모델 키 조회가 None을 반환하는 경우"""

import sys
from pathlib import Path

# cost.py 임포트
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import cost

def test_p_dict_key_lookup():
    """P 딕셔너리에서 키 조회 테스트"""
    print("\n=== H1 Test: P dictionary key lookup ===")

    # 정상 케이스
    print("\n1. 정상 케이스 (opus):")
    result_opus = cost.P.get("opus")
    print(f"   P.get('opus') = {result_opus}")
    assert result_opus is not None

    print("\n2. 정상 케이스 (sonnet):")
    result_sonnet = cost.P.get("sonnet")
    print(f"   P.get('sonnet') = {result_sonnet}")
    assert result_sonnet is not None

    # 비정상 케이스: 존재하지 않는 모델 키
    print("\n3. 비정상 케이스 (존재하지 않는 모델):")
    result_invalid = cost.P.get("gpt4")
    print(f"   P.get('gpt4') = {result_invalid}")
    assert result_invalid is None, "존재하지 않는 키는 None 반환"

    # 직접 인덱싱 케이스
    print("\n4. 직접 인덱싱 (유효):")
    try:
        result = cost.P["opus"]
        print(f"   P['opus'] = {result}")
    except KeyError as e:
        print(f"   KeyError 발생: {e}")

    print("\n5. 직접 인덱싱 (유효하지 않음):")
    try:
        result = cost.P["gpt4"]
        print(f"   P['gpt4'] = {result}")
    except KeyError as e:
        print(f"   KeyError 발생: {e}")
        print(f"   → _c() 함수에서 i, o = P[m] 실행 시 KeyError 발생")

def test_c_function_with_invalid_model():
    """_c 함수를 유효하지 않은 모델과 호출"""
    print("\n\n=== H1 Simulation: _c() with invalid model ===")

    print("\n1. 유효한 모델 호출:")
    try:
        result = cost._c(1000000, 2000000, "opus")
        print(f"   _c(1000000, 2000000, 'opus') = ${result}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n2. 유효하지 않은 모델 호출:")
    try:
        result = cost._c(1000000, 2000000, "invalid_model")
        print(f"   _c(1000000, 2000000, 'invalid_model') = ${result}")
    except KeyError as e:
        print(f"   KeyError 발생: {e}")
        print(f"   → line 14에서 'i, o = P[m]' 실행 시 발생")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")

if __name__ == "__main__":
    test_p_dict_key_lookup()
    test_c_function_with_invalid_model()
    print("\n\n✓ H1 검증 완료")
