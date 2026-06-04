"""
总控Agent模块

职责：全局协调、任务管理、权限控制、验收确认

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import json
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class AgentStatus(str, Enum):
    """Agent状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class PermissionLevel(str, Enum):
    """权限级别"""
    READ_ONLY = "read_only"
    EXECUTE = "execute"
    MODIFY = "modify"
    ADMIN = "admin"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass
class Permission:
    """权限配置"""
    level: PermissionLevel = PermissionLevel.READ_ONLY
    resources: List[str] = field(default_factory=list)
    can_create: bool = False
    can_modify: bool = False
    can_delete: bool = False
    can_execute: bool = False
    permission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    """任务"""
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 3  # 1=highest, 5=lowest
    assignee: Optional[str] = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    output: Optional[str] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    max_tasks: int = 10
    enable_parallel: bool = True
    permissions: List[Permission] = field(default_factory=list)


@dataclass
class CoordinationState:
    """协调状态"""
    active_agents: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    running_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.permissions: Dict[str, Permission] = {}
    
    def grant_permission(self, agent_id: str, level: PermissionLevel, 
                        resources: Optional[List[str]] = None) -> Permission:
        """授予权限"""
        perm = Permission(
            level=level,
            resources=resources or [],
            can_create=level in [PermissionLevel.MODIFY, PermissionLevel.ADMIN],
            can_modify=level in [PermissionLevel.MODIFY, PermissionLevel.ADMIN],
            can_delete=level in [PermissionLevel.ADMIN],
            can_execute=level in [PermissionLevel.EXECUTE, PermissionLevel.MODIFY, PermissionLevel.ADMIN]
        )
        
        self.permissions[agent_id] = perm
        return perm
    
    def has_permission(self, agent_id: str, action: str, 
                     resource: Optional[str] = None) -> bool:
        """检查权限"""
        if agent_id not in self.permissions:
            return False
        
        perm = self.permissions[agent_id]
        
        if action == "create":
            return perm.can_create
        elif action == "modify":
            return perm.can_modify
        elif action == "delete":
            return perm.can_delete
        elif action == "execute":
            return perm.can_execute
        
        return False
    
    def update_permission(self, agent_id: str, **kwargs) -> Optional[Permission]:
        """动态更新权限"""
        if agent_id not in self.permissions:
            return None
        
        perm = self.permissions[agent_id]
        
        for key, value in kwargs.items():
            if hasattr(perm, key):
                setattr(perm, key, value)
        
        perm.updated_at = datetime.now()
        return perm


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
    
    def create_task(self, name: str, description: str = "", 
                   priority: int = 3) -> Task:
        """创建任务"""
        task = Task(
            name=name,
            description=description,
            priority=priority
        )
        self.tasks[task.task_id] = task
        return task
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        """更新任务状态"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        task.status = status
        
        if status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.now()
        elif status in [TaskStatus.ACCEPTED, TaskStatus.REJECTED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
        
        return task
    
    def accept_task(self, task_id: str, output: Optional[str] = None) -> Optional[Task]:
        """验收通过任务"""
        task = self.update_task_status(task_id, TaskStatus.ACCEPTED)
        if task and output:
            task.output = output
        return task
    
    def reject_task(self, task_id: str, reason: str) -> Optional[Task]:
        """拒绝任务"""
        task = self.update_task_status(task_id, TaskStatus.REJECTED)
        if task:
            task.errors.append(reason)
        return task
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """按状态获取任务"""
        return [t for t in self.tasks.values() if t.status == status]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取任务汇总"""
        return {
            "total": len(self.tasks),
            "pending": len(self.get_tasks_by_status(TaskStatus.PENDING)),
            "in_progress": len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS)),
            "accepted": len(self.get_tasks_by_status(TaskStatus.ACCEPTED)),
            "rejected": len(self.get_tasks_by_status(TaskStatus.REJECTED))
        }


class Coordinator:
    """协调器"""
    
    def __init__(self):
        self.state = CoordinationState()
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
    
    def register_agent(self, agent_id: str, agent_type: str) -> bool:
        """注册Agent"""
        if agent_id not in self.agent_registry:
            self.agent_registry[agent_id] = {
                "type": agent_type,
                "registered_at": datetime.now()
            }
            if agent_id not in self.state.active_agents:
                self.state.active_agents.append(agent_id)
            self.state.last_updated = datetime.now()
            return True
        return False
    
    def assign_task(self, agent_id: str, task_id: str) -> bool:
        """分配任务给Agent"""
        if agent_id not in self.agent_registry:
            return False
        
        if task_id not in self.state.pending_tasks:
            self.state.pending_tasks.append(task_id)
        
        self.state.last_updated = datetime.now()
        return True
    
    def get_state(self) -> CoordinationState:
        """获取协调状态"""
        return self.state


class ControlAgent:
    """总控Agent"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.status = AgentStatus.IDLE
        self.permission_manager = PermissionManager()
        self.task_manager = TaskManager()
        self.coordinator = Coordinator()
        
        # 授予自己Admin权限
        self.permission_manager.grant_permission(
            self.agent_id,
            PermissionLevel.ADMIN
        )
    
    def initialize(self) -> bool:
        """初始化Agent"""
        self.status = AgentStatus.RUNNING
        return True
    
    def shutdown(self) -> bool:
        """关闭Agent"""
        self.status = AgentStatus.COMPLETED
        return True
    
    def create_task(self, name: str, description: str = "") -> Task:
        """创建任务"""
        task = self.task_manager.create_task(name, description)
        self.coordinator.state.pending_tasks.append(task.task_id)
        return task
    
    def accept_task(self, task_id: str) -> Optional[Task]:
        """验收确认任务"""
        task = self.task_manager.accept_task(task_id)
        if task and task_id in self.coordinator.state.running_tasks:
            self.coordinator.state.running_tasks.remove(task_id)
            self.coordinator.state.completed_tasks.append(task_id)
        return task
    
    def grant_permission_to_agent(self, agent_id: str, level: PermissionLevel) -> Permission:
        """授予其他Agent权限"""
        return self.permission_manager.grant_permission(agent_id, level)
    
    def register_subagent(self, agent_id: str, agent_type: str) -> bool:
        """注册子Agent"""
        return self.coordinator.register_agent(agent_id, agent_type)
    
    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务汇总"""
        return self.task_manager.get_summary()
    
    def get_coordination_state(self) -> CoordinationState:
        """获取协调状态"""
        return self.coordinator.state


# 全局总控Agent
_global_control_agent: Optional[ControlAgent] = None


def get_control_agent(config: Optional[AgentConfig] = None) -> ControlAgent:
    """获取全局总控Agent"""
    global _global_control_agent
    if _global_control_agent is None:
        if config is None:
            config = AgentConfig(name="GlobalControlAgent")
        _global_control_agent = ControlAgent(config)
    return _global_control_agent


def reset_control_agent() -> None:
    """重置总控Agent"""
    global _global_control_agent
    _global_control_agent = None
