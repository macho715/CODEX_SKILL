#!/usr/bin/env python3
"""H3 검증: 타입 강제 변환 실패 (ti, to가 정수 변환 불가능한 타입)"""

import sys
from pathlib import Path

# cost.py 임포트
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import cost

def test_type_conversion_failure():
    """타입 변환 실패 시뮬레이션"""
    print("\n=== H3 Test: Type conversion failure ===")

    print("\n1. 정상 케이스 (int, float):")
    ti, to = 1000000, 2000000
    try:
        cost1 = cost._c(int(ti * .25), int(to * .25), "opus")
        print(f"   _c(int({ti} * .25), int({to} * .25), 'opus') = ${cost1}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n2. ti가 객체인 경우:")
    class CustomObject:
        def __init__(self, val):
            self.val = val

    ti = CustomObject(1000000)
    to = 2000000
    print(f"   ti=CustomObject({ti.val}), to={to}")
    try:
        result = cost._c(int(ti * .25), int(to * .25), "opus")
        print(f"   result = {result}")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")
        print(f"   → ti * .25 계산에서 발생 (CustomObject에 __mul__ 없음)")

    print("\n3. ti가 str인 경우:")
    ti = "1000000"
    to = 2000000
    print(f"   ti='{ti}', to={to}")
    try:
        # str * float = str 반복 (정수로 변환 가능)
        result_intermediate = ti * .25
        print(f"   '{ti}' * .25 = {repr(result_intermediate)}")
        result = int(result_intermediate)
        print(f"   int(result) = {result}")
    except Exception as e:
        print(f"   Error during int() conversion: {e}")

    print("\n4. ti가 str이고 int() 변환 실패:")
    ti = "not_a_number"
    to = 2000000
    print(f"   ti='{ti}', to={to}")
    try:
        # str * float은 TypeError
        result = ti * .25
        print(f"   '{ti}' * .25 = {repr(result)}")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")
        print(f"   → str과 float의 곱셈 연산 불지원")

def test_P_dict_type_issue():
    """P 딕셔너리 값의 타입 문제"""
    print("\n\n=== H3 Alternative: P dict values are None ===")

    print("\n1. P 딕셔너리 현재 상태:")
    print(f"   P = {cost.P}")

    print("\n2. 만약 P['opus']가 None이면:")
    # 시뮬레이션
    original_P = cost.P.copy()
    cost.P["opus"] = None

    print(f"   P['opus'] = {cost.P['opus']}")
    try:
        i, o = cost.P["opus"]
        print(f"   i, o = {i}, {o}")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")
        print(f"   → None을 언패킹할 수 없음")

    # 복원
    cost.P = original_P

    print("\n3. 만약 P['opus']의 첫 번째 요소가 None이면:")
    cost.P["opus"] = (None, 25)
    print(f"   P['opus'] = {cost.P['opus']}")
    try:
        i, o = cost.P["opus"]
        print(f"   i = {i}, o = {o}")
        # _c 함수에서: ti / 1e6 * i
        ti = 250000
        result = ti / 1e6 * i  # None * float
        print(f"   {ti} / 1e6 * {i} = {result}")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")
        print(f"   → 정확히 에러 메시지와 일치! 'NoneType' and 'float'")

    # 복원
    cost.P = original_P

if __name__ == "__main__":
    test_type_conversion_failure()
    test_P_dict_type_issue()
    print("\n\n✓ H3 검증 완료")
