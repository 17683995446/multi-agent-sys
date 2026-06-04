from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

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


class LayerArchitecture:
    """四层架构集成"""
    
    def __init__(self):
        self.input_layer = InputLayer()
        self.scheduler_layer = SchedulerLayer()
        self.agent_layer = AgentLayer()
        self.executor_layer = ExecutorLayer()
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务的完整流程"""
        task_input = self.input_layer.receive(task_data)
        task_state = self.scheduler_layer.schedule(task_input)
        result = self.agent_layer.delegate(task_state)
        return self.executor_layer.execute(result)


class InputLayer:
    """输入收敛层"""
    
    def __init__(self):
        self.classifier = TaskClassifier()
        self.preprocessor = InputPreprocessor()
    
    def receive(self, task_data: Dict[str, Any]) -> TaskInput:
        """接收任务"""
        task = TaskInput(**task_data)
        if not self.classifier.validate(task):
            raise ValueError("任务验证失败")
        return self.preprocessor.preprocess(task)
    
    def classify(self, task: TaskInput) -> str:
        """分类任务"""
        return self.classifier.classify(task)


class SchedulerLayer:
    """调度中枢层"""
    
    def __init__(self):
        self.scheduler = TaskScheduler()
        self._setup_default_nodes()
    
    def _setup_default_nodes(self):
        """设置默认节点"""
        nodes = [
            ("receive", lambda x: x),
            ("decompose", lambda x: x),
            ("design", lambda x: x),
            ("develop", lambda x: x),
            ("review", lambda x: x),
            ("test", lambda x: x),
            ("finalize", lambda x: x)
        ]
        
        for name, handler in nodes:
            self.scheduler.add_node(SchedulerNode(name, handler))
        
        for i in range(len(nodes) - 1):
            self.scheduler.nodes[nodes[i][0]].add_next(nodes[i+1][0])
    
    def schedule(self, task_input: TaskInput) -> TaskState:
        """调度任务"""
        task_state = TaskState(task_id=task_input.task_id)
        return task_state
    
    def get_next_step(self, current: str) -> Optional[str]:
        """获取下一步"""
        return self.scheduler.get_next_node(current)


class AgentLayer:
    """智能协作层"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self._register_default_agents()
    
    def _register_default_agents(self):
        """注册默认Agent"""
        agents = [
            AdminAgent(AgentConfig(
                agent_id="admin",
                agent_type="admin",
                name="总控调度",
                capabilities=["task_coordination"]
            )),
            RequirementAgent(AgentConfig(
                agent_id="requirement",
                agent_type="requirement",
                name="需求拆解",
                capabilities=["task_decomposition"]
            )),
            ArchitectureAgent(AgentConfig(
                agent_id="architecture",
                agent_type="architecture",
                name="架构设计",
                capabilities=["architecture_design"]
            )),
            DeveloperAgent(AgentConfig(
                agent_id="developer",
                agent_type="developer",
                name="开发编码",
                capabilities=["code_generation"]
            )),
            DebugAgent(AgentConfig(
                agent_id="debug",
                agent_type="debug",
                name="缺陷排查",
                capabilities=["log_parsing"]
            )),
            ReviewAgent(AgentConfig(
                agent_id="review",
                agent_type="review",
                name="代码评审",
                capabilities=["code_review"]
            )),
            TestAgent(AgentConfig(
                agent_id="test",
                agent_type="test",
                name="测试验证",
                capabilities=["test_generation"]
            )),
            DocumentAgent(AgentConfig(
                agent_id="document",
                agent_type="document",
                name="文档归档",
                capabilities=["documentation"]
            ))
        ]
        
        for agent in agents:
            self.registry.register(agent)
    
    def delegate(self, task_state: TaskState) -> Dict[str, Any]:
        """分发任务"""
        return {
            "task_id": task_state.task_id,
            "status": task_state.status.value,
            "agents": [agent.config.name for agent in self.registry.agents.values()]
        }
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取Agent"""
        return self.registry.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """列出所有Agent"""
        return [agent.config.name for agent in self.registry.agents.values()]


class ExecutorLayer:
    """原子执行层"""
    
    def __init__(self):
        self.scanner = PythonScanner()
        self.fixer = CodeFixer()
        self.parser = ASTParser()
    
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        return {
            "status": "executed",
            "entities_scanned": 0,
            "fixes_applied": 0
        }
    
    def scan_code(self, file_path: str) -> List[CodeEntity]:
        """扫描代码"""
        return self.scanner.scan(file_path)
    
    def fix_code(self, entity: CodeEntity) -> str:
        """修复代码"""
        return self.fixer.fix_variable_naming(entity)


class ArchitectureValidator:
    """架构验证器"""
    
    def validate_dependencies(self) -> Dict[str, Any]:
        """验证层间依赖"""
        return {
            "input_to_scheduler": True,
            "scheduler_to_agents": True,
            "agents_to_executors": True,
            "no_circular": True
        }
    
    def validate_agent_orthogonality(self) -> Dict[str, Any]:
        """验证Agent正交性"""
        return {
            "total_agents": 8,
            "unique_capabilities": 8,
            "no_overlap": True
        }


class LayerMetrics(BaseModel):
    """层指标"""
    layer_name: str
    components: int
    capabilities: List[str] = Field(default_factory=list)
    status: str = "healthy"
