
"""
阶段45验收测试：多Agent协商谈判机制
"""

import pytest
from src.architecture.negotiation_engine import (
    NegotiationPhase,
    NegotiationStatus,
    NegotiationStrategy,
    MessageType,
    NegotiationIssue,
    NegotiationProposal,
    NegotiationMessage,
    NegotiationAgent,
    NegotiationHistory,
    NegotiationStrategyEngine,
    NegotiationSession,
    NegotiationProtocol,
    NegotiationService,
    get_negotiation_service,
    reset_negotiation_service
)


class TestNegotiationEnums:
    """测试枚举类型"""

    def test_negotiation_phase_enum(self):
        """测试协商阶段枚举"""
        assert NegotiationPhase.INITIALIZATION == "initialization"
        assert NegotiationPhase.PROPOSAL == "proposal"
        assert NegotiationPhase.CONSENSUS == "consensus"
        assert NegotiationPhase.TERMINATION == "termination"

    def test_negotiation_status_enum(self):
        """测试协商状态枚举"""
        assert NegotiationStatus.PENDING == "pending"
        assert NegotiationStatus.ACTIVE == "active"
        assert NegotiationStatus.SUCCESS == "success"
        assert NegotiationStatus.FAILED == "failed"

    def test_negotiation_strategy_enum(self):
        """测试谈判策略枚举"""
        assert NegotiationStrategy.CONCILIATORY == "conciliatory"
        assert NegotiationStrategy.COMPETITIVE == "competitive"
        assert NegotiationStrategy.COLLABORATIVE == "collaborative"
        assert NegotiationStrategy.ADAPTIVE == "adaptive"

    def test_message_type_enum(self):
        """测试消息类型枚举"""
        assert MessageType.PROPOSAL == "proposal"
        assert MessageType.ACCEPT == "accept"
        assert MessageType.REJECT == "reject"
        assert MessageType.TERMINATE == "terminate"


class TestNegotiationDataStructures:
    """测试数据结构"""

    def test_negotiation_issue(self):
        """测试协商议题"""
        issue = NegotiationIssue(
            name="price",
            description="产品价格",
            priority=1.0,
            possible_values=[100, 150, 200, 250, 300]
        )

        assert issue.name == "price"
        assert issue.description == "产品价格"
        assert issue.priority == 1.0
        assert len(issue.possible_values) == 5

    def test_negotiation_proposal(self):
        """测试协商提案"""
        proposal = NegotiationProposal(
            proposer_id="agent_1",
            issue_values={"price": 200, "delivery": "fast"}
        )

        proposal.set_issue_value("quality", "high")

        assert proposal.proposer_id == "agent_1"
        assert proposal.get_issue_value("price") == 200
        assert proposal.get_issue_value("quality") == "high"

    def test_negotiation_message(self):
        """测试协商消息"""
        message = NegotiationMessage(
            sender_id="agent_1",
            receiver_ids=["agent_2", "agent_3"],
            message_type=MessageType.PROPOSAL,
            content="Proposal 1"
        )

        assert message.sender_id == "agent_1"
        assert len(message.receiver_ids) == 2
        assert message.message_type == MessageType.PROPOSAL

    def test_negotiation_agent(self):
        """测试协商Agent"""
        issue1 = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        issue2 = NegotiationIssue(name="quality", possible_values=["low", "medium", "high"])

        agent = NegotiationAgent(
            name="buyer",
            role="buyer",
            strategy=NegotiationStrategy.COLLABORATIVE,
            issues=[issue1, issue2]
        )

        assert agent.name == "buyer"
        assert agent.role == "buyer"
        assert agent.strategy == NegotiationStrategy.COLLABORATIVE
        assert len(agent.issues) == 2

    def test_negotiation_history(self):
        """测试协商历史"""
        history = NegotiationHistory()

        message = NegotiationMessage(sender_id="agent_1", message_type=MessageType.INFORM)
        proposal = NegotiationProposal(proposer_id="agent_1")

        history.add_message(message)
        history.add_proposal(proposal)
        history.accept_proposal(proposal)

        assert len(history.messages) == 1
        assert len(history.proposals) == 1
        assert len(history.accepted_proposals) == 1


class TestNegotiationStrategyEngine:
    """测试协商策略引擎"""

    def setup_method(self):
        """设置测试环境"""
        self.engine = NegotiationStrategyEngine()
        self.issue1 = NegotiationIssue(name="price", possible_values=[100, 150, 200, 250, 300])
        self.issue2 = NegotiationIssue(name="delivery", possible_values=["slow", "normal", "fast"])
        self.agent = NegotiationAgent(
            name="agent_1",
            issues=[self.issue1, self.issue2]
        )
        self.history = NegotiationHistory()

    def test_conciliatory_strategy(self):
        """测试和解策略"""
        self.agent.strategy = NegotiationStrategy.CONCILIATORY
        proposal = self.engine.generate_proposal(self.agent, [self.issue1, self.issue2], self.history)

        assert proposal is not None
        assert proposal.get_issue_value("price") == 300
        assert proposal.get_issue_value("delivery") == "fast"

    def test_competitive_strategy(self):
        """测试竞争策略"""
        self.agent.strategy = NegotiationStrategy.COMPETITIVE
        proposal = self.engine.generate_proposal(self.agent, [self.issue1, self.issue2], self.history)

        assert proposal is not None
        assert proposal.get_issue_value("price") == 100
        assert proposal.get_issue_value("delivery") == "slow"

    def test_collaborative_strategy(self):
        """测试协作策略"""
        self.agent.strategy = NegotiationStrategy.COLLABORATIVE
        proposal = self.engine.generate_proposal(self.agent, [self.issue1, self.issue2], self.history)

        assert proposal is not None
        assert proposal.get_issue_value("price") == 200
        assert proposal.get_issue_value("delivery") == "normal"

    def test_evaluate_proposal(self):
        """测试评估提案"""
        proposal = NegotiationProposal(
            proposer_id="agent_2",
            issue_values={"price": 200, "delivery": "normal"}
        )

        accept, utility = self.engine.evaluate_proposal(self.agent, proposal)

        assert isinstance(accept, bool)
        assert utility >= 0.0
        assert utility <= 1.0

    def test_agent_calculate_utility(self):
        """测试Agent计算效用"""
        proposal = NegotiationProposal(
            proposer_id="agent_2",
            issue_values={"price": 200, "delivery": "normal"}
        )

        utility = self.agent.calculate_utility(proposal)

        assert utility >= 0.0
        assert utility <= 1.0


class TestNegotiationSession:
    """测试协商会话"""

    def setup_method(self):
        """设置测试环境"""
        self.issue1 = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        self.issue2 = NegotiationIssue(name="quality", possible_values=["low", "high"])

        self.agent1 = NegotiationAgent(name="buyer", role="buyer", strategy=NegotiationStrategy.COLLABORATIVE)
        self.agent2 = NegotiationAgent(name="seller", role="seller", strategy=NegotiationStrategy.COLLABORATIVE)

        self.session = NegotiationSession(topic="product_negotiation")

    def test_add_agent(self):
        """测试添加Agent"""
        self.session.add_agent(self.agent1)
        self.session.add_agent(self.agent2)

        assert len(self.session.agents) == 2

    def test_add_issue(self):
        """测试添加议题"""
        self.session.add_issue(self.issue1)
        self.session.add_issue(self.issue2)

        assert len(self.session.issues) == 2

    def test_start_session(self):
        """测试开始会话"""
        assert self.session.status == NegotiationStatus.PENDING

        self.session.start()

        assert self.session.status == NegotiationStatus.ACTIVE
        assert self.session.phase == NegotiationPhase.PROPOSAL

    def test_check_consensus(self):
        """测试检查共识"""
        self.session.add_agent(self.agent1)
        self.session.add_agent(self.agent2)
        self.session.add_issue(self.issue1)

        self.session.start()

        assert self.session.check_consensus() == False


class TestNegotiationProtocol:
    """测试协商协议"""

    def setup_method(self):
        """设置测试环境"""
        self.protocol = NegotiationProtocol()

        self.issue1 = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        self.agent1 = NegotiationAgent(agent_id="agent_1", name="buyer")
        self.agent2 = NegotiationAgent(agent_id="agent_2", name="seller")

    def test_create_session(self):
        """测试创建会话"""
        session = self.protocol.create_session("test_topic")

        assert session is not None
        assert session.topic == "test_topic"
        assert session.session_id in self.protocol.sessions

    def test_propose(self):
        """测试发起提案"""
        session = self.protocol.create_session("test_topic")
        session.add_agent(self.agent1)
        session.add_agent(self.agent2)
        session.start()

        proposal = NegotiationProposal(proposer_id="agent_1", issue_values={"price": 200})

        result = self.protocol.propose(session.session_id, "agent_1", proposal)

        assert result == True
        assert len(session.history.proposals) == 1

    def test_accept(self):
        """测试接受提案"""
        session = self.protocol.create_session("test_topic")
        session.add_agent(self.agent1)
        session.add_agent(self.agent2)
        session.start()

        proposal = NegotiationProposal(proposer_id="agent_1", issue_values={"price": 200})
        self.protocol.propose(session.session_id, "agent_1", proposal)

        result = self.protocol.accept(session.session_id, "agent_2", proposal.proposal_id)

        assert result == True
        assert len(session.history.accepted_proposals) == 1


class TestNegotiationService:
    """测试协商服务"""

    def setup_method(self):
        """设置测试环境"""
        reset_negotiation_service()
        self.service = get_negotiation_service()

        self.issue1 = NegotiationIssue(name="price", possible_values=[100, 150, 200, 250, 300])
        self.issue2 = NegotiationIssue(name="delivery", possible_values=["slow", "normal", "fast"])

        self.agent1 = NegotiationAgent(
            agent_id="agent_1",
            name="buyer",
            role="buyer",
            strategy=NegotiationStrategy.COLLABORATIVE,
            issues=[self.issue1, self.issue2]
        )

        self.agent2 = NegotiationAgent(
            agent_id="agent_2",
            name="seller",
            role="seller",
            strategy=NegotiationStrategy.COLLABORATIVE,
            issues=[self.issue1, self.issue2]
        )

    def test_create_negotiation(self):
        """测试创建协商"""
        session = self.service.create_negotiation(
            topic="product_negotiation",
            agents=[self.agent1, self.agent2],
            issues=[self.issue1, self.issue2]
        )

        assert session is not None
        assert session.topic == "product_negotiation"
        assert len(session.agents) == 2
        assert len(session.issues) == 2

    def test_start_negotiation(self):
        """测试开始协商"""
        session = self.service.create_negotiation(
            topic="test",
            agents=[self.agent1, self.agent2],
            issues=[self.issue1]
        )

        result = self.service.start_negotiation(session.session_id)

        assert result == True
        assert session.status == NegotiationStatus.ACTIVE

    def test_get_session_status(self):
        """测试获取协商状态"""
        session = self.service.create_negotiation(
            topic="test",
            agents=[self.agent1, self.agent2],
            issues=[self.issue1]
        )

        status = self.service.get_session_status(session.session_id)

        assert status == NegotiationStatus.PENDING

    def test_get_consensus(self):
        """测试获取共识"""
        session = self.service.create_negotiation(
            topic="test",
            agents=[self.agent1, self.agent2],
            issues=[self.issue1]
        )

        consensus = self.service.get_consensus(session.session_id)

        assert consensus is None


class TestNegotiationIntegration:
    """集成测试"""

    def setup_method(self):
        """设置测试环境"""
        reset_negotiation_service()
        self.service = get_negotiation_service()

    def test_two_agent_negotiation(self):
        """测试双Agent协商"""
        issue1 = NegotiationIssue(
            name="price",
            possible_values=[100, 150, 200, 250, 300]
        )

        agent1 = NegotiationAgent(
            agent_id="agent_1",
            name="buyer",
            strategy=NegotiationStrategy.COLLABORATIVE,
            issues=[issue1]
        )

        agent2 = NegotiationAgent(
            agent_id="agent_2",
            name="seller",
            strategy=NegotiationStrategy.COLLABORATIVE,
            issues=[issue1]
        )

        session = self.service.create_negotiation(
            topic="price_negotiation",
            agents=[agent1, agent2],
            issues=[issue1]
        )

        self.service.start_negotiation(session.session_id)

        assert session.status == NegotiationStatus.ACTIVE
        assert len(session.agents) == 2

    def test_multiple_strategies(self):
        """测试多种策略"""
        issue = NegotiationIssue(name="value", possible_values=[1, 2, 3, 4, 5])
        engine = NegotiationStrategyEngine()
        history = NegotiationHistory()

        strategies = [
            NegotiationStrategy.CONCILIATORY,
            NegotiationStrategy.COMPETITIVE,
            NegotiationStrategy.COLLABORATIVE,
            NegotiationStrategy.RANDOM
        ]

        for strategy in strategies:
            agent = NegotiationAgent(name="test_agent", strategy=strategy, issues=[issue])
            proposal = engine.generate_proposal(agent, [issue], history)
            assert proposal is not None

    def test_proposal_acceptance_flow(self):
        """测试提案接受流程"""
        issue = NegotiationIssue(name="price", possible_values=[100, 200, 300])

        agent1 = NegotiationAgent(agent_id="a1", name="agent1", issues=[issue])
        agent2 = NegotiationAgent(agent_id="a2", name="agent2", issues=[issue])

        session = self.service.create_negotiation(
            topic="test_flow",
            agents=[agent1, agent2],
            issues=[issue]
        )

        self.service.start_negotiation(session.session_id)

        proposal = NegotiationProposal(proposer_id="a1", issue_values={"price": 200})
        result = self.service.protocol.propose(session.session_id, "a1", proposal)
        assert result == True

        result = self.service.protocol.accept(session.session_id, "a2", proposal.proposal_id)
        assert result == True

        assert len(session.history.accepted_proposals) == 1

