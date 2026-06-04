"""
智能协作层 (Agents Layer)

职责：多角色Agent交互、任务分发、协商会诊

依赖关系：
- 被依赖：scheduler (调度层)
- 依赖：executors (执行层)

8大Agent角色体系（正交分工）：
1. 总控调度Agent - 任务收口、优先级管控、全局协调
2. 需求拆解Agent - 需求转技术任务、层级拆分
3. 架构设计Agent - 模块边界划分、依赖梳理
4. 开发编码Agent - 原子化编码、代码重构
5. 缺陷排查Agent - 报错根因定位、修复方案
6. 代码评审Agent - 四级原子合规校验
7. 测试验证Agent - 用例生成、回归测试
8. 文档归档Agent - 资料同步、变更记录

第一性原理：
- 职责正交：Agent职责无重叠、无空缺
- 状态分离：业务状态与Agent状态隔离
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field as dc_field
from datetime import datetime

try:
    from pydantic import BaseModel, Field
    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False


if _HAS_PYDANTIC:
    class AgentConfig(BaseModel):
        """Agent配置"""
        agent_id: str = ""
        agent_type: str = ""
        name: str = ""
        capabilities: List[str] = Field(default_factory=list)
        permissions: List[str] = Field(default_factory=list)
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class AgentMessage(BaseModel):
        """Agent消息"""
        sender: str = ""
        receiver: str = ""
        content: Any = None
        timestamp: datetime = Field(default_factory=datetime.now)
        message_type: str = "request"
else:
    @dataclass
    class AgentConfig:
        """Agent配置"""
        agent_id: str = ""
        agent_type: str = ""
        name: str = ""
        capabilities: List[str] = dc_field(default_factory=list)
        permissions: List[str] = dc_field(default_factory=list)
        metadata: Dict[str, Any] = dc_field(default_factory=dict)

    @dataclass
    class AgentMessage:
        """Agent消息"""
        sender: str = ""
        receiver: str = ""
        content: Any = None
        timestamp: datetime = dc_field(default_factory=datetime.now)
        message_type: str = "request"


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.state: Dict[str, Any] = {}

    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """处理输入"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取能力列表"""
        pass


class AdminAgent(BaseAgent):
    """总控调度Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, input_data: Any) -> Any:
        """处理全局协调"""
        return {"status": "coordinated", "agent": self.config.name}

    def get_capabilities(self) -> List[str]:
        return ["task_coordination", "priority_management", "global_oversight"]


class RequirementAgent(BaseAgent):
    """需求拆解Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, input_data: Any) -> Any:
        """处理需求拆解"""
        return {"status": "decomposed", "agent": self.config.name}

    def get_capabilities(self) -> List[str]:
        return ["requirement_analysis", "task_decomposition", "impact_analysis"]


class ArchitectureAgent(BaseAgent):
    """架构设计Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, input_data: Any) -> Any:
        """处理架构设计"""
        return {"status": "architected", "agent": self.config.name}

    def get_capabilities(self) -> List[str]:
        return ["architecture_design", "dependency_analysis", "boundary_locking"]


class DeveloperAgent(BaseAgent):
    """开发编码Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, input_data: Any) -> Any:
        """处理开发任务"""
        return {"status": "developed", "agent": self.config.name}

    def get_capabilities(self) -> List[str]:
        return ["code_generation", "code_modification", "refactoring"]


class DebugAgent(BaseAgent):
    """缺陷排查Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, input_data: Any) -> Any:
        """处理缺陷排查"""
        return {"status": "debugged", "agent": self.config.name}

    def get_capabilities(self) -> List[str]:
        return ["log_parsing", "stack_trace_analysis", "root_cause_locating"]


class ReviewAgent(BaseAgent):
    """代码评审Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, input_data: Any) -> Any:
        """处理代码评审"""
        return {"status": "reviewed", "agent": self.config.name}

    def get_capabilities(self) -> List[str]:
        return ["code_review", "standard_checking", "compliance_validation"]


class TestAgent(BaseAgent):
    """测试验证Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, input_data: Any) -> Any:
        """处理测试任务"""
        return {"status": "tested", "agent": self.config.name}

    def get_capabilities(self) -> List[str]:
        return ["test_generation", "regression_testing", "test_automation"]


class DocumentAgent(BaseAgent):
    """文档归档Agent"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def process(self, input_data: Any) -> Any:
        """处理文档任务"""
        return {"status": "documented", "agent": self.config.name}

    def get_capabilities(self) -> List[str]:
        return ["documentation", "archiving", "change_tracking"]


class AgentRegistry:
    """Agent注册中心"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """注册Agent"""
        self.agents[agent.config.agent_id] = agent

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """获取Agent"""
        return self.agents.get(agent_id)

    def get_by_type(self, agent_type: str) -> List[BaseAgent]:
        """按类型获取Agent"""
        return [
            agent for agent in self.agents.values()
            if agent.config.agent_type == agent_type
        ]

    def list_all(self) -> List[AgentConfig]:
        """列出所有Agent配置"""
        return [agent.config for agent in self.agents.values()]


# AutoGen相关模块 - 安全导入
try:
    from .autogen_core import (
        AgentMessage as AutoGenAgentMessage,
        MessageRole,
        MessageQueue,
        get_global_queue
    )
    from .autogen_session import (
        BaseAutoGenAgent,
        SimpleAutoGenAgent,
        AgentConversation
    )
    _HAS_AUTOGEN = True
except (ImportError, Exception):
    _HAS_AUTOGEN = False
    AutoGenAgentMessage = None
    MessageRole = None
    MessageQueue = None
    get_global_queue = None
    BaseAutoGenAgent = None
    SimpleAutoGenAgent = None
    AgentConversation = None

__all__ = [
    # 基础Agent
    "AgentConfig",
    "AgentMessage",
    "BaseAgent",
    "AdminAgent",
    "RequirementAgent",
    "ArchitectureAgent",
    "DeveloperAgent",
    "DebugAgent",
    "ReviewAgent",
    "TestAgent",
    "DocumentAgent",
    "AgentRegistry",

    # AutoGen核心
    "AutoGenAgentMessage",
    "MessageRole",
    "MessageQueue",
    "get_global_queue",

    # AutoGen会话
    "BaseAutoGenAgent",
    "SimpleAutoGenAgent",
    "AgentConversation"
]
