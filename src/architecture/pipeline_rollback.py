"""
评审失败回退重改分支
职责：检查点管理、回退操作、修订跟踪

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RollbackReason(str, Enum):
    """回退原因"""
    REVIEW_FAILED = "review_failed"
    TEST_FAILED = "test_failed"
    BUILD_FAILED = "build_failed"
    MANUAL = "manual"


class RollbackStatus(str, Enum):
    """回退状态"""
    PENDING = "pending"
    ROLLING_BACK = "rolling_back"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RollbackPoint:
    """回退检查点"""
    point_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    snapshot: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"RollbackPoint created: id={self.point_id}, "
                     f"description={self.description}")


@dataclass
class RollbackAction:
    """回退操作记录"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reason: RollbackReason = RollbackReason.MANUAL
    from_point: str = ""
    to_point: str = ""
    status: RollbackStatus = RollbackStatus.PENDING
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"RollbackAction created: id={self.action_id}, "
                     f"reason={self.reason.value}, status={self.status.value}")


class RollbackManager:
    """回退管理器"""

    def __init__(self):
        """初始化回退管理器"""
        self.checkpoints: Dict[str, RollbackPoint] = {}
        self.actions: Dict[str, RollbackAction] = {}
        self.current_point_id: Optional[str] = None
        logger.info("RollbackManager initialized")

    def create_checkpoint(self, description: str = "",
                          snapshot: Optional[Dict[str, Any]] = None) -> RollbackPoint:
        """创建检查点"""
        logger.info(f"RollbackManager: creating checkpoint, description={description}")
        try:
            point = RollbackPoint(
                description=description,
                snapshot=snapshot or {},
            )
            self.checkpoints[point.point_id] = point
            self.current_point_id = point.point_id
            logger.info(f"RollbackManager: checkpoint created id={point.point_id}")
        except Exception as e:
            logger.error(f"RollbackManager: create_checkpoint failed: {e}")
            raise

        return point

    def rollback(self, to_point_id: str,
                 reason: RollbackReason = RollbackReason.MANUAL) -> Optional[RollbackAction]:
        """执行回退"""
        logger.info(f"RollbackManager: rolling back to point_id={to_point_id}, "
                    f"reason={reason.value}")
        if to_point_id not in self.checkpoints:
            logger.warning(f"RollbackManager: point_id={to_point_id} not found")
            return None

        if self.current_point_id is None:
            logger.warning("RollbackManager: no current point, cannot rollback")
            return None

        try:
            action = RollbackAction(
                reason=reason,
                from_point=self.current_point_id,
                to_point=to_point_id,
                status=RollbackStatus.ROLLING_BACK,
            )

            # 模拟回退操作
            target_point = self.checkpoints[to_point_id]
            self.current_point_id = to_point_id
            action.status = RollbackStatus.COMPLETED

            self.actions[action.action_id] = action
            logger.info(f"RollbackManager: rollback completed, action_id={action.action_id}, "
                        f"from={action.from_point}, to={action.to_point}")
        except Exception as e:
            logger.error(f"RollbackManager: rollback failed: {e}")
            action.status = RollbackStatus.FAILED
            self.actions[action.action_id] = action
            return action

        return action

    def get_checkpoint(self, point_id: str) -> Optional[RollbackPoint]:
        """获取检查点"""
        logger.debug(f"RollbackManager: getting checkpoint id={point_id}")
        point = self.checkpoints.get(point_id)
        if point is None:
            logger.warning(f"RollbackManager: checkpoint id={point_id} not found")
        return point

    def list_checkpoints(self) -> List[RollbackPoint]:
        """列出所有检查点"""
        logger.debug("RollbackManager: listing checkpoints")
        points = list(self.checkpoints.values())
        logger.debug(f"RollbackManager: found {len(points)} checkpoints")
        return points


class RevisionHandler:
    """修订处理器"""

    def __init__(self):
        """初始化修订处理器"""
        self.revision_plans: Dict[str, Dict[str, Any]] = {}
        self.revision_tracks: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("RevisionHandler initialized")

    def handle_review_failure(self, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理评审失败"""
        logger.info("RevisionHandler: handling review failure")
        try:
            plan = self.create_revision_plan(
                reason=RollbackReason.REVIEW_FAILED,
                details=review_result,
            )
            findings = review_result.get("findings", [])
            plan["focus_areas"] = [f.get("area", "unknown") for f in findings]
            plan["priority"] = "high"
            logger.info(f"RevisionHandler: review failure handled, "
                        f"plan_id={plan['plan_id']}")
        except Exception as e:
            logger.error(f"RevisionHandler: handle_review_failure failed: {e}")
            plan = {"plan_id": str(uuid.uuid4()), "error": str(e)}

        return plan

    def handle_test_failure(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理测试失败"""
        logger.info("RevisionHandler: handling test failure")
        try:
            plan = self.create_revision_plan(
                reason=RollbackReason.TEST_FAILED,
                details=test_result,
            )
            failed_tests = test_result.get("failed_tests", [])
            plan["affected_modules"] = [t.get("module", "unknown") for t in failed_tests]
            plan["priority"] = "critical"
            logger.info(f"RevisionHandler: test failure handled, "
                        f"plan_id={plan['plan_id']}")
        except Exception as e:
            logger.error(f"RevisionHandler: handle_test_failure failed: {e}")
            plan = {"plan_id": str(uuid.uuid4()), "error": str(e)}

        return plan

    def create_revision_plan(self, reason: RollbackReason = RollbackReason.MANUAL,
                             details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建修订计划"""
        logger.info(f"RevisionHandler: creating revision plan, reason={reason.value}")
        try:
            plan_id = str(uuid.uuid4())
            plan = {
                "plan_id": plan_id,
                "reason": reason.value,
                "details": details or {},
                "created_at": time.time(),
                "status": "pending",
                "focus_areas": [],
                "priority": "medium",
            }
            self.revision_plans[plan_id] = plan
            self.revision_tracks[plan_id] = []
            logger.info(f"RevisionHandler: revision plan created id={plan_id}")
        except Exception as e:
            logger.error(f"RevisionHandler: create_revision_plan failed: {e}")
            raise

        return plan

    def track_revision(self, plan_id: str, revision_info: Dict[str, Any]) -> bool:
        """跟踪修订进度"""
        logger.info(f"RevisionHandler: tracking revision for plan_id={plan_id}")
        if plan_id not in self.revision_plans:
            logger.warning(f"RevisionHandler: plan_id={plan_id} not found")
            return False

        try:
            track_entry = {
                "timestamp": time.time(),
                "info": revision_info,
            }
            self.revision_tracks[plan_id].append(track_entry)

            # 更新计划状态
            status = revision_info.get("status", "in_progress")
            self.revision_plans[plan_id]["status"] = status
            logger.info(f"RevisionHandler: revision tracked for plan_id={plan_id}, "
                        f"status={status}")
        except Exception as e:
            logger.error(f"RevisionHandler: track_revision failed: {e}")
            return False

        return True


class RollbackPipeline:
    """回退流水线"""

    def __init__(self):
        """初始化回退流水线"""
        self.manager = RollbackManager()
        self.handler = RevisionHandler()
        self.failure_records: Dict[str, Dict[str, Any]] = {}
        logger.info("RollbackPipeline initialized")

    def process_failure(self, reason: RollbackReason,
                        failure_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理失败：创建修订计划并执行回退"""
        logger.info(f"RollbackPipeline: processing failure, reason={reason.value}")
        try:
            failure_id = str(uuid.uuid4())
            failure_data = failure_data or {}

            # 根据失败原因创建修订计划
            if reason == RollbackReason.REVIEW_FAILED:
                revision_plan = self.handler.handle_review_failure(failure_data)
            elif reason == RollbackReason.TEST_FAILED:
                revision_plan = self.handler.handle_test_failure(failure_data)
            else:
                revision_plan = self.handler.create_revision_plan(reason, failure_data)

            # 尝试回退到上一个检查点
            rollback_action = None
            checkpoints = self.manager.list_checkpoints()
            if len(checkpoints) > 1:
                # 回退到倒数第二个检查点（排除当前点）
                sorted_points = sorted(checkpoints, key=lambda p: p.timestamp)
                if len(sorted_points) >= 2:
                    target_point = sorted_points[-2]
                    rollback_action = self.manager.rollback(
                        target_point.point_id, reason
                    )

            result = {
                "failure_id": failure_id,
                "reason": reason.value,
                "revision_plan": revision_plan,
                "rollback_action": rollback_action,
            }
            self.failure_records[failure_id] = result
            logger.info(f"RollbackPipeline: failure processed, failure_id={failure_id}")
        except Exception as e:
            logger.error(f"RollbackPipeline: process_failure failed: {e}")
            raise

        return result

    def get_rollback_status(self, failure_id: str) -> Optional[Dict[str, Any]]:
        """获取回退状态"""
        logger.debug(f"RollbackPipeline: getting rollback status for failure_id={failure_id}")
        record = self.failure_records.get(failure_id)
        if record is None:
            logger.warning(f"RollbackPipeline: failure_id={failure_id} not found")
        return record
