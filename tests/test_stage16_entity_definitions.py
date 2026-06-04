import pytest
from src.architecture import (
    TaskPriority,
    TaskType,
    CodeEntityType,
    MessageType,
    StateType,
    TaskEntity,
    VariableEntity,
    MethodEntity,
    ClassEntity,
    ModuleEntity,
    CodeEntity,
    MessageEntity,
    StateEntity,
    StateMachine,
    EntityRegistry,
    get_entity_registry,
    reset_entity_registry
)


class TestTaskEntity:
    """测试任务实体"""

    def test_create_task_entity(self):
        """测试创建任务实体"""
        task = TaskEntity(
            name="Test Task",
            description="Test Description",
            task_type=TaskType.CODE_GENERATION,
            priority=TaskPriority.HIGH
        )
        assert task.name == "Test Task"
        assert task.task_type == TaskType.CODE_GENERATION
        assert task.priority == TaskPriority.HIGH
        assert task.task_id is not None

    def test_task_to_dict(self):
        """测试任务转字典"""
        task = TaskEntity(name="Test Task")
        data = task.to_dict()
        assert "task_id" in data
        assert "name" in data
        assert "created_at" in data

    def test_task_from_dict(self):
        """测试从字典创建任务"""
        data = {
            "name": "Test Task",
            "task_type": "code_generation",
            "priority": "high"
        }
        task = TaskEntity.from_dict(data)
        assert task.name == "Test Task"
        assert task.task_type == TaskType.CODE_GENERATION


class TestCodeEntities:
    """测试代码实体"""

    def test_create_variable_entity(self):
        """测试创建变量实体"""
        var = VariableEntity(
            name="x",
            data_type="int",
            scope="local"
        )
        assert var.name == "x"
        assert var.data_type == "int"
        assert var.is_mutable is True

    def test_create_method_entity(self):
        """测试创建方法实体"""
        method = MethodEntity(
            name="test_method",
            parameters=[{"name": "x", "type": "int"}],
            return_type="str"
        )
        assert method.name == "test_method"
        assert len(method.parameters) == 1
        assert method.return_type == "str"

    def test_create_class_entity(self):
        """测试创建类实体"""
        cls = ClassEntity(
            name="TestClass",
            bases=["BaseClass"]
        )
        assert cls.name == "TestClass"
        assert "BaseClass" in cls.bases

    def test_create_module_entity(self):
        """测试创建模块实体"""
        module = ModuleEntity(
            name="test_module",
            file_path="test.py"
        )
        assert module.name == "test_module"
        assert module.file_path == "test.py"

    def test_code_entity_creation(self):
        """测试统一代码实体"""
        entity = CodeEntity(
            entity_type=CodeEntityType.VARIABLE,
            name="x"
        )
        assert entity.name == "x"
        assert entity.entity_type == CodeEntityType.VARIABLE


class TestMessageEntity:
    """测试消息实体"""

    def test_create_message(self):
        """测试创建消息"""
        msg = MessageEntity(
            message_type=MessageType.REQUEST,
            sender="Agent1",
            receiver="Agent2",
            content="Test message"
        )
        assert msg.sender == "Agent1"
        assert msg.receiver == "Agent2"
        assert msg.message_type == MessageType.REQUEST

    def test_create_request(self):
        """测试创建请求消息"""
        msg = MessageEntity.create_request(
            sender="Agent1",
            receiver="Agent2",
            content="Request",
            payload={"key": "value"}
        )
        assert msg.message_type == MessageType.REQUEST
        assert msg.payload["key"] == "value"

    def test_create_response(self):
        """测试创建响应消息"""
        msg = MessageEntity.create_response(
            sender="Agent1",
            receiver="Agent2",
            content="Response",
            correlation_id="req-123"
        )
        assert msg.message_type == MessageType.RESPONSE
        assert msg.correlation_id == "req-123"

    def test_message_to_dict(self):
        """测试消息转字典"""
        msg = MessageEntity(
            sender="Agent1",
            receiver="Agent2",
            content="Test"
        )
        data = msg.to_dict()
        assert "message_id" in data
        assert "timestamp" in data


class TestStateEntity:
    """测试状态实体"""

    def test_create_state_entity(self):
        """测试创建状态实体"""
        state = StateEntity(
            state_type=StateType.ACTIVE,
            name="ActiveState"
        )
        assert state.name == "ActiveState"
        assert state.state_type == StateType.ACTIVE

    def test_add_transition(self):
        """测试添加状态转换"""
        state = StateEntity(name="State1")
        state.add_transition("State2", "event1")
        assert len(state.transitions) == 1
        assert state.transitions[0]["to_state"] == "State2"

    def test_state_to_dict(self):
        """测试状态转字典"""
        state = StateEntity(name="TestState")
        data = state.to_dict()
        assert "state_id" in data
        assert "transitions" in data


class TestStateMachine:
    """测试状态机"""

    def test_create_state_machine(self):
        """测试创建状态机"""
        sm = StateMachine("TestSM")
        assert sm.name == "TestSM"
        assert len(sm.states) == 0

    def test_add_and_set_state(self):
        """测试添加和设置状态"""
        sm = StateMachine("TestSM")
        state1 = StateEntity(name="State1", state_type=StateType.INITIAL)
        state2 = StateEntity(name="State2", state_type=StateType.ACTIVE)
        
        sm.add_state(state1)
        sm.add_state(state2)
        assert sm.set_initial_state("State1") is True

    def test_transition(self):
        """测试状态转换"""
        sm = StateMachine("TestSM")
        state1 = StateEntity(name="State1", state_type=StateType.INITIAL)
        state2 = StateEntity(name="State2", state_type=StateType.ACTIVE)
        
        state1.add_transition("State2", "start")
        sm.add_state(state1)
        sm.add_state(state2)
        sm.set_initial_state("State1")
        
        assert sm.transition("start") is True
        assert sm.current_state.name == "State2"

    def test_get_current_state(self):
        """测试获取当前状态"""
        sm = StateMachine("TestSM")
        state = StateEntity(name="State1")
        sm.add_state(state)
        sm.set_initial_state("State1")
        
        current = sm.get_current_state()
        assert current.name == "State1"


class TestEntityRegistry:
    """测试实体注册中心"""

    def test_create_registry(self):
        """测试创建注册中心"""
        registry = EntityRegistry()
        assert len(registry.tasks) == 0

    def test_register_task(self):
        """测试注册任务"""
        registry = EntityRegistry()
        task = TaskEntity(name="Task1")
        registry.register_task(task)
        assert registry.get_task(task.task_id) is task

    def test_register_code_entity(self):
        """测试注册代码实体"""
        registry = EntityRegistry()
        entity = CodeEntity(name="Var1")
        registry.register_code_entity(entity)
        assert registry.get_code_entity(entity.entity_id) is entity

    def test_register_message(self):
        """测试注册消息"""
        registry = EntityRegistry()
        msg = MessageEntity(sender="Agent1", receiver="Agent2", content="Test")
        registry.register_message(msg)
        assert registry.get_message(msg.message_id) is msg

    def test_register_state(self):
        """测试注册状态"""
        registry = EntityRegistry()
        state = StateEntity(name="State1")
        registry.register_state(state)
        assert registry.get_state(state.state_id) is state


class TestGlobalRegistry:
    """测试全局注册中心"""

    def test_get_entity_registry(self):
        """测试获取全局注册中心"""
        reset_entity_registry()
        registry = get_entity_registry()
        assert isinstance(registry, EntityRegistry)
        assert get_entity_registry() is registry

    def test_reset_entity_registry(self):
        """测试重置全局注册中心"""
        registry1 = get_entity_registry()
        reset_entity_registry()
        registry2 = get_entity_registry()
        assert registry1 is not registry2


class TestEntityTypes:
    """测试实体类型枚举"""

    def test_task_priority_values(self):
        """测试任务优先级枚举"""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.HIGH.value == "high"

    def test_task_type_values(self):
        """测试任务类型枚举"""
        assert TaskType.CODE_GENERATION.value == "code_generation"
        assert TaskType.CODE_REVIEW.value == "code_review"

    def test_code_entity_type_values(self):
        """测试代码实体类型枚举"""
        assert CodeEntityType.VARIABLE.value == "variable"
        assert CodeEntityType.METHOD.value == "method"
        assert CodeEntityType.CLASS.value == "class"
        assert CodeEntityType.MODULE.value == "module"

    def test_message_type_values(self):
        """测试消息类型枚举"""
        assert MessageType.REQUEST.value == "request"
        assert MessageType.RESPONSE.value == "response"

    def test_state_type_values(self):
        """测试状态类型枚举"""
        assert StateType.INITIAL.value == "initial"
        assert StateType.COMPLETED.value == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
