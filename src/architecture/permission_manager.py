from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable


class ActionType(str, Enum):
    """操作类型"""
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class AccessLevel(str, Enum):
    """访问级别"""
    NONE = "none"
    VIEW = "view"
    EDIT = "edit"
    OWNER = "owner"
    ADMIN = "admin"


@dataclass
class Permission:
    """权限定义"""
    permission_id: str
    resource: str
    action: ActionType
    level: AccessLevel
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "permission_id": self.permission_id,
            "resource": self.resource,
            "action": self.action.value,
            "level": self.level.value,
            "description": self.description,
            "metadata": self.metadata
        }


@dataclass
class Role:
    """角色定义"""
    role_id: str
    name: str
    description: str = ""
    permissions: List[Permission] = field(default_factory=list)
    parent_roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_permission(self, permission: Permission) -> None:
        self.permissions.append(permission)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "permissions": [p.to_dict() for p in self.permissions],
            "parent_roles": self.parent_roles,
            "metadata": self.metadata
        }


@dataclass
class User:
    """用户定义"""
    user_id: str
    username: str
    roles: List[str] = field(default_factory=list)
    direct_permissions: List[Permission] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_role(self, role_id: str) -> None:
        self.roles.append(role_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "roles": self.roles,
            "direct_permissions": [p.to_dict() for p in self.direct_permissions],
            "metadata": self.metadata
        }


@dataclass
class AuditLog:
    """审计日志"""
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    username: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[ActionType] = None
    granted: bool = False
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "username": self.username,
            "resource": self.resource,
            "action": self.action.value if self.action else None,
            "granted": self.granted,
            "reason": self.reason,
            "metadata": self.metadata
        }


class ReadOnlyResource:
    """只读资源封装"""

    def __init__(self, resource_name: str, data: Any, owner: Optional[str] = None):
        self._resource_name = resource_name
        self._data = data
        self._owner = owner
        self._read_only = True
        self._created_at = datetime.now()

    def __getattribute__(self, name: str) -> Any:
        if name.startswith('_') or name in (
            'get', 'is_read_only', 'resource_name', 'created_at', 'owner'
        ):
            return object.__getattribute__(self, name)
        return object.__getattribute__(self, '_data').get(name) if hasattr(self._data, 'get') else getattr(self._data, name, None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            raise PermissionError(f"Resource '{self._resource_name}' is read-only")

    def __delattr__(self, name: str) -> None:
        if not name.startswith('_'):
            raise PermissionError(f"Resource '{self._resource_name}' is read-only")
        object.__delattr__(self, name)

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self._data, 'get'):
            return self._data.get(key, default)
        return getattr(self._data, key, default)

    @property
    def is_read_only(self) -> bool:
        return self._read_only

    @property
    def resource_name(self) -> str:
        return self._resource_name

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def owner(self) -> Optional[str]:
        return self._owner


class PermissionTree:
    """权限树"""

    def __init__(self):
        self._resources: Dict[str, Dict[ActionType, AccessLevel]] = {}
        self._parents: Dict[str, str] = {}

    def add_resource(self, resource: str, parent: Optional[str] = None) -> None:
        if resource not in self._resources:
            self._resources[resource] = {}
        if parent:
            self._parents[resource] = parent

    def set_permission(self, resource: str, action: ActionType, level: AccessLevel) -> None:
        if resource not in self._resources:
            self._resources[resource] = {}
        self._resources[resource][action] = level

    def get_inherited_permission(self, resource: str, action: ActionType) -> Optional[AccessLevel]:
        current = resource
        while current:
            if current in self._resources and action in self._resources[current]:
                return self._resources[current][action]
            if current not in self._parents:
                break
            current = self._parents[current]
        return None

    def get_effective_level(self, resource: str, action: ActionType) -> AccessLevel:
        level = self.get_inherited_permission(resource, action)
        return level if level is not None else AccessLevel.NONE


class AuditLogger:
    """审计记录器"""

    def __init__(self):
        self._logs: List[AuditLog] = []
        self._lock = threading.Lock()

    def log_access(
        self,
        user: Optional[User],
        resource: str,
        action: ActionType,
        granted: bool,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        log = AuditLog(
            user_id=user.user_id if user else None,
            username=user.username if user else None,
            resource=resource,
            action=action,
            granted=granted,
            reason=reason,
            metadata=metadata or {}
        )
        with self._lock:
            self._logs.append(log)
        return log

    def get_logs(
        self,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[ActionType] = None,
        granted: Optional[bool] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        with self._lock:
            filtered = [log for log in reversed(self._logs)]
            if user_id:
                filtered = [log for log in filtered if log.user_id == user_id]
            if resource:
                filtered = [log for log in filtered if log.resource == resource]
            if action:
                filtered = [log for log in filtered if log.action == action]
            if granted is not None:
                filtered = [log for log in filtered if log.granted == granted]
            return filtered[:limit]


class RoleBasedAccessControl:
    """基于角色的访问控制（RBAC）"""

    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._users: Dict[str, User] = {}
        self._permission_tree = PermissionTree()
        self._audit_logger = AuditLogger()

    def create_role(
        self,
        role_id: str,
        name: str,
        description: str = "",
        parent_roles: Optional[List[str]] = None
    ) -> Role:
        role = Role(
            role_id=role_id,
            name=name,
            description=description,
            parent_roles=parent_roles or []
        )
        self._roles[role_id] = role
        return role

    def get_role(self, role_id: str) -> Optional[Role]:
        return self._roles.get(role_id)

    def create_user(self, user_id: str, username: str, roles: Optional[List[str]] = None) -> User:
        user = User(user_id=user_id, username=username, roles=roles or [])
        self._users[user_id] = user
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        user = self._users.get(user_id)
        if not user or role_id not in self._roles:
            return False
        user.add_role(role_id)
        return True

    def add_permission_to_role(self, role_id: str, permission: Permission) -> bool:
        role = self._roles.get(role_id)
        if not role:
            return False
        role.add_permission(permission)
        return True

    def get_all_user_permissions(self, user_id: str) -> List[Permission]:
        user = self._users.get(user_id)
        if not user:
            return []
        
        all_perms: List[Permission] = list(user.direct_permissions)
        visited = set()
        queue = list(user.roles)
        
        while queue:
            role_id = queue.pop(0)
            if role_id in visited:
                continue
            visited.add(role_id)
            
            role = self._roles.get(role_id)
            if role:
                all_perms.extend(role.permissions)
                queue.extend(role.parent_roles)
        
        return all_perms

    def check_permission(
        self,
        user: Optional[User],
        resource: str,
        action: ActionType
    ) -> bool:
        if not user:
            self._audit_logger.log_access(
                user, resource, action, False, "No user provided"
            )
            return False
        
        perms = self.get_all_user_permissions(user.user_id)
        
        for perm in perms:
            if perm.resource == resource and perm.action == action:
                if perm.level != AccessLevel.NONE:
                    self._audit_logger.log_access(
                        user, resource, action, True, "Permission granted"
                    )
                    return True
        
        tree_level = self._permission_tree.get_effective_level(resource, action)
        if tree_level != AccessLevel.NONE:
            self._audit_logger.log_access(
                user, resource, action, True, "Resource-level permission granted"
            )
            return True
        
        self._audit_logger.log_access(
            user, resource, action, False, "No matching permission"
        )
        return False

    def wrap_read_only(self, resource_name: str, data: Any, owner: Optional[str] = None) -> ReadOnlyResource:
        return ReadOnlyResource(resource_name, data, owner)

    def get_audit_logger(self) -> AuditLogger:
        return self._audit_logger

    def get_permission_tree(self) -> PermissionTree:
        return self._permission_tree


_global_rbac: Optional[RoleBasedAccessControl] = None


def get_rbac() -> RoleBasedAccessControl:
    global _global_rbac
    if _global_rbac is None:
        _global_rbac = RoleBasedAccessControl()
    return _global_rbac


def reset_rbac() -> None:
    global _global_rbac
    _global_rbac = None
