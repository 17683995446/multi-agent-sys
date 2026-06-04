
"""
多轮协商与让步策略优化
职责：多轮协商管理、动态让步机制、策略自适应调整、协商效率评估
"""

import uuid
import time
import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConcessionPattern(str, Enum):
    """让步模式"""
    LINEAR = "linear"          # 线性让步
    EXPONENTIAL = "exponential"  # 指数让步
    LOGARITHMIC = "logarithmic"  # 对数让步
    STEP = "step"              # 阶梯让步
    ADAPTIVE = "adaptive"       # 自适应让步


class RoundStatus(str, Enum):
    """轮次状态"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    DEADLOCKED = "deadlocked"


@dataclass
class ConcessionConfig:
    """让步配置"""
    initial_threshold: float = 0.8
    min_threshold: float = 0.3
    concession_rate: float = 0.1
    pattern: ConcessionPattern = ConcessionPattern.LINEAR
    max_rounds: int = 20
    deadlock_threshold: int = 3  # 连续无进展轮次


@dataclass
class NegotiationRound:
    """协商轮次"""
    round_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    round_number: int = 0
    status: RoundStatus = RoundStatus.PENDING
    proposals: List[Dict[str, Any]] = field(default_factory=list)
    acceptances: List[str] = field(default_factory=list)
    rejections: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    progress_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_proposal(self, proposal_data: Dict[str, Any]) -> None:
        """添加提案"""
        self.proposals.append(proposal_data)
        logger.debug(f"Round {self.round_number}: proposal added")

    def add_acceptance(self, agent_id: str) -> None:
        """添加接受"""
        self.acceptances.append(agent_id)
        logger.debug(f"Round {self.round_number}: accepted by {agent_id}")

    def add_rejection(self, agent_id: str) -> None:
        """添加拒绝"""
        self.rejections.append(agent_id)
        logger.debug(f"Round {self.round_number}: rejected by {agent_id}")

    def complete(self) -> None:
        """完成轮次"""
        self.status = RoundStatus.COMPLETED
        self.end_time = time.time()

    def duration(self) -> float:
        """轮次持续时间"""
        end = self.end_time or time.time()
        return end - self.start_time


@dataclass
class ConcessionState:
    """让步状态"""
    current_threshold: float = 0.8
    current_round: int = 0
    total_concession: float = 0.0
    consecutive_no_progress: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record_concession(self, old_threshold: float, new_threshold: float) -> None:
        """记录让步"""
        concession = old_threshold - new_threshold
        self.total_concession += concession
        self.history.append({
            "round": self.current_round,
            "old_threshold": old_threshold,
            "new_threshold": new_threshold,
            "concession": concession,
            "timestamp": time.time(),
        })
        logger.info(f"Concession: round={self.current_round}, {old_threshold:.3f} -> {new_threshold:.3f}")


class ConcessionEngine:
    """让步引擎"""

    def __init__(self, config: Optional[ConcessionConfig] = None):
        self.config = config or ConcessionConfig()
        self.state = ConcessionState(current_threshold=self.config.initial_threshold)
        logger.info(f"ConcessionEngine initialized: pattern={self.config.pattern}, "
                    f"initial={self.config.initial_threshold}, min={self.config.min_threshold}")

    def compute_threshold(self, round_number: int) -> float:
        """计算当前轮次的接受阈值"""
        pattern = self.config.pattern
        rate = self.config.concession_rate
        initial = self.config.initial_threshold
        minimum = self.config.min_threshold
        max_rounds = self.config.max_rounds

        if pattern == ConcessionPattern.LINEAR:
            threshold = initial - rate * round_number
        elif pattern == ConcessionPattern.EXPONENTIAL:
            decay = math.exp(-rate * round_number)
            threshold = minimum + (initial - minimum) * decay
        elif pattern == ConcessionPattern.LOGARITHMIC:
            if round_number == 0:
                threshold = initial
            else:
                threshold = initial - rate * math.log(1 + round_number)
        elif pattern == ConcessionPattern.STEP:
            step_size = max(1, max_rounds // 5)
            step = round_number // step_size
            # 阶梯让步：每个阶梯内阈值不变，跨阶梯时降低
            threshold = initial - (initial - minimum) * (step / max(1, max_rounds // step_size))
        elif pattern == ConcessionPattern.ADAPTIVE:
            threshold = self._adaptive_threshold(round_number)
        else:
            threshold = initial - rate * round_number

        threshold = max(threshold, minimum)
        logger.debug(f"ConcessionEngine: round={round_number}, threshold={threshold:.3f}")
        return threshold

    def _adaptive_threshold(self, round_number: int) -> float:
        """自适应阈值计算"""
        initial = self.config.initial_threshold
        minimum = self.config.min_threshold
        rate = self.config.concession_rate

        # 如果连续无进展，加速让步
        if self.state.consecutive_no_progress >= self.config.deadlock_threshold:
            accelerated_rate = rate * 2.0
            threshold = initial - accelerated_rate * round_number
            logger.info(f"Adaptive: deadlock detected, accelerating concession")
        else:
            threshold = initial - rate * round_number

        return max(threshold, minimum)

    def should_accept(self, utility: float, round_number: int) -> bool:
        """判断是否应该接受"""
        threshold = self.compute_threshold(round_number)
        accepted = utility >= threshold

        old_threshold = self.state.current_threshold
        self.state.current_threshold = threshold
        self.state.current_round = round_number

        if old_threshold != threshold:
            self.state.record_concession(old_threshold, threshold)

        if accepted:
            self.state.consecutive_no_progress = 0
            logger.info(f"Should accept: utility={utility:.3f} >= threshold={threshold:.3f}")
        else:
            self.state.consecutive_no_progress += 1
            logger.debug(f"Should reject: utility={utility:.3f} < threshold={threshold:.3f}")

        return accepted

    def is_deadlocked(self) -> bool:
        """是否陷入僵局"""
        return self.state.consecutive_no_progress >= self.config.deadlock_threshold

    def get_concession_summary(self) -> Dict[str, Any]:
        """获取让步摘要"""
        return {
            "current_threshold": self.state.current_threshold,
            "current_round": self.state.current_round,
            "total_concession": self.state.total_concession,
            "consecutive_no_progress": self.state.consecutive_no_progress,
            "is_deadlocked": self.is_deadlocked(),
            "concession_count": len(self.state.history),
        }


class MultiRoundNegotiator:
    """多轮协商管理器"""

    def __init__(self, concession_config: Optional[ConcessionConfig] = None):
        self.concession_engine = ConcessionEngine(concession_config)
        self.rounds: List[NegotiationRound] = []
        self.current_round: Optional[NegotiationRound] = None
        self.negotiation_result: Optional[Dict[str, Any]] = None
        logger.info("MultiRoundNegotiator initialized")

    def start_round(self, round_number: int) -> NegotiationRound:
        """开始新轮次"""
        round_obj = NegotiationRound(
            round_number=round_number,
            status=RoundStatus.ACTIVE,
        )
        self.rounds.append(round_obj)
        self.current_round = round_obj
        logger.info(f"Round {round_number} started")
        return round_obj

    def end_round(self, progress_score: float = 0.0) -> None:
        """结束当前轮次"""
        if self.current_round:
            self.current_round.progress_score = progress_score
            self.current_round.complete()
            logger.info(f"Round {self.current_round.round_number} completed, "
                       f"progress={progress_score:.3f}")

    def get_round_history(self) -> List[Dict[str, Any]]:
        """获取轮次历史"""
        return [
            {
                "round_number": r.round_number,
                "status": r.status.value,
                "proposal_count": len(r.proposals),
                "acceptance_count": len(r.acceptances),
                "rejection_count": len(r.rejections),
                "progress_score": r.progress_score,
                "duration": r.duration(),
            }
            for r in self.rounds
        ]

    def calculate_progress(self, total_agents: int) -> float:
        """计算当前轮次进展分数"""
        if not self.current_round:
            return 0.0
        acceptances = len(self.current_round.acceptances)
        if total_agents == 0:
            return 0.0
        return acceptances / total_agents

    def run_multi_round(self, session: Any, max_rounds: Optional[int] = None) -> Dict[str, Any]:
        """运行多轮协商"""
        from src.architecture.negotiation_engine import (
            NegotiationStrategyEngine, NegotiationStatus, NegotiationPhase
        )

        max_rounds = max_rounds or self.concession_engine.config.max_rounds
        strategy_engine = NegotiationStrategyEngine()
        agents = session.get_active_agents()
        total_agents = len(agents)

        logger.info(f"Multi-round negotiation started: {total_agents} agents, max {max_rounds} rounds")

        for round_num in range(1, max_rounds + 1):
            if session.status != NegotiationStatus.ACTIVE:
                break

            round_obj = self.start_round(round_num)

            for agent in agents:
                if not session.is_active():
                    break

                proposal = strategy_engine.generate_proposal(
                    agent, session.issues, session.history
                )

                round_obj.add_proposal({
                    "proposal_id": proposal.proposal_id,
                    "proposer_id": agent.agent_id,
                    "issue_values": proposal.issue_values,
                    "utility": proposal.utility,
                })

                session.history.add_proposal(proposal)

                # 评估
                for other_agent in agents:
                    if other_agent.agent_id != agent.agent_id:
                        utility = other_agent.calculate_utility(proposal)
                        if self.concession_engine.should_accept(utility, round_num):
                            round_obj.add_acceptance(other_agent.agent_id)
                        else:
                            round_obj.add_rejection(other_agent.agent_id)

            progress = self.calculate_progress(total_agents)
            self.end_round(progress)

            # 检查共识
            if progress >= 0.5:
                session.status = NegotiationStatus.SUCCESS
                session.phase = NegotiationPhase.CONSENSUS
                session.consensus_proposal = proposal if session.history.proposals else None
                logger.info(f"Consensus reached at round {round_num}")
                break

            # 检查僵局
            if self.concession_engine.is_deadlocked():
                logger.warning(f"Deadlock detected at round {round_num}")
                round_obj.status = RoundStatus.DEADLOCKED
                break

        result = {
            "success": session.status == NegotiationStatus.SUCCESS,
            "total_rounds": len(self.rounds),
            "concession_summary": self.concession_engine.get_concession_summary(),
            "round_history": self.get_round_history(),
        }
        self.negotiation_result = result
        logger.info(f"Multi-round negotiation finished: success={result['success']}, "
                    f"rounds={result['total_rounds']}")
        return result


class NegotiationEfficiencyEvaluator:
    """协商效率评估器"""

    def __init__(self):
        self.evaluations: List[Dict[str, Any]] = []

    def evaluate(self, negotiator: MultiRoundNegotiator) -> Dict[str, Any]:
        """评估协商效率"""
        rounds = negotiator.rounds
        total_rounds = len(rounds)
        total_proposals = sum(len(r.proposals) for r in rounds)
        total_acceptances = sum(len(r.acceptances) for r in rounds)
        total_rejections = sum(len(r.rejections) for r in rounds)
        total_duration = sum(r.duration() for r in rounds)

        avg_progress = 0.0
        if total_rounds > 0:
            avg_progress = sum(r.progress_score for r in rounds) / total_rounds

        acceptance_rate = total_acceptances / (total_acceptances + total_rejections) \
            if (total_acceptances + total_rejections) > 0 else 0.0

        efficiency_score = 0.0
        if total_rounds > 0 and total_proposals > 0:
            efficiency_score = (acceptance_rate * avg_progress) / (total_rounds * 0.1 + 1)

        evaluation = {
            "total_rounds": total_rounds,
            "total_proposals": total_proposals,
            "total_acceptances": total_acceptances,
            "total_rejections": total_rejections,
            "acceptance_rate": acceptance_rate,
            "avg_progress": avg_progress,
            "total_duration": total_duration,
            "efficiency_score": efficiency_score,
            "concession_summary": negotiator.concession_engine.get_concession_summary(),
        }

        self.evaluations.append(evaluation)
        logger.info(f"Efficiency evaluation: score={efficiency_score:.3f}, "
                    f"acceptance_rate={acceptance_rate:.3f}")
        return evaluation
