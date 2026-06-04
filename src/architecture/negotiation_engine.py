
"""
多Agent协商谈判机制
职责：协商协议、协商会话管理、谈判策略、共识达成
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class NegotiationPhase(str, Enum):
    """协商阶段"""
    INITIALIZATION = "initialization"
    PROPOSAL = "proposal"
    COUNTER_PROPOSAL = "counter_proposal"
    ARGUMENTATION = "argumentation"
    CONSENSUS = "consensus"
    TERMINATION = "termination"


class NegotiationStatus(str, Enum):
    """协商状态"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class NegotiationStrategy(str, Enum):
    """谈判策略"""
    CONCILIATORY = "conciliatory"
    COMPETITIVE = "competitive"
    COLLABORATIVE = "collaborative"
    ADAPTIVE = "adaptive"
    RANDOM = "random"


class MessageType(str, Enum):
    """消息类型"""
    PROPOSAL = "proposal"
    COUNTER_PROPOSAL = "counter_proposal"
    ACCEPT = "accept"
    REJECT = "reject"
    ARGUMENT = "argument"
    QUESTION = "question"
    INFORM = "inform"
    TERMINATE = "terminate"


@dataclass
class NegotiationIssue:
    """协商议题"""
    issue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    priority: float = 1.0
    possible_values: List[Any] = field(default_factory=list)
    current_value: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"NegotiationIssue created: id={self.issue_id}, name={self.name}")


@dataclass
class NegotiationProposal:
    """协商提案"""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposer_id: str = ""
    issue_values: Dict[str, Any] = field(default_factory=dict)
    utility: float = 0.0
    arguments: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_issue_value(self, issue_key: str) -> Any:
        """获取议题值"""
        return self.issue_values.get(issue_key)

    def set_issue_value(self, issue_key: str, value: Any) -> None:
        """设置议题值"""
        self.issue_values[issue_key] = value
        logger.debug(f"Proposal {self.proposal_id[:8]}: set {issue_key}={value}")


@dataclass
class NegotiationMessage:
    """协商消息"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_ids: List[str] = field(default_factory=list)
    message_type: MessageType = MessageType.INFORM
    content: Any = None
    proposal: Optional[NegotiationProposal] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NegotiationAgent:
    """协商Agent"""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: str = ""
    strategy: NegotiationStrategy = NegotiationStrategy.COLLABORATIVE
    issues: List[NegotiationIssue] = field(default_factory=list)
    preferences: Dict[str, float] = field(default_factory=dict)
    utility_function: Optional[Callable[[Dict[str, Any]], float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def _build_issue_map(self) -> Dict[str, NegotiationIssue]:
        """构建name到issue的映射"""
        result = {}
        for issue in self.issues:
            result[issue.name] = issue
        return result

    def calculate_utility(self, proposal: NegotiationProposal) -> float:
        """计算提案效用"""
        if self.utility_function:
            return self.utility_function(proposal.issue_values)

        total_utility = 0.0
        total_priority = 0.0
        issue_map = self._build_issue_map()

        for issue_name, value in proposal.issue_values.items():
            issue = issue_map.get(issue_name)
            if issue is not None and value in issue.possible_values:
                index = issue.possible_values.index(value)
                max_index = len(issue.possible_values) - 1
                normalized_value = index / max_index if max_index > 0 else 0.0
                total_utility += normalized_value * issue.priority
                total_priority += issue.priority

        result = total_utility / total_priority if total_priority > 0 else 0.0
        logger.debug(f"Agent {self.name}: utility={result:.4f}")
        return result

    def get_best_proposal(self, proposals: List[NegotiationProposal]) -> Optional[NegotiationProposal]:
        """获取最佳提案"""
        if not proposals:
            return None

        best_proposal = None
        best_utility = -float('inf')

        for proposal in proposals:
            utility = self.calculate_utility(proposal)
            if utility > best_utility:
                best_utility = utility
                best_proposal = proposal

        return best_proposal


@dataclass
class NegotiationHistory:
    """协商历史记录"""
    history_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[NegotiationMessage] = field(default_factory=list)
    proposals: List[NegotiationProposal] = field(default_factory=list)
    accepted_proposals: List[NegotiationProposal] = field(default_factory=list)

    def add_message(self, message: NegotiationMessage) -> None:
        """添加消息"""
        self.messages.append(message)
        logger.debug(f"History: message added from {message.sender_id}, type={message.message_type}")

    def add_proposal(self, proposal: NegotiationProposal) -> None:
        """添加提案"""
        self.proposals.append(proposal)
        logger.debug(f"History: proposal added by {proposal.proposer_id}")

    def accept_proposal(self, proposal: NegotiationProposal) -> None:
        """接受提案"""
        self.accepted_proposals.append(proposal)
        logger.debug(f"History: proposal {proposal.proposal_id[:8]} accepted")


class NegotiationStrategyEngine:
    """协商策略引擎"""

    def __init__(self):
        self.strategies: Dict[NegotiationStrategy, Callable] = {}
        self._register_default_strategies()
        logger.debug("NegotiationStrategyEngine initialized")

    def _register_default_strategies(self):
        """注册默认策略"""
        self.strategies[NegotiationStrategy.CONCILIATORY] = self._conciliatory_strategy
        self.strategies[NegotiationStrategy.COMPETITIVE] = self._competitive_strategy
        self.strategies[NegotiationStrategy.COLLABORATIVE] = self._collaborative_strategy
        self.strategies[NegotiationStrategy.ADAPTIVE] = self._adaptive_strategy
        self.strategies[NegotiationStrategy.RANDOM] = self._random_strategy

    def generate_proposal(self, agent: NegotiationAgent,
                        issues: List[NegotiationIssue],
                        history: NegotiationHistory) -> NegotiationProposal:
        """生成提案"""
        strategy_func = self.strategies.get(agent.strategy)
        if strategy_func:
            proposal = strategy_func(agent, issues, history)
        else:
            proposal = self._collaborative_strategy(agent, issues, history)
        logger.info(f"Agent {agent.name} generated proposal via {agent.strategy}: {proposal.issue_values}")
        return proposal

    def _conciliatory_strategy(self, agent: NegotiationAgent,
                             issues: List[NegotiationIssue],
                             history: NegotiationHistory) -> NegotiationProposal:
        """和解策略：逐步让步"""
        proposal = NegotiationProposal(proposer_id=agent.agent_id)
        for issue in issues:
            if issue.possible_values:
                proposal.set_issue_value(issue.name, issue.possible_values[-1])
        proposal.utility = agent.calculate_utility(proposal)
        return proposal

    def _competitive_strategy(self, agent: NegotiationAgent,
                            issues: List[NegotiationIssue],
                            history: NegotiationHistory) -> NegotiationProposal:
        """竞争策略：提出最佳提案"""
        proposal = NegotiationProposal(proposer_id=agent.agent_id)
        for issue in issues:
            if issue.possible_values:
                proposal.set_issue_value(issue.name, issue.possible_values[0])
        proposal.utility = agent.calculate_utility(proposal)
        return proposal

    def _collaborative_strategy(self, agent: NegotiationAgent,
                              issues: List[NegotiationIssue],
                              history: NegotiationHistory) -> NegotiationProposal:
        """协作策略：尝试中间值"""
        proposal = NegotiationProposal(proposer_id=agent.agent_id)
        for issue in issues:
            if issue.possible_values:
                mid_index = len(issue.possible_values) // 2
                proposal.set_issue_value(issue.name, issue.possible_values[mid_index])
        proposal.utility = agent.calculate_utility(proposal)
        return proposal

    def _adaptive_strategy(self, agent: NegotiationAgent,
                           issues: List[NegotiationIssue],
                           history: NegotiationHistory) -> NegotiationProposal:
        """自适应策略：根据历史调整"""
        if not history.proposals:
            return self._collaborative_strategy(agent, issues, history)

        last_proposal = history.proposals[-1]
        proposal = NegotiationProposal(proposer_id=agent.agent_id)

        for issue in issues:
            if issue.possible_values:
                current_value = last_proposal.get_issue_value(issue.name)
                if current_value is not None and current_value in issue.possible_values:
                    idx = issue.possible_values.index(current_value)
                    new_idx = min(idx + 1, len(issue.possible_values) - 1)
                    proposal.set_issue_value(issue.name, issue.possible_values[new_idx])
                else:
                    mid_index = len(issue.possible_values) // 2
                    proposal.set_issue_value(issue.name, issue.possible_values[mid_index])

        proposal.utility = agent.calculate_utility(proposal)
        return proposal

    def _random_strategy(self, agent: NegotiationAgent,
                         issues: List[NegotiationIssue],
                         history: NegotiationHistory) -> NegotiationProposal:
        """随机策略"""
        import random
        proposal = NegotiationProposal(proposer_id=agent.agent_id)
        for issue in issues:
            if issue.possible_values:
                value = random.choice(issue.possible_values)
                proposal.set_issue_value(issue.name, value)
        proposal.utility = agent.calculate_utility(proposal)
        return proposal

    def evaluate_proposal(self, agent: NegotiationAgent,
                        proposal: NegotiationProposal) -> Tuple[bool, float]:
        """评估提案"""
        utility = agent.calculate_utility(proposal)
        threshold = 0.5
        accepted = utility >= threshold
        logger.info(f"Agent {agent.name} evaluates proposal: utility={utility:.4f}, accepted={accepted}")
        return accepted, utility


@dataclass
class NegotiationSession:
    """协商会话"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    agents: Dict[str, NegotiationAgent] = field(default_factory=dict)
    issues: List[NegotiationIssue] = field(default_factory=list)
    status: NegotiationStatus = NegotiationStatus.PENDING
    phase: NegotiationPhase = NegotiationPhase.INITIALIZATION
    history: NegotiationHistory = field(default_factory=NegotiationHistory)
    strategy_engine: NegotiationStrategyEngine = field(default_factory=NegotiationStrategyEngine)
    current_turn: int = 0
    max_turns: int = 100
    start_time: float = field(default_factory=time.time)
    timeout: float = 3600.0
    consensus_proposal: Optional[NegotiationProposal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_agent(self, agent: NegotiationAgent) -> None:
        """添加Agent"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Session {self.session_id[:8]}: agent {agent.name} added")

    def add_issue(self, issue: NegotiationIssue) -> None:
        """添加议题"""
        self.issues.append(issue)
        logger.info(f"Session {self.session_id[:8]}: issue {issue.name} added")

    def start(self) -> None:
        """开始协商"""
        self.status = NegotiationStatus.ACTIVE
        self.phase = NegotiationPhase.PROPOSAL
        self.start_time = time.time()
        logger.info(f"Session {self.session_id[:8]}: negotiation started, topic={self.topic}")

    def is_active(self) -> bool:
        """是否活跃"""
        return self.status == NegotiationStatus.ACTIVE

    def is_timeout(self) -> bool:
        """是否超时"""
        return (time.time() - self.start_time) > self.timeout

    def check_consensus(self) -> bool:
        """检查是否达成共识"""
        if not self.history.accepted_proposals:
            return False

        accepted_count = sum(
            1 for msg in self.history.messages
            if msg.message_type == MessageType.ACCEPT
        )

        result = accepted_count >= len(self.agents) // 2
        if result:
            logger.info(f"Session {self.session_id[:8]}: CONSENSUS reached!")
        return result

    def get_active_agents(self) -> List[NegotiationAgent]:
        """获取活跃Agent"""
        return list(self.agents.values())


class NegotiationProtocol:
    """协商协议"""

    def __init__(self):
        self.sessions: Dict[str, NegotiationSession] = {}
        logger.debug("NegotiationProtocol initialized")

    def create_session(self, topic: str, **kwargs) -> NegotiationSession:
        """创建协商会话"""
        session = NegotiationSession(topic=topic, **kwargs)
        self.sessions[session.session_id] = session
        logger.info(f"Protocol: session created, topic={topic}, id={session.session_id[:8]}")
        return session

    def get_session(self, session_id: str) -> Optional[NegotiationSession]:
        """获取协商会话"""
        return self.sessions.get(session_id)

    def send_message(self, session_id: str, message: NegotiationMessage) -> bool:
        """发送消息"""
        session = self.get_session(session_id)
        if not session or not session.is_active():
            logger.warning(f"Protocol: send_message failed, session not active or not found")
            return False

        session.history.add_message(message)
        session.current_turn += 1

        if session.is_timeout():
            session.status = NegotiationStatus.TIMEOUT
            session.phase = NegotiationPhase.TERMINATION
            logger.warning(f"Session {session_id[:8]}: TIMEOUT")

        return True

    def propose(self, session_id: str, agent_id: str,
                proposal: NegotiationProposal) -> bool:
        """发起提案"""
        session = self.get_session(session_id)
        if not session or not session.is_active():
            logger.warning(f"Protocol: propose failed, session not active")
            return False

        if agent_id not in session.agents:
            logger.warning(f"Protocol: propose failed, agent {agent_id} not in session")
            return False

        session.history.add_proposal(proposal)

        message = NegotiationMessage(
            sender_id=agent_id,
            receiver_ids=[aid for aid in session.agents if aid != agent_id],
            message_type=MessageType.PROPOSAL,
            proposal=proposal
        )

        logger.info(f"Protocol: agent {agent_id} proposed in session {session_id[:8]}")
        return self.send_message(session_id, message)

    def accept(self, session_id: str, agent_id: str,
              proposal_id: str) -> bool:
        """接受提案"""
        session = self.get_session(session_id)
        if not session or not session.is_active():
            logger.warning(f"Protocol: accept failed, session not active")
            return False

        proposal = next(
            (p for p in session.history.proposals if p.proposal_id == proposal_id),
            None
        )

        if not proposal:
            logger.warning(f"Protocol: accept failed, proposal {proposal_id[:8]} not found")
            return False

        session.history.accept_proposal(proposal)

        message = NegotiationMessage(
            sender_id=agent_id,
            receiver_ids=[aid for aid in session.agents if aid != agent_id],
            message_type=MessageType.ACCEPT,
            proposal=proposal
        )

        if session.check_consensus():
            session.status = NegotiationStatus.SUCCESS
            session.phase = NegotiationPhase.CONSENSUS
            session.consensus_proposal = proposal
            logger.info(f"Session {session_id[:8]}: consensus achieved!")

        return self.send_message(session_id, message)

    def reject(self, session_id: str, agent_id: str,
              proposal_id: str, reason: str = "") -> bool:
        """拒绝提案"""
        session = self.get_session(session_id)
        if not session or not session.is_active():
            return False

        message = NegotiationMessage(
            sender_id=agent_id,
            receiver_ids=[aid for aid in session.agents if aid != agent_id],
            message_type=MessageType.REJECT,
            content=reason
        )

        logger.info(f"Protocol: agent {agent_id} rejected proposal in session {session_id[:8]}")
        return self.send_message(session_id, message)

    def terminate(self, session_id: str, agent_id: str) -> bool:
        """终止协商"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.status = NegotiationStatus.FAILED
        session.phase = NegotiationPhase.TERMINATION

        message = NegotiationMessage(
            sender_id=agent_id,
            receiver_ids=list(session.agents.keys()),
            message_type=MessageType.TERMINATE
        )

        logger.info(f"Session {session_id[:8]}: terminated by {agent_id}")
        return self.send_message(session_id, message)


class NegotiationService:
    """协商服务"""

    def __init__(self):
        self.protocol = NegotiationProtocol()
        self.sessions: Dict[str, NegotiationSession] = {}
        logger.info("NegotiationService initialized")

    def create_negotiation(self, topic: str,
                          agents: List[NegotiationAgent],
                          issues: List[NegotiationIssue],
                          **kwargs) -> NegotiationSession:
        """创建协商"""
        session = self.protocol.create_session(topic, **kwargs)

        for agent in agents:
            session.add_agent(agent)

        for issue in issues:
            session.add_issue(issue)

        self.sessions[session.session_id] = session
        logger.info(f"NegotiationService: created negotiation '{topic}' with {len(agents)} agents, {len(issues)} issues")
        return session

    def start_negotiation(self, session_id: str) -> bool:
        """开始协商"""
        session = self.protocol.get_session(session_id)
        if not session:
            logger.warning(f"NegotiationService: start failed, session not found")
            return False

        session.start()
        return True

    def get_session_status(self, session_id: str) -> Optional[NegotiationStatus]:
        """获取协商状态"""
        session = self.protocol.get_session(session_id)
        return session.status if session else None

    def get_consensus(self, session_id: str) -> Optional[NegotiationProposal]:
        """获取共识提案"""
        session = self.protocol.get_session(session_id)
        return session.consensus_proposal if session else None

    def run_full_negotiation(self, session_id: str) -> Tuple[bool, Optional[NegotiationProposal]]:
        """运行完整协商流程"""
        session = self.protocol.get_session(session_id)
        if not session:
            logger.warning(f"NegotiationService: run_full_negotiation failed, session not found")
            return False, None

        session.start()

        agents = session.get_active_agents()
        logger.info(f"Starting full negotiation: {len(agents)} agents, max {session.max_turns} turns")

        for turn in range(session.max_turns):
            if session.is_timeout():
                logger.warning(f"Negotiation timed out at turn {turn}")
                break

            for agent in agents:
                if not session.is_active():
                    break

                proposal = session.strategy_engine.generate_proposal(
                    agent, session.issues, session.history
                )

                self.protocol.propose(session_id, agent.agent_id, proposal)

                for other_agent in agents:
                    if other_agent.agent_id != agent.agent_id:
                        accept, utility = session.strategy_engine.evaluate_proposal(
                            other_agent, proposal
                        )
                        if accept:
                            self.protocol.accept(session_id, other_agent.agent_id, proposal.proposal_id)

                if session.check_consensus():
                    break

            if session.status == NegotiationStatus.SUCCESS:
                break

        success = session.status == NegotiationStatus.SUCCESS
        logger.info(f"Negotiation finished: success={success}, turns={session.current_turn}")
        return success, session.consensus_proposal


_global_negotiation_service: Optional[NegotiationService] = None


def get_negotiation_service() -> NegotiationService:
    """获取全局协商服务"""
    global _global_negotiation_service
    if _global_negotiation_service is None:
        _global_negotiation_service = NegotiationService()
    return _global_negotiation_service


def reset_negotiation_service() -> None:
    """重置全局协商服务"""
    global _global_negotiation_service
    _global_negotiation_service = None
