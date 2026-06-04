"""
阶段31验收测试：总控Agent实例初始化

验收标准：
1. ✓ Agent类定义（完整属性）
2. ✓ 权限配置（动态权限）
3. ✓ 任务收口能力（验收确认）
4. ✓ 全局协调（完整协调）
"""

import pytest
from src.architecture.control_agent import (
    AgentStatus,
    PermissionLevel,
    TaskStatus,
    Permission,
    Task,
    AgentConfig,
    CoordinationState,
    PermissionManager,
    TaskManager,
    Coordinator,
    ControlAgent,
    get_control_agent,
    reset_control_agent
)


class TestAgentConfig:
    """测试Agent类定义"""
    
    def test_agent_config_creation(self):
        """测试Agent配置创建"""
        config = AgentConfig(name="TestAgent")
        
        assert config.name == "TestAgent"
        assert config.version == "1.0.0"
        assert config.max_tasks == 10
        assert config.enable_parallel is True
    
    def test_agent_config_custom(self):
        """测试自定义Agent配置"""
        config = AgentConfig(
            name="CustomAgent",
            version="2.0.0",
            description="A custom agent",
            max_tasks=50,
            enable_parallel=False
        )
        
        assert config.name == "CustomAgent"
        assert config.version == "2.0.0"
        assert config.max_tasks == 50
        assert config.enable_parallel is False


class TestPermissionManager:
    """测试权限配置"""
    
    def test_grant_permission(self):
        """测试授予权限"""
        manager = PermissionManager()
        
        perm = manager.grant_permission(
            "agent1",
            PermissionLevel.EXECUTE
        )
        
        assert perm.level == PermissionLevel.EXECUTE
        assert perm.can_execute is True
    
    def test_has_permission(self):
        """测试权限检查"""
        manager = PermissionManager()
        
        manager.grant_permission("agent1", PermissionLevel.MODIFY)
        manager.grant_permission("agent2", PermissionLevel.READ_ONLY)
        
        assert manager.has_permission("agent1", "create") is True
        assert manager.has_permission("agent1", "modify") is True
        assert manager.has_permission("agent2", "create") is False
        assert manager.has_permission("agent2", "execute") is False
    
    def test_dynamic_update_permission(self):
        """测试动态权限更新"""
        manager = PermissionManager()
        
        manager.grant_permission("agent1", PermissionLevel.READ_ONLY)
        
        # 初始权限
        assert manager.has_permission("agent1", "modify") is False
        
        # 动态更新权限
        updated = manager.update_permission("agent1", can_modify=True)
        
        assert updated is not None
        assert manager.has_permission("agent1", "modify") is True


class TestTaskManager:
    """测试任务管理"""
    
    def test_create_task(self):
        """测试创建任务"""
        manager = TaskManager()
        
        task = manager.create_task("Test Task", "A test description")
        
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
    
    def test_update_task_status(self):
        """测试更新任务状态"""
        manager = TaskManager()
        
        task = manager.create_task("Test Task")
        
        updated = manager.update_task_status(task.task_id, TaskStatus.IN_PROGRESS)
        
        assert updated is not None
        assert updated.status == TaskStatus.IN_PROGRESS
        assert updated.started_at is not None
    
    def test_accept_task(self):
        """测试验收确认"""
        manager = TaskManager()
        
        task = manager.create_task("Test Task")
        manager.update_task_status(task.task_id, TaskStatus.IN_PROGRESS)
        
        accepted = manager.accept_task(task.task_id, "All good!")
        
        assert accepted is not None
        assert accepted.status == TaskStatus.ACCEPTED
        assert accepted.output == "All good!"
        assert accepted.completed_at is not None
    
    def test_get_summary(self):
        """测试任务汇总"""
        manager = TaskManager()
        
        task1 = manager.create_task("Task 1")
        task2 = manager.create_task("Task 2")
        
        manager.update_task_status(task1.task_id, TaskStatus.ACCEPTED)
        
        summary = manager.get_summary()
        
        assert summary["total"] == 2
        assert summary["pending"] == 1
        assert summary["accepted"] == 1


class TestCoordinator:
    """测试协调器"""
    
    def test_register_agent(self):
        """测试注册Agent"""
        coordinator = Coordinator()
        
        success = coordinator.register_agent("agent1", "analysis")
        
        assert success is True
        assert "agent1" in coordinator.state.active_agents
    
    def test_assign_task(self):
        """测试分配任务"""
        coordinator = Coordinator()
        
        coordinator.register_agent("agent1", "analysis")
        
        success = coordinator.assign_task("agent1", "task1")
        
        assert success is True
        assert "task1" in coordinator.state.pending_tasks
    
    def test_get_state(self):
        """测试获取协调状态"""
        coordinator = Coordinator()
        
        coordinator.register_agent("agent1", "analysis")
        coordinator.assign_task("agent1", "task1")
        
        state = coordinator.get_state()
        
        assert isinstance(state, CoordinationState)
        assert len(state.active_agents) == 1
        assert len(state.pending_tasks) == 1


class TestControlAgent:
    """测试总控Agent"""
    
    def test_initialize(self):
        """测试初始化Agent"""
        config = AgentConfig(name="TestControlAgent")
        agent = ControlAgent(config)
        
        success = agent.initialize()
        
        assert success is True
        assert agent.status == AgentStatus.RUNNING
    
    def test_shutdown(self):
        """测试关闭Agent"""
        config = AgentConfig(name="TestControlAgent")
        agent = ControlAgent(config)
        
        agent.initialize()
        success = agent.shutdown()
        
        assert success is True
        assert agent.status == AgentStatus.COMPLETED
    
    def test_create_and_accept_task(self):
        """测试创建并验收任务"""
        config = AgentConfig(name="TestControlAgent")
        agent = ControlAgent(config)
        
        agent.initialize()
        
        # 创建任务
        task = agent.create_task("Important Task", "Very important")
        
        # 验收任务
        agent.task_manager.update_task_status(task.task_id, TaskStatus.IN_PROGRESS)
        accepted = agent.accept_task(task.task_id)
        
        assert accepted is not None
        assert accepted.status == TaskStatus.ACCEPTED
    
    def test_register_subagent(self):
        """测试注册子Agent"""
        config = AgentConfig(name="TestControlAgent")
        agent = ControlAgent(config)
        
        agent.initialize()
        
        success = agent.register_subagent("req_agent", "requirement")
        
        assert success is True
    
    def test_task_summary(self):
        """测试任务汇总"""
        config = AgentConfig(name="TestControlAgent")
        agent = ControlAgent(config)
        
        agent.initialize()
        
        agent.create_task("Task 1")
        task2 = agent.create_task("Task 2")
        
        agent.task_manager.update_task_status(task2.task_id, TaskStatus.IN_PROGRESS)
        agent.accept_task(task2.task_id)
        
        summary = agent.get_task_summary()
        
        assert summary["total"] >= 2
        assert summary["accepted"] >= 1


class TestGlobalAgent:
    """测试全局Agent"""
    
    def test_get_global_agent(self):
        """测试获取全局Agent"""
        reset_control_agent()
        
        agent1 = get_control_agent()
        agent2 = get_control_agent()
        
        assert agent1 is agent2
    
    def test_reset_global_agent(self):
        """测试重置全局Agent"""
        agent1 = get_control_agent()
        reset_control_agent()
        agent2 = get_control_agent()
        
        assert agent1 is not agent2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
