"""
阶段53验收测试：工作流引擎
"""

import pytest
from src.architecture.workflow_engine import (
    WorkflowStatus,
    StepStatus,
    WorkflowStep,
    WorkflowDefinition,
    WorkflowContext,
    WorkflowEngine,
)


class TestWorkflowStatus:
    """测试工作流状态枚举"""

    def test_status_values(self):
        """测试工作流状态枚举值"""
        assert WorkflowStatus.CREATED.value == "created"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.PAUSED.value == "paused"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(WorkflowStatus)
        assert len(statuses) == 5


class TestStepStatus:
    """测试步骤状态枚举"""

    def test_status_values(self):
        """测试步骤状态枚举值"""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.ACTIVE.value == "active"
        assert StepStatus.DONE.value == "done"
        assert StepStatus.ERROR.value == "error"
        assert StepStatus.SKIPPED.value == "skipped"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(StepStatus)
        assert len(statuses) == 5


class TestWorkflowStep:
    """测试工作流步骤"""

    def test_default_creation(self):
        """测试默认创建"""
        step = WorkflowStep()
        assert step.step_id != ""
        assert step.name == ""
        assert step.handler_name == ""
        assert step.next_steps == []
        assert step.condition is None
        assert step.status == StepStatus.PENDING

    def test_custom_creation(self):
        """测试自定义创建"""
        step = WorkflowStep(
            name="步骤1",
            handler_name="handle_step1",
            next_steps=["step2"],
            condition="x > 0",
        )
        assert step.name == "步骤1"
        assert step.handler_name == "handle_step1"
        assert step.next_steps == ["step2"]
        assert step.condition == "x > 0"


class TestWorkflowDefinition:
    """测试工作流定义"""

    def test_default_creation(self):
        """测试默认创建"""
        defn = WorkflowDefinition()
        assert defn.workflow_id != ""
        assert defn.name == ""
        assert defn.steps == []
        assert defn.initial_step == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        step1 = WorkflowStep(step_id="s1", name="步骤1")
        step2 = WorkflowStep(step_id="s2", name="步骤2")
        defn = WorkflowDefinition(name="测试工作流", steps=[step1, step2], initial_step="s1")
        assert defn.name == "测试工作流"
        assert len(defn.steps) == 2
        assert defn.initial_step == "s1"


class TestWorkflowContext:
    """测试工作流上下文"""

    def test_default_creation(self):
        """测试默认创建"""
        ctx = WorkflowContext()
        assert ctx.workflow_id != ""
        assert ctx.current_step == ""
        assert ctx.data == {}
        assert ctx.history == []
        assert ctx.status == WorkflowStatus.CREATED

    def test_custom_creation(self):
        """测试自定义创建"""
        ctx = WorkflowContext(
            current_step="s1",
            data={"key": "value"},
            status=WorkflowStatus.RUNNING,
        )
        assert ctx.current_step == "s1"
        assert ctx.data["key"] == "value"
        assert ctx.status == WorkflowStatus.RUNNING


class TestWorkflowEngine:
    """测试工作流引擎"""

    def _create_simple_workflow(self):
        """创建简单工作流"""
        engine = WorkflowEngine()
        step1 = WorkflowStep(step_id="s1", name="步骤1", handler_name="handler1", next_steps=["s2"])
        step2 = WorkflowStep(step_id="s2", name="步骤2", handler_name="handler2")
        defn = WorkflowDefinition(name="简单工作流", steps=[step1, step2], initial_step="s1")
        engine.register_workflow(defn)
        engine.handlers["handler1"] = lambda data: {"step1_result": "done"}
        engine.handlers["handler2"] = lambda data: {"step2_result": "done"}
        return engine, defn

    def test_register_workflow(self):
        """测试注册工作流"""
        engine = WorkflowEngine()
        defn = WorkflowDefinition(name="测试工作流")
        result = engine.register_workflow(defn)
        assert result is True
        assert defn.workflow_id in engine.definitions

    def test_start_workflow(self):
        """测试启动工作流"""
        engine, defn = self._create_simple_workflow()
        context_id = engine.start_workflow(defn.workflow_id)
        assert context_id is not None
        context = engine.get_context(context_id)
        assert context is not None
        assert context.status == WorkflowStatus.RUNNING
        assert context.current_step == "s1"

    def test_start_workflow_nonexistent(self):
        """测试启动不存在的工作流"""
        engine = WorkflowEngine()
        result = engine.start_workflow("nonexistent")
        assert result is None

    def test_execute_step(self):
        """测试执行步骤"""
        engine, defn = self._create_simple_workflow()
        context_id = engine.start_workflow(defn.workflow_id)
        result = engine.execute_step(context_id)
        assert result["success"] is True
        assert result["current_step"] == "s2"

    def test_execute_step_complete(self):
        """测试执行到最后一步"""
        engine, defn = self._create_simple_workflow()
        context_id = engine.start_workflow(defn.workflow_id)
        engine.execute_step(context_id)  # s1 -> s2
        result = engine.execute_step(context_id)  # s2 -> completed
        assert result["success"] is True
        assert result["status"] == "completed"

    def test_execute_step_nonexistent_context(self):
        """测试执行不存在上下文的步骤"""
        engine = WorkflowEngine()
        result = engine.execute_step("nonexistent")
        assert result["success"] is False

    def test_get_context(self):
        """测试获取上下文"""
        engine, defn = self._create_simple_workflow()
        context_id = engine.start_workflow(defn.workflow_id)
        context = engine.get_context(context_id)
        assert context is not None
        assert context.current_step == "s1"

    def test_get_context_nonexistent(self):
        """测试获取不存在的上下文"""
        engine = WorkflowEngine()
        context = engine.get_context("nonexistent")
        assert context is None

    def test_pause_workflow(self):
        """测试暂停工作流"""
        engine, defn = self._create_simple_workflow()
        context_id = engine.start_workflow(defn.workflow_id)
        result = engine.pause_workflow(context_id)
        assert result is True
        context = engine.get_context(context_id)
        assert context.status == WorkflowStatus.PAUSED

    def test_pause_workflow_nonexistent(self):
        """测试暂停不存在的工作流"""
        engine = WorkflowEngine()
        result = engine.pause_workflow("nonexistent")
        assert result is False

    def test_resume_workflow(self):
        """测试恢复工作流"""
        engine, defn = self._create_simple_workflow()
        context_id = engine.start_workflow(defn.workflow_id)
        engine.pause_workflow(context_id)
        result = engine.resume_workflow(context_id)
        assert result is True
        context = engine.get_context(context_id)
        assert context.status == WorkflowStatus.RUNNING

    def test_resume_workflow_not_paused(self):
        """测试恢复未暂停的工作流"""
        engine, defn = self._create_simple_workflow()
        context_id = engine.start_workflow(defn.workflow_id)
        result = engine.resume_workflow(context_id)
        assert result is False

    def test_resume_workflow_nonexistent(self):
        """测试恢复不存在的工作流"""
        engine = WorkflowEngine()
        result = engine.resume_workflow("nonexistent")
        assert result is False

    def test_execute_step_while_paused(self):
        """测试暂停时执行步骤"""
        engine, defn = self._create_simple_workflow()
        context_id = engine.start_workflow(defn.workflow_id)
        engine.pause_workflow(context_id)
        result = engine.execute_step(context_id)
        assert result["success"] is False

    def test_full_workflow(self):
        """测试完整工作流执行"""
        engine = WorkflowEngine()
        step1 = WorkflowStep(step_id="s1", name="开始", handler_name="h1", next_steps=["s2"])
        step2 = WorkflowStep(step_id="s2", name="处理", handler_name="h2", next_steps=["s3"])
        step3 = WorkflowStep(step_id="s3", name="结束", handler_name="h3")
        defn = WorkflowDefinition(name="完整工作流", steps=[step1, step2, step3], initial_step="s1")
        engine.register_workflow(defn)
        engine.handlers["h1"] = lambda data: {"phase": "started"}
        engine.handlers["h2"] = lambda data: {"phase": "processing"}
        engine.handlers["h3"] = lambda data: {"phase": "completed"}

        context_id = engine.start_workflow(defn.workflow_id, initial_data={"input": "test"})
        assert context_id is not None

        result1 = engine.execute_step(context_id)
        assert result1["success"] is True
        assert result1["current_step"] == "s2"

        result2 = engine.execute_step(context_id)
        assert result2["success"] is True
        assert result2["current_step"] == "s3"

        result3 = engine.execute_step(context_id)
        assert result3["success"] is True
        assert result3["status"] == "completed"

        context = engine.get_context(context_id)
        assert len(context.history) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
