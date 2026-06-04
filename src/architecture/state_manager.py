from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import threading
import uuid

from src.core import get_logger


logger = get_logger("state_manager")


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStateMachine:
    """任务状态机"""

    VALID_TRANSITIONS = {
        TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
        TaskStatus.RUNNING: {TaskStatus.WAITING, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.WAITING: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
        TaskStatus.COMPLETED: set(),
        TaskStatus.FAILED: {TaskStatus.PENDING, TaskStatus.CANCELLED},
        TaskStatus.CANCELLED: {TaskStatus.PENDING}
    }

    @classmethod
    def can_transition(cls, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """检查状态转换是否合法"""
        return to_status in cls.VALID_TRANSITIONS.get(from_status, set())


@dataclass
class TaskState:
    """任务状态"""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def transition_to(self, new_status: TaskStatus) -> bool:
        """状态转换"""
        if TaskStateMachine.can_transition(self.status, new_status):
            self.status = new_status
            self.updated_at = datetime.now()
            logger.debug(f"任务 {self.task_id} 状态从 {self.status} 转换为 {new_status}")
            return True
        logger.warning(f"任务 {self.task_id} 状态转换失败: {self.status} -> {new_status}")
        return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "priority": self.priority,
            "metadata": self.metadata,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


@dataclass
class BusinessState:
    """业务状态"""
    business_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    version: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: Set[str] = field(default_factory=set)
    locked: bool = False
    lock_holder: Optional[str] = None

    def update(self, key: str, value: Any) -> None:
        """更新业务数据"""
        if self.locked:
            raise ValueError(f"业务状态 {self.business_id} 已被锁定")
        self.data[key] = value
        self.version += 1
        self.updated_at = datetime.now()
        logger.debug(f"业务状态 {self.business_id} 更新: {key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取业务数据"""
        return self.data.get(key, default)

    def lock(self, holder: str) -> bool:
        """锁定业务状态"""
        if not self.locked:
            self.locked = True
            self.lock_holder = holder
            return True
        return False

    def unlock(self, holder: str) -> bool:
        """解锁业务状态"""
        if self.locked and self.lock_holder == holder:
            self.locked = False
            self.lock_holder = None
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "business_id": self.business_id,
            "data": self.data,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": list(self.tags),
            "locked": self.locked,
            "lock_holder": self.lock_holder
        }


@dataclass
class SystemState:
    """系统状态"""
    healthy: bool = True
    start_time: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    components: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def record_metric(self, name: str, value: int) -> None:
        """记录指标"""
        self.metrics[name] = value
        logger.debug(f"系统指标记录: {name} = {value}")

    def add_warning(self, message: str) -> None:
        """添加警告"""
        self.warnings.append(message)
        logger.warning(f"系统警告: {message}")

    def add_error(self, message: str) -> None:
        """添加错误"""
        self.errors.append(message)
        self.healthy = False
        logger.error(f"系统错误: {message}")

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "healthy": self.healthy,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "version": self.version,
            "metrics": self.metrics,
            "warning_count": len(self.warnings),
            "error_count": len(self.errors),
            "components": self.components
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "healthy": self.healthy,
            "start_time": self.start_time.isoformat(),
            "version": self.version,
            "components": self.components,
            "metrics": self.metrics,
            "warnings": self.warnings,
            "errors": self.errors
        }


class StateNamespace:
    """状态命名空间"""

    def __init__(self, name: str):
        self.name = name
        self.task_states: Dict[str, TaskState] = {}
        self.business_states: Dict[str, BusinessState] = {}
        self.system_state: Optional[SystemState] = None
        self.logger = get_logger(f"namespace.{name}")

    def create_task(self, task_id: Optional[str] = None, priority: int = 0) -> TaskState:
        """创建任务状态"""
        task_id = task_id or str(uuid.uuid4())
        if task_id in self.task_states:
            raise ValueError(f"任务 {task_id} 已存在")
        task = TaskState(task_id=task_id, priority=priority)
        self.task_states[task_id] = task
        self.logger.debug(f"创建任务状态: {task_id}")
        return task

    def get_task(self, task_id: str) -> Optional[TaskState]:
        """获取任务状态"""
        return self.task_states.get(task_id)

    def create_business(self, business_id: str, initial_data: Optional[Dict[str, Any]] = None) -> BusinessState:
        """创建业务状态"""
        if business_id in self.business_states:
            raise ValueError(f"业务状态 {business_id} 已存在")
        business = BusinessState(
            business_id=business_id,
            data=initial_data or {}
        )
        self.business_states[business_id] = business
        self.logger.debug(f"创建业务状态: {business_id}")
        return business

    def get_business(self, business_id: str) -> Optional[BusinessState]:
        """获取业务状态"""
        return self.business_states.get(business_id)

    def init_system(self) -> SystemState:
        """初始化系统状态"""
        if self.system_state is None:
            self.system_state = SystemState()
            self.logger.debug("初始化系统状态")
        return self.system_state

    def get_system(self) -> Optional[SystemState]:
        """获取系统状态"""
        return self.system_state


class StateManager:
    """统一状态管理器"""

    def __init__(self):
        self.namespaces: Dict[str, StateNamespace] = {}
        self.default_namespace: Optional[StateNamespace] = None
        self._lock = threading.RLock()
        self.logger = get_logger("state_manager")

    def create_namespace(self, name: str) -> StateNamespace:
        """创建命名空间"""
        with self._lock:
            if name in self.namespaces:
                raise ValueError(f"命名空间 {name} 已存在")
            namespace = StateNamespace(name)
            self.namespaces[name] = namespace
            if self.default_namespace is None:
                self.default_namespace = namespace
            self.logger.info(f"创建状态命名空间: {name}")
            return namespace

    def get_namespace(self, name: str) -> Optional[StateNamespace]:
        """获取命名空间"""
        return self.namespaces.get(name)

    def get_or_create_namespace(self, name: str) -> StateNamespace:
        """获取或创建命名空间"""
        with self._lock:
            if name not in self.namespaces:
                return self.create_namespace(name)
            return self.namespaces[name]

    def get_default_namespace(self) -> StateNamespace:
        """获取默认命名空间"""
        if self.default_namespace is None:
            self.default_namespace = self.create_namespace("default")
        return self.default_namespace

    def list_namespaces(self) -> List[str]:
        """列出所有命名空间"""
        return list(self.namespaces.keys())

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """所有命名空间的健康检查"""
        results = {}
        for name, namespace in self.namespaces.items():
            system_state = namespace.get_system()
            if system_state:
                results[name] = system_state.health_check()
            else:
                results[name] = {"healthy": True, "status": "not_initialized"}
        return results


_global_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """获取全局状态管理器"""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = StateManager()
    return _global_state_manager


def reset_state_manager() -> None:
    """重置全局状态管理器"""
    global _global_state_manager
    _global_state_manager = None
