"""
需求接收→拆解链路
职责：需求接收、验证、优先级拆解、领域拆解、子任务估算
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class RequirementPriority(str, Enum):
    """需求优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementStatus(str, Enum):
    """需求状态"""
    RECEIVED = "received"
    ANALYZING = "analyzing"
    DECOMPOSED = "decomposed"
    FAILED = "failed"


@dataclass
class Requirement:
    """需求实体"""
    req_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    priority: RequirementPriority = RequirementPriority.MEDIUM
    status: RequirementStatus = RequirementStatus.RECEIVED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"Requirement created: id={self.req_id[:8]}, title={self.title[:20]}")


@dataclass
class DecompositionResult:
    """拆解结果"""
    req_id: str = ""
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    decomposition_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"DecompositionResult created: req_id={self.req_id[:8] if self.req_id else 'N/A'}, subtasks={len(self.subtasks)}")


class RequirementReceiver:
    """需求接收器"""

    def __init__(self):
        self._requirements: Dict[str, Requirement] = {}
        logger.info("RequirementReceiver initialized")

    def receive_requirement(self, title: str, description: str = "",
                            priority: RequirementPriority = RequirementPriority.MEDIUM,
                            metadata: Optional[Dict[str, Any]] = None) -> Requirement:
        """接收新需求"""
        # 输入验证
        if not title or not title.strip():
            logger.warning("receive_requirement: title is empty")
            raise ValueError("需求标题不能为空")

        # 业务逻辑
        try:
            requirement = Requirement(
                title=title.strip(),
                description=description,
                priority=priority,
                status=RequirementStatus.RECEIVED,
                metadata=metadata or {},
            )
            self._requirements[requirement.req_id] = requirement
            logger.info(f"RequirementReceiver: received requirement id={requirement.req_id[:8]}, title={title[:20]}")
        except Exception as e:
            # 异常处理
            logger.error(f"RequirementReceiver: receive_requirement failed: {e}")
            raise

        # 返回结果
        return requirement

    def validate_requirement(self, req_id: str) -> bool:
        """验证需求是否有效"""
        # 输入验证
        if not req_id:
            logger.warning("validate_requirement: req_id is empty")
            return False

        # 业务逻辑
        if req_id not in self._requirements:
            logger.debug(f"validate_requirement: req_id={req_id[:8]} not found")
            return False

        req = self._requirements[req_id]
        is_valid = bool(req.title and req.title.strip())
        logger.debug(f"validate_requirement: req_id={req_id[:8]}, valid={is_valid}")

        # 返回结果
        return is_valid

    def get_requirements(self, priority: Optional[RequirementPriority] = None,
                         status: Optional[RequirementStatus] = None) -> List[Requirement]:
        """获取需求列表"""
        # 业务逻辑
        try:
            result = list(self._requirements.values())
            if priority is not None:
                result = [r for r in result if r.priority == priority]
            if status is not None:
                result = [r for r in result if r.status == status]
            logger.debug(f"RequirementReceiver: get_requirements returned {len(result)} items")
        except Exception as e:
            # 异常处理
            logger.error(f"RequirementReceiver: get_requirements failed: {e}")
            return []

        # 返回结果
        return result


class RequirementDecomposer:
    """需求拆解器"""

    def __init__(self):
        self._domain_keywords: Dict[str, List[str]] = {
            "frontend": ["ui", "界面", "页面", "组件", "视图", "display", "view", "component"],
            "backend": ["api", "接口", "服务", "逻辑", "controller", "service", "route"],
            "database": ["数据", "存储", "查询", "模型", "database", "model", "repository"],
            "infra": ["部署", "运维", "监控", "配置", "deploy", "monitor", "config"],
        }
        logger.info("RequirementDecomposer initialized")

    def decompose(self, requirement: Requirement) -> DecompositionResult:
        """拆解需求为子任务列表"""
        # 输入验证
        if not requirement or not requirement.req_id:
            logger.warning("decompose: invalid requirement")
            raise ValueError("无效的需求对象")

        # 业务逻辑
        start_time = time.time()
        try:
            # 更新状态为分析中
            requirement.status = RequirementStatus.ANALYZING

            # 按优先级拆解
            priority_subtasks = self._split_by_priority(requirement)

            # 按领域拆解
            domain_subtasks = self._split_by_domain(requirement)

            # 合并子任务
            subtasks = priority_subtasks + domain_subtasks

            # 如果没有拆解出子任务，生成默认子任务
            if not subtasks:
                estimated = self._estimate_subtasks(requirement)
                subtasks = [{
                    "subtask_id": str(uuid.uuid4()),
                    "title": f"实现: {requirement.title}",
                    "domain": "general",
                    "priority": requirement.priority.value,
                    "estimated_effort": estimated,
                }]

            # 计算拆解耗时
            decomposition_time = time.time() - start_time

            # 更新状态为已拆解
            requirement.status = RequirementStatus.DECOMPOSED

            result = DecompositionResult(
                req_id=requirement.req_id,
                subtasks=subtasks,
                decomposition_time=decomposition_time,
                metadata={
                    "original_priority": requirement.priority.value,
                    "subtask_count": len(subtasks),
                },
            )
            logger.info(f"RequirementDecomposer: decomposed req_id={requirement.req_id[:8]}, "
                       f"subtasks={len(subtasks)}, time={decomposition_time:.4f}s")
        except Exception as e:
            # 异常处理
            requirement.status = RequirementStatus.FAILED
            logger.error(f"RequirementDecomposer: decompose failed: {e}")
            result = DecompositionResult(
                req_id=requirement.req_id,
                metadata={"error": str(e)},
            )

        # 返回结果
        return result

    def _split_by_priority(self, requirement: Requirement) -> List[Dict[str, Any]]:
        """按优先级拆解需求"""
        logger.debug(f"_split_by_priority: req_id={requirement.req_id[:8]}, priority={requirement.priority.value}")
        subtasks = []

        if requirement.priority == RequirementPriority.CRITICAL:
            subtasks.append({
                "subtask_id": str(uuid.uuid4()),
                "title": f"[紧急] 核心功能: {requirement.title}",
                "domain": "core",
                "priority": "critical",
                "estimated_effort": 8.0,
            })
            subtasks.append({
                "subtask_id": str(uuid.uuid4()),
                "title": f"[紧急] 验证与回滚: {requirement.title}",
                "domain": "testing",
                "priority": "critical",
                "estimated_effort": 4.0,
            })
        elif requirement.priority == RequirementPriority.HIGH:
            subtasks.append({
                "subtask_id": str(uuid.uuid4()),
                "title": f"[高优] 主要功能: {requirement.title}",
                "domain": "core",
                "priority": "high",
                "estimated_effort": 6.0,
            })
            subtasks.append({
                "subtask_id": str(uuid.uuid4()),
                "title": f"[高优] 辅助功能: {requirement.title}",
                "domain": "support",
                "priority": "high",
                "estimated_effort": 3.0,
            })

        logger.debug(f"_split_by_priority: generated {len(subtasks)} subtasks")
        return subtasks

    def _split_by_domain(self, requirement: Requirement) -> List[Dict[str, Any]]:
        """按领域拆解需求"""
        logger.debug(f"_split_by_domain: req_id={requirement.req_id[:8]}")
        subtasks = []
        text = (requirement.title + " " + requirement.description).lower()

        for domain, keywords in self._domain_keywords.items():
            if any(kw in text for kw in keywords):
                subtasks.append({
                    "subtask_id": str(uuid.uuid4()),
                    "title": f"[{domain}] {requirement.title}",
                    "domain": domain,
                    "priority": requirement.priority.value,
                    "estimated_effort": 4.0,
                })

        logger.debug(f"_split_by_domain: generated {len(subtasks)} subtasks")
        return subtasks

    def _estimate_subtasks(self, requirement: Requirement) -> float:
        """估算子任务工作量"""
        logger.debug(f"_estimate_subtasks: req_id={requirement.req_id[:8]}")
        base_effort = 2.0
        desc_length = len(requirement.description)

        if desc_length > 500:
            base_effort = 8.0
        elif desc_length > 200:
            base_effort = 5.0
        elif desc_length > 50:
            base_effort = 3.0

        if requirement.priority in (RequirementPriority.CRITICAL, RequirementPriority.HIGH):
            base_effort *= 1.5

        logger.debug(f"_estimate_subtasks: estimated effort={base_effort}")
        return base_effort


class RequirementPipeline:
    """需求接收→拆解链路"""

    def __init__(self):
        self.receiver = RequirementReceiver()
        self.decomposer = RequirementDecomposer()
        self._results: Dict[str, DecompositionResult] = {}
        logger.info("RequirementPipeline initialized")

    def process(self, title: str, description: str = "",
                priority: RequirementPriority = RequirementPriority.MEDIUM,
                metadata: Optional[Dict[str, Any]] = None) -> DecompositionResult:
        """处理需求：接收→验证→拆解"""
        # 业务逻辑
        try:
            # 1. 接收需求
            requirement = self.receiver.receive_requirement(
                title=title,
                description=description,
                priority=priority,
                metadata=metadata,
            )
            logger.info(f"RequirementPipeline: received req_id={requirement.req_id[:8]}")

            # 2. 验证需求
            if not self.receiver.validate_requirement(requirement.req_id):
                logger.warning(f"RequirementPipeline: validation failed for req_id={requirement.req_id[:8]}")
                return DecompositionResult(
                    req_id=requirement.req_id,
                    metadata={"error": "需求验证失败"},
                )

            # 3. 拆解需求
            result = self.decomposer.decompose(requirement)
            self._results[requirement.req_id] = result
            logger.info(f"RequirementPipeline: processed req_id={requirement.req_id[:8]}, "
                       f"subtasks={len(result.subtasks)}")
        except Exception as e:
            # 异常处理
            logger.error(f"RequirementPipeline: process failed: {e}")
            return DecompositionResult(metadata={"error": str(e)})

        # 返回结果
        return result

    def get_status(self, req_id: str) -> Optional[Dict[str, Any]]:
        """获取需求处理状态"""
        # 输入验证
        if not req_id:
            logger.warning("get_status: req_id is empty")
            return None

        # 业务逻辑
        requirements = self.receiver.get_requirements()
        req = next((r for r in requirements if r.req_id == req_id), None)

        if req is None:
            logger.debug(f"get_status: req_id={req_id[:8]} not found")
            return None

        result = self._results.get(req_id)
        status_info = {
            "req_id": req.req_id,
            "title": req.title,
            "priority": req.priority.value,
            "status": req.status.value,
            "has_result": result is not None,
            "subtask_count": len(result.subtasks) if result else 0,
        }
        logger.debug(f"get_status: req_id={req_id[:8]}, status={req.status.value}")

        # 返回结果
        return status_info
