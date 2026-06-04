"""
Agent身份、能力、权限注册体系
职责：身份注册、能力注册、权限注册、注册验证
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable


class AgentType(str, Enum):
    """Agent类型"""
    CONTROL = "control"
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    DEVELOPMENT = "development"
    REVIEW = "review"
    DEBUG = "debug"
    TEST = "test"
    DOC = "doc"


class PermissionLevel(str, Enum):
    """权限级别"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class CapabilityType(str, Enum):
    """能力类型"""
    ANALYSIS = "analysis"
    GENERATION = "generation"
    VALIDATION = "validation"
    SYNCHRONIZATION = "synchronization"
    COORDINATION = "coordination"


@dataclass
class AgentIdentity:
    """Agent身份"""
    agent_type: AgentType
    identity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0.0"
    status: str = "inactive"
    created_at: datetime = field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None


@dataclass
class Capability:
    """能力定义"""
    capability_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    capability_type: CapabilityType = CapabilityType.ANALYSIS
    handler: Optional[Callable] = None
    version: str = "1.0.0"


@dataclass
class Permission:
    """权限定义"""
    permission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    level: PermissionLevel = PermissionLevel.READ
    resource: str = ""
    allowed: bool = True


@dataclass
class PermissionNode:
    """权限树节点"""
    permission: Permission
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    children: List["PermissionNode"] = field(default_factory=list)
    parent: Optional["PermissionNode"] = None


@dataclass
class AgentRegistration:
    """Agent注册信息"""
    identity: AgentIdentity
    registration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    capabilities: List[Capability] = field(default_factory=list)
    permission_tree: Optional[PermissionNode] = None
    permissions: List[Permission] = field(default_factory=list)
    registered_at: datetime = field(default_factory=datetime.now)
    validated_at: Optional[datetime] = None
    is_valid: bool = False


class IdentityRegistry:
    """身份注册表"""
    
    def __init__(self):
        self.identities: Dict[str, AgentIdentity] = {}
        self.agent_type_map: Dict[AgentType, List[AgentIdentity]] = {}
    
    def register_identity(self, agent_type: AgentType, name: str, version: str = "1.0.0") -> AgentIdentity:
        """注册Agent身份（静态注册）"""
        identity = AgentIdentity(
            agent_type=agent_type,
            name=name,
            version=version
        )
        self.identities[identity.identity_id] = identity
        
        if agent_type not in self.agent_type_map:
            self.agent_type_map[agent_type] = []
        self.agent_type_map[agent_type].append(identity)
        
        return identity
    
    def register_dynamic(self, agent_type: AgentType, name: str, metadata: Dict = None) -> AgentIdentity:
        """动态注册Agent身份"""
        identity = self.register_identity(agent_type, name)
        
        if metadata:
            pass
        
        identity.status = "active"
        identity.activated_at = datetime.now()
        
        return identity
    
    def get_identity(self, identity_id: str) -> Optional[AgentIdentity]:
        """获取身份"""
        return self.identities.get(identity_id)
    
    def get_identities_by_type(self, agent_type: AgentType) -> List[AgentIdentity]:
        """按类型获取身份"""
        return self.agent_type_map.get(agent_type, [])


class CapabilityRegistry:
    """能力注册表"""
    
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.capability_map: Dict[str, List[Capability]] = {}
    
    def register_capability(self, name: str, description: str, 
                          capability_type: CapabilityType,
                          handler: Callable = None,
                          version: str = "1.0.0") -> Capability:
        """注册能力（能力列表）"""
        capability = Capability(
            name=name,
            description=description,
            capability_type=capability_type,
            handler=handler,
            version=version
        )
        self.capabilities[capability.capability_id] = capability
        
        key = capability_type.value
        if key not in self.capability_map:
            self.capability_map[key] = []
        self.capability_map[key].append(capability)
        
        return capability
    
    def register_capability_mapping(self, capability: Capability, 
                                  agent_type: AgentType) -> bool:
        """注册能力映射"""
        key = f"{agent_type.value}:{capability.name}"
        if key not in self.capability_map:
            self.capability_map[key] = []
        self.capability_map[key].append(capability)
        return True
    
    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """获取能力"""
        return self.capabilities.get(capability_id)
    
    def get_capabilities_by_type(self, capability_type: CapabilityType) -> List[Capability]:
        """按类型获取能力"""
        return self.capability_map.get(capability_type.value, [])


class PermissionRegistry:
    """权限注册表"""
    
    def __init__(self):
        self.permissions: Dict[str, Permission] = {}
        self.resource_map: Dict[str, List[Permission]] = {}
        self.permission_trees: Dict[str, PermissionNode] = {}
    
    def register_permission(self, name: str, description: str, 
                          level: PermissionLevel,
                          resource: str,
                          allowed: bool = True) -> Permission:
        """注册权限（权限列表）"""
        permission = Permission(
            name=name,
            description=description,
            level=level,
            resource=resource,
            allowed=allowed
        )
        self.permissions[permission.permission_id] = permission
        
        if resource not in self.resource_map:
            self.resource_map[resource] = []
        self.resource_map[resource].append(permission)
        
        return permission
    
    def create_permission_tree(self, root_permission: Permission) -> PermissionNode:
        """创建权限树"""
        root = PermissionNode(permission=root_permission)
        self.permission_trees[root.node_id] = root
        return root
    
    def add_permission_to_tree(self, parent_node: PermissionNode, 
                             child_permission: Permission) -> PermissionNode:
        """向权限树添加权限"""
        child = PermissionNode(permission=child_permission, parent=parent_node)
        parent_node.children.append(child)
        self.permission_trees[child.node_id] = child
        return child
    
    def get_permission(self, permission_id: str) -> Optional[Permission]:
        """获取权限"""
        return self.permissions.get(permission_id)
    
    def get_permissions_by_resource(self, resource: str) -> List[Permission]:
        """按资源获取权限"""
        return self.resource_map.get(resource, [])


class RegistrationValidator:
    """注册验证器"""
    
    def __init__(self):
        pass
    
    def validate_startup(self, registration: AgentRegistration) -> Tuple[bool, List[str]]:
        """启动验证"""
        errors = []
        
        if not registration.identity:
            errors.append("No identity registered")
        
        if registration.identity.status == "inactive":
            errors.append("Agent is inactive")
        
        if len(registration.capabilities) == 0:
            errors.append("No capabilities registered")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            registration.validated_at = datetime.now()
            registration.is_valid = True
        
        return is_valid, errors
    
    def validate_runtime(self, registration: AgentRegistration, 
                        action: str, resource: str) -> Tuple[bool, List[str]]:
        """运行时验证"""
        errors = []
        
        if not registration.is_valid or not registration.validated_at:
            errors.append("Agent not validated")
        
        has_permission = False
        for perm in registration.permissions:
            if perm.resource == resource and perm.allowed:
                has_permission = True
                break
        
        if not has_permission:
            errors.append(f"No permission for {action} on {resource}")
        
        return len(errors) == 0, errors


class AgentRegistrationSystem:
    """Agent注册系统"""
    
    def __init__(self):
        self.identity_registry = IdentityRegistry()
        self.capability_registry = CapabilityRegistry()
        self.permission_registry = PermissionRegistry()
        self.registration_validator = RegistrationValidator()
        self.registrations: Dict[str, AgentRegistration] = {}
    
    def register_agent(self, agent_type: AgentType, name: str, 
                     capabilities: List[Capability] = None,
                     permissions: List[Permission] = None,
                     permission_tree: PermissionNode = None,
                     dynamic: bool = False) -> AgentRegistration:
        """注册Agent"""
        if dynamic:
            identity = self.identity_registry.register_dynamic(agent_type, name)
        else:
            identity = self.identity_registry.register_identity(agent_type, name)
        
        registration = AgentRegistration(
            identity=identity,
            capabilities=capabilities or [],
            permission_tree=permission_tree,
            permissions=permissions or []
        )
        
        self.registrations[registration.registration_id] = registration
        
        return registration
    
    def validate_agent(self, registration_id: str) -> Tuple[bool, List[str]]:
        """验证Agent"""
        registration = self.registrations.get(registration_id)
        if not registration:
            return False, ["Registration not found"]
        
        return self.registration_validator.validate_startup(registration)
    
    def initialize_standard_agents(self) -> List[AgentRegistration]:
        """初始化标准Agent"""
        registrations = []
        
        for agent_type in AgentType:
            name = f"{agent_type.value.capitalize()} Agent"
            registration = self.register_agent(agent_type, name, dynamic=True)
            registrations.append(registration)
        
        return registrations


_global_registration_system: Optional[AgentRegistrationSystem] = None


def get_registration_system() -> AgentRegistrationSystem:
    """获取全局注册系统"""
    global _global_registration_system
    if _global_registration_system is None:
        _global_registration_system = AgentRegistrationSystem()
    return _global_registration_system


def reset_registration_system() -> None:
    """重置全局注册系统"""
    global _global_registration_system
    _global_registration_system = None
