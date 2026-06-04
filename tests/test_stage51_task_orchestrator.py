"""
阶段51验收测试：任务编排引擎
"""

import pytest
from src.architecture.task_orchestrator import (
    OrchestrationMode,
    TaskDependency,
    OrchestrationPlan,
    TaskOrchestrator,
    OrchestrationService,
)


class TestOrchestrationMode:
    """测试编排模式枚举"""

    def test_mode_values(self):
        """测试编排模式枚举值"""
        assert OrchestrationMode.SEQUENTIAL.value == "sequential"
        assert OrchestrationMode.PARALLEL.value == "parallel"
        assert OrchestrationMode.CONDITIONAL.value == "conditional"
        assert OrchestrationMode.HYBRID.value == "hybrid"

    def test_all_modes(self):
        """测试所有模式"""
        modes = list(OrchestrationMode)
        assert len(modes) == 4


class TestTaskDependency:
    """测试任务依赖关系"""

    def test_default_creation(self):
        """测试默认创建"""
        dep = TaskDependency()
        assert dep.task_id == ""
        assert dep.depends_on == []
        assert dep.condition is None

    def test_custom_creation(self):
        """测试自定义创建"""
        dep = TaskDependency(task_id="t3", depends_on=["t1", "t2"], condition="x > 0")
        assert dep.task_id == "t3"
        assert dep.depends_on == ["t1", "t2"]
        assert dep.condition == "x > 0"


class TestOrchestrationPlan:
    """测试编排计划"""

    def test_default_creation(self):
        """测试默认创建"""
        plan = OrchestrationPlan()
        assert plan.plan_id != ""
        assert plan.name == ""
        assert plan.tasks == []
        assert plan.dependencies == []
        assert plan.mode == OrchestrationMode.SEQUENTIAL

    def test_custom_creation(self):
        """测试自定义创建"""
        plan = OrchestrationPlan(name="测试计划", mode=OrchestrationMode.PARALLEL)
        assert plan.name == "测试计划"
        assert plan.mode == OrchestrationMode.PARALLEL


class TestTaskOrchestrator:
    """测试任务编排器"""

    def test_create_plan(self):
        """测试创建编排计划"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1", mode=OrchestrationMode.SEQUENTIAL)
        assert plan.name == "计划1"
        assert plan.mode == OrchestrationMode.SEQUENTIAL
        assert plan.plan_id in orchestrator.plans

    def test_add_task(self):
        """测试添加任务"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        result = orchestrator.add_task(plan.plan_id, "task1")
        assert result is True
        assert "task1" in plan.tasks

    def test_add_task_duplicate(self):
        """测试添加重复任务"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        orchestrator.add_task(plan.plan_id, "task1")
        assert plan.tasks.count("task1") == 1

    def test_add_task_nonexistent_plan(self):
        """测试向不存在的计划添加任务"""
        orchestrator = TaskOrchestrator()
        result = orchestrator.add_task("nonexistent", "task1")
        assert result is False

    def test_add_dependency(self):
        """测试添加依赖"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        orchestrator.add_task(plan.plan_id, "task2")
        result = orchestrator.add_dependency(plan.plan_id, "task2", ["task1"])
        assert result is True
        assert len(plan.dependencies) == 1
        assert plan.dependencies[0].task_id == "task2"
        assert plan.dependencies[0].depends_on == ["task1"]

    def test_add_dependency_with_condition(self):
        """测试添加带条件的依赖"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        orchestrator.add_task(plan.plan_id, "task2")
        result = orchestrator.add_dependency(plan.plan_id, "task2", ["task1"], condition="success")
        assert result is True
        assert plan.dependencies[0].condition == "success"

    def test_resolve_execution_order_simple(self):
        """测试简单执行顺序解析"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        orchestrator.add_task(plan.plan_id, "task2")
        orchestrator.add_task(plan.plan_id, "task3")
        orchestrator.add_dependency(plan.plan_id, "task2", ["task1"])
        orchestrator.add_dependency(plan.plan_id, "task3", ["task2"])
        order = orchestrator.resolve_execution_order(plan.plan_id)
        assert order is not None
        assert order.index("task1") < order.index("task2")
        assert order.index("task2") < order.index("task3")

    def test_resolve_execution_order_parallel(self):
        """测试并行任务执行顺序"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        orchestrator.add_task(plan.plan_id, "task2")
        orchestrator.add_task(plan.plan_id, "task3")
        orchestrator.add_dependency(plan.plan_id, "task2", ["task1"])
        orchestrator.add_dependency(plan.plan_id, "task3", ["task1"])
        order = orchestrator.resolve_execution_order(plan.plan_id)
        assert order is not None
        assert order.index("task1") < order.index("task2")
        assert order.index("task1") < order.index("task3")

    def test_resolve_execution_order_cyclic(self):
        """测试循环依赖检测"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        orchestrator.add_task(plan.plan_id, "task2")
        orchestrator.add_dependency(plan.plan_id, "task1", ["task2"])
        orchestrator.add_dependency(plan.plan_id, "task2", ["task1"])
        order = orchestrator.resolve_execution_order(plan.plan_id)
        assert order is None

    def test_get_ready_tasks(self):
        """测试获取就绪任务"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        orchestrator.add_task(plan.plan_id, "task2")
        orchestrator.add_dependency(plan.plan_id, "task2", ["task1"])
        ready = orchestrator.get_ready_tasks(plan.plan_id)
        assert "task1" in ready
        assert "task2" not in ready

    def test_get_ready_tasks_after_completion(self):
        """测试任务完成后获取就绪任务"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        orchestrator.add_task(plan.plan_id, "task2")
        orchestrator.add_dependency(plan.plan_id, "task2", ["task1"])
        orchestrator.mark_completed(plan.plan_id, "task1")
        ready = orchestrator.get_ready_tasks(plan.plan_id)
        assert "task2" in ready

    def test_mark_completed(self):
        """测试标记任务完成"""
        orchestrator = TaskOrchestrator()
        plan = orchestrator.create_plan(name="计划1")
        orchestrator.add_task(plan.plan_id, "task1")
        result = orchestrator.mark_completed(plan.plan_id, "task1")
        assert result is True
        assert "task1" in orchestrator.completed_tasks[plan.plan_id]

    def test_mark_completed_nonexistent_plan(self):
        """测试标记不存在的计划的任务"""
        orchestrator = TaskOrchestrator()
        result = orchestrator.mark_completed("nonexistent", "task1")
        assert result is False


class TestOrchestrationService:
    """测试编排服务"""

    def test_execute_plan(self):
        """测试执行编排计划"""
        service = OrchestrationService()
        plan = service.orchestrator.create_plan(name="计划1")
        service.orchestrator.add_task(plan.plan_id, "task1")
        service.orchestrator.add_task(plan.plan_id, "task2")
        service.orchestrator.add_dependency(plan.plan_id, "task2", ["task1"])
        result = service.execute_plan(plan.plan_id)
        assert result["success"] is True
        assert "task1" in result["execution_order"]
        assert "task2" in result["execution_order"]

    def test_execute_plan_cyclic(self):
        """测试执行有循环依赖的计划"""
        service = OrchestrationService()
        plan = service.orchestrator.create_plan(name="计划1")
        service.orchestrator.add_task(plan.plan_id, "task1")
        service.orchestrator.add_task(plan.plan_id, "task2")
        service.orchestrator.add_dependency(plan.plan_id, "task1", ["task2"])
        service.orchestrator.add_dependency(plan.plan_id, "task2", ["task1"])
        result = service.execute_plan(plan.plan_id)
        assert result["success"] is False

    def test_get_plan_status(self):
        """测试获取计划状态"""
        service = OrchestrationService()
        plan = service.orchestrator.create_plan(name="计划1")
        service.orchestrator.add_task(plan.plan_id, "task1")
        service.orchestrator.add_task(plan.plan_id, "task2")
        status = service.get_plan_status(plan.plan_id)
        assert status["exists"] is True
        assert status["total_tasks"] == 2
        assert status["completed_tasks"] == 0
        assert status["progress"] == 0.0

    def test_get_plan_status_after_execution(self):
        """测试执行后获取计划状态"""
        service = OrchestrationService()
        plan = service.orchestrator.create_plan(name="计划1")
        service.orchestrator.add_task(plan.plan_id, "task1")
        service.orchestrator.add_task(plan.plan_id, "task2")
        service.execute_plan(plan.plan_id)
        status = service.get_plan_status(plan.plan_id)
        assert status["completed_tasks"] == 2
        assert status["progress"] == 1.0

    def test_get_plan_status_nonexistent(self):
        """测试获取不存在的计划状态"""
        service = OrchestrationService()
        status = service.get_plan_status("nonexistent")
        assert status["exists"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
