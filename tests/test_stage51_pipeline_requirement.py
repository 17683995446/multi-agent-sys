"""
阶段51验收测试：需求接收→拆解链路
"""

import pytest
import time

from src.architecture.pipeline_requirement import (
    RequirementPriority, RequirementStatus,
    Requirement, DecompositionResult,
    RequirementReceiver, RequirementDecomposer, RequirementPipeline,
)


class TestRequirementPriority:
    """测试需求优先级枚举"""

    def test_priority_values(self):
        """测试优先级枚举值"""
        assert RequirementPriority.LOW.value == "low"
        assert RequirementPriority.MEDIUM.value == "medium"
        assert RequirementPriority.HIGH.value == "high"
        assert RequirementPriority.CRITICAL.value == "critical"

    def test_all_priorities(self):
        """测试所有优先级"""
        priorities = list(RequirementPriority)
        assert len(priorities) == 4


class TestRequirementStatus:
    """测试需求状态枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        assert RequirementStatus.RECEIVED.value == "received"
        assert RequirementStatus.ANALYZING.value == "analyzing"
        assert RequirementStatus.DECOMPOSED.value == "decomposed"
        assert RequirementStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(RequirementStatus)
        assert len(statuses) == 4


class TestRequirement:
    """测试需求实体"""

    def test_default_creation(self):
        """测试默认创建"""
        req = Requirement()
        assert req.req_id != ""
        assert req.title == ""
        assert req.description == ""
        assert req.priority == RequirementPriority.MEDIUM
        assert req.status == RequirementStatus.RECEIVED
        assert req.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        req = Requirement(
            title="用户登录",
            description="实现用户登录功能",
            priority=RequirementPriority.HIGH,
            metadata={"source": "product"},
        )
        assert req.title == "用户登录"
        assert req.description == "实现用户登录功能"
        assert req.priority == RequirementPriority.HIGH
        assert req.metadata["source"] == "product"

    def test_unique_ids(self):
        """测试唯一ID"""
        req1 = Requirement()
        req2 = Requirement()
        assert req1.req_id != req2.req_id


class TestDecompositionResult:
    """测试拆解结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = DecompositionResult()
        assert result.req_id == ""
        assert result.subtasks == []
        assert result.decomposition_time == 0.0
        assert result.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        result = DecompositionResult(
            req_id="test-123",
            subtasks=[{"title": "子任务1"}],
            decomposition_time=0.5,
            metadata={"subtask_count": 1},
        )
        assert result.req_id == "test-123"
        assert len(result.subtasks) == 1
        assert result.decomposition_time == 0.5


class TestRequirementReceiver:
    """测试需求接收器"""

    def test_initial_state(self):
        """测试初始状态"""
        receiver = RequirementReceiver()
        assert len(receiver.get_requirements()) == 0

    def test_receive_requirement(self):
        """测试接收需求"""
        receiver = RequirementReceiver()
        req = receiver.receive_requirement("用户注册", "实现用户注册功能")
        assert req.title == "用户注册"
        assert req.status == RequirementStatus.RECEIVED
        assert len(receiver.get_requirements()) == 1

    def test_receive_requirement_empty_title(self):
        """测试空标题接收"""
        receiver = RequirementReceiver()
        with pytest.raises(ValueError):
            receiver.receive_requirement("")

    def test_receive_requirement_with_priority(self):
        """测试带优先级接收"""
        receiver = RequirementReceiver()
        req = receiver.receive_requirement("紧急修复", priority=RequirementPriority.CRITICAL)
        assert req.priority == RequirementPriority.CRITICAL

    def test_validate_requirement(self):
        """测试验证需求"""
        receiver = RequirementReceiver()
        req = receiver.receive_requirement("测试需求")
        assert receiver.validate_requirement(req.req_id) is True

    def test_validate_requirement_not_found(self):
        """测试验证不存在的需求"""
        receiver = RequirementReceiver()
        assert receiver.validate_requirement("nonexistent") is False

    def test_validate_requirement_empty_id(self):
        """测试空ID验证"""
        receiver = RequirementReceiver()
        assert receiver.validate_requirement("") is False

    def test_get_requirements_all(self):
        """测试获取所有需求"""
        receiver = RequirementReceiver()
        receiver.receive_requirement("需求1")
        receiver.receive_requirement("需求2")
        reqs = receiver.get_requirements()
        assert len(reqs) == 2

    def test_get_requirements_by_priority(self):
        """测试按优先级获取需求"""
        receiver = RequirementReceiver()
        receiver.receive_requirement("低优先级", priority=RequirementPriority.LOW)
        receiver.receive_requirement("高优先级", priority=RequirementPriority.HIGH)
        reqs = receiver.get_requirements(priority=RequirementPriority.HIGH)
        assert len(reqs) == 1
        assert reqs[0].priority == RequirementPriority.HIGH

    def test_get_requirements_by_status(self):
        """测试按状态获取需求"""
        receiver = RequirementReceiver()
        receiver.receive_requirement("需求1")
        reqs = receiver.get_requirements(status=RequirementStatus.RECEIVED)
        assert len(reqs) == 1


class TestRequirementDecomposer:
    """测试需求拆解器"""

    def test_decompose_basic(self):
        """测试基本拆解"""
        decomposer = RequirementDecomposer()
        req = Requirement(title="用户登录", description="实现用户登录api接口")
        result = decomposer.decompose(req)
        assert result.req_id == req.req_id
        assert len(result.subtasks) > 0
        assert result.decomposition_time >= 0
        assert req.status == RequirementStatus.DECOMPOSED

    def test_decompose_critical_priority(self):
        """测试紧急优先级拆解"""
        decomposer = RequirementDecomposer()
        req = Requirement(
            title="紧急修复",
            priority=RequirementPriority.CRITICAL,
        )
        result = decomposer.decompose(req)
        # 紧急优先级应产生核心+验证子任务
        assert len(result.subtasks) >= 2

    def test_decompose_high_priority(self):
        """测试高优先级拆解"""
        decomposer = RequirementDecomposer()
        req = Requirement(
            title="高优功能",
            priority=RequirementPriority.HIGH,
        )
        result = decomposer.decompose(req)
        assert len(result.subtasks) >= 2

    def test_decompose_with_domain_keywords(self):
        """测试含领域关键词的拆解"""
        decomposer = RequirementDecomposer()
        req = Requirement(
            title="数据库优化",
            description="优化数据库查询性能",
        )
        result = decomposer.decompose(req)
        # 应包含database领域子任务
        domains = [st.get("domain") for st in result.subtasks]
        assert "database" in domains

    def test_decompose_frontend_domain(self):
        """测试前端领域拆解"""
        decomposer = RequirementDecomposer()
        req = Requirement(
            title="UI组件开发",
            description="开发新的界面组件",
        )
        result = decomposer.decompose(req)
        domains = [st.get("domain") for st in result.subtasks]
        assert "frontend" in domains

    def test_decompose_invalid_requirement(self):
        """测试拆解无效需求"""
        decomposer = RequirementDecomposer()
        with pytest.raises(ValueError):
            decomposer.decompose(Requirement(req_id=""))

    def test_decompose_metadata(self):
        """测试拆解结果元数据"""
        decomposer = RequirementDecomposer()
        req = Requirement(title="测试需求", description="测试描述")
        result = decomposer.decompose(req)
        assert "original_priority" in result.metadata
        assert "subtask_count" in result.metadata


class TestRequirementPipeline:
    """测试需求接收→拆解链路"""

    def test_initial_state(self):
        """测试初始状态"""
        pipeline = RequirementPipeline()
        assert len(pipeline.receiver.get_requirements()) == 0
        assert len(pipeline._results) == 0

    def test_process_basic(self):
        """测试基本处理流程"""
        pipeline = RequirementPipeline()
        result = pipeline.process("用户注册", "实现用户注册功能")
        assert result.req_id != ""
        assert len(result.subtasks) > 0

    def test_process_with_priority(self):
        """测试带优先级处理"""
        pipeline = RequirementPipeline()
        result = pipeline.process("紧急需求", priority=RequirementPriority.CRITICAL)
        assert len(result.subtasks) >= 2

    def test_process_empty_title(self):
        """测试空标题处理"""
        pipeline = RequirementPipeline()
        result = pipeline.process("")
        assert result.metadata.get("error") is not None

    def test_get_status(self):
        """测试获取状态"""
        pipeline = RequirementPipeline()
        result = pipeline.process("测试需求")
        status = pipeline.get_status(result.req_id)
        assert status is not None
        assert status["status"] == RequirementStatus.DECOMPOSED.value
        assert status["has_result"] is True

    def test_get_status_not_found(self):
        """测试获取不存在需求的状态"""
        pipeline = RequirementPipeline()
        status = pipeline.get_status("nonexistent")
        assert status is None

    def test_get_status_empty_id(self):
        """测试空ID获取状态"""
        pipeline = RequirementPipeline()
        status = pipeline.get_status("")
        assert status is None

    def test_full_pipeline_workflow(self):
        """测试完整链路工作流"""
        pipeline = RequirementPipeline()

        # 1. 处理多个需求
        r1 = pipeline.process("前端页面开发", "开发新的UI页面组件", RequirementPriority.HIGH)
        r2 = pipeline.process("后端API开发", "实现数据查询api接口", RequirementPriority.MEDIUM)
        r3 = pipeline.process("数据库迁移", "迁移数据库存储模型", RequirementPriority.LOW)

        # 2. 验证所有需求已接收
        reqs = pipeline.receiver.get_requirements()
        assert len(reqs) == 3

        # 3. 验证拆解结果
        assert len(r1.subtasks) > 0
        assert len(r2.subtasks) > 0
        assert len(r3.subtasks) > 0

        # 4. 验证状态
        s1 = pipeline.get_status(r1.req_id)
        assert s1["status"] == RequirementStatus.DECOMPOSED.value
        assert s1["priority"] == RequirementPriority.HIGH.value
