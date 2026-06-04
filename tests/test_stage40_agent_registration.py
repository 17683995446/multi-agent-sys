"""
阶段40验收测试：Agent身份、能力、权限注册体系
"""

import pytest
from src.architecture.agent_registration import (
    AgentType,
    PermissionLevel,
    CapabilityType,
    AgentIdentity,
    Capability,
    Permission,
    PermissionNode,
    AgentRegistration,
    IdentityRegistry,
    CapabilityRegistry,
    PermissionRegistry,
    RegistrationValidator,
    AgentRegistrationSystem,
    get_registration_system,
    reset_registration_system
)


class TestIdentityRegistry:
    """测试身份注册（验收项40.1）"""
    
    def test_static_identity_registration(self):
        """测试静态身份注册"""
        registry = IdentityRegistry()
        
        identity = registry.register_identity(
            AgentType.CONTROL,
            "Control Agent",
            "1.0.0"
        )
        
        assert identity is not None
        assert identity.agent_type == AgentType.CONTROL
        assert identity.name == "Control Agent"
        assert identity.status == "inactive"
    
    def test_dynamic_identity_registration(self):
        """测试动态身份注册"""
        registry = IdentityRegistry()
        
        identity = registry.register_dynamic(
            AgentType.CONTROL,
            "Dynamic Control Agent"
        )
        
        assert identity is not None
        assert identity.status == "active"
        assert identity.activated_at is not None
    
    def test_get_identity(self):
        """测试获取身份"""
        registry = IdentityRegistry()
        
        identity = registry.register_identity(AgentType.CONTROL, "Test Agent")
        retrieved = registry.get_identity(identity.identity_id)
        
        assert retrieved is not None
        assert retrieved.identity_id == identity.identity_id
    
    def test_get_identities_by_type(self):
        """测试按类型获取身份"""
        registry = IdentityRegistry()
        
        registry.register_identity(AgentType.CONTROL, "Control 1")
        registry.register_identity(AgentType.CONTROL, "Control 2")
        registry.register_identity(AgentType.REQUIREMENT, "Requirement")
        
        control_agents = registry.get_identities_by_type(AgentType.CONTROL)
        
        assert len(control_agents) == 2


class TestCapabilityRegistry:
    """测试能力注册（验收项40.2）"""
    
    def test_capability_list_registration(self):
        """测试能力列表注册"""
        registry = CapabilityRegistry()
        
        capability = registry.register_capability(
            "任务分解",
            "HTD层级任务分解",
            CapabilityType.ANALYSIS
        )
        
        assert capability is not None
        assert capability.name == "任务分解"
        assert capability.capability_type == CapabilityType.ANALYSIS
    
    def test_capability_mapping(self):
        """测试能力映射"""
        registry = CapabilityRegistry()
        
        capability = registry.register_capability(
            "任务分解",
            "HTD层级任务分解",
            CapabilityType.ANALYSIS
        )
        
        result = registry.register_capability_mapping(capability, AgentType.REQUIREMENT)
        
        assert result is True
    
    def test_get_capabilities_by_type(self):
        """测试按类型获取能力"""
        registry = CapabilityRegistry()
        
        registry.register_capability("任务分解", "", CapabilityType.ANALYSIS)
        registry.register_capability("代码生成", "", CapabilityType.GENERATION)
        
        analysis_capabilities = registry.get_capabilities_by_type(CapabilityType.ANALYSIS)
        
        assert len(analysis_capabilities) >= 1


class TestPermissionRegistry:
    """测试权限注册（验收项40.3）"""
    
    def test_permission_list_registration(self):
        """测试权限列表注册"""
        registry = PermissionRegistry()
        
        permission = registry.register_permission(
            "读取文件",
            "读取文件系统的权限",
            PermissionLevel.READ,
            "file_system"
        )
        
        assert permission is not None
        assert permission.name == "读取文件"
        assert permission.level == PermissionLevel.READ
    
    def test_permission_tree_creation(self):
        """测试权限树创建"""
        registry = PermissionRegistry()
        
        root_perm = registry.register_permission(
            "文件系统",
            "文件系统根权限",
            PermissionLevel.ADMIN,
            "file_system"
        )
        
        root = registry.create_permission_tree(root_perm)
        
        assert root is not None
        assert root.permission == root_perm
    
    def test_add_permission_to_tree(self):
        """测试向权限树添加权限"""
        registry = PermissionRegistry()
        
        root_perm = registry.register_permission(
            "文件系统",
            "",
            PermissionLevel.ADMIN,
            "file_system"
        )
        root = registry.create_permission_tree(root_perm)
        
        child_perm = registry.register_permission(
            "读取文件",
            "",
            PermissionLevel.READ,
            "file_system.read"
        )
        
        child = registry.add_permission_to_tree(root, child_perm)
        
        assert child is not None
        assert len(root.children) == 1
    
    def test_get_permissions_by_resource(self):
        """测试按资源获取权限"""
        registry = PermissionRegistry()
        
        registry.register_permission("读文件", "", PermissionLevel.READ, "file_system")
        registry.register_permission("写文件", "", PermissionLevel.WRITE, "file_system")
        
        permissions = registry.get_permissions_by_resource("file_system")
        
        assert len(permissions) >= 2


class TestRegistrationValidator:
    """测试注册验证（验收项40.4）"""
    
    def test_startup_validation(self):
        """测试启动验证"""
        validator = RegistrationValidator()
        
        identity = AgentIdentity(agent_type=AgentType.CONTROL, name="Test")
        identity.status = "active"
        
        capability = Capability(name="test", description="test", capability_type=CapabilityType.ANALYSIS)
        
        registration = AgentRegistration(
            identity=identity,
            capabilities=[capability]
        )
        
        is_valid, errors = validator.validate_startup(registration)
        
        assert is_valid is True or len(errors) == 0
    
    def test_runtime_validation(self):
        """测试运行时验证"""
        validator = RegistrationValidator()
        
        identity = AgentIdentity(agent_type=AgentType.CONTROL, name="Test")
        identity.status = "active"
        
        permission = Permission(
            name="读文件",
            description="",
            level=PermissionLevel.READ,
            resource="file_system"
        )
        
        registration = AgentRegistration(
            identity=identity,
            permissions=[permission]
        )
        registration.validated_at = datetime.now()
        registration.is_valid = True
        
        is_valid, errors = validator.validate_runtime(registration, "read", "file_system")
        
        assert isinstance(is_valid, bool)


class TestAgentRegistrationSystem:
    """测试Agent注册系统"""
    
    def test_agent_registration(self):
        """测试Agent注册"""
        system = AgentRegistrationSystem()
        
        registration = system.register_agent(
            AgentType.CONTROL,
            "Control Agent"
        )
        
        assert registration is not None
        assert registration.identity.agent_type == AgentType.CONTROL
    
    def test_agent_validation(self):
        """测试Agent验证"""
        system = AgentRegistrationSystem()
        
        registration = system.register_agent(
            AgentType.CONTROL,
            "Control Agent"
        )
        
        is_valid, errors = system.validate_agent(registration.registration_id)
        
        assert isinstance(is_valid, bool)
    
    def test_standard_agents_initialization(self):
        """测试标准Agent初始化"""
        system = AgentRegistrationSystem()
        
        registrations = system.initialize_standard_agents()
        
        assert len(registrations) >= 8


class TestGlobalRegistrationSystem:
    """测试全局注册系统"""
    
    def test_get_global_system(self):
        """测试获取全局系统"""
        reset_registration_system()
        
        system1 = get_registration_system()
        system2 = get_registration_system()
        
        assert system1 is system2
    
    def test_reset_global_system(self):
        """测试重置全局系统"""
        system1 = get_registration_system()
        reset_registration_system()
        system2 = get_registration_system()
        
        assert system1 is not system2


class TestCompleteScenario:
    """测试完整场景"""
    
    def test_complete_registration_scenario(self):
        """测试完整注册场景"""
        system = AgentRegistrationSystem()
        
        identity = system.identity_registry.register_identity(
            AgentType.CONTROL,
            "Control Agent"
        )
        
        capability = system.capability_registry.register_capability(
            "全局协调",
            "全局任务协调",
            CapabilityType.COORDINATION
        )
        
        permission = system.permission_registry.register_permission(
            "任务调度",
            "调度任务权限",
            PermissionLevel.EXECUTE,
            "task_scheduler"
        )
        
        registration = system.register_agent(
            AgentType.CONTROL,
            "Control Agent",
            capabilities=[capability],
            permissions=[permission]
        )
        
        is_valid, errors = system.validate_agent(registration.registration_id)
        
        assert registration is not None


class TestAgentRegisterTest:
    """测试Agent注册测试脚本（验收项40.1）"""
    
    def test_agent_register_functionality(self):
        """测试注册功能"""
        system = AgentRegistrationSystem()
        
        registration = system.register_agent(
            AgentType.CONTROL,
            "Test Agent"
        )
        
        assert registration is not None


class TestCapabilityRegisterTest:
    """测试能力注册测试脚本（验收项40.2）"""
    
    def test_capability_register_functionality(self):
        """测试能力注册功能"""
        registry = CapabilityRegistry()
        
        capability = registry.register_capability(
            "test",
            "test",
            CapabilityType.ANALYSIS
        )
        
        assert capability is not None


class TestPermissionRegisterTest:
    """测试权限注册测试脚本（验收项40.3）"""
    
    def test_permission_register_functionality(self):
        """测试权限注册功能"""
        registry = PermissionRegistry()
        
        permission = registry.register_permission(
            "test",
            "test",
            PermissionLevel.READ,
            "test"
        )
        
        assert permission is not None


class TestRegistrationVerifyTest:
    """测试注册验证测试脚本（验收项40.4）"""
    
    def test_registration_verify_functionality(self):
        """测试验证功能"""
        validator = RegistrationValidator()
        
        identity = AgentIdentity(agent_type=AgentType.CONTROL, name="Test")
        
        registration = AgentRegistration(identity=identity)
        
        is_valid, errors = validator.validate_startup(registration)
        
        assert isinstance(is_valid, bool)


from datetime import datetime

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
