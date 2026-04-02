#!/usr/bin/env python3
"""cost.py 모듈 테스트 (calculate_3tier_cost 포함)"""

import sys
import pytest
from pathlib import Path

# cost.py 임포트
sys.path.insert(0, str(Path(__file__).parent.parent))
import cost


class TestCFunction:
    """_c() 함수 테스트"""

    def test_c_opus_basic(self):
        """Opus 기본 가격 계산"""
        # 1M input tokens = $5, 1M output tokens = $25
        result = cost._c(1000000, 1000000, "opus")
        assert result == 30.0

    def test_c_sonnet_basic(self):
        """Sonnet 기본 가격 계산"""
        # 1M input tokens = $3, 1M output tokens = $15
        result = cost._c(1000000, 1000000, "sonnet")
        assert result == 18.0

    def test_c_haiku_basic(self):
        """Haiku 기본 가격 계산"""
        # 1M input tokens = $1, 1M output tokens = $5
        result = cost._c(1000000, 1000000, "haiku")
        assert result == 6.0

    def test_c_zero_tokens(self):
        """0 토큰 계산"""
        result = cost._c(0, 0, "opus")
        assert result == 0.0

    def test_c_rounding(self):
        """가격 라운딩 검증"""
        result = cost._c(333333, 666666, "opus")
        # 333333/1e6 * 5 + 666666/1e6 * 25 = 1.666665 + 16.66665 = 18.333315
        assert result == 18.33


class TestCalculate3TierCost:
    """calculate_3tier_cost() 함수 테스트"""

    def test_basic_calculation(self):
        """기본 3-tier 비용 계산"""
        result = cost.calculate_3tier_cost(members=3, tokens=1000000)
        
        # 검증: 결과 구조
        assert 'total_cost' in result
        assert 'opus_cost' in result
        assert 'sonnet_cost' in result
        assert 'cost_per_member' in result
        
        # 검증: 1M 토큰, Opus 25%, Sonnet 75% 비율
        # ti = to = 500000
        # opus: 500000*0.25 = 125000 각각 -> _c(125000, 125000, "opus") = 3.75
        # sonnet: 500000*0.75 = 375000 각각 -> _c(375000, 375000, "sonnet") = 10.8
        # total = 14.55, per_member = 14.55 / 3 = 4.85
        assert result['total_cost'] > 0
        assert result['cost_per_member'] == result['total_cost'] / 3

    def test_single_member(self):
        """1인 팀원 비용"""
        result = cost.calculate_3tier_cost(members=1, tokens=1000000)
        assert result['cost_per_member'] == result['total_cost']

    def test_multiple_members(self):
        """다중 팀원 비용 분산"""
        tokens = 1000000
        result_1 = cost.calculate_3tier_cost(members=1, tokens=tokens)
        result_3 = cost.calculate_3tier_cost(members=3, tokens=tokens)
        
        # 동일 토큰에 대해 팀원이 많을수록 1인당 비용은 같아야 함
        assert result_1['total_cost'] == result_3['total_cost']
        assert result_3['cost_per_member'] == result_1['total_cost'] / 3

    def test_zero_tokens(self):
        """0 토큰 입력"""
        result = cost.calculate_3tier_cost(members=2, tokens=0)
        assert result['total_cost'] == 0.0
        assert result['opus_cost'] == 0.0
        assert result['sonnet_cost'] == 0.0
        assert result['cost_per_member'] == 0.0

    def test_invalid_members_zero(self):
        """팀원 수 0 (에러)"""
        with pytest.raises(ValueError, match="members must be > 0"):
            cost.calculate_3tier_cost(members=0, tokens=1000000)

    def test_invalid_members_negative(self):
        """팀원 수 음수 (에러)"""
        with pytest.raises(ValueError, match="members must be > 0"):
            cost.calculate_3tier_cost(members=-1, tokens=1000000)

    def test_invalid_tokens_negative(self):
        """토큰 수 음수 (에러)"""
        with pytest.raises(ValueError, match="tokens must be >= 0"):
            cost.calculate_3tier_cost(members=1, tokens=-1000)

    def test_custom_tier_split(self):
        """커스텀 티어 분할 비율"""
        # 50% Opus, 50% Sonnet
        custom_split = {'opus': 0.5, 'sonnet': 0.5}
        result = cost.calculate_3tier_cost(
            members=1, 
            tokens=1000000, 
            tier_split=custom_split
        )
        
        # Opus와 Sonnet 비용이 다르므로 총액이 다름
        default_result = cost.calculate_3tier_cost(members=1, tokens=1000000)
        assert result['total_cost'] != default_result['total_cost']

    def test_cost_per_member_precision(self):
        """1인당 비용 정밀도"""
        result = cost.calculate_3tier_cost(members=7, tokens=350000)
        # 라운딩 검증: 소수점 이하 2자리
        assert len(str(result['cost_per_member']).split('.')[-1]) <= 2


class TestCostIntegration:
    """통합 테스트"""

    def test_3tier_vs_all_opus(self):
        """3-tier vs All-Opus 비용 비교"""
        members = 3
        tokens = 350000
        
        # 3-tier 비용
        result_3tier = cost.calculate_3tier_cost(members=members, tokens=tokens)
        
        # All-Opus 비용 (근사치 계산)
        ti = int(tokens * 0.5)
        to = int(tokens * 0.5)
        all_opus = cost._c(ti, to, "opus") * members
        
        # 3-tier가 더 저렴해야 함
        assert result_3tier['total_cost'] < all_opus

    def test_consistency_across_models(self):
        """다양한 조건에서 일관성"""
        for members in [1, 3, 5, 10]:
            for tokens in [0, 100000, 1000000, 5000000]:
                result = cost.calculate_3tier_cost(members=members, tokens=tokens)
                
                # 기본 검증
                assert result['total_cost'] >= 0
                assert result['opus_cost'] >= 0
                assert result['sonnet_cost'] >= 0
                assert result['cost_per_member'] >= 0
                
                # 합산 검증
                assert abs(result['total_cost'] - 
                          (result['opus_cost'] + result['sonnet_cost'])) < 0.01


class TestLogAutoEnd:
    """v1.2: log_auto_end() 함수 테스트"""

    def test_log_auto_end_creates_entry(self, tmp_path):
        """JSONL에 auto_end 엔트리 기록"""
        log_file = tmp_path / "sessions.jsonl"
        import cost as _cost
        original_log = _cost.LOG
        _cost.LOG = log_file
        try:
            _cost.log_auto_end("test-sess-001", "2026-03-22T12:00:00Z")
            lines = log_file.read_text().strip().split("\n")
            assert len(lines) == 1
            import json
            entry = json.loads(lines[0])
            assert entry["ev"] == "auto_end"
            assert entry["session_id"] == "test-sess-001"
            assert entry["ts"] == "2026-03-22T12:00:00Z"
        finally:
            _cost.LOG = original_log

    def test_log_auto_end_creates_directory(self, tmp_path):
        """로그 디렉토리 없을 때 자동 생성"""
        log_file = tmp_path / "deep" / "nested" / "sessions.jsonl"
        import cost as _cost
        original_log = _cost.LOG
        _cost.LOG = log_file
        try:
            _cost.log_auto_end("test-sess-002")
            assert log_file.exists()
        finally:
            _cost.LOG = original_log

    def test_log_auto_end_default_timestamp(self, tmp_path):
        """timestamp 미지정 시 현재 시각 사용"""
        log_file = tmp_path / "sessions.jsonl"
        import cost as _cost
        original_log = _cost.LOG
        _cost.LOG = log_file
        try:
            _cost.log_auto_end("test-sess-003")
            import json
            entry = json.loads(log_file.read_text().strip())
            assert "ts" in entry
            assert entry["ts"].startswith("2026") or entry["ts"].startswith("20")  # ISO format
        finally:
            _cost.LOG = original_log


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


# ── v1.1: core/cost.py 테스트 ──────────────────────────

class TestCoreCost:
    """core/cost.py 모듈 테스트 (v1.1 신규)"""

    def test_parse_jsonl_empty_for_missing_file(self, tmp_path):
        """파일이 없으면 빈 리스트 반환"""
        from core.cost import parse_jsonl
        result = parse_jsonl(tmp_path / "nonexistent.jsonl")
        assert result == []

    def test_parse_jsonl_parses_entries(self, sample_cost_jsonl):
        """sample_cost_jsonl fixture에서 10건 파싱"""
        from core.cost import parse_jsonl
        entries = parse_jsonl(sample_cost_jsonl)
        assert len(entries) == 10

    def test_aggregate_total_sessions(self, sample_cost_jsonl):
        """aggregate가 올바른 total_sessions 반환"""
        from core.cost import parse_jsonl, aggregate
        entries = parse_jsonl(sample_cost_jsonl)
        data = aggregate(entries)
        assert data.total_sessions == 10

    def test_aggregate_empty(self):
        """빈 리스트 aggregate는 N/A 반환"""
        from core.cost import aggregate
        data = aggregate([])
        assert data.total_sessions == 0
        assert data.period == "N/A"

    def test_format_ascii_table_contains_header(self, sample_cost_jsonl):
        """ASCII 테이블에 'mstack Cost Report' 포함"""
        from core.cost import parse_jsonl, aggregate, format_ascii_table
        data = aggregate(parse_jsonl(sample_cost_jsonl))
        table = format_ascii_table(data)
        assert "mstack Cost Report" in table
