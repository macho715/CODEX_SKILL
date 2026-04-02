#!/usr/bin/env python3
"""H2 검증: log_end() 호출 시 ti 또는 to 매개변수가 None인 경우"""

import sys
from pathlib import Path

# cost.py 임포트
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import cost as cost_module

def test_mixed_cost_with_none_values():
    """log_end() 함수에 None 값 전달"""
    print("\n=== H2 Test: log_end() with None values ===")

    # 시뮬레이션: line 30의 계산 과정
    print("\n1. 정상 케이스:")
    ti, to = 1000000, 2000000
    print(f"   ti={ti}, to={to}")
    try:
        cost1 = cost_module._c(int(ti * .25), int(to * .25), "opus")
        cost2 = cost_module._c(int(ti * .75), int(to * .75), "sonnet")
        total = cost1 + cost2
        print(f"   cost1 (opus) = ${cost1}")
        print(f"   cost2 (sonnet) = ${cost2}")
        print(f"   total = ${total}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n2. ti가 None인 경우:")
    ti, to = None, 2000000
    print(f"   ti={ti}, to={to}")
    try:
        result = cost_module._c(int(ti * .25), int(to * .25), "opus")
        print(f"   result = {result}")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")
        print(f"   → int(None * .25) 계산에서 발생")

    print("\n3. to가 None인 경우:")
    ti, to = 1000000, None
    print(f"   ti={ti}, to={to}")
    try:
        result = cost_module._c(int(ti * .25), int(to * .25), "opus")
        print(f"   result = {result}")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")
        print(f"   → int(to * .25) 계산에서 발생")

    print("\n4. 둘 다 None인 경우:")
    ti, to = None, None
    print(f"   ti={ti}, to={to}")
    try:
        result = cost_module._c(int(ti * .25), int(to * .25), "opus")
        print(f"   result = {result}")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")

def test_mixed_cost_direct_simulation():
    """line 30의 정확한 코드 재현"""
    print("\n\n=== H2 Direct Simulation: Line 30 calculation ===")

    # 케이스 1: 정상
    print("\n1. 정상 케이스:")
    ti, to = 4000000, 8000000
    try:
        total_cost = cost_module._c(int(ti * .25), int(to * .25), "opus") + cost_module._c(int(ti * .75), int(to * .75), "sonnet")
        print(f"   cost = ${total_cost}")
    except Exception as e:
        print(f"   Error: {type(e).__name__}: {e}")

    # 케이스 2: ti가 None (예: 데이터베이스 쿼리 결과가 None)
    print("\n2. ti=None 케이스:")
    ti, to = None, 8000000
    try:
        # 이 부분이 정확히 line 30에서 실행되는 코드
        total_cost = cost_module._c(int(ti * .25), int(to * .25), "opus") + cost_module._c(int(ti * .75), int(to * .75), "sonnet")
        print(f"   cost = ${total_cost}")
    except TypeError as e:
        print(f"   TypeError 발생: {e}")
        print(f"   → 정확히 에러 메시지와 일치! 'NoneType' and 'float'")

    # 케이스 3: 함수 호출 스택 추적
    print("\n3. 에러 발생 지점 추적:")
    print("   line 30: cost = _c(...) + _c(...)")
    print("   첫 번째 _c 호출에서:")
    print("     - int(ti * .25) 실행")
    print("     - ti=None이므로 None * .25 = TypeError")

if __name__ == "__main__":
    test_mixed_cost_with_none_values()
    test_mixed_cost_direct_simulation()
    print("\n\n✓ H2 검증 완료")
