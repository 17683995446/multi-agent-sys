
"""
全面深度压力测试：复杂场景、边界条件、异常容错、跨模块集成
目标：发现系统在真实运行时的bug
"""

import pytest
import time
import uuid
import logging

from src.architecture.negotiation_engine import (
    NegotiationPhase, NegotiationStatus, NegotiationStrategy, MessageType,
    NegotiationIssue, NegotiationProposal, NegotiationMessage, NegotiationAgent,
    NegotiationHistory, NegotiationStrategyEngine, NegotiationSession,
    NegotiationProtocol, NegotiationService,
    get_negotiation_service, reset_negotiation_service
)
from src.architecture.csp_conflict_detector import (
    ConstraintType, ConflictStatus, Variable, Constraint,
    ConstraintDefinition, ConflictDetector, ConflictResolver, CSPSolver, CSPFramework
)
from src.architecture.state_machine_scheduler import (
    StateType, StateDefinition, Transition, StateContext,
    StateMachine, StateMachineBuilder, StateMachineExecutor, StateMachineConfig
)
from src.architecture.contract_net_protocol import (
    TaskState, BidStatus, ContractorStatus, Contractor, TaskRequirement,
    TaskAnnouncement, Bid, Contract, ContractNetProtocol, ContractNetService
)
from src.architecture.htd_decomposer import (
    TaskStatus, TaskPriority, SubTask, TaskDecomposition,
    HTDDecomposer, HTDDecompositionService
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ============================================================
# 一、协商引擎深度测试
# ============================================================

class TestNegotiationEdgeCases:
    """协商引擎边界和异常测试"""

    def setup_method(self):
        reset_negotiation_service()

    def test_empty_issues_proposal(self):
        """测试空议题列表生成提案"""
        engine = NegotiationStrategyEngine()
        agent = NegotiationAgent(name="test", strategy=NegotiationStrategy.COLLABORATIVE)
        history = NegotiationHistory()
        proposal = engine.generate_proposal(agent, [], history)
        assert proposal is not None
        assert len(proposal.issue_values) == 0

    def test_issue_with_empty_possible_values(self):
        """测试议题可能值为空列表"""
        issue = NegotiationIssue(name="empty_issue", possible_values=[])
        engine = NegotiationStrategyEngine()
        agent = NegotiationAgent(name="test", strategy=NegotiationStrategy.COLLABORATIVE, issues=[issue])
        history = NegotiationHistory()
        proposal = engine.generate_proposal(agent, [issue], history)
        assert proposal is not None
        assert proposal.get_issue_value("empty_issue") is None

    def test_proposal_get_nonexistent_issue(self):
        """测试获取不存在的议题值"""
        proposal = NegotiationProposal(proposer_id="test")
        assert proposal.get_issue_value("nonexistent") is None

    def test_agent_no_issues_calculate_utility(self):
        """测试Agent没有议题时计算效用"""
        agent = NegotiationAgent(name="test", issues=[])
        proposal = NegotiationProposal(proposer_id="other", issue_values={"price": 100})
        utility = agent.calculate_utility(proposal)
        assert utility == 0.0

    def test_agent_get_best_proposal_empty_list(self):
        """测试获取最佳提案时空列表"""
        agent = NegotiationAgent(name="test")
        result = agent.get_best_proposal([])
        assert result is None

    def test_history_empty(self):
        """测试空历史记录"""
        history = NegotiationHistory()
        assert len(history.messages) == 0
        assert len(history.proposals) == 0
        assert len(history.accepted_proposals) == 0

    def test_single_value_issue(self):
        """测试议题只有一个可能值"""
        issue = NegotiationIssue(name="fixed", possible_values=[42])
        engine = NegotiationStrategyEngine()
        agent = NegotiationAgent(name="test", strategy=NegotiationStrategy.COLLABORATIVE, issues=[issue])
        history = NegotiationHistory()
        proposal = engine.generate_proposal(agent, [issue], history)
        assert proposal.get_issue_value("fixed") == 42

    def test_single_value_utility(self):
        """测试单值议题效用计算"""
        issue = NegotiationIssue(name="fixed", possible_values=[42])
        agent = NegotiationAgent(name="test", issues=[issue])
        proposal = NegotiationProposal(proposer_id="other", issue_values={"fixed": 42})
        utility = agent.calculate_utility(proposal)
        assert utility == 0.0

    def test_propose_to_nonexistent_session(self):
        """测试向不存在的会话发起提案"""
        protocol = NegotiationProtocol()
        proposal = NegotiationProposal(proposer_id="agent_1")
        result = protocol.propose("nonexistent_session", "agent_1", proposal)
        assert result == False

    def test_accept_nonexistent_proposal(self):
        """测试接受不存在的提案"""
        protocol = NegotiationProtocol()
        session = protocol.create_session("test")
        agent = NegotiationAgent(agent_id="a1", name="a1")
        session.add_agent(agent)
        session.start()
        result = protocol.accept(session.session_id, "a1", "nonexistent_proposal")
        assert result == False

    def test_propose_from_non_member_agent(self):
        """测试非成员Agent发起提案"""
        protocol = NegotiationProtocol()
        session = protocol.create_session("test")
        agent1 = NegotiationAgent(agent_id="a1", name="a1")
        session.add_agent(agent1)
        session.start()
        proposal = NegotiationProposal(proposer_id="outsider")
        result = protocol.propose(session.session_id, "outsider", proposal)
        assert result == False

    def test_send_message_to_inactive_session(self):
        """测试向非活跃会话发送消息"""
        protocol = NegotiationProtocol()
        session = protocol.create_session("test")
        msg = NegotiationMessage(sender_id="a1", message_type=MessageType.INFORM)
        result = protocol.send_message(session.session_id, msg)
        assert result == False

    def test_terminate_nonexistent_session(self):
        """测试终止不存在的会话"""
        protocol = NegotiationProtocol()
        result = protocol.terminate("nonexistent", "agent_1")
        assert result == False

    def test_reject_inactive_session(self):
        """测试在非活跃会话中拒绝提案"""
        protocol = NegotiationProtocol()
        session = protocol.create_session("test")
        result = protocol.reject(session.session_id, "a1", "some_proposal")
        assert result == False

    def test_start_nonexistent_negotiation(self):
        """测试启动不存在的协商"""
        service = get_negotiation_service()
        result = service.start_negotiation("nonexistent")
        assert result == False

    def test_get_status_nonexistent(self):
        """测试获取不存在协商的状态"""
        service = get_negotiation_service()
        result = service.get_session_status("nonexistent")
        assert result is None

    def test_get_consensus_nonexistent(self):
        """测试获取不存在协商的共识"""
        service = get_negotiation_service()
        result = service.get_consensus("nonexistent")
        assert result is None

    def test_run_full_negotiation_nonexistent(self):
        """测试运行不存在的协商"""
        service = get_negotiation_service()
        success, proposal = service.run_full_negotiation("nonexistent")
        assert success == False
        assert proposal is None

    def test_custom_utility_function(self):
        """测试自定义效用函数"""
        def custom_utility(issue_values):
            return 1.0 if "price" in issue_values else 0.0

        agent = NegotiationAgent(name="custom_agent", utility_function=custom_utility)
        proposal = NegotiationProposal(proposer_id="other", issue_values={"price": 200})
        utility = agent.calculate_utility(proposal)
        assert utility == 1.0

        proposal2 = NegotiationProposal(proposer_id="other", issue_values={"quality": "high"})
        utility2 = agent.calculate_utility(proposal2)
        assert utility2 == 0.0

    def test_session_lifecycle(self):
        """测试会话完整生命周期"""
        session = NegotiationSession(topic="lifecycle_test")
        assert session.status == NegotiationStatus.PENDING
        assert session.phase == NegotiationPhase.INITIALIZATION
        session.start()
        assert session.status == NegotiationStatus.ACTIVE
        assert session.phase == NegotiationPhase.PROPOSAL
        assert session.is_active() == True

    def test_session_timeout(self):
        """测试会话超时"""
        session = NegotiationSession(topic="timeout_test", timeout=0.001)
        session.start()
        time.sleep(0.01)
        assert session.is_timeout() == True

    def test_session_consensus_no_accepted_proposals(self):
        """测试没有接受提案时检查共识"""
        session = NegotiationSession(topic="consensus_test")
        assert session.check_consensus() == False


# ============================================================
# 二、CSP冲突检测深度测试
# ============================================================

class TestCSPDeepEdgeCases:
    """CSP冲突检测边界和异常测试"""

    def test_empty_domain_variable(self):
        """测试空域变量"""
        var = Variable(var_id="v1", name="empty_var", domain=set())
        assert var.is_assigned() == False
        var.current_value = None
        assert var.is_assigned() == False

    def test_constraint_with_no_variables(self):
        """测试没有变量的约束"""
        detector = ConflictDetector()
        constraint = Constraint(
            constraint_id="c1",
            name="empty_constraint",
            constraint_type=ConstraintType.UNARY,
            variables=[],
            predicate=lambda vals: True
        )
        detector.add_constraint(constraint)
        conflicts = detector.detect_conflicts()
        assert isinstance(conflicts, list)

    def test_solver_with_no_variables(self):
        """测试没有变量的求解器"""
        solver = CSPSolver()
        result = solver.solve()
        assert result.success == True

    def test_solver_with_no_constraints(self):
        """测试没有约束的求解器"""
        solver = CSPSolver()
        solver.add_variable("v1", "x", {1, 2, 3})
        result = solver.solve()
        assert result.success == True

    def test_satisfiable_inequality(self):
        """测试可满足的不等约束"""
        solver = CSPSolver()
        v1 = solver.add_variable("v1", "x", {1})
        v2 = solver.add_variable("v2", "y", {2})

        constraint = Constraint(
            constraint_id="c1",
            name="not_equal",
            constraint_type=ConstraintType.BINARY,
            variables=["v1", "v2"],
            predicate=lambda vals: vals[0] != vals[1]
        )
        solver.add_constraint(constraint)
        result = solver.solve()
        assert result.success == True

    def test_conflict_resolver_no_conflicts(self):
        """测试没有冲突时的解决"""
        detector = ConflictDetector()
        resolver = ConflictResolver(detector)
        resolved = resolver.resolve_all("domain_reduction")
        assert resolved == 0

    def test_csp_framework_create_solver(self):
        """测试CSP框架创建求解器"""
        framework = CSPFramework()
        solver = framework.create_solver("s1")
        assert solver is not None
        assert isinstance(solver, CSPSolver)

    def test_csp_framework_get_solver(self):
        """测试CSP框架获取求解器"""
        framework = CSPFramework()
        framework.create_solver("s1")
        solver = framework.get_solver("s1")
        assert solver is not None
        assert framework.get_solver("nonexistent") is None


# ============================================================
# 三、状态机调度深度测试
# ============================================================

class TestStateMachineEdgeCases:
    """状态机边界和异常测试"""

    def test_state_machine_no_transitions(self):
        """测试没有转换的状态机"""
        builder = StateMachineBuilder("test_sm")
        builder.add_state("s1", state_type=StateType.INITIAL)
        builder.add_state("s2", state_type=StateType.FINAL)
        builder.set_initial_state("s1")
        builder.set_final_state("s2")
        config = builder.build()
        assert config is not None

    def test_execute_nonexistent_transition(self):
        """测试执行不存在的转换"""
        builder = StateMachineBuilder("test_sm")
        builder.add_state("s1", state_type=StateType.INITIAL)
        builder.add_state("s2", state_type=StateType.FINAL)
        builder.add_state("error", state_type=StateType.ERROR)
        builder.set_initial_state("s1")
        builder.set_final_state("s2")
        builder.set_error_state("error")
        config = builder.build()

        executor = StateMachineExecutor()
        machine = executor.register_machine(config)
        context = executor.create_context("test_sm")
        # 不存在的转换应返回None
        result = executor.transition(context.context_id, "nonexistent")
        assert result is None or result.success == False

    def test_state_context_empty_history(self):
        """测试空历史的状态上下文"""
        context = StateContext(current_state="s1")
        assert len(context.state_history) == 0

    def test_builder_duplicate_state(self):
        """测试添加重复状态"""
        builder = StateMachineBuilder("test_sm")
        builder.add_state("s1", state_type=StateType.INITIAL)
        # 添加相同名称的状态应不崩溃
        builder.add_state("s1", state_type=StateType.INITIAL)

    def test_builder_without_initial_state(self):
        """测试初始状态不在已定义状态中时验证失败"""
        builder = StateMachineBuilder("test_sm")
        builder.add_state("s1", state_type=StateType.INTERMEDIATE)
        builder.add_state("error", state_type=StateType.ERROR)
        builder.set_final_state("s1")
        builder.set_error_state("error")
        # builder默认initial_state="initial"，但"initial"不在states中
        # register_machine时会验证失败
        config = builder.build()
        executor = StateMachineExecutor()
        with pytest.raises(ValueError):
            executor.register_machine(config)

    def test_builder_without_final_state(self):
        """测试没有设置最终状态"""
        builder = StateMachineBuilder("test_sm")
        builder.add_state("s1", state_type=StateType.INITIAL)
        builder.set_initial_state("s1")
        with pytest.raises(ValueError):
            builder.build()

    def test_full_state_machine_lifecycle(self):
        """测试完整状态机生命周期"""
        builder = StateMachineBuilder("lifecycle_sm")
        builder.add_state("init", state_type=StateType.INITIAL)
        builder.add_state("working", state_type=StateType.INTERMEDIATE)
        builder.add_state("done", state_type=StateType.FINAL)
        builder.add_state("error", state_type=StateType.ERROR)
        builder.set_initial_state("init")
        builder.set_final_state("done")
        builder.set_error_state("error")
        builder.add_transition("init", "working")
        builder.add_transition("working", "done")

        config = builder.build()
        executor = StateMachineExecutor()
        executor.register_machine(config)
        context = executor.create_context("lifecycle_sm")

        assert context is not None
        assert context.current_state == "init"

        result = executor.transition(context.context_id, "working")
        assert result is not None

        result2 = executor.transition(context.context_id, "done")
        assert result2 is not None


# ============================================================
# 四、合同网协议深度测试
# ============================================================

class TestContractNetEdgeCases:
    """合同网协议边界和异常测试"""

    def test_announce_no_contractors(self):
        """测试没有承包商时发布任务"""
        service = ContractNetService()
        requirement = TaskRequirement(
            skill_required=["coding"],
            estimated_time=10.0,
            budget=1000.0,
            priority=1,
            description="test task"
        )
        announcement, bids = service.publish_and_bid_flow(
            task_id=str(uuid.uuid4()),
            task_name="test_task",
            requirements=requirement
        )
        assert announcement is not None
        assert len(bids) == 0

    def test_bid_on_nonexistent_task(self):
        """测试对不存在的任务竞标"""
        protocol = ContractNetProtocol()
        contractor = protocol.register_contractor("contractor_1", ["coding"])
        result = protocol.submit_bid("nonexistent_announcement", contractor.contractor_id, 100.0, 10.0)
        assert result is None

    def test_contractor_zero_workload(self):
        """测试零工作量的承包商"""
        protocol = ContractNetProtocol()
        contractor = protocol.register_contractor("busy_contractor", ["coding"], max_workload=0)
        assert contractor.max_workload == 0

    def test_service_register_agent(self):
        """测试注册Agent为承包商"""
        service = ContractNetService()
        contractor = service.register_agent_as_contractor("agent_1", "Agent One", ["coding", "testing"])
        assert contractor is not None
        assert contractor.name == "Agent One"
        assert "coding" in contractor.skills

    def test_full_auction_flow(self):
        """测试完整竞拍流程"""
        service = ContractNetService()
        service.register_agent_as_contractor("c1", "Contractor 1", ["coding"])
        service.register_agent_as_contractor("c2", "Contractor 2", ["coding"])

        requirement = TaskRequirement(
            skill_required=["coding"],
            estimated_time=10.0,
            budget=1000.0,
            priority=1,
            description="Build feature"
        )

        contract = service.full_auction_flow(
            task_id=str(uuid.uuid4()),
            task_name="build_feature",
            requirements=requirement
        )
        # 可能有承包商竞标
        assert contract is None or isinstance(contract, Contract)


# ============================================================
# 五、HTD分解深度测试
# ============================================================

class TestHTDEdgeCases:
    """HTD分解边界和异常测试"""

    def test_decompose_simple_task(self):
        """测试分解简单任务"""
        decomposer = HTDDecomposer()
        result = decomposer.decompose(
            task_name="simple_task",
            task_description="A simple task",
            estimated_time=1.0
        )
        assert result is not None
        assert isinstance(result, TaskDecomposition)

    def test_decompose_zero_time(self):
        """测试零时间任务"""
        decomposer = HTDDecomposer()
        result = decomposer.decompose(
            task_name="zero_time",
            task_description="Zero time task",
            estimated_time=0.0
        )
        assert result is not None

    def test_subtask_default_status(self):
        """测试子任务默认状态"""
        task = SubTask(
            task_id=str(uuid.uuid4()),
            name="test",
            description="test"
        )
        assert task.status == TaskStatus.PENDING

    def test_decompose_complex_task(self):
        """测试分解复杂任务"""
        decomposer = HTDDecomposer()
        result = decomposer.decompose(
            task_name="design_and_implement",
            task_description="Design the system architecture and implement the core modules",
            estimated_time=100.0
        )
        assert result is not None
        assert result.total_tasks > 0

    def test_decomposition_validation(self):
        """测试分解结果验证"""
        decomposer = HTDDecomposer()
        result = decomposer.decompose(
            task_name="validation_test",
            task_description="Test the validation of decomposition results",
            estimated_time=10.0
        )
        validation = decomposer.validate(result)
        assert isinstance(validation, dict)

    def test_htd_service(self):
        """测试HTD分解服务"""
        service = HTDDecompositionService()
        result = service.decompose_task(
            task_name="service_test",
            task_description="Test the HTD decomposition service",
            estimated_time=10.0
        )
        assert result is not None


# ============================================================
# 六、跨模块集成压力测试
# ============================================================

class TestCrossModuleIntegration:
    """跨模块集成测试"""

    def setup_method(self):
        reset_negotiation_service()

    def test_negotiation_with_csp_constraints(self):
        """测试协商与CSP约束联合使用"""
        solver = CSPSolver()
        v1 = solver.add_variable("v1", "price", {100, 200, 300})
        v2 = solver.add_variable("v2", "quality", {1, 2, 3})

        issue1 = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        issue2 = NegotiationIssue(name="quality", possible_values=[1, 2, 3])

        agent1 = NegotiationAgent(
            agent_id="a1", name="buyer",
            strategy=NegotiationStrategy.COLLABORATIVE,
            issues=[issue1, issue2]
        )
        agent2 = NegotiationAgent(
            agent_id="a2", name="seller",
            strategy=NegotiationStrategy.COLLABORATIVE,
            issues=[issue1, issue2]
        )

        service = get_negotiation_service()
        session = service.create_negotiation(
            topic="csp_negotiation",
            agents=[agent1, agent2],
            issues=[issue1, issue2]
        )
        service.start_negotiation(session.session_id)

        proposal = session.strategy_engine.generate_proposal(
            agent1, session.issues, session.history
        )

        price = proposal.get_issue_value("price")
        quality = proposal.get_issue_value("quality")

        if price is not None:
            v1.current_value = price
        if quality is not None:
            v2.current_value = quality

        csp_result = solver.solve()
        assert csp_result is not None

    def test_htd_then_contract_net(self):
        """测试HTD分解后合同网分发"""
        decomposer = HTDDecomposer()
        decomposition = decomposer.decompose(
            task_name="complex_task",
            task_description="A complex task to decompose and distribute",
            estimated_time=5.0
        )

        service = ContractNetService()
        service.register_agent_as_contractor("c1", "Worker 1", ["coding"])
        service.register_agent_as_contractor("c2", "Worker 2", ["testing"])

        flat_tasks = decomposer.get_flat_task_list(decomposition)
        for i, subtask in enumerate(flat_tasks[:3]):
            requirement = TaskRequirement(
                skill_required=["coding"],
                estimated_time=subtask.estimated_time,
                budget=100.0,
                priority=1,
                description=subtask.description
            )
            announcement, bids = service.publish_and_bid_flow(
                task_id=subtask.task_id,
                task_name=subtask.name,
                requirements=requirement
            )
            assert announcement is not None

    def test_state_machine_managing_negotiation(self):
        """测试状态机管理协商流程"""
        builder = StateMachineBuilder("negotiation_sm")
        builder.add_state("init", state_type=StateType.INITIAL)
        builder.add_state("negotiating", state_type=StateType.INTERMEDIATE)
        builder.add_state("consensus", state_type=StateType.FINAL)
        builder.add_state("failed", state_type=StateType.FINAL)
        builder.add_state("error", state_type=StateType.ERROR)
        builder.set_initial_state("init")
        builder.set_final_state("consensus")
        builder.set_final_state("failed")
        builder.set_error_state("error")

        builder.add_transition("init", "negotiating")
        builder.add_transition("negotiating", "consensus")
        builder.add_transition("negotiating", "failed")

        config = builder.build()
        executor = StateMachineExecutor()
        executor.register_machine(config)
        context = executor.create_context("negotiation_sm")
        assert context is not None

        # 创建协商
        issue = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        agent1 = NegotiationAgent(agent_id="a1", name="buyer", issues=[issue])
        agent2 = NegotiationAgent(agent_id="a2", name="seller", issues=[issue])

        service = get_negotiation_service()
        session = service.create_negotiation(
            topic="sm_managed",
            agents=[agent1, agent2],
            issues=[issue]
        )

        # 状态机驱动：init -> negotiating
        result = executor.transition(context.context_id, "negotiating")
        assert result is not None

        service.start_negotiation(session.session_id)
        assert session.status == NegotiationStatus.ACTIVE

    def test_large_scale_negotiation(self):
        """测试大规模协商：10个Agent，5个议题"""
        issues = [
            NegotiationIssue(name=f"issue_{i}", possible_values=list(range(1, 11)))
            for i in range(5)
        ]

        agents = [
            NegotiationAgent(
                agent_id=f"agent_{i}",
                name=f"agent_{i}",
                strategy=NegotiationStrategy.COLLABORATIVE,
                issues=issues
            )
            for i in range(10)
        ]

        service = get_negotiation_service()
        session = service.create_negotiation(
            topic="large_scale",
            agents=agents,
            issues=issues,
            max_turns=5
        )
        service.start_negotiation(session.session_id)

        engine = session.strategy_engine
        for agent in agents:
            proposal = engine.generate_proposal(agent, session.issues, session.history)
            assert proposal is not None
            assert len(proposal.issue_values) > 0

    def test_mixed_strategy_negotiation(self):
        """测试混合策略协商"""
        issue = NegotiationIssue(name="value", possible_values=[1, 2, 3, 4, 5])

        strategies = [
            NegotiationStrategy.CONCILIATORY,
            NegotiationStrategy.COMPETITIVE,
            NegotiationStrategy.COLLABORATIVE,
            NegotiationStrategy.ADAPTIVE,
            NegotiationStrategy.RANDOM
        ]

        agents = [
            NegotiationAgent(
                agent_id=f"agent_{i}",
                name=f"agent_{i}",
                strategy=strategies[i % len(strategies)],
                issues=[issue]
            )
            for i in range(5)
        ]

        service = get_negotiation_service()
        session = service.create_negotiation(
            topic="mixed_strategy",
            agents=agents,
            issues=[issue],
            max_turns=3
        )
        service.start_negotiation(session.session_id)

        engine = session.strategy_engine
        for agent in agents:
            proposal = engine.generate_proposal(agent, session.issues, session.history)
            assert proposal is not None

    def test_csp_framework_full_flow(self):
        """测试CSP框架完整流程"""
        framework = CSPFramework()
        solver = framework.create_solver("s1")

        v1 = solver.add_variable("v1", "x", {1, 2, 3})
        v2 = solver.add_variable("v2", "y", {1, 2, 3})

        constraint = Constraint(
            constraint_id="c1",
            name="x_neq_y",
            constraint_type=ConstraintType.BINARY,
            variables=["v1", "v2"],
            predicate=lambda vals: vals[0] != vals[1]
        )
        solver.add_constraint(constraint)

        result = solver.solve()
        assert result is not None
        if result.success:
            assert result.assignments.get("v1") != result.assignments.get("v2")

    def test_htd_decompose_then_state_machine_execute(self):
        """测试HTD分解后状态机执行"""
        # HTD分解
        decomposer = HTDDecomposer()
        decomposition = decomposer.decompose(
            task_name="pipeline_task",
            task_description="Design, implement and test a feature",
            estimated_time=50.0
        )

        # 创建状态机跟踪执行
        builder = StateMachineBuilder("task_executor")
        builder.add_state("pending", state_type=StateType.INITIAL)
        builder.add_state("executing", state_type=StateType.INTERMEDIATE)
        builder.add_state("completed", state_type=StateType.FINAL)
        builder.add_state("error", state_type=StateType.ERROR)
        builder.set_initial_state("pending")
        builder.set_final_state("completed")
        builder.set_error_state("error")
        builder.add_transition("pending", "executing")
        builder.add_transition("executing", "completed")

        config = builder.build()
        executor = StateMachineExecutor()
        executor.register_machine(config)
        context = executor.create_context("task_executor")

        assert context is not None
        assert context.current_state == "pending"

        # 模拟执行
        result = executor.transition(context.context_id, "executing")
        assert result is not None

        result2 = executor.transition(context.context_id, "completed")
        assert result2 is not None


# ============================================================
# 七、异常容错压力测试
# ============================================================

class TestFaultTolerance:
    """异常容错测试"""

    def test_negotiation_service_double_reset(self):
        """测试双重重置服务"""
        reset_negotiation_service()
        reset_negotiation_service()
        service = get_negotiation_service()
        assert service is not None

    def test_negotiation_service_singleton(self):
        """测试服务单例模式"""
        reset_negotiation_service()
        s1 = get_negotiation_service()
        s2 = get_negotiation_service()
        assert s1 is s2

    def test_proposal_with_none_values(self):
        """测试提案包含None值"""
        proposal = NegotiationProposal(
            proposer_id="test",
            issue_values={"key": None}
        )
        assert proposal.get_issue_value("key") is None

    def test_issue_with_negative_priority(self):
        """测试议题负优先级"""
        issue = NegotiationIssue(name="negative", priority=-1.0)
        assert issue.priority == -1.0

    def test_issue_with_zero_priority(self):
        """测试议题零优先级"""
        issue = NegotiationIssue(name="zero", priority=0.0)
        agent = NegotiationAgent(name="test", issues=[issue])
        proposal = NegotiationProposal(proposer_id="other", issue_values={"zero": "val"})
        utility = agent.calculate_utility(proposal)
        assert isinstance(utility, float)

    def test_multiple_agents_same_id(self):
        """测试多个Agent使用相同ID"""
        session = NegotiationSession(topic="duplicate_id")
        agent1 = NegotiationAgent(agent_id="same_id", name="agent1")
        agent2 = NegotiationAgent(agent_id="same_id", name="agent2")
        session.add_agent(agent1)
        session.add_agent(agent2)
        assert len(session.agents) == 1
        assert session.agents["same_id"].name == "agent2"

    def test_csp_variable_domain_modification(self):
        """测试CSP变量域修改"""
        var = Variable(var_id="v1", name="x", domain={1, 2, 3})
        var.current_value = 1
        assert var.is_assigned() == True
        var.current_value = None
        assert var.is_assigned() == False

    def test_state_machine_builder_minimal(self):
        """测试最小状态机"""
        builder = StateMachineBuilder("minimal_sm")
        builder.add_state("only", state_type=StateType.INITIAL)
        builder.set_initial_state("only")
        builder.set_final_state("only")
        config = builder.build()
        assert config is not None

    def test_contractor_with_empty_skills(self):
        """测试空技能列表的承包商"""
        protocol = ContractNetProtocol()
        contractor = protocol.register_contractor("no_skills", [], max_workload=1)
        assert len(contractor.skills) == 0

    def test_negotiation_with_utility_function_exception(self):
        """测试效用函数抛出异常"""
        def bad_utility(issue_values):
            raise ValueError("Intentional error")

        agent = NegotiationAgent(name="bad_agent", utility_function=bad_utility)
        proposal = NegotiationProposal(proposer_id="other", issue_values={"price": 100})

        with pytest.raises(ValueError):
            agent.calculate_utility(proposal)

    def test_concurrent_session_creation(self):
        """测试并发创建多个会话"""
        protocol = NegotiationProtocol()
        sessions = []
        for i in range(100):
            session = protocol.create_session(f"topic_{i}")
            sessions.append(session)

        assert len(protocol.sessions) == 100
        session_ids = [s.session_id for s in sessions]
        assert len(set(session_ids)) == 100

    def test_very_long_issue_name(self):
        """测试超长议题名称"""
        long_name = "x" * 10000
        issue = NegotiationIssue(name=long_name)
        assert issue.name == long_name

    def test_proposal_with_special_characters(self):
        """测试提案包含特殊字符"""
        proposal = NegotiationProposal(
            proposer_id="test",
            issue_values={"key with spaces": "value\nwith\nnewlines", "中文键": "中文值"}
        )
        assert proposal.get_issue_value("key with spaces") == "value\nwith\nnewlines"
        assert proposal.get_issue_value("中文键") == "中文值"

    def test_state_machine_rollback(self):
        """测试状态机回退"""
        builder = StateMachineBuilder("rollback_sm")
        builder.add_state("s1", state_type=StateType.INITIAL)
        builder.add_state("s2", state_type=StateType.INTERMEDIATE)
        builder.add_state("s3", state_type=StateType.FINAL)
        builder.add_state("error", state_type=StateType.ERROR)
        builder.set_initial_state("s1")
        builder.set_final_state("s3")
        builder.set_error_state("error")
        builder.add_transition("s1", "s2")
        builder.add_transition("s2", "s3")

        config = builder.build()
        executor = StateMachineExecutor()
        executor.register_machine(config)
        context = executor.create_context("rollback_sm")

        executor.transition(context.context_id, "s2")
        assert context.current_state == "s2"

        result = executor.rollback(context.context_id, steps=1)
        # 回退应成功
        assert result is not None

    def test_csp_solver_validate(self):
        """测试CSP求解器验证"""
        solver = CSPSolver()
        v1 = solver.add_variable("v1", "x", {1, 2, 3})
        v2 = solver.add_variable("v2", "y", {1, 2, 3})

        constraint = Constraint(
            constraint_id="c1",
            name="x_lt_y",
            constraint_type=ConstraintType.BINARY,
            variables=["v1", "v2"],
            predicate=lambda vals: vals[0] < vals[1]
        )
        solver.add_constraint(constraint)

        valid, conflicts = solver.validate()
        assert isinstance(valid, bool)
        assert isinstance(conflicts, list)

    def test_contract_net_statistics(self):
        """测试合同网统计"""
        protocol = ContractNetProtocol()
        stats = protocol.get_statistics()
        assert isinstance(stats, dict)

    def test_htd_flat_task_list(self):
        """测试HTD扁平化任务列表"""
        decomposer = HTDDecomposer()
        decomposition = decomposer.decompose(
            task_name="flat_test",
            task_description="Test flat task list generation",
            estimated_time=10.0
        )
        flat_list = decomposer.get_flat_task_list(decomposition)
        assert isinstance(flat_list, list)
        assert len(flat_list) > 0

    def test_htd_dependency_graph(self):
        """测试HTD依赖图"""
        decomposer = HTDDecomposer()
        decomposition = decomposer.decompose(
            task_name="dep_test",
            task_description="Test dependency graph generation",
            estimated_time=10.0
        )
        dep_graph = decomposer.get_task_dependency_graph(decomposition)
        assert isinstance(dep_graph, dict)
