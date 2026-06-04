"""
阶段49验收测试：协商安全与权限控制
"""

import pytest
import time

from src.architecture.negotiation_security import (
    PermissionLevel, SecurityRole, ROLE_PERMISSIONS,
    AccessControlEntry, SecurityPolicy, ProposalSignature,
    AccessController, ProposalAuthenticator, NegotiationSecurityService,
    get_security_service, reset_security_service
)


class TestPermissionLevel:
    """测试权限级别枚举"""

    def test_permission_values(self):
        """测试权限枚举值"""
        assert PermissionLevel.READ.value == "read"
        assert PermissionLevel.PROPOSE.value == "propose"
        assert PermissionLevel.ACCEPT.value == "accept"
        assert PermissionLevel.ADMIN.value == "admin"

    def test_all_permissions(self):
        """测试所有权限"""
        perms = list(PermissionLevel)
        assert len(perms) == 4


class TestSecurityRole:
    """测试安全角色枚举"""

    def test_role_values(self):
        """测试角色枚举值"""
        assert SecurityRole.OBSERVER.value == "observer"
        assert SecurityRole.PARTICIPANT.value == "participant"
        assert SecurityRole.MODERATOR.value == "moderator"
        assert SecurityRole.OWNER.value == "owner"

    def test_role_permissions_mapping(self):
        """测试角色权限映射"""
        assert PermissionLevel.READ in ROLE_PERMISSIONS[SecurityRole.OBSERVER]
        assert PermissionLevel.ADMIN not in ROLE_PERMISSIONS[SecurityRole.OBSERVER]
        assert PermissionLevel.PROPOSE in ROLE_PERMISSIONS[SecurityRole.PARTICIPANT]
        assert PermissionLevel.ADMIN in ROLE_PERMISSIONS[SecurityRole.MODERATOR]
        assert PermissionLevel.ADMIN in ROLE_PERMISSIONS[SecurityRole.OWNER]


class TestAccessControlEntry:
    """测试访问控制条目"""

    def test_default_creation(self):
        """测试默认创建"""
        ace = AccessControlEntry()
        assert ace.agent_id == ""
        assert ace.role == SecurityRole.OBSERVER
        assert PermissionLevel.READ in ace.permissions
        assert ace.granted_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        ace = AccessControlEntry(
            agent_id="agent1",
            role=SecurityRole.MODERATOR,
            permissions=[PermissionLevel.READ, PermissionLevel.ADMIN],
        )
        assert ace.agent_id == "agent1"
        assert ace.role == SecurityRole.MODERATOR
        assert len(ace.permissions) == 2

    def test_auto_permissions_from_role(self):
        """测试根据角色自动设置权限"""
        ace = AccessControlEntry(agent_id="a1", role=SecurityRole.PARTICIPANT)
        assert PermissionLevel.READ in ace.permissions
        assert PermissionLevel.PROPOSE in ace.permissions
        assert PermissionLevel.ACCEPT in ace.permissions


class TestSecurityPolicy:
    """测试安全策略"""

    def test_default_creation(self):
        """测试默认创建"""
        policy = SecurityPolicy()
        assert policy.session_id != ""
        assert policy.require_authentication == True
        assert policy.require_encryption == False
        assert policy.max_proposals_per_round == 10
        assert len(policy.allowed_strategies) == 3

    def test_custom_creation(self):
        """测试自定义创建"""
        policy = SecurityPolicy(
            session_id="s1",
            require_authentication=False,
            require_encryption=True,
            max_proposals_per_round=5,
            allowed_strategies=["collaborative"],
        )
        assert policy.session_id == "s1"
        assert policy.require_authentication == False
        assert policy.require_encryption == True
        assert policy.max_proposals_per_round == 5
        assert len(policy.allowed_strategies) == 1


class TestProposalSignature:
    """测试提案签名"""

    def test_default_creation(self):
        """测试默认创建"""
        sig = ProposalSignature()
        assert sig.proposal_id != ""
        assert sig.signer_id == ""
        assert sig.signature == ""
        assert sig.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        sig = ProposalSignature(
            proposal_id="p1",
            signer_id="agent1",
            signature="abc123",
        )
        assert sig.proposal_id == "p1"
        assert sig.signer_id == "agent1"
        assert sig.signature == "abc123"


class TestAccessController:
    """测试访问控制器"""

    def test_initial_state(self):
        """测试初始状态"""
        controller = AccessController()
        assert len(controller.aces) == 0
        assert len(controller.policies) == 0

    def test_grant_access(self):
        """测试授予权限"""
        controller = AccessController()
        ace = controller.grant_access("agent1", SecurityRole.PARTICIPANT)
        assert ace.agent_id == "agent1"
        assert ace.role == SecurityRole.PARTICIPANT
        assert "agent1" in controller.aces

    def test_grant_access_empty_agent(self):
        """测试空agent_id授予权限"""
        controller = AccessController()
        with pytest.raises(ValueError):
            controller.grant_access("", SecurityRole.OBSERVER)

    def test_grant_access_custom_permissions(self):
        """测试自定义权限授予"""
        controller = AccessController()
        ace = controller.grant_access(
            "agent1", SecurityRole.OBSERVER,
            permissions=[PermissionLevel.READ, PermissionLevel.PROPOSE]
        )
        assert PermissionLevel.PROPOSE in ace.permissions

    def test_revoke_access(self):
        """测试撤销权限"""
        controller = AccessController()
        controller.grant_access("agent1", SecurityRole.PARTICIPANT)
        result = controller.revoke_access("agent1")
        assert result == True
        assert "agent1" not in controller.aces

    def test_revoke_access_nonexistent(self):
        """测试撤销不存在的权限"""
        controller = AccessController()
        result = controller.revoke_access("nonexistent")
        assert result == False

    def test_revoke_access_empty(self):
        """测试撤销空agent_id"""
        controller = AccessController()
        result = controller.revoke_access("")
        assert result == False

    def test_check_permission(self):
        """测试检查权限"""
        controller = AccessController()
        controller.grant_access("agent1", SecurityRole.PARTICIPANT)
        assert controller.check_permission("agent1", PermissionLevel.READ) == True
        assert controller.check_permission("agent1", PermissionLevel.PROPOSE) == True
        assert controller.check_permission("agent1", PermissionLevel.ADMIN) == False

    def test_check_permission_no_ace(self):
        """测试检查无权限条目的权限"""
        controller = AccessController()
        assert controller.check_permission("unknown", PermissionLevel.READ) == False

    def test_check_permission_empty_agent(self):
        """测试检查空agent_id的权限"""
        controller = AccessController()
        assert controller.check_permission("", PermissionLevel.READ) == False

    def test_get_role(self):
        """测试获取角色"""
        controller = AccessController()
        controller.grant_access("agent1", SecurityRole.MODERATOR)
        role = controller.get_role("agent1")
        assert role == SecurityRole.MODERATOR

    def test_get_role_unknown(self):
        """测试获取未知角色"""
        controller = AccessController()
        role = controller.get_role("unknown")
        assert role is None

    def test_get_role_empty(self):
        """测试获取空agent_id的角色"""
        controller = AccessController()
        role = controller.get_role("")
        assert role is None

    def test_validate_access(self):
        """测试验证访问"""
        controller = AccessController()
        controller.grant_access("agent1", SecurityRole.PARTICIPANT)
        assert controller.validate_access("agent1", "read") == True
        assert controller.validate_access("agent1", "propose") == True
        assert controller.validate_access("agent1", "admin") == False

    def test_validate_access_action_mapping(self):
        """测试验证访问操作映射"""
        controller = AccessController()
        controller.grant_access("agent1", SecurityRole.PARTICIPANT)
        assert controller.validate_access("agent1", "view") == True
        assert controller.validate_access("agent1", "submit") == True
        assert controller.validate_access("agent1", "manage") == False

    def test_validate_access_unknown_action(self):
        """测试验证未知操作"""
        controller = AccessController()
        controller.grant_access("agent1", SecurityRole.OWNER)
        assert controller.validate_access("agent1", "unknown_action") == False

    def test_validate_access_empty_params(self):
        """测试验证空参数"""
        controller = AccessController()
        assert controller.validate_access("", "read") == False
        assert controller.validate_access("agent1", "") == False


class TestProposalAuthenticator:
    """测试提案认证器"""

    def test_initial_state(self):
        """测试初始状态"""
        auth = ProposalAuthenticator()
        assert len(auth.signatures) == 0

    def test_sign_proposal(self):
        """测试签名提案"""
        auth = ProposalAuthenticator()
        sig = auth.sign_proposal("p1", "agent1", "proposal_data")
        assert sig.proposal_id == "p1"
        assert sig.signer_id == "agent1"
        assert sig.signature != ""
        assert len(auth.signatures) == 1

    def test_sign_proposal_empty_params(self):
        """测试空参数签名"""
        auth = ProposalAuthenticator()
        with pytest.raises(ValueError):
            auth.sign_proposal("", "agent1")
        with pytest.raises(ValueError):
            auth.sign_proposal("p1", "")

    def test_verify_signature_valid(self):
        """测试验证有效签名"""
        auth = ProposalAuthenticator()
        sig = auth.sign_proposal("p1", "agent1", "data")
        result = auth.verify_signature("p1", "agent1", sig.signature, "data")
        assert result == True

    def test_verify_signature_invalid(self):
        """测试验证无效签名"""
        auth = ProposalAuthenticator()
        auth.sign_proposal("p1", "agent1", "data")
        result = auth.verify_signature("p1", "agent1", "wrong_signature", "data")
        assert result == False

    def test_verify_signature_different_data(self):
        """测试验证不同数据的签名"""
        auth = ProposalAuthenticator()
        sig = auth.sign_proposal("p1", "agent1", "original_data")
        result = auth.verify_signature("p1", "agent1", sig.signature, "tampered_data")
        assert result == False

    def test_verify_signature_missing_params(self):
        """测试验证缺少参数的签名"""
        auth = ProposalAuthenticator()
        assert auth.verify_signature("", "agent1", "sig") == False
        assert auth.verify_signature("p1", "", "sig") == False
        assert auth.verify_signature("p1", "agent1", "") == False

    def test_detect_tampering_no_tampering(self):
        """测试检测未篡改的提案"""
        auth = ProposalAuthenticator()
        sig = auth.sign_proposal("p1", "agent1", "data")
        result = auth.detect_tampering("p1", "agent1", sig.signature, "data")
        assert result == False

    def test_detect_tampering_tampered(self):
        """测试检测被篡改的提案"""
        auth = ProposalAuthenticator()
        auth.sign_proposal("p1", "agent1", "data")
        result = auth.detect_tampering("p1", "agent1", "fake_signature", "data")
        assert result == True

    def test_detect_tampering_missing_params(self):
        """测试检测缺少参数的篡改"""
        auth = ProposalAuthenticator()
        result = auth.detect_tampering("", "agent1", "sig")
        assert result == True
        result = auth.detect_tampering("p1", "", "sig")
        assert result == True

    def test_different_secret_keys(self):
        """测试不同密钥"""
        auth1 = ProposalAuthenticator(secret_key="key1")
        auth2 = ProposalAuthenticator(secret_key="key2")
        sig = auth1.sign_proposal("p1", "agent1", "data")
        result = auth2.verify_signature("p1", "agent1", sig.signature, "data")
        assert result == False


class TestNegotiationSecurityService:
    """测试协商安全服务"""

    def setup_method(self):
        reset_security_service()

    def test_initial_state(self):
        """测试初始状态"""
        service = NegotiationSecurityService()
        assert len(service.policies) == 0
        assert len(service.authenticated_agents) == 0

    def test_create_policy(self):
        """测试创建安全策略"""
        service = NegotiationSecurityService()
        policy = service.create_policy(session_id="s1")
        assert policy.session_id == "s1"
        assert "s1" in service.policies

    def test_create_policy_custom(self):
        """测试创建自定义安全策略"""
        service = NegotiationSecurityService()
        policy = service.create_policy(
            session_id="s2",
            require_authentication=False,
            max_proposals_per_round=5,
        )
        assert policy.require_authentication == False
        assert policy.max_proposals_per_round == 5

    def test_authenticate_agent_with_token(self):
        """测试使用token认证Agent"""
        service = NegotiationSecurityService()
        result = service.authenticate_agent("agent1", {"token": "valid_token"})
        assert result == True
        assert "agent1" in service.authenticated_agents

    def test_authenticate_agent_without_token(self):
        """测试无token认证Agent"""
        service = NegotiationSecurityService()
        # 没有策略要求认证时，无token也可以通过
        result = service.authenticate_agent("agent1", {})
        assert result == True

    def test_authenticate_agent_empty_id(self):
        """测试空agent_id认证"""
        service = NegotiationSecurityService()
        result = service.authenticate_agent("", {"token": "valid"})
        assert result == False

    def test_authenticate_agent_with_policy_requiring_auth(self):
        """测试有认证策略时的认证"""
        service = NegotiationSecurityService()
        service.create_policy(session_id="s1", require_authentication=True)
        # 无token应失败
        result = service.authenticate_agent("agent1", {})
        assert result == False
        # 有token应成功
        result = service.authenticate_agent("agent1", {"token": "valid"})
        assert result == True

    def test_authorize_action(self):
        """测试授权操作"""
        service = NegotiationSecurityService()
        service.access_controller.grant_access("agent1", SecurityRole.PARTICIPANT)
        service.authenticate_agent("agent1", {"token": "valid"})
        result = service.authorize_action("agent1", "read")
        assert result == True

    def test_authorize_action_denied(self):
        """测试拒绝授权"""
        service = NegotiationSecurityService()
        service.access_controller.grant_access("agent1", SecurityRole.OBSERVER)
        service.authenticate_agent("agent1", {"token": "valid"})
        result = service.authorize_action("agent1", "admin")
        assert result == False

    def test_authorize_action_not_authenticated(self):
        """测试未认证时授权"""
        service = NegotiationSecurityService()
        service.create_policy(session_id="s1", require_authentication=True)
        service.access_controller.grant_access("agent1", SecurityRole.PARTICIPANT)
        # 未认证，应拒绝
        result = service.authorize_action("agent1", "read", session_id="s1")
        assert result == False

    def test_authorize_action_empty_params(self):
        """测试空参数授权"""
        service = NegotiationSecurityService()
        assert service.authorize_action("", "read") == False
        assert service.authorize_action("agent1", "") == False

    def test_sign_proposal(self):
        """测试签名提案"""
        service = NegotiationSecurityService()
        sig = service.sign_proposal("p1", "agent1", "data")
        assert sig is not None
        assert sig.proposal_id == "p1"
        assert sig.signer_id == "agent1"
        assert sig.signature != ""

    def test_sign_proposal_empty_params(self):
        """测试空参数签名"""
        service = NegotiationSecurityService()
        result = service.sign_proposal("", "agent1")
        assert result is None
        result = service.sign_proposal("p1", "")
        assert result is None

    def test_verify_proposal(self):
        """测试验证提案"""
        service = NegotiationSecurityService()
        sig = service.sign_proposal("p1", "agent1", "data")
        result = service.verify_proposal("p1", "agent1", sig.signature, "data")
        assert result == True

    def test_verify_proposal_invalid(self):
        """测试验证无效提案"""
        service = NegotiationSecurityService()
        service.sign_proposal("p1", "agent1", "data")
        result = service.verify_proposal("p1", "agent1", "wrong_sig", "data")
        assert result == False

    def test_verify_proposal_missing_params(self):
        """测试验证缺少参数的提案"""
        service = NegotiationSecurityService()
        assert service.verify_proposal("", "agent1", "sig") == False
        assert service.verify_proposal("p1", "", "sig") == False
        assert service.verify_proposal("p1", "agent1", "") == False

    def test_global_service(self):
        """测试全局服务"""
        service1 = get_security_service()
        service2 = get_security_service()
        assert service1 is service2
        reset_security_service()
        service3 = get_security_service()
        assert service3 is not service1

    def test_full_security_workflow(self):
        """测试完整安全工作流"""
        service = NegotiationSecurityService()

        # 1. 创建策略
        policy = service.create_policy(session_id="s1", require_authentication=True)

        # 2. 授予权限
        service.access_controller.grant_access("agent1", SecurityRole.PARTICIPANT)

        # 3. 认证
        auth_result = service.authenticate_agent("agent1", {"token": "my_token"})
        assert auth_result == True

        # 4. 授权操作
        assert service.authorize_action("agent1", "read", session_id="s1") == True
        assert service.authorize_action("agent1", "propose", session_id="s1") == True
        assert service.authorize_action("agent1", "admin", session_id="s1") == False

        # 5. 签名和验证
        sig = service.sign_proposal("p1", "agent1", "proposal_content")
        assert sig is not None
        assert service.verify_proposal("p1", "agent1", sig.signature, "proposal_content") == True
