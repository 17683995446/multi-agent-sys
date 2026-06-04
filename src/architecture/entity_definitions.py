from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(str, Enum):
    """任务类型"""
    CODE_GENERATION = "code_generation"
    CODE_MODIFICATION = "code_modification"
    CODE_REVIEW = "code_review"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"


class CodeEntityType(str, Enum):
    """代码实体类型"""
    VARIABLE = "variable"
    METHOD = "method"
    CLASS = "class"
    MODULE = "module"
    FUNCTION = "function"
    PROPERTY = "property"
    CONSTANT = "constant"


class MessageType(str, Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class StateType(str, Enum):
    """状态类型"""
    INITIAL = "initial"
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskEntity:
    """任务实体 - 完整Schema定义"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.CODE_GENERATION
    priority: TaskPriority = TaskPriority.NORMAL
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    parent_task_id: Optional[str] = None
    child_task_ids: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assigned_to": self.assigned_to,
            "created_by": self.created_by,
            "parent_task_id": self.parent_task_id,
            "child_task_ids": self.child_task_ids,
            "dependencies": self.dependencies,
            "tags": list(self.tags),
            "metadata": self.metadata,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskEntity:
        """从字典创建"""
        task = cls()
        task.task_id = data.get("task_id", str(uuid.uuid4()))
        task.name = data.get("name", "")
        task.description = data.get("description", "")
        task.task_type = TaskType(data.get("task_type", "code_generation"))
        task.priority = TaskPriority(data.get("priority", "normal"))
        task.status = data.get("status", "pending")
        task.created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        task.updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        task.tags = set(data.get("tags", []))
        task.metadata = data.get("metadata", {})
        task.input_data = data.get("input_data", {})
        task.output_data = data.get("output_data", {})
        return task


@dataclass
class VariableEntity:
    """变量实体 - 原子级代码实体"""
    name: str
    entity_type: str = "variable"
    data_type: str = "Any"
    scope: str = "local"
    is_mutable: bool = True
    is_static: bool = False
    is_final: bool = False
    initial_value: Optional[Any] = None
    line_number: int = 0
    column_number: int = 0
    file_path: str = ""
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "data_type": self.data_type,
            "scope": self.scope,
            "is_mutable": self.is_mutable,
            "is_static": self.is_static,
            "is_final": self.is_final,
            "initial_value": str(self.initial_value) if self.initial_value is not None else None,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "file_path": self.file_path,
            "docstring": self.docstring,
            "metadata": self.metadata
        }


@dataclass
class MethodEntity:
    """方法实体 - 原子级代码实体"""
    name: str
    entity_type: str = "method"
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: str = "None"
    is_async: bool = False
    is_static: bool = False
    is_abstract: bool = False
    visibility: str = "public"
    line_number: int = 0
    end_line_number: int = 0
    file_path: str = ""
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    local_variables: List[VariableEntity] = field(default_factory=list)
    complexity: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "is_async": self.is_async,
            "is_static": self.is_static,
            "is_abstract": self.is_abstract,
            "visibility": self.visibility,
            "line_number": self.line_number,
            "end_line_number": self.end_line_number,
            "file_path": self.file_path,
            "docstring": self.docstring,
            "decorators": self.decorators,
            "local_variables": [v.to_dict() for v in self.local_variables],
            "complexity": self.complexity,
            "metadata": self.metadata
        }


@dataclass
class ClassEntity:
    """类实体 - 原子级代码实体"""
    name: str
    entity_type: str = "class"
    bases: List[str] = field(default_factory=list)
    methods: List[MethodEntity] = field(default_factory=list)
    attributes: List[VariableEntity] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    line_number: int = 0
    end_line_number: int = 0
    file_path: str = ""
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_final: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "bases": self.bases,
            "methods": [m.to_dict() for m in self.methods],
            "attributes": [a.to_dict() for a in self.attributes],
            "properties": self.properties,
            "line_number": self.line_number,
            "end_line_number": self.end_line_number,
            "file_path": self.file_path,
            "docstring": self.docstring,
            "decorators": self.decorators,
            "is_abstract": self.is_abstract,
            "is_final": self.is_final,
            "metadata": self.metadata
        }


@dataclass
class ModuleEntity:
    """模块实体 - 文件级代码实体"""
    name: str
    entity_type: str = "module"
    file_path: str = ""
    classes: List[ClassEntity] = field(default_factory=list)
    functions: List[MethodEntity] = field(default_factory=list)
    global_variables: List[VariableEntity] = field(default_factory=list)
    imports: List[Dict[str, str]] = field(default_factory=list)
    docstring: Optional[str] = None
    line_count: int = 0
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "file_path": self.file_path,
            "classes": [c.to_dict() for c in self.classes],
            "functions": [f.to_dict() for f in self.functions],
            "global_variables": [v.to_dict() for v in self.global_variables],
            "imports": self.imports,
            "docstring": self.docstring,
            "line_count": self.line_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "metadata": self.metadata
        }


@dataclass
class CodeEntity:
    """统一代码实体 - 支持四级原子化"""
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: CodeEntityType = CodeEntityType.VARIABLE
    name: str = ""
    file_path: str = ""
    line_number: int = 0
    
    variable: Optional[VariableEntity] = None
    method: Optional[MethodEntity] = None
    class_entity: Optional[ClassEntity] = None
    module: Optional[ModuleEntity] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
        
        if self.variable:
            data["variable"] = self.variable.to_dict()
        if self.method:
            data["method"] = self.method.to_dict()
        if self.class_entity:
            data["class_entity"] = self.class_entity.to_dict()
        if self.module:
            data["module"] = self.module.to_dict()
            
        return data


@dataclass
class MessageEntity:
    """消息实体 - 完整协议定义"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    sender: str = ""
    receiver: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    status: str = "pending"
    error: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "headers": self.headers,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata
        }

    @classmethod
    def create_request(cls, sender: str, receiver: str, content: str, payload: Optional[Dict] = None) -> MessageEntity:
        """创建请求消息"""
        return cls(
            message_type=MessageType.REQUEST,
            sender=sender,
            receiver=receiver,
            content=content,
            payload=payload or {}
        )

    @classmethod
    def create_response(cls, sender: str, receiver: str, content: str, correlation_id: str) -> MessageEntity:
        """创建响应消息"""
        return cls(
            message_type=MessageType.RESPONSE,
            sender=sender,
            receiver=receiver,
            content=content,
            correlation_id=correlation_id
        )

    @classmethod
    def create_notification(cls, sender: str, receivers: List[str], content: str) -> MessageEntity:
        """创建通知消息"""
        return cls(
            message_type=MessageType.NOTIFICATION,
            sender=sender,
            receiver=",".join(receivers),
            content=content
        )


@dataclass
class StateEntity:
    """状态实体 - 完整状态机定义"""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state_type: StateType = StateType.INITIAL
    name: str = ""
    description: str = ""
    
    is_active: bool = False
    is_terminal: bool = False
    
    entered_at: Optional[datetime] = None
    exited_at: Optional[datetime] = None
    duration: Optional[int] = None
    
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "state_id": self.state_id,
            "state_type": self.state_type.value,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "is_terminal": self.is_terminal,
            "entered_at": self.entered_at.isoformat() if self.entered_at else None,
            "exited_at": self.exited_at.isoformat() if self.exited_at else None,
            "duration": self.duration,
            "transitions": self.transitions,
            "data": self.data,
            "context": self.context,
            "metadata": self.metadata
        }

    def add_transition(self, to_state: str, event: str, condition: Optional[str] = None) -> None:
        """添加状态转换"""
        self.transitions.append({
            "to_state": to_state,
            "event": event,
            "condition": condition
        })


class StateMachine:
    """状态机"""

    def __init__(self, name: str):
        self.name = name
        self.states: Dict[str, StateEntity] = {}
        self.current_state: Optional[StateEntity] = None
        self.history: List[StateEntity] = []

    def add_state(self, state: StateEntity) -> None:
        """添加状态"""
        self.states[state.name] = state

    def set_initial_state(self, state_name: str) -> bool:
        """设置初始状态"""
        if state_name in self.states:
            self.current_state = self.states[state_name]
            self.current_state.is_active = True
            self.current_state.entered_at = datetime.now()
            return True
        return False

    def transition(self, event: str) -> bool:
        """状态转换"""
        if not self.current_state:
            return False

        for transition in self.current_state.transitions:
            if transition["event"] == event:
                target_state = transition["to_state"]
                if target_state in self.states:
                    self.current_state.is_active = False
                    self.current_state.exited_at = datetime.now()
                    if self.current_state.entered_at:
                        self.current_state.duration = int(
                            (self.current_state.exited_at - self.current_state.entered_at).total_seconds()
                        )
                    
                    self.history.append(self.current_state)
                    self.current_state = self.states[target_state]
                    self.current_state.is_active = True
                    self.current_state.entered_at = datetime.now()
                    return True

        return False

    def get_current_state(self) -> Optional[StateEntity]:
        """获取当前状态"""
        return self.current_state

    def get_history(self) -> List[StateEntity]:
        """获取状态历史"""
        return self.history


class EntityRegistry:
    """实体注册中心"""

    def __init__(self):
        self.tasks: Dict[str, TaskEntity] = {}
        self.code_entities: Dict[str, CodeEntity] = {}
        self.messages: Dict[str, MessageEntity] = {}
        self.states: Dict[str, StateEntity] = {}

    def register_task(self, task: TaskEntity) -> None:
        """注册任务"""
        self.tasks[task.task_id] = task

    def get_task(self, task_id: str) -> Optional[TaskEntity]:
        """获取任务"""
        return self.tasks.get(task_id)

    def register_code_entity(self, entity: CodeEntity) -> None:
        """注册代码实体"""
        self.code_entities[entity.entity_id] = entity

    def get_code_entity(self, entity_id: str) -> Optional[CodeEntity]:
        """获取代码实体"""
        return self.code_entities.get(entity_id)

    def register_message(self, message: MessageEntity) -> None:
        """注册消息"""
        self.messages[message.message_id] = message

    def get_message(self, message_id: str) -> Optional[MessageEntity]:
        """获取消息"""
        return self.messages.get(message_id)

    def register_state(self, state: StateEntity) -> None:
        """注册状态"""
        self.states[state.state_id] = state

    def get_state(self, state_id: str) -> Optional[StateEntity]:
        """获取状态"""
        return self.states.get(state_id)


_global_registry: Optional[EntityRegistry] = None


def get_entity_registry() -> EntityRegistry:
    """获取全局实体注册中心"""
    global _global_registry
    if _global_registry is None:
        _global_registry = EntityRegistry()
    return _global_registry


def reset_entity_registry() -> None:
    """重置全局实体注册中心"""
    global _global_registry
    _global_registry = None
