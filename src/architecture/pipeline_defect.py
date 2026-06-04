"""
测试失败缺陷回流分支
职责：缺陷检测、缺陷路由、缺陷修复跟踪

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


class DefectSeverity(str, Enum):
    """缺陷严重程度"""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


class DefectStatus(str, Enum):
    """缺陷状态"""
    DETECTED = "detected"
    ANALYZING = "analyzing"
    ASSIGNED = "assigned"
    FIXING = "fixing"
    FIXED = "fixed"
    VERIFIED = "verified"
    CLOSED = "closed"


@dataclass
class DefectRecord:
    """缺陷记录"""
    defect_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_case_id: str = ""
    severity: DefectSeverity = DefectSeverity.MAJOR
    description: str = ""
    status: DefectStatus = DefectStatus.DETECTED
    assignee: str = ""
    root_cause: str = ""
    fix_description: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"DefectRecord created: id={self.defect_id}, "
                     f"severity={self.severity.value}, status={self.status.value}")


class DefectDetector:
    """缺陷检测器"""

    def __init__(self):
        """初始化缺陷检测器"""
        self.detected_defects: Dict[str, DefectRecord] = {}
        logger.info("DefectDetector initialized")

    def detect_from_test(self, test_case_id: str = "",
                         test_result: Optional[Dict[str, Any]] = None) -> Optional[DefectRecord]:
        """从测试结果检测缺陷"""
        logger.info(f"DefectDetector: detecting from test, test_case_id={test_case_id}")
        try:
            test_result = test_result or {}

            # 仅当测试失败时才创建缺陷
            if not test_result.get("failed", False):
                logger.debug(f"DefectDetector: test {test_case_id} passed, no defect")
                return None

            description = test_result.get("error_message", f"测试用例 {test_case_id} 失败")
            severity = self.classify_severity(test_result)

            defect = DefectRecord(
                test_case_id=test_case_id,
                severity=severity,
                description=description,
                status=DefectStatus.DETECTED,
                metadata=test_result,
            )

            self.detected_defects[defect.defect_id] = defect
            logger.info(f"DefectDetector: defect detected id={defect.defect_id}, "
                        f"severity={severity.value}")
        except Exception as e:
            logger.error(f"DefectDetector: detect_from_test failed: {e}")
            return None

        return defect

    def analyze_root_cause(self, defect_id: str) -> Optional[DefectRecord]:
        """分析缺陷根因"""
        logger.info(f"DefectDetector: analyzing root cause for defect_id={defect_id}")
        if defect_id not in self.detected_defects:
            logger.warning(f"DefectDetector: defect_id={defect_id} not found")
            return None

        try:
            defect = self.detected_defects[defect_id]
            defect.status = DefectStatus.ANALYZING

            # 模拟根因分析
            metadata = defect.metadata
            if metadata.get("error_type") == "assertion":
                defect.root_cause = "断言失败：预期结果与实际结果不符"
            elif metadata.get("error_type") == "timeout":
                defect.root_cause = "超时错误：操作未在规定时间内完成"
            elif metadata.get("error_type") == "exception":
                defect.root_cause = "异常抛出：代码存在未处理的异常路径"
            else:
                defect.root_cause = "未知根因：需要进一步分析"

            defect.updated_at = time.time()
            logger.info(f"DefectDetector: root cause analyzed for defect_id={defect_id}, "
                        f"root_cause={defect.root_cause}")
        except Exception as e:
            logger.error(f"DefectDetector: analyze_root_cause failed: {e}")
            return None

        return defect

    def classify_severity(self, test_result: Dict[str, Any]) -> DefectSeverity:
        """分类缺陷严重程度"""
        logger.debug(f"DefectDetector: classifying severity")
        error_type = test_result.get("error_type", "")
        impact = test_result.get("impact", "")

        if impact == "system_down" or error_type == "crash":
            severity = DefectSeverity.BLOCKER
        elif impact == "data_loss" or error_type == "timeout":
            severity = DefectSeverity.CRITICAL
        elif impact == "feature_broken" or error_type == "assertion":
            severity = DefectSeverity.MAJOR
        elif impact == "cosmetic" or error_type == "warning":
            severity = DefectSeverity.MINOR
        else:
            severity = DefectSeverity.TRIVIAL

        logger.debug(f"DefectDetector: severity classified as {severity.value}")
        return severity


class DefectRouter:
    """缺陷路由器"""

    def __init__(self):
        """初始化缺陷路由器"""
        self.assignments: Dict[str, str] = {}  # defect_id -> agent_id
        self.fix_records: Dict[str, Dict[str, Any]] = {}
        logger.info("DefectRouter initialized")

    def route_to_agent(self, defect: DefectRecord,
                       agent_id: str = "") -> bool:
        """将缺陷路由到指定Agent"""
        logger.info(f"DefectRouter: routing defect id={defect.defect_id} "
                    f"to agent={agent_id}")
        try:
            if not agent_id:
                # 根据严重程度自动路由
                if defect.severity in (DefectSeverity.BLOCKER, DefectSeverity.CRITICAL):
                    agent_id = "senior_dev_agent"
                elif defect.severity == DefectSeverity.MAJOR:
                    agent_id = "dev_agent"
                else:
                    agent_id = "junior_dev_agent"

            defect.assignee = agent_id
            defect.status = DefectStatus.ASSIGNED
            defect.updated_at = time.time()
            self.assignments[defect.defect_id] = agent_id
            logger.info(f"DefectRouter: defect id={defect.defect_id} "
                        f"routed to agent={agent_id}")
        except Exception as e:
            logger.error(f"DefectRouter: route_to_agent failed: {e}")
            return False

        return True

    def track_fix(self, defect_id: str, fix_description: str = "",
                  agent_id: str = "") -> bool:
        """跟踪缺陷修复"""
        logger.info(f"DefectRouter: tracking fix for defect_id={defect_id}")
        if defect_id not in self.assignments:
            logger.warning(f"DefectRouter: defect_id={defect_id} not assigned")
            return False

        try:
            self.fix_records[defect_id] = {
                "fix_description": fix_description,
                "agent_id": agent_id or self.assignments.get(defect_id, ""),
                "fixed_at": time.time(),
            }
            logger.info(f"DefectRouter: fix tracked for defect_id={defect_id}")
        except Exception as e:
            logger.error(f"DefectRouter: track_fix failed: {e}")
            return False

        return True

    def verify_fix(self, defect: DefectRecord,
                   verification_result: bool = False) -> bool:
        """验证缺陷修复"""
        logger.info(f"DefectRouter: verifying fix for defect_id={defect.defect_id}, "
                    f"result={verification_result}")
        try:
            if verification_result:
                defect.status = DefectStatus.VERIFIED
                defect.fix_description = self.fix_records.get(
                    defect.defect_id, {}
                ).get("fix_description", "")
            else:
                defect.status = DefectStatus.FIXING
            defect.updated_at = time.time()
            logger.info(f"DefectRouter: fix verified for defect_id={defect.defect_id}, "
                        f"status={defect.status.value}")
        except Exception as e:
            logger.error(f"DefectRouter: verify_fix failed: {e}")
            return False

        return True

    def escalate(self, defect: DefectRecord,
                 target_severity: DefectSeverity = DefectSeverity.CRITICAL) -> bool:
        """升级缺陷严重程度"""
        logger.info(f"DefectRouter: escalating defect id={defect.defect_id} "
                    f"to severity={target_severity.value}")
        try:
            severity_order = [
                DefectSeverity.TRIVIAL,
                DefectSeverity.MINOR,
                DefectSeverity.MAJOR,
                DefectSeverity.CRITICAL,
                DefectSeverity.BLOCKER,
            ]
            current_idx = severity_order.index(defect.severity)
            target_idx = severity_order.index(target_severity)

            if target_idx > current_idx:
                defect.severity = target_severity
                defect.updated_at = time.time()
                logger.info(f"DefectRouter: defect id={defect.defect_id} "
                            f"escalated to {target_severity.value}")
            else:
                logger.info(f"DefectRouter: defect id={defect.defect_id} "
                            f"already at equal or higher severity")
        except Exception as e:
            logger.error(f"DefectRouter: escalate failed: {e}")
            return False

        return True


class DefectPipeline:
    """缺陷回流流水线"""

    def __init__(self):
        """初始化缺陷回流流水线"""
        self.detector = DefectDetector()
        self.router = DefectRouter()
        self.defects: Dict[str, DefectRecord] = {}
        logger.info("DefectPipeline initialized")

    def process_defect(self, test_case_id: str = "",
                       test_result: Optional[Dict[str, Any]] = None,
                       agent_id: str = "") -> Optional[DefectRecord]:
        """处理缺陷：检测→分析→路由"""
        logger.info(f"DefectPipeline: processing defect for test_case_id={test_case_id}")
        try:
            # 1. 检测缺陷
            defect = self.detector.detect_from_test(test_case_id, test_result)
            if defect is None:
                logger.info("DefectPipeline: no defect detected")
                return None

            # 2. 分析根因
            defect = self.detector.analyze_root_cause(defect.defect_id)
            if defect is None:
                logger.warning("DefectPipeline: root cause analysis failed")
                return defect

            # 3. 路由到Agent
            self.router.route_to_agent(defect, agent_id)

            self.defects[defect.defect_id] = defect
            logger.info(f"DefectPipeline: defect processed id={defect.defect_id}, "
                        f"status={defect.status.value}, assignee={defect.assignee}")
        except Exception as e:
            logger.error(f"DefectPipeline: process_defect failed: {e}")
            raise

        return defect

    def get_defect_status(self, defect_id: str) -> Optional[Dict[str, Any]]:
        """获取缺陷状态"""
        logger.debug(f"DefectPipeline: getting defect status for id={defect_id}")
        defect = self.defects.get(defect_id)
        if defect is None:
            logger.warning(f"DefectPipeline: defect id={defect_id} not found")
            return None

        return {
            "defect_id": defect.defect_id,
            "status": defect.status.value,
            "severity": defect.severity.value,
            "assignee": defect.assignee,
            "root_cause": defect.root_cause,
        }

    def get_defect_metrics(self) -> Dict[str, Any]:
        """获取缺陷指标"""
        logger.debug("DefectPipeline: getting defect metrics")
        total = len(self.defects)
        if total == 0:
            return {
                "total": 0,
                "by_severity": {},
                "by_status": {},
                "fix_rate": 0.0,
            }

        by_severity: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        fixed_count = 0

        for defect in self.defects.values():
            sev_key = defect.severity.value
            by_severity[sev_key] = by_severity.get(sev_key, 0) + 1

            status_key = defect.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1

            if defect.status in (DefectStatus.FIXED, DefectStatus.VERIFIED, DefectStatus.CLOSED):
                fixed_count += 1

        fix_rate = round(fixed_count / total, 4) if total > 0 else 0.0

        metrics = {
            "total": total,
            "by_severity": by_severity,
            "by_status": by_status,
            "fix_rate": fix_rate,
        }
        logger.debug(f"DefectPipeline: metrics computed, total={total}, "
                     f"fix_rate={fix_rate}")
        return metrics
