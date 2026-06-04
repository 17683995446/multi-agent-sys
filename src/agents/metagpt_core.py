from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field as dc_field

try:
    from pydantic import BaseModel, Field
    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False


class RoleType(str, Enum):
    """工程角色类型"""
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    TESTER = "tester"
    REVIEWER = "reviewer"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


if _HAS_PYDANTIC:
    class Message(BaseModel):
        """消息实体"""
        role: str = ""
        content: str = ""
        timestamp: float = Field(default_factory=lambda: __import__("time").time())
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class Task(BaseModel):
        """任务实体"""
        id: str = ""
        title: str = ""
        description: str = ""
        role: RoleType = RoleType.ENGINEER
        status: TaskStatus = TaskStatus.PENDING
        dependencies: List[str] = Field(default_factory=list)
        output: Optional[str] = None
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class WorkflowTemplate(BaseModel):
        """工作流模板"""
        name: str = ""
        description: str = ""
        tasks: List[Task] = Field(default_factory=list)
        entry_point: str = ""
else:
    @dataclass
    class Message:
        """消息实体"""
        role: str = ""
        content: str = ""
        timestamp: float = dc_field(default_factory=lambda: __import__("time").time())
        metadata: Dict[str, Any] = dc_field(default_factory=dict)

    @dataclass
    class Task:
        """任务实体"""
        id: str = ""
        title: str = ""
        description: str = ""
        role: RoleType = RoleType.ENGINEER
        status: TaskStatus = TaskStatus.PENDING
        dependencies: List[str] = dc_field(default_factory=list)
        output: Optional[str] = None
        metadata: Dict[str, Any] = dc_field(default_factory=dict)

    @dataclass
    class WorkflowTemplate:
        """工作流模板"""
        name: str = ""
        description: str = ""
        tasks: List[Task] = dc_field(default_factory=list)
        entry_point: str = ""


@dataclass
class RoleAction:
    """角色动作"""
    name: str = ""
    description: str = ""
    handler: Callable[[Dict[str, Any]], Any] = None


class BaseRole:
    """基础角色类"""

    def __init__(self, name: str, role_type: RoleType):
        self.name = name
        self.role_type = role_type
        self._actions: Dict[str, RoleAction] = {}
        self._context: Dict[str, Any] = {}
        self._inbox: List[Message] = []
        self._outbox: List[Message] = []

    def register_action(self, action: RoleAction) -> None:
        """注册角色动作"""
        self._actions[action.name] = action

    def execute_action(self, action_name: str, context: Dict[str, Any]) -> Any:
        """执行角色动作"""
        if action_name not in self._actions:
            raise ValueError(f"Action '{action_name}' not found for role {self.role_type}")
        return self._actions[action_name].handler(context)

    def send_message(self, message: Message) -> None:
        """发送消息"""
        self._outbox.append(message)

    def receive_message(self, message: Message) -> None:
        """接收消息"""
        self._inbox.append(message)

    def get_inbox(self) -> List[Message]:
        """获取收件箱"""
        return self._inbox.copy()

    def get_outbox(self) -> List[Message]:
        """获取发件箱"""
        return self._outbox.copy()

    def clear_inbox(self) -> None:
        """清空收件箱"""
        self._inbox.clear()

    def clear_outbox(self) -> None:
        """清空发件箱"""
        self._outbox.clear()

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文"""
        return self._context.get(key, default)


class ProductManager(BaseRole):
    """产品经理角色"""

    def __init__(self, name: str = "ProductManager"):
        super().__init__(name, RoleType.PRODUCT_MANAGER)
        self._register_default_actions()

    def _register_default_actions(self) -> None:
        """注册默认动作"""
        self.register_action(RoleAction(
            name="define_prd",
            description="定义产品需求文档(PRD)",
            handler=self._define_prd
        ))

    def _define_prd(self, context: Dict[str, Any]) -> str:
        """定义PRD"""
        title = context.get("title", "Untitled Project")
        return f"# Product Requirements Document (PRD)\n\n## {title}\n\n{context.get('description', '')}"


class Architect(BaseRole):
    """架构师角色"""

    def __init__(self, name: str = "Architect"):
        super().__init__(name, RoleType.ARCHITECT)
        self._register_default_actions()

    def _register_default_actions(self) -> None:
        """注册默认动作"""
        self.register_action(RoleAction(
            name="design_architecture",
            description="设计系统架构",
            handler=self._design_architecture
        ))
        self.register_action(RoleAction(
            name="define_interfaces",
            description="定义接口规范",
            handler=self._define_interfaces
        ))

    def _design_architecture(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """设计架构"""
        return {
            "layers": ["input", "scheduler", "agents", "executors"],
            "components": context.get("components", []),
            "architecture_style": context.get("style", "layered")
        }

    def _define_interfaces(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """定义接口"""
        return [
            {"name": "API", "type": "REST", "version": "1.0"},
            {"name": "Message", "type": "Async", "version": "1.0"}
        ]


class Engineer(BaseRole):
    """工程师角色"""

    def __init__(self, name: str = "Engineer"):
        super().__init__(name, RoleType.ENGINEER)
        self._register_default_actions()

    def _register_default_actions(self) -> None:
        """注册默认动作"""
        self.register_action(RoleAction(
            name="write_code",
            description="编写代码",
            handler=self._write_code
        ))
        self.register_action(RoleAction(
            name="review_code",
            description="代码审查",
            handler=self._review_code
        ))

    def _write_code(self, context: Dict[str, Any]) -> str:
        """编写代码"""
        task = context.get("task", "unknown")
        return f"# Code for {task}\n\n# Implementation here..."

    def _review_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """审查代码"""
        return {
            "status": "reviewed",
            "issues": [],
            "suggestions": []
        }


class Tester(BaseRole):
    """测试工程师角色"""

    def __init__(self, name: str = "Tester"):
        super().__init__(name, RoleType.TESTER)
        self._register_default_actions()

    def _register_default_actions(self) -> None:
        """注册默认动作"""
        self.register_action(RoleAction(
            name="write_tests",
            description="编写测试用例",
            handler=self._write_tests
        ))
        self.register_action(RoleAction(
            name="execute_tests",
            description="执行测试",
            handler=self._execute_tests
        ))

    def _write_tests(self, context: Dict[str, Any]) -> str:
        """编写测试"""
        return f"# Test Cases\n\n# Test implementation here..."

    def _execute_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试"""
        return {
            "total": 10,
            "passed": 10,
            "failed": 0,
            "coverage": "90%"
        }


class RoleRegistry:
    """角色注册表"""

    def __init__(self):
        self._roles: Dict[RoleType, BaseRole] = {}

    def register(self, role: BaseRole) -> None:
        """注册角色"""
        self._roles[role.role_type] = role

    def get(self, role_type: RoleType) -> Optional[BaseRole]:
        """获取角色"""
        return self._roles.get(role_type)

    def list_roles(self) -> List[RoleType]:
        """列出所有角色"""
        return list(self._roles.keys())


def create_default_registry() -> RoleRegistry:
    """创建默认角色注册表"""
    registry = RoleRegistry()
    registry.register(ProductManager())
    registry.register(Architect())
    registry.register(Engineer())
    registry.register(Tester())
    return registry
