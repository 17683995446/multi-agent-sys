import pytest
from src.architecture import (
    ActionType,
    AccessLevel,
    Permission,
    Role,
    User,
    AuditLog,
    ReadOnlyResource,
    PermissionTree,
    AuditLogger,
    RoleBasedAccessControl,
    get_rbac,
    reset_rbac
)


class TestPermissionModel:
    """测试权限模型"""

    def test_create_permission(self):
        perm = Permission(
            permission_id="perm-1",
            resource="file:test.txt",
            action=ActionType.READ,
            level=AccessLevel.VIEW,
            description="Read test file"
        )
        assert perm.permission_id == "perm-1"
        assert perm.resource == "file:test.txt"
        assert perm.action == ActionType.READ

    def test_permission_to_dict(self):
        perm = Permission(
            permission_id="perm-1",
            resource="file:test.txt",
            action=ActionType.READ,
            level=AccessLevel.VIEW
        )
        data = perm.to_dict()
        assert data["permission_id"] == "perm-1"
        assert data["action"] == "read"
        assert data["level"] == "view"


class TestRoleModel:
    """测试角色模型"""

    def test_create_role(self):
        role = Role(
            role_id="role-editor",
            name="Editor",
            description="Can edit documents"
        )
        assert role.role_id == "role-editor"
        assert role.name == "Editor"

    def test_add_permission_to_role(self):
        role = Role(role_id="role-editor", name="Editor")
        perm = Permission(
            permission_id="perm-1",
            resource="file:doc.txt",
            action=ActionType.WRITE,
            level=AccessLevel.EDIT
        )
        role.add_permission(perm)
        assert len(role.permissions) == 1
        assert role.permissions[0].permission_id == "perm-1"


class TestUserModel:
    """测试用户模型"""

    def test_create_user(self):
        user = User(
            user_id="user-alice",
            username="alice",
            roles=["role-editor"]
        )
        assert user.user_id == "user-alice"
        assert user.username == "alice"
        assert "role-editor" in user.roles

    def test_add_role_to_user(self):
        user = User(user_id="user-alice", username="alice")
        user.add_role("role-editor")
        assert "role-editor" in user.roles


class TestReadOnlyResource:
    """测试只读资源"""

    def test_create_readonly_resource(self):
        data = {"key": "value", "number": 42}
        ro = ReadOnlyResource("test-resource", data, owner="alice")
        assert ro.resource_name == "test-resource"
        assert ro.is_read_only is True
        assert ro.owner == "alice"

    def test_readonly_resource_read(self):
        data = {"key": "value"}
        ro = ReadOnlyResource("test", data)
        assert ro.get("key") == "value"

    def test_readonly_resource_write_forbidden(self):
        data = {"key": "value"}
        ro = ReadOnlyResource("test", data)
        with pytest.raises(PermissionError):
            ro.key = "new"

    def test_readonly_resource_delete_forbidden(self):
        data = {"key": "value"}
        ro = ReadOnlyResource("test", data)
        with pytest.raises(PermissionError):
            del ro.key


class TestPermissionTree:
    """测试权限树"""

    def test_add_resource(self):
        tree = PermissionTree()
        tree.add_resource("app")
        tree.add_resource("app:files", parent="app")
        tree.add_resource("app:files:test.txt", parent="app:files")

    def test_inheritance(self):
        tree = PermissionTree()
        tree.add_resource("app")
        tree.add_resource("app:files", parent="app")
        tree.set_permission("app", ActionType.READ, AccessLevel.VIEW)

        level = tree.get_effective_level("app:files", ActionType.READ)
        assert level == AccessLevel.VIEW

    def test_override_permission(self):
        tree = PermissionTree()
        tree.add_resource("app")
        tree.add_resource("app:files", parent="app")
        tree.set_permission("app", ActionType.READ, AccessLevel.VIEW)
        tree.set_permission("app:files", ActionType.READ, AccessLevel.EDIT)

        level = tree.get_effective_level("app:files", ActionType.READ)
        assert level == AccessLevel.EDIT


class TestAuditLogger:
    """测试审计日志"""

    def test_create_audit_log(self):
        log = AuditLog(
            user_id="user-alice",
            username="alice",
            resource="file:test.txt",
            action=ActionType.READ,
            granted=True,
            reason="Permission granted"
        )
        assert log.user_id == "user-alice"
        assert log.granted is True

    def test_log_access(self):
        logger = AuditLogger()
        user = User(user_id="user-alice", username="alice")
        log = logger.log_access(
            user,
            "file:test.txt",
            ActionType.READ,
            True,
            "Permission granted"
        )
        assert log.granted is True

    def test_query_logs(self):
        logger = AuditLogger()
        user = User(user_id="user-alice", username="alice")
        
        logger.log_access(user, "file:1", ActionType.READ, True)
        logger.log_access(user, "file:2", ActionType.WRITE, False)
        
        logs = logger.get_logs(user_id="user-alice")
        assert len(logs) == 2


class TestRBAC:
    """测试基于角色的访问控制"""

    def test_create_role_and_user(self):
        rbac = RoleBasedAccessControl()
        rbac.create_role("role-editor", "Editor")
        rbac.create_user("user-alice", "alice", ["role-editor"])
        
        assert rbac.get_role("role-editor") is not None
        assert rbac.get_user("user-alice") is not None

    def test_assign_role(self):
        rbac = RoleBasedAccessControl()
        rbac.create_role("role-editor", "Editor")
        rbac.create_user("user-alice", "alice")
        
        result = rbac.assign_role_to_user("user-alice", "role-editor")
        assert result is True
        
        user = rbac.get_user("user-alice")
        assert "role-editor" in user.roles

    def test_add_permission(self):
        rbac = RoleBasedAccessControl()
        role = rbac.create_role("role-editor", "Editor")
        perm = Permission(
            permission_id="perm-write",
            resource="file:test.txt",
            action=ActionType.WRITE,
            level=AccessLevel.EDIT
        )
        
        result = rbac.add_permission_to_role("role-editor", perm)
        assert result is True
        
        role_check = rbac.get_role("role-editor")
        assert len(role_check.permissions) == 1

    def test_check_permission_granted(self):
        rbac = RoleBasedAccessControl()
        rbac.create_role("role-editor", "Editor")
        perm = Permission(
            permission_id="perm-read",
            resource="file:test.txt",
            action=ActionType.READ,
            level=AccessLevel.VIEW
        )
        rbac.add_permission_to_role("role-editor", perm)
        user = rbac.create_user("user-alice", "alice", ["role-editor"])
        
        result = rbac.check_permission(user, "file:test.txt", ActionType.READ)
        assert result is True

    def test_check_permission_denied(self):
        rbac = RoleBasedAccessControl()
        rbac.create_role("role-viewer", "Viewer")
        user = rbac.create_user("user-alice", "alice", ["role-viewer"])
        
        result = rbac.check_permission(user, "file:secret.txt", ActionType.READ)
        assert result is False

    def test_check_permission_no_user(self):
        rbac = RoleBasedAccessControl()
        result = rbac.check_permission(None, "file:test.txt", ActionType.READ)
        assert result is False

    def test_wrap_readonly(self):
        rbac = RoleBasedAccessControl()
        data = {"content": "secret"}
        ro = rbac.wrap_read_only("doc:1", data, owner="alice")
        assert ro.is_read_only is True
        assert ro.get("content") == "secret"

    def test_role_inheritance(self):
        rbac = RoleBasedAccessControl()
        base_role = rbac.create_role("role-base", "Base")
        base_perm = Permission(
            permission_id="perm-base",
            resource="app:*",
            action=ActionType.READ,
            level=AccessLevel.VIEW
        )
        rbac.add_permission_to_role("role-base", base_perm)
        
        editor_role = rbac.create_role(
            "role-editor",
            "Editor",
            parent_roles=["role-base"]
        )
        editor_perm = Permission(
            permission_id="perm-editor",
            resource="file:*",
            action=ActionType.WRITE,
            level=AccessLevel.EDIT
        )
        rbac.add_permission_to_role("role-editor", editor_perm)
        
        user = rbac.create_user("user-alice", "alice", ["role-editor"])
        perms = rbac.get_all_user_permissions("user-alice")
        assert len(perms) >= 2


class TestGlobalRBAC:
    """测试全局RBAC"""

    def test_get_global_rbac(self):
        reset_rbac()
        rbac = get_rbac()
        assert isinstance(rbac, RoleBasedAccessControl)
        assert get_rbac() is rbac

    def test_reset_global_rbac(self):
        rbac1 = get_rbac()
        reset_rbac()
        rbac2 = get_rbac()
        assert rbac1 is not rbac2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
