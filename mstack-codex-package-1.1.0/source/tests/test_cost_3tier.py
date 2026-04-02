"""회귀 테스트: calculate_3tier_cost()"""
import sys
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from cost import calculate_3tier_cost


class TestCalculate3TierCostHappyPath:
    """정상 경로 테스트"""

    def test_basic_calculation(self):
        """기본 계산: 3명, 1M 토큰"""
        result = calculate_3tier_cost(members=3, tokens=1_000_000)
        assert isinstance(result, dict)
        assert 'total_cost' in result
        assert 'opus_cost' in result
        assert 'sonnet_cost' in result
        assert 'cost_per_member' in result
        assert result['total_cost'] > 0
        assert result['cost_per_member'] == result['total_cost'] / 3

    def test_zero_tokens(self):
        """0 토큰: 0 비용"""
        result = calculate_3tier_cost(members=1, tokens=0)
        assert result['total_cost'] == 0.0
        assert result['opus_cost'] == 0.0
        assert result['sonnet_cost'] == 0.0
        assert result['cost_per_member'] == 0.0

    def test_custom_tier_split(self):
        """커스텀 Tier 비율"""
        custom_split = {'opus': 0.5, 'sonnet': 0.5}
        result = calculate_3tier_cost(members=2, tokens=1_000_000, tier_split=custom_split)
        assert result['total_cost'] > 0
        # Opus와 Sonnet 비용이 거의 같아야 함 (같은 토큰이 배분되었으므로)
        assert abs(result['opus_cost'] - result['sonnet_cost']) < 5  # 가격 차이로 인한 오차 허용

    def test_single_member(self):
        """1명 팀"""
        result = calculate_3tier_cost(members=1, tokens=500_000)
        assert result['cost_per_member'] == result['total_cost']

    def test_large_tokens(self):
        """대량 토큰"""
        result = calculate_3tier_cost(members=5, tokens=10_000_000)
        assert result['total_cost'] > 0
        assert result['cost_per_member'] > 0
        # 타임아웃 없이 완료됨을 확인
        assert isinstance(result, dict)


class TestCalculate3TierCostEdgeCases:
    """경계/에러 경로 테스트"""

    def test_zero_members_raises(self):
        """members=0 → ValueError"""
        with pytest.raises(ValueError, match="members must be > 0"):
            calculate_3tier_cost(members=0, tokens=1_000_000)

    def test_negative_members_raises(self):
        """members<0 → ValueError"""
        with pytest.raises(ValueError, match="members must be > 0"):
            calculate_3tier_cost(members=-1, tokens=1_000_000)

    def test_negative_tokens_raises(self):
        """tokens<0 → ValueError"""
        with pytest.raises(ValueError, match="tokens must be >= 0"):
            calculate_3tier_cost(members=3, tokens=-100)

    def test_fractional_members_accepted(self):
        """실수형 members는 허용 (예: 2.5 FTE)"""
        result = calculate_3tier_cost(members=2.5, tokens=1_000_000)
        assert result['cost_per_member'] == result['total_cost'] / 2.5

    def test_result_types(self):
        """반환 값의 타입 검증"""
        result = calculate_3tier_cost(members=3, tokens=500_000)
        assert isinstance(result['total_cost'], float)
        assert isinstance(result['opus_cost'], float)
        assert isinstance(result['sonnet_cost'], float)
        assert isinstance(result['cost_per_member'], float)

    def test_cost_composition(self):
        """opus_cost + sonnet_cost == total_cost"""
        result = calculate_3tier_cost(members=3, tokens=1_000_000)
        assert abs(result['opus_cost'] + result['sonnet_cost'] - result['total_cost']) < 0.01


class TestCalculate3TierCostRegressions:
    """회귀 시나리오"""

    def test_docstring_exists(self):
        """함수 docstring 존재"""
        from cost import calculate_3tier_cost
        assert calculate_3tier_cost.__doc__ is not None
        assert '3-Tier' in calculate_3tier_cost.__doc__

    def test_default_tier_split(self):
        """기본 Tier 비율 (Opus 25%, Sonnet 75%)"""
        result = calculate_3tier_cost(members=1, tokens=1_000_000)
        # Sonnet 비용이 Opus보다 커야 함 (더 많은 토큰 배분)
        assert result['sonnet_cost'] > result['opus_cost']

    def test_cost_per_member_precision(self):
        """비용/인당 정밀도 (소수점 2자리)"""
        result = calculate_3tier_cost(members=3, tokens=999_999)
        # cost_per_member는 round(..., 2)로 처리되어야 함
        assert len(str(result['cost_per_member']).split('.')[-1]) <= 2
