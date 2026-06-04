
"""
阶段47验收测试：多轮协商与让步策略优化
"""

import pytest
import time
import math

from src.architecture.multi_round_negotiator import (
    ConcessionPattern, RoundStatus,
    ConcessionConfig, NegotiationRound, ConcessionState,
    ConcessionEngine, MultiRoundNegotiator, NegotiationEfficiencyEvaluator
)
from src.architecture.negotiation_engine import (
    NegotiationPhase, NegotiationStatus, NegotiationStrategy,
    NegotiationIssue, NegotiationProposal, NegotiationAgent,
    NegotiationHistory, NegotiationSession,
    reset_negotiation_service
)


class TestConcessionConfig:
    """测试让步配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = ConcessionConfig()
        assert config.initial_threshold == 0.8
        assert config.min_threshold == 0.3
        assert config.concession_rate == 0.1
        assert config.pattern == ConcessionPattern.LINEAR
        assert config.max_rounds == 20

    def test_custom_config(self):
        """测试自定义配置"""
        config = ConcessionConfig(
            initial_threshold=0.9,
            min_threshold=0.2,
            concession_rate=0.05,
            pattern=ConcessionPattern.EXPONENTIAL,
            max_rounds=50,
        )
        assert config.initial_threshold == 0.9
        assert config.pattern == ConcessionPattern.EXPONENTIAL


class TestNegotiationRound:
    """测试协商轮次"""

    def test_round_creation(self):
        """测试轮次创建"""
        r = NegotiationRound(round_number=1)
        assert r.round_number == 1
        assert r.status == RoundStatus.PENDING
        assert len(r.proposals) == 0

    def test_add_proposal(self):
        """测试添加提案"""
        r = NegotiationRound(round_number=1)
        r.add_proposal({"proposal_id": "p1", "utility": 0.5})
        assert len(r.proposals) == 1

    def test_add_acceptance(self):
        """测试添加接受"""
        r = NegotiationRound(round_number=1)
        r.add_acceptance("agent_1")
        assert len(r.acceptances) == 1

    def test_add_rejection(self):
        """测试添加拒绝"""
        r = NegotiationRound(round_number=1)
        r.add_rejection("agent_2")
        assert len(r.rejections) == 1

    def test_complete_round(self):
        """测试完成轮次"""
        r = NegotiationRound(round_number=1)
        r.complete()
        assert r.status == RoundStatus.COMPLETED
        assert r.end_time is not None

    def test_round_duration(self):
        """测试轮次持续时间"""
        r = NegotiationRound(round_number=1)
        duration = r.duration()
        assert duration >= 0


class TestConcessionEngine:
    """测试让步引擎"""

    def test_linear_concession(self):
        """测试线性让步"""
        config = ConcessionConfig(
            pattern=ConcessionPattern.LINEAR,
            initial_threshold=0.8,
            concession_rate=0.1,
            min_threshold=0.3,
        )
        engine = ConcessionEngine(config)

        t0 = engine.compute_threshold(0)
        t5 = engine.compute_threshold(5)
        t10 = engine.compute_threshold(10)

        assert t0 == pytest.approx(0.8, abs=0.01)
        assert t5 == pytest.approx(0.3, abs=0.01)  # 0.8 - 0.1*5 = 0.3
        assert t10 == pytest.approx(0.3, abs=0.01)  # clamped to min

    def test_exponential_concession(self):
        """测试指数让步"""
        config = ConcessionConfig(
            pattern=ConcessionPattern.EXPONENTIAL,
            initial_threshold=0.8,
            min_threshold=0.3,
            concession_rate=0.2,
        )
        engine = ConcessionEngine(config)

        t0 = engine.compute_threshold(0)
        t5 = engine.compute_threshold(5)

        assert t0 > t5  # 阈值应递减
        assert t5 >= config.min_threshold

    def test_logarithmic_concession(self):
        """测试对数让步"""
        config = ConcessionConfig(
            pattern=ConcessionPattern.LOGARITHMIC,
            initial_threshold=0.8,
            concession_rate=0.1,
            min_threshold=0.3,
        )
        engine = ConcessionEngine(config)

        t0 = engine.compute_threshold(0)
        t1 = engine.compute_threshold(1)
        t10 = engine.compute_threshold(10)

        assert t0 == pytest.approx(0.8, abs=0.01)
        assert t1 < t0
        assert t10 < t1

    def test_step_concession(self):
        """测试阶梯让步"""
        config = ConcessionConfig(
            pattern=ConcessionPattern.STEP,
            initial_threshold=0.8,
            concession_rate=0.1,
            min_threshold=0.3,
            max_rounds=20,
        )
        engine = ConcessionEngine(config)

        t0 = engine.compute_threshold(0)
        t1 = engine.compute_threshold(1)
        t4 = engine.compute_threshold(4)
        t5 = engine.compute_threshold(5)

        # 同一阶梯内阈值相同
        assert t0 == t1
        # 跨阶梯阈值降低
        assert t5 < t0

    def test_should_accept(self):
        """测试接受判断"""
        config = ConcessionConfig(
            pattern=ConcessionPattern.LINEAR,
            initial_threshold=0.8,
            concession_rate=0.1,
            min_threshold=0.3,
        )
        engine = ConcessionEngine(config)

        # 第0轮，阈值0.8
        assert engine.should_accept(0.9, 0) == True
        assert engine.should_accept(0.7, 0) == False

    def test_deadlock_detection(self):
        """测试僵局检测"""
        config = ConcessionConfig(deadlock_threshold=3)
        engine = ConcessionEngine(config)

        assert engine.is_deadlocked() == False

        engine.state.consecutive_no_progress = 3
        assert engine.is_deadlocked() == True

    def test_concession_summary(self):
        """测试让步摘要"""
        engine = ConcessionEngine()
        summary = engine.get_concession_summary()

        assert "current_threshold" in summary
        assert "current_round" in summary
        assert "is_deadlocked" in summary


class TestMultiRoundNegotiator:
    """测试多轮协商管理器"""

    def setup_method(self):
        reset_negotiation_service()

    def test_start_and_end_round(self):
        """测试开始和结束轮次"""
        negotiator = MultiRoundNegotiator()
        r = negotiator.start_round(1)
        assert r.round_number == 1
        assert r.status == RoundStatus.ACTIVE

        negotiator.end_round(0.5)
        assert r.status == RoundStatus.COMPLETED
        assert r.progress_score == 0.5

    def test_round_history(self):
        """测试轮次历史"""
        negotiator = MultiRoundNegotiator()
        negotiator.start_round(1)
        negotiator.end_round(0.3)
        negotiator.start_round(2)
        negotiator.end_round(0.6)

        history = negotiator.get_round_history()
        assert len(history) == 2
        assert history[0]["round_number"] == 1
        assert history[1]["round_number"] == 2

    def test_calculate_progress(self):
        """测试进展计算"""
        negotiator = MultiRoundNegotiator()
        assert negotiator.calculate_progress(10) == 0.0

        negotiator.start_round(1)
        negotiator.current_round.add_acceptance("a1")
        negotiator.current_round.add_acceptance("a2")

        progress = negotiator.calculate_progress(5)
        assert progress == pytest.approx(0.4, abs=0.01)

    def test_run_multi_round_negotiation(self):
        """测试运行多轮协商"""
        issue = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        agent1 = NegotiationAgent(agent_id="a1", name="buyer", strategy=NegotiationStrategy.COLLABORATIVE, issues=[issue])
        agent2 = NegotiationAgent(agent_id="a2", name="seller", strategy=NegotiationStrategy.COLLABORATIVE, issues=[issue])

        session = NegotiationSession(topic="multi_round_test")
        session.add_agent(agent1)
        session.add_agent(agent2)
        session.add_issue(issue)
        session.start()  # 必须先启动会话

        config = ConcessionConfig(max_rounds=5, initial_threshold=0.3, min_threshold=0.1)
        negotiator = MultiRoundNegotiator(config)
        result = negotiator.run_multi_round(session, max_rounds=5)

        assert result is not None
        assert "total_rounds" in result
        assert "concession_summary" in result


class TestEfficiencyEvaluator:
    """测试协商效率评估器"""

    def test_evaluate_empty(self):
        """测试评估空协商"""
        negotiator = MultiRoundNegotiator()
        evaluator = NegotiationEfficiencyEvaluator()
        result = evaluator.evaluate(negotiator)

        assert result["total_rounds"] == 0
        assert result["total_proposals"] == 0
        assert result["efficiency_score"] == 0.0

    def test_evaluate_with_rounds(self):
        """测试评估有轮次的协商"""
        negotiator = MultiRoundNegotiator()
        r1 = negotiator.start_round(1)
        r1.add_proposal({"proposal_id": "p1"})
        r1.add_acceptance("a1")
        r1.add_rejection("a2")
        negotiator.end_round(0.5)

        evaluator = NegotiationEfficiencyEvaluator()
        result = evaluator.evaluate(negotiator)

        assert result["total_rounds"] == 1
        assert result["total_proposals"] == 1
        assert result["total_acceptances"] == 1
        assert result["total_rejections"] == 1
        assert result["acceptance_rate"] == pytest.approx(0.5, abs=0.01)
