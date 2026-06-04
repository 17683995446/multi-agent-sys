import pytest
from src.agents.metagpt_core import (
    RoleType, TaskStatus, BaseRole, ProductManager, Architect,
    Engineer, Tester, RoleRegistry, create_default_registry,
    Task, Message, RoleAction
)
from src.agents.metagpt_workflow import (
    WorkflowEngine, create_standard_development_workflow
)


class TestMetaGPTCore:
    """测试MetaGPT核心功能"""
    
    def test_role_types(self):
        """测试角色类型枚举"""
        assert RoleType.PRODUCT_MANAGER == "product_manager"
        assert RoleType.ARCHITECT == "architect"
        assert RoleType.ENGINEER == "engineer"
        assert RoleType.TESTER == "tester"
    
    def test_create_product_manager(self):
        """测试创建产品经理角色"""
        pm = ProductManager()
        assert pm.name == "ProductManager"
        assert pm.role_type == RoleType.PRODUCT_MANAGER
    
    def test_create_architect(self):
        """测试创建架构师角色"""
        architect = Architect()
        assert architect.name == "Architect"
        assert architect.role_type == RoleType.ARCHITECT
    
    def test_create_engineer(self):
        """测试创建工程师角色"""
        engineer = Engineer()
        assert engineer.name == "Engineer"
        assert engineer.role_type == RoleType.ENGINEER
    
    def test_create_tester(self):
        """测试创建测试工程师角色"""
        tester = Tester()
        assert tester.name == "Tester"
        assert tester.role_type == RoleType.TESTER
    
    def test_role_registry(self):
        """测试角色注册表"""
        registry = RoleRegistry()
        registry.register(ProductManager())
        registry.register(Architect())
        
        assert RoleType.PRODUCT_MANAGER in registry.list_roles()
        assert RoleType.ARCHITECT in registry.list_roles()
        
        pm = registry.get(RoleType.PRODUCT_MANAGER)
        assert pm is not None
        assert pm.role_type == RoleType.PRODUCT_MANAGER
    
    def test_default_registry(self):
        """测试默认注册表"""
        registry = create_default_registry()
        assert len(registry.list_roles()) == 4
    
    def test_task_creation(self):
        """测试任务创建"""
        task = Task(
            id="test-1",
            title="Test Task",
            description="A test task",
            role=RoleType.ENGINEER
        )
        assert task.id == "test-1"
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING
    
    def test_message_creation(self):
        """测试消息创建"""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"


class TestRoleActions:
    """测试角色动作"""
    
    def test_pm_define_prd(self):
        """测试产品经理定义PRD"""
        pm = ProductManager()
        result = pm.execute_action("define_prd", {"title": "Test Project"})
        assert "Product Requirements Document" in result
        assert "Test Project" in result
    
    def test_architect_design_architecture(self):
        """测试架构师设计架构"""
        architect = Architect()
        result = architect.execute_action("design_architecture", {})
        assert "layers" in result
        assert len(result["layers"]) == 4
    
    def test_engineer_write_code(self):
        """测试工程师编写代码"""
        engineer = Engineer()
        result = engineer.execute_action("write_code", {"task": "Test Feature"})
        assert "Code for Test Feature" in result
    
    def test_tester_execute_tests(self):
        """测试测试工程师执行测试"""
        tester = Tester()
        result = tester.execute_action("execute_tests", {})
        assert result["passed"] == 10
        assert result["failed"] == 0


class TestWorkflowEngine:
    """测试工作流引擎"""
    
    def test_create_workflow_engine(self):
        """测试创建工作流引擎"""
        engine = WorkflowEngine()
        assert engine.registry is not None
        assert len(engine.tasks) == 0
    
    def test_load_workflow(self):
        """测试加载工作流"""
        engine = WorkflowEngine()
        template = create_standard_development_workflow()
        engine.load_workflow(template)
        assert len(engine.tasks) == 4
    
    def test_get_ready_tasks(self):
        """测试获取准备好的任务"""
        engine = WorkflowEngine()
        template = create_standard_development_workflow()
        engine.load_workflow(template)
        ready = engine.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "task-1"
    
    def test_execute_task(self):
        """测试执行任务"""
        engine = WorkflowEngine()
        template = create_standard_development_workflow()
        engine.load_workflow(template)
        result = engine.execute_task("task-1", {"title": "Test"})
        assert result is not None
    
    def test_run_workflow(self):
        """测试运行完整工作流"""
        engine = WorkflowEngine()
        template = create_standard_development_workflow()
        engine.load_workflow(template)
        results = engine.run_workflow("task-1", {"title": "Test Project"})
        assert len(results) == 4
