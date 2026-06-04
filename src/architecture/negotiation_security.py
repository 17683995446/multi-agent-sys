"""
协商安全与权限控制
职责：访问控制、提案认证、签名验证、安全策略管理
"""

import uuid
import time
import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """权限级别"""
    READ = "read"
    PROPOSE = "propose"
    ACCEPT = "accept"
    ADMIN = "admin"


class SecurityRole(str, Enum):
    """安全角色"""
    OBSERVER = "observer"
    PARTICIPANT = "participant"
    MODERATOR = "moderator"
    OWNER = "owner"


# 角色到权限的映射
ROLE_PERMISSIONS: Dict[SecurityRole, Set[PermissionLevel]] = {
    SecurityRole.OBSERVER: {PermissionLevel.READ},
    SecurityRole.PARTICIPANT: {PermissionLevel.READ, PermissionLevel.PROPOSE, PermissionLevel.ACCEPT},
    SecurityRole.MODERATOR: {PermissionLevel.READ, PermissionLevel.PROPOSE, PermissionLevel.ACCEPT, PermissionLevel.ADMIN},
    SecurityRole.OWNER: {PermissionLevel.READ, PermissionLevel.PROPOSE, PermissionLevel.ACCEPT, PermissionLevel.ADMIN},
}


@dataclass
class AccessControlEntry:
    """访问控制条目"""
    agent_id: str = ""
    role: SecurityRole = SecurityRole.OBSERVER
    permissions: List[PermissionLevel] = field(default_factory=list)
    granted_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.permissions:
            self.permissions = list(ROLE_PERMISSIONS.get(self.role, set()))
        logger.debug(f"AccessControlEntry created: agent={self.agent_id}, role={self.role}")


@dataclass
class SecurityPolicy:
    """安全策略"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    require_authentication: bool = True
    require_encryption: bool = False
    max_proposals_per_round: int = 10
    allowed_strategies: List[str] = field(default_factory=lambda: ["collaborative", "competitive", "conciliatory"])

    def __post_init__(self):
        logger.debug(f"SecurityPolicy created: session={self.session_id[:8]}")


@dataclass
class ProposalSignature:
    """提案签名"""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signer_id: str = ""
    signature: str = ""
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"ProposalSignature created: proposal={self.proposal_id[:8]}, signer={self.signer_id}")


class AccessController:
    """访问控制器"""

    def __init__(self):
        self.policies: Dict[str, SecurityPolicy] = {}
        self.aces: Dict[str, AccessControlEntry] = {}
        logger.info("AccessController initialized")

    def grant_access(self, agent_id: str, role: SecurityRole,
                     permissions: Optional[List[PermissionLevel]] = None) -> AccessControlEntry:
        """授予访问权限"""
        # 输入验证
        if not agent_id:
            logger.warning("grant_access: agent_id is empty")
            raise ValueError("agent_id不能为空")

        # 业务逻辑
        try:
            perms = permissions or list(ROLE_PERMISSIONS.get(role, set()))
            ace = AccessControlEntry(
                agent_id=agent_id,
                role=role,
                permissions=perms,
            )
            self.aces[agent_id] = ace
            logger.info(f"AccessController: granted access to agent={agent_id}, role={role}")
        except Exception as e:
            # 异常处理
            logger.error(f"AccessController: grant_access failed: {e}")
            raise

        # 返回结果
        return ace

    def revoke_access(self, agent_id: str) -> bool:
        """撤销访问权限"""
        # 输入验证
        if not agent_id:
            logger.warning("revoke_access: agent_id is empty")
            return False

        # 业务逻辑
        try:
            if agent_id in self.aces:
                del self.aces[agent_id]
                logger.info(f"AccessController: revoked access for agent={agent_id}")
                return True
            else:
                logger.debug(f"AccessController: agent={agent_id} not found")
                return False
        except Exception as e:
            # 异常处理
            logger.error(f"AccessController: revoke_access failed: {e}")
            return False

    def check_permission(self, agent_id: str, permission: PermissionLevel) -> bool:
        """检查权限"""
        # 输入验证
        if not agent_id:
            logger.debug("check_permission: agent_id is empty")
            return False

        # 业务逻辑
        try:
            ace = self.aces.get(agent_id)
            if ace is None:
                logger.debug(f"AccessController: agent={agent_id} has no ACE")
                return False

            has_perm = permission in ace.permissions
            logger.debug(f"AccessController: agent={agent_id}, permission={permission}, "
                        f"granted={has_perm}")
        except Exception as e:
            # 异常处理
            logger.error(f"AccessController: check_permission failed: {e}")
            return False

        # 返回结果
        return has_perm

    def get_role(self, agent_id: str) -> Optional[SecurityRole]:
        """获取角色"""
        # 输入验证
        if not agent_id:
            return None

        # 业务逻辑 + 返回结果
        ace = self.aces.get(agent_id)
        if ace:
            return ace.role
        return None

    def validate_access(self, agent_id: str, action: str) -> bool:
        """验证访问"""
        # 输入验证
        if not agent_id or not action:
            logger.debug("validate_access: agent_id or action is empty")
            return False

        # 业务逻辑
        try:
            # 将action映射到权限
            action_to_perm: Dict[str, PermissionLevel] = {
                "read": PermissionLevel.READ,
                "propose": PermissionLevel.PROPOSE,
                "accept": PermissionLevel.ACCEPT,
                "admin": PermissionLevel.ADMIN,
                "view": PermissionLevel.READ,
                "submit": PermissionLevel.PROPOSE,
                "approve": PermissionLevel.ACCEPT,
                "manage": PermissionLevel.ADMIN,
            }
            perm = action_to_perm.get(action)
            if perm is None:
                logger.debug(f"AccessController: unknown action={action}")
                return False

            result = self.check_permission(agent_id, perm)
            logger.debug(f"AccessController: validate_access agent={agent_id}, "
                        f"action={action}, result={result}")
        except Exception as e:
            # 异常处理
            logger.error(f"AccessController: validate_access failed: {e}")
            return False

        # 返回结果
        return result


class ProposalAuthenticator:
    """提案认证器"""

    def __init__(self, secret_key: str = "default-secret-key"):
        self.secret_key = secret_key
        self.signatures: Dict[str, ProposalSignature] = {}
        logger.info("ProposalAuthenticator initialized")

    def sign_proposal(self, proposal_id: str, signer_id: str, proposal_data: str = "") -> ProposalSignature:
        """签名提案"""
        # 输入验证
        if not proposal_id or not signer_id:
            logger.warning("sign_proposal: proposal_id or signer_id is empty")
            raise ValueError("proposal_id和signer_id不能为空")

        # 业务逻辑
        try:
            data_to_sign = f"{proposal_id}:{signer_id}:{proposal_data}:{self.secret_key}"
            signature = hashlib.sha256(data_to_sign.encode()).hexdigest()
            sig = ProposalSignature(
                proposal_id=proposal_id,
                signer_id=signer_id,
                signature=signature,
            )
            self.signatures[f"{proposal_id}:{signer_id}"] = sig
            logger.info(f"ProposalAuthenticator: signed proposal={proposal_id[:8]}, "
                       f"signer={signer_id}")
        except Exception as e:
            # 异常处理
            logger.error(f"ProposalAuthenticator: sign_proposal failed: {e}")
            raise

        # 返回结果
        return sig

    def verify_signature(self, proposal_id: str, signer_id: str,
                         signature: str, proposal_data: str = "") -> bool:
        """验证签名"""
        # 输入验证
        if not proposal_id or not signer_id or not signature:
            logger.debug("verify_signature: missing required parameters")
            return False

        # 业务逻辑
        try:
            data_to_sign = f"{proposal_id}:{signer_id}:{proposal_data}:{self.secret_key}"
            expected = hashlib.sha256(data_to_sign.encode()).hexdigest()
            result = signature == expected
            logger.debug(f"ProposalAuthenticator: verify_signature result={result}")
        except Exception as e:
            # 异常处理
            logger.error(f"ProposalAuthenticator: verify_signature failed: {e}")
            return False

        # 返回结果
        return result

    def detect_tampering(self, proposal_id: str, signer_id: str,
                         signature: str, proposal_data: str = "") -> bool:
        """检测篡改"""
        # 输入验证
        if not proposal_id or not signer_id or not signature:
            logger.debug("detect_tampering: missing required parameters")
            return True  # 缺少参数视为被篡改

        # 业务逻辑
        try:
            # 先查找存储的签名
            key = f"{proposal_id}:{signer_id}"
            stored = self.signatures.get(key)

            if stored is None:
                # 没有存储的签名，用计算方式验证
                result = not self.verify_signature(proposal_id, signer_id, signature, proposal_data)
                logger.debug(f"ProposalAuthenticator: detect_tampering (no stored sig) result={result}")
                return result

            # 比较存储的签名与提供的签名
            tampered = stored.signature != signature
            if tampered:
                logger.warning(f"ProposalAuthenticator: tampering detected for "
                              f"proposal={proposal_id[:8]}, signer={signer_id}")
            else:
                logger.debug(f"ProposalAuthenticator: no tampering detected")
        except Exception as e:
            # 异常处理
            logger.error(f"ProposalAuthenticator: detect_tampering failed: {e}")
            return True

        # 返回结果
        return tampered


class NegotiationSecurityService:
    """协商安全服务"""

    def __init__(self, secret_key: str = "default-secret-key"):
        self.access_controller = AccessController()
        self.authenticator = ProposalAuthenticator(secret_key=secret_key)
        self.policies: Dict[str, SecurityPolicy] = {}
        self.authenticated_agents: Dict[str, Dict[str, Any]] = {}
        logger.info("NegotiationSecurityService initialized")

    def create_policy(self, session_id: str = "", **kwargs) -> SecurityPolicy:
        """创建安全策略"""
        # 业务逻辑
        try:
            policy = SecurityPolicy(session_id=session_id or str(uuid.uuid4()), **kwargs)
            self.policies[policy.session_id] = policy
            logger.info(f"NegotiationSecurityService: created policy for session={policy.session_id[:8]}")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationSecurityService: create_policy failed: {e}")
            raise

        # 返回结果
        return policy

    def authenticate_agent(self, agent_id: str, credentials: Dict[str, Any] = None) -> bool:
        """认证Agent"""
        # 输入验证
        if not agent_id:
            logger.warning("authenticate_agent: agent_id is empty")
            return False

        # 业务逻辑
        try:
            # 简化的认证逻辑：检查凭证中是否包含有效token
            credentials = credentials or {}
            token = credentials.get("token", "")
            authenticated = bool(token) or not self._any_policy_requires_auth()

            if authenticated:
                self.authenticated_agents[agent_id] = {
                    "authenticated_at": time.time(),
                    "credentials": credentials,
                }
                logger.info(f"NegotiationSecurityService: agent={agent_id} authenticated")
            else:
                logger.warning(f"NegotiationSecurityService: agent={agent_id} authentication failed")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationSecurityService: authenticate_agent failed: {e}")
            return False

        # 返回结果
        return authenticated

    def _any_policy_requires_auth(self) -> bool:
        """检查是否有策略要求认证"""
        for policy in self.policies.values():
            if policy.require_authentication:
                return True
        return False

    def authorize_action(self, agent_id: str, action: str, session_id: str = "") -> bool:
        """授权操作"""
        # 输入验证
        if not agent_id or not action:
            logger.debug("authorize_action: agent_id or action is empty")
            return False

        # 业务逻辑
        try:
            # 检查是否已认证
            if agent_id not in self.authenticated_agents:
                # 如果有策略要求认证，则拒绝
                if session_id and session_id in self.policies:
                    policy = self.policies[session_id]
                    if policy.require_authentication:
                        logger.debug(f"NegotiationSecurityService: agent={agent_id} not authenticated")
                        return False

            # 检查权限
            result = self.access_controller.validate_access(agent_id, action)
            logger.debug(f"NegotiationSecurityService: authorize_action agent={agent_id}, "
                        f"action={action}, result={result}")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationSecurityService: authorize_action failed: {e}")
            return False

        # 返回结果
        return result

    def sign_proposal(self, proposal_id: str, signer_id: str, proposal_data: str = "") -> Optional[ProposalSignature]:
        """签名提案"""
        # 输入验证
        if not proposal_id or not signer_id:
            logger.warning("sign_proposal: missing proposal_id or signer_id")
            return None

        # 业务逻辑
        try:
            signature = self.authenticator.sign_proposal(proposal_id, signer_id, proposal_data)
            logger.info(f"NegotiationSecurityService: signed proposal={proposal_id[:8]}")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationSecurityService: sign_proposal failed: {e}")
            return None

        # 返回结果
        return signature

    def verify_proposal(self, proposal_id: str, signer_id: str,
                        signature: str, proposal_data: str = "") -> bool:
        """验证提案"""
        # 输入验证
        if not proposal_id or not signer_id or not signature:
            logger.debug("verify_proposal: missing required parameters")
            return False

        # 业务逻辑
        try:
            result = self.authenticator.verify_signature(
                proposal_id, signer_id, signature, proposal_data
            )
            logger.debug(f"NegotiationSecurityService: verify_proposal result={result}")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationSecurityService: verify_proposal failed: {e}")
            return False

        # 返回结果
        return result


_global_security_service: Optional[NegotiationSecurityService] = None


def get_security_service() -> NegotiationSecurityService:
    """获取全局安全服务"""
    global _global_security_service
    if _global_security_service is None:
        _global_security_service = NegotiationSecurityService()
    return _global_security_service


def reset_security_service() -> None:
    """重置全局安全服务"""
    global _global_security_service
    _global_security_service = None
