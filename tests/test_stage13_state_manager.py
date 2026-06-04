import pytest
from src.architecture import (
    TaskStatus,
    TaskState,
    TaskStateMachine,
    BusinessState,
    SystemState,
    StateNamespace,
    StateManager,
    get_state_manager,
    reset_state_manager
)


class TestTaskStatus:
    """测试任务状态"""

    def test_task_status_values(self):
        """测试任务状态枚举值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.WAITING.value == "waiting"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_task_status_count(self):
        """测试任务状态数量"""
        assert len(TaskStatus) == 6


class TestTaskStateMachine:
    """测试任务状态机"""

    def test_valid_transition(self):
        """测试有效的状态转换"""
        assert TaskStateMachine.can_transition(TaskStatus.PENDING, TaskStatus.RUNNING) is True
        assert TaskStateMachine.can_transition(TaskStatus.RUNNING, TaskStatus.COMPLETED) is True
        assert TaskStateMachine.can_transition(TaskStatus.RUNNING, TaskStatus.FAILED) is True

    def test_invalid_transition(self):
        """测试无效的状态转换"""
        assert TaskStateMachine.can_transition(TaskStatus.COMPLETED, TaskStatus.RUNNING) is False
        assert TaskStateMachine.can_transition(TaskStatus.PENDING, TaskStatus.COMPLETED) is False


class TestTaskState:
    """测试任务状态对象"""

    def test_create_task_state(self):
        """测试创建任务状态"""
        task = TaskState(task_id="test-001", priority=5)
        assert task.task_id == "test-001"
        assert task.status == TaskStatus.PENDING
        assert task.priority == 5
        assert task.retry_count == 0

    def test_task_transition(self):
        """测试任务状态转换"""
        task = TaskState(task_id="test-001")
        assert task.transition_to(TaskStatus.RUNNING) is True
        assert task.status == TaskStatus.RUNNING

    def test_invalid_task_transition(self):
        """测试无效的任务状态转换"""
        task = TaskState(task_id="test-001")
        assert task.transition_to(TaskStatus.COMPLETED) is False
        assert task.status == TaskStatus.PENDING

    def test_task_to_dict(self):
        """测试任务状态转字典"""
        task = TaskState(task_id="test-001")
        data = task.to_dict()
        assert data["task_id"] == "test-001"
        assert data["status"] == "pending"
        assert "created_at" in data
        assert "updated_at" in data


class TestBusinessState:
    """测试业务状态"""

    def test_create_business_state(self):
        """测试创建业务状态"""
        business = BusinessState(
            business_id="biz-001",
            data={"name": "test"}
        )
        assert business.business_id == "biz-001"
        assert business.data["name"] == "test"
        assert business.version == 0

    def test_business_update(self):
        """测试业务数据更新"""
        business = BusinessState(business_id="biz-001")
        business.update("key1", "value1")
        assert business.get("key1") == "value1"
        assert business.version == 1

    def test_business_lock(self):
        """测试业务状态锁定"""
        business = BusinessState(business_id="biz-001")
        assert business.lock("holder-1") is True
        assert business.locked is True
        assert business.lock_holder == "holder-1"

    def test_business_unlock(self):
        """测试业务状态解锁"""
        business = BusinessState(business_id="biz-001")
        business.lock("holder-1")
        assert business.unlock("holder-1") is True
        assert business.locked is False

    def test_business_lock_prevents_update(self):
        """测试锁定后无法更新"""
        business = BusinessState(business_id="biz-001")
        business.lock("holder-1")
        with pytest.raises(ValueError):
            business.update("key", "value")

    def test_business_to_dict(self):
        """测试业务状态转字典"""
        business = BusinessState(business_id="biz-001")
        data = business.to_dict()
        assert data["business_id"] == "biz-001"
        assert "version" in data
        assert "created_at" in data


class TestSystemState:
    """测试系统状态"""

    def test_create_system_state(self):
        """测试创建系统状态"""
        system = SystemState()
        assert system.healthy is True
        assert len(system.warnings) == 0
        assert len(system.errors) == 0

    def test_record_metric(self):
        """测试记录指标"""
        system = SystemState()
        system.record_metric("requests", 100)
        assert system.metrics["requests"] == 100

    def test_add_warning(self):
        """测试添加警告"""
        system = SystemState()
        system.add_warning("Test warning")
        assert len(system.warnings) == 1
        assert system.warnings[0] == "Test warning"

    def test_add_error(self):
        """测试添加错误"""
        system = SystemState()
        system.add_error("Test error")
        assert len(system.errors) == 1
        assert system.healthy is False

    def test_health_check(self):
        """测试健康检查"""
        system = SystemState()
        health = system.health_check()
        assert "healthy" in health
        assert "uptime_seconds" in health
        assert "version" in health
        assert "metrics" in health


class TestStateNamespace:
    """测试状态命名空间"""

    def test_create_namespace(self):
        """测试创建命名空间"""
        namespace = StateNamespace("test-ns")
        assert namespace.name == "test-ns"

    def test_create_task_in_namespace(self):
        """测试在命名空间中创建任务"""
        namespace = StateNamespace("test-ns")
        task = namespace.create_task(task_id="task-001")
        assert task.task_id == "task-001"
        assert namespace.get_task("task-001") is task

    def test_create_business_in_namespace(self):
        """测试在命名空间中创建业务"""
        namespace = StateNamespace("test-ns")
        business = namespace.create_business("biz-001", {"key": "value"})
        assert business.business_id == "biz-001"
        assert namespace.get_business("biz-001") is business

    def test_init_system_in_namespace(self):
        """测试在命名空间中初始化系统状态"""
        namespace = StateNamespace("test-ns")
        system = namespace.init_system()
        assert isinstance(system, SystemState)
        assert namespace.get_system() is system

    def test_duplicate_task_raises(self):
        """测试重复创建任务抛出异常"""
        namespace = StateNamespace("test-ns")
        namespace.create_task(task_id="task-001")
        with pytest.raises(ValueError):
            namespace.create_task(task_id="task-001")


class TestStateManager:
    """测试状态管理器"""

    def test_create_namespace(self):
        """测试创建命名空间"""
        manager = StateManager()
        ns = manager.create_namespace("ns-1")
        assert ns.name == "ns-1"

    def test_get_namespace(self):
        """测试获取命名空间"""
        manager = StateManager()
        manager.create_namespace("ns-1")
        assert manager.get_namespace("ns-1") is not None
        assert manager.get_namespace("ns-nonexistent") is None

    def test_get_or_create_namespace(self):
        """测试获取或创建命名空间"""
        manager = StateManager()
        ns1 = manager.get_or_create_namespace("ns-1")
        ns2 = manager.get_or_create_namespace("ns-1")
        assert ns1 is ns2

    def test_default_namespace(self):
        """测试默认命名空间"""
        manager = StateManager()
        default = manager.get_default_namespace()
        assert default.name == "default"

    def test_list_namespaces(self):
        """测试列出所有命名空间"""
        manager = StateManager()
        manager.create_namespace("ns-1")
        manager.create_namespace("ns-2")
        namespaces = manager.list_namespaces()
        assert len(namespaces) == 2
        assert "ns-1" in namespaces
        assert "ns-2" in namespaces

    def test_health_check_all(self):
        """测试所有命名空间健康检查"""
        manager = StateManager()
        ns = manager.create_namespace("ns-1")
        ns.init_system()
        results = manager.health_check_all()
        assert "ns-1" in results


class TestGlobalStateManager:
    """测试全局状态管理器"""

    def test_get_state_manager(self):
        """测试获取全局状态管理器"""
        reset_state_manager()
        manager = get_state_manager()
        assert isinstance(manager, StateManager)
        assert get_state_manager() is manager

    def test_reset_state_manager(self):
        """测试重置全局状态管理器"""
        manager1 = get_state_manager()
        reset_state_manager()
        manager2 = get_state_manager()
        assert manager1 is not manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
