"""
调度中枢层 (Scheduler Layer)

职责：流程流转、状态管控、分支回退、全局调度

依赖关系：
- 被依赖：input_layer (输入层)
- 依赖：agents (Agent层)

第一性原理：
- 依赖单向性：调度流程单向无环
- 状态分离：任务状态、业务状态、系统状态隔离
"""

from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskState(BaseModel):
    """任务状态模型"""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SchedulerNode:
    """调度节点"""
    name: str
    handler: Callable
    next_nodes: List[str] = []
    condition: Optional[Callable] = None

    def __init__(self, name: str, handler: Callable):
        self.name = name
        self.handler = handler
        self.next_nodes = []

    def add_next(self, node_name: str):
        """添加下一节点"""
        self.next_nodes.append(node_name)

    def set_condition(self, condition: Callable):
        """设置条件"""
        self.condition = condition


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.nodes: Dict[str, SchedulerNode] = {}
        self.current_node: Optional[str] = None

    def add_node(self, node: SchedulerNode):
        """添加调度节点"""
        self.nodes[node.name] = node

    def execute(self, task_id: str) -> Any:
        """执行调度"""
        if self.current_node and self.current_node in self.nodes:
            node = self.nodes[self.current_node]
            return node.handler(task_id)
        return None

    def get_next_node(self, current: str) -> Optional[str]:
        """获取下一节点"""
        if current in self.nodes:
            node = self.nodes[current]
            if node.next_nodes:
                if node.condition:
                    for next_node in node.next_nodes:
                        if node.condition(next_node):
                            return next_node
                    return node.next_nodes[0]
                return node.next_nodes[0]
        return None


# 导入LangGraph相关模块
from .langgraph_core import (
    WorkflowState,
    TaskStateEnum,
    initialize_task_decomposition,
    generate_architecture_design,
    code_development,
    code_review,
    code_testing,
    finalize_task
)

from .workflows import (
    create_engineering_workflow,
    create_review_feedback_workflow,
    execute_workflow_simple,
    get_workflow_stream
)

__all__ = [
    # 原始任务调度
    "TaskStatus",
    "TaskState",
    "SchedulerNode",
    "TaskScheduler",

    # LangGraph核心
    "WorkflowState",
    "TaskStateEnum",
    "initialize_task_decomposition",
    "generate_architecture_design",
    "code_development",
    "code_review",
    "code_testing",
    "finalize_task",

    # LangGraph工作流
    "create_engineering_workflow",
    "create_review_feedback_workflow",
    "execute_workflow_simple",
    "get_workflow_stream"
]
