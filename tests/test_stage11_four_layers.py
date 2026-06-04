import pytest
from src.architecture.layer_integration import (
    LayerArchitecture,
    InputLayer,
    SchedulerLayer,
    AgentLayer,
    ExecutorLayer,
    ArchitectureValidator,
    LayerMetrics
)
from src.input_layer import TaskInput, TaskClassifier, InputPreprocessor
from src.scheduler import TaskStatus, TaskState, TaskScheduler, SchedulerNode
from src.agents import (
    BaseAgent, AgentConfig, AgentRegistry,
    AdminAgent, RequirementAgent, ArchitectureAgent, DeveloperAgent,
    DebugAgent, ReviewAgent, TestAgent, DocumentAgent
)
from src.executors import (
    CodeEntity, VariableAtom, MethodAtom, ClassAtom, ModuleAtom,
    ASTParser, PythonScanner, CodeFixer
)
import ast


class TestInputLayer:
    """测试输入层"""
    
    def test_task_classifier(self):
        """测试任务分类器"""
        classifier = TaskClassifier()
        task = TaskInput(
            task_id="task_001",
            task_type="requirement"
        )
        result = classifier.classify(task)
        assert result == "需求开发"
    
    def test_input_preprocessor(self):
        """测试输入预处理器"""
        preprocessor = InputPreprocessor()
        task = TaskInput(
            task_id="task_002",
            task_type="refactor"
        )
        result = preprocessor.preprocess(task)
        assert result.task_id == "task_002"
    
    def test_input_layer_receive(self):
        """测试输入层接收"""
        layer = InputLayer()
        task_data = {
            "task_id": "task_003",
            "task_type": "bug_fix"
        }
        task = layer.receive(task_data)
        assert task.task_id == "task_003"
        assert task.task_type == "bug_fix"


class TestSchedulerLayer:
    """测试调度层"""
    
    def test_scheduler_node(self):
        """测试调度节点"""
        node = SchedulerNode("test_node", lambda x: x)
        assert node.name == "test_node"
        node.add_next("next_node")
        assert "next_node" in node.next_nodes
    
    def test_task_scheduler(self):
        """测试任务调度器"""
        scheduler = TaskScheduler()
        node = SchedulerNode("test", lambda x: x)
        scheduler.add_node(node)
        assert "test" in scheduler.nodes
    
    def test_task_state(self):
        """测试任务状态"""
        state = TaskState(task_id="task_001")
        assert state.task_id == "task_001"
        assert state.status == TaskStatus.PENDING
    
    def test_scheduler_layer(self):
        """测试调度层"""
        layer = SchedulerLayer()
        assert len(layer.scheduler.nodes) >= 5


class TestAgentLayer:
    """测试Agent层"""
    
    def test_agent_config(self):
        """测试Agent配置"""
        config = AgentConfig(
            agent_id="test_agent",
            agent_type="test",
            name="测试Agent",
            capabilities=["capability1"]
        )
        assert config.agent_id == "test_agent"
        assert len(config.capabilities) == 1
    
    def test_admin_agent(self):
        """测试总控Agent"""
        config = AgentConfig(
            agent_id="admin",
            agent_type="admin",
            name="总控"
        )
        agent = AdminAgent(config)
        result = agent.process({})
        assert result["status"] == "coordinated"
    
    def test_requirement_agent(self):
        """测试需求Agent"""
        config = AgentConfig(
            agent_id="req",
            agent_type="requirement",
            name="需求"
        )
        agent = RequirementAgent(config)
        result = agent.process({})
        assert result["status"] == "decomposed"
    
    def test_architecture_agent(self):
        """测试架构Agent"""
        config = AgentConfig(
            agent_id="arch",
            agent_type="architecture",
            name="架构"
        )
        agent = ArchitectureAgent(config)
        result = agent.process({})
        assert result["status"] == "architected"
    
    def test_developer_agent(self):
        """测试开发Agent"""
        config = AgentConfig(
            agent_id="dev",
            agent_type="developer",
            name="开发"
        )
        agent = DeveloperAgent(config)
        result = agent.process({})
        assert result["status"] == "developed"
    
    def test_debug_agent(self):
        """测试调试Agent"""
        config = AgentConfig(
            agent_id="debug",
            agent_type="debug",
            name="调试"
        )
        agent = DebugAgent(config)
        result = agent.process({})
        assert result["status"] == "debugged"
    
    def test_review_agent(self):
        """测试评审Agent"""
        config = AgentConfig(
            agent_id="review",
            agent_type="review",
            name="评审"
        )
        agent = ReviewAgent(config)
        result = agent.process({})
        assert result["status"] == "reviewed"
    
    def test_test_agent(self):
        """测试测试Agent"""
        config = AgentConfig(
            agent_id="test",
            agent_type="test",
            name="测试"
        )
        agent = TestAgent(config)
        result = agent.process({})
        assert result["status"] == "tested"
    
    def test_document_agent(self):
        """测试文档Agent"""
        config = AgentConfig(
            agent_id="doc",
            agent_type="document",
            name="文档"
        )
        agent = DocumentAgent(config)
        result = agent.process({})
        assert result["status"] == "documented"
    
    def test_agent_registry(self):
        """测试Agent注册"""
        registry = AgentRegistry()
        config = AgentConfig(
            agent_id="test",
            agent_type="test",
            name="测试"
        )
        agent = AdminAgent(config)
        registry.register(agent)
        
        retrieved = registry.get("test")
        assert retrieved is not None
        assert retrieved.config.agent_id == "test"
    
    def test_agent_layer(self):
        """测试Agent层"""
        layer = AgentLayer()
        agents = layer.list_agents()
        assert len(agents) == 8


class TestExecutorLayer:
    """测试执行层"""
    
    def test_code_entity(self):
        """测试代码实体"""
        entity = CodeEntity(
            entity_type="function",
            name="test_func",
            file_path="test.py",
            line_number=10,
            content="def test_func(): pass"
        )
        assert entity.name == "test_func"
        assert entity.entity_type == "function"
    
    def test_variable_atom(self):
        """测试变量原子"""
        atom = VariableAtom(
            name="test_var",
            type_annotation="int"
        )
        assert atom.name == "test_var"
        assert atom.type_annotation == "int"
    
    def test_method_atom(self):
        """测试方法原子"""
        atom = MethodAtom(
            name="test_method",
            parameters=["arg1", "arg2"],
            lines=20
        )
        assert atom.name == "test_method"
        assert len(atom.parameters) == 2
    
    def test_class_atom(self):
        """测试类原子"""
        atom = ClassAtom(
            name="TestClass",
            methods=["method1", "method2"]
        )
        assert atom.name == "TestClass"
        assert len(atom.methods) == 2
    
    def test_module_atom(self):
        """测试模块原子"""
        atom = ModuleAtom(
            name="test_module",
            file_path="test.py",
            imports=["os", "sys"]
        )
        assert atom.name == "test_module"
        assert len(atom.imports) == 2
    
    def test_ast_parser(self):
        """测试AST解析器"""
        parser = ASTParser()
        code = """
def test_func():
    x = 1
    return x
"""
        tree = ast.parse(code)
        functions = parser.extract_functions(tree)
        assert len(functions) >= 1
    
    def test_code_fixer(self):
        """测试代码修复器"""
        fixer = CodeFixer()
        entity = CodeEntity(
            entity_type="variable",
            name="TestVar",
            file_path="test.py",
            line_number=1,
            content="TestVar = 1"
        )
        fixed = fixer.fix_variable_naming(entity)
        assert fixed == "testvar"
    
    def test_executor_layer(self):
        """测试执行层"""
        layer = ExecutorLayer()
        result = layer.execute({})
        assert result["status"] == "executed"


class TestLayerArchitecture:
    """测试四层架构集成"""
    
    def test_layer_architecture_init(self):
        """测试架构初始化"""
        arch = LayerArchitecture()
        assert arch.input_layer is not None
        assert arch.scheduler_layer is not None
        assert arch.agent_layer is not None
        assert arch.executor_layer is not None
    
    def test_process_task(self):
        """测试处理任务"""
        arch = LayerArchitecture()
        task_data = {
            "task_id": "task_001",
            "task_type": "requirement"
        }
        result = arch.process_task(task_data)
        assert "status" in result


class TestArchitectureValidator:
    """测试架构验证器"""
    
    def test_validate_dependencies(self):
        """测试依赖验证"""
        validator = ArchitectureValidator()
        result = validator.validate_dependencies()
        assert result["input_to_scheduler"] is True
        assert result["scheduler_to_agents"] is True
        assert result["agents_to_executors"] is True
        assert result["no_circular"] is True
    
    def test_validate_agent_orthogonality(self):
        """测试Agent正交性"""
        validator = ArchitectureValidator()
        result = validator.validate_agent_orthogonality()
        assert result["total_agents"] == 8
        assert result["no_overlap"] is True


class TestLayerMetrics:
    """测试层指标"""
    
    def test_layer_metrics(self):
        """测试层指标"""
        metrics = LayerMetrics(
            layer_name="input_layer",
            components=3,
            capabilities=["task_classification", "task_validation"]
        )
        assert metrics.layer_name == "input_layer"
        assert metrics.components == 3
        assert len(metrics.capabilities) == 2


class TestEightAgents:
    """测试8个Agent"""
    
    def test_all_8_agents_registered(self):
        """测试所有8个Agent都已注册"""
        layer = AgentLayer()
        agents = layer.list_agents()
        assert len(agents) == 8
        
        expected_names = [
            "总控调度", "需求拆解", "架构设计", "开发编码",
            "缺陷排查", "代码评审", "测试验证", "文档归档"
        ]
        for name in expected_names:
            assert name in agents
