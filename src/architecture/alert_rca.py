"""
智能告警与根因分析模块

职责：管理告警生命周期、关联告警分析、根因追溯、生成RCA报告

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """告警严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """告警状态"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """告警"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: AlertSeverity = AlertSeverity.INFO
    status: AlertStatus = AlertStatus.ACTIVE
    source: str = ""
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"Alert created: alert_id={self.alert_id}, "
                     f"severity={self.severity.value}, source={self.source}")


@dataclass
class RootCause:
    """根因"""
    cause_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str = ""
    category: str = ""
    description: str = ""
    confidence: float = 0.0
    remediation: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"RootCause created: cause_id={self.cause_id}, "
                     f"alert_id={self.alert_id}, confidence={self.confidence}")


class AlertManager:
    """告警管理器"""

    def __init__(self):
        """初始化告警管理器"""
        self._alerts: Dict[str, Alert] = {}
        logger.info("AlertManager initialized")

    def create_alert(self, severity: AlertSeverity, source: str,
                     message: str, metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """创建告警"""
        logger.info(f"AlertManager: creating alert, "
                    f"severity={severity.value}, source={source}")
        try:
            alert = Alert(
                severity=severity,
                source=source,
                message=message,
                metadata=metadata or {},
            )
            self._alerts[alert.alert_id] = alert
            logger.info(f"AlertManager: alert created, "
                        f"alert_id={alert.alert_id}")
        except Exception as e:
            logger.error(f"AlertManager: create_alert failed: {e}")
            alert = Alert(severity=severity, source=source, message=message)
        return alert

    def acknowledge(self, alert_id: str) -> Optional[Alert]:
        """确认告警"""
        logger.info(f"AlertManager: acknowledging alert, alert_id={alert_id}")
        alert = self._alerts.get(alert_id)
        if alert is None:
            logger.warning(f"AlertManager: alert_id={alert_id} not found")
            return None
        alert.status = AlertStatus.ACKNOWLEDGED
        logger.info(f"AlertManager: alert acknowledged, alert_id={alert_id}")
        return alert

    def resolve(self, alert_id: str) -> Optional[Alert]:
        """解决告警"""
        logger.info(f"AlertManager: resolving alert, alert_id={alert_id}")
        alert = self._alerts.get(alert_id)
        if alert is None:
            logger.warning(f"AlertManager: alert_id={alert_id} not found")
            return None
        alert.status = AlertStatus.RESOLVED
        logger.info(f"AlertManager: alert resolved, alert_id={alert_id}")
        return alert

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        logger.debug("AlertManager: getting active alerts")
        active = [a for a in self._alerts.values()
                  if a.status == AlertStatus.ACTIVE]
        logger.debug(f"AlertManager: found {len(active)} active alerts")
        return active

    def suppress(self, alert_id: str) -> Optional[Alert]:
        """抑制告警"""
        logger.info(f"AlertManager: suppressing alert, alert_id={alert_id}")
        alert = self._alerts.get(alert_id)
        if alert is None:
            logger.warning(f"AlertManager: alert_id={alert_id} not found")
            return None
        alert.status = AlertStatus.SUPPRESSED
        logger.info(f"AlertManager: alert suppressed, alert_id={alert_id}")
        return alert


class RootCauseAnalyzer:
    """根因分析器"""

    def __init__(self):
        """初始化根因分析器"""
        self._root_causes: Dict[str, RootCause] = {}
        logger.info("RootCauseAnalyzer initialized")

    def analyze(self, alerts: List[Alert]) -> List[RootCause]:
        """分析告警列表，生成根因"""
        logger.info(f"RootCauseAnalyzer: analyzing {len(alerts)} alerts")
        try:
            if not alerts:
                logger.debug("RootCauseAnalyzer: no alerts to analyze")
                return []

            # 1. 关联告警
            correlated = self._correlate_alerts(alerts)
            # 2. 追溯因果
            causal_chains = self._trace_causality(correlated)
            # 3. 识别根因
            root_causes = self._identify_root(causal_chains, alerts)

            for rc in root_causes:
                self._root_causes[rc.cause_id] = rc

            logger.info(f"RootCauseAnalyzer: found {len(root_causes)} root causes")
        except Exception as e:
            logger.error(f"RootCauseAnalyzer: analyze failed: {e}")
            root_causes = []
        return root_causes

    def _correlate_alerts(self, alerts: List[Alert]) -> Dict[str, List[Alert]]:
        """关联告警"""
        logger.debug(f"RootCauseAnalyzer: correlating {len(alerts)} alerts")
        try:
            groups: Dict[str, List[Alert]] = {}
            for alert in alerts:
                key = alert.source
                if key not in groups:
                    groups[key] = []
                groups[key].append(alert)
            logger.debug(f"RootCauseAnalyzer: found {len(groups)} correlation groups")
        except Exception as e:
            logger.error(f"RootCauseAnalyzer: _correlate_alerts failed: {e}")
            groups = {}
        return groups

    def _trace_causality(self, groups: Dict[str, List[Alert]]) -> List[Dict[str, Any]]:
        """追溯因果关系"""
        logger.debug(f"RootCauseAnalyzer: tracing causality for {len(groups)} groups")
        try:
            chains: List[Dict[str, Any]] = []
            for source, group_alerts in groups.items():
                # 按严重级别排序，最严重的可能是根因
                sorted_alerts = sorted(
                    group_alerts,
                    key=lambda a: list(AlertSeverity).index(a.severity),
                    reverse=True,
                )
                chains.append({
                    "source": source,
                    "alerts": sorted_alerts,
                    "potential_root": sorted_alerts[0] if sorted_alerts else None,
                })
            logger.debug(f"RootCauseAnalyzer: traced {len(chains)} causal chains")
        except Exception as e:
            logger.error(f"RootCauseAnalyzer: _trace_causality failed: {e}")
            chains = []
        return chains

    def _identify_root(self, chains: List[Dict[str, Any]],
                       alerts: List[Alert]) -> List[RootCause]:
        """识别根因"""
        logger.debug(f"RootCauseAnalyzer: identifying root causes from {len(chains)} chains")
        try:
            root_causes: List[RootCause] = []
            for chain in chains:
                potential_root = chain.get("potential_root")
                if potential_root is None:
                    continue

                # 根据严重级别和关联数量计算置信度
                severity_weight = {
                    AlertSeverity.CRITICAL: 0.9,
                    AlertSeverity.ERROR: 0.7,
                    AlertSeverity.WARNING: 0.5,
                    AlertSeverity.INFO: 0.3,
                }
                confidence = severity_weight.get(potential_root.severity, 0.3)
                related_count = len(chain.get("alerts", []))
                if related_count > 1:
                    confidence = min(1.0, confidence + 0.1)

                category = f"{chain['source']}_failure"
                description = f"根因: {potential_root.source} - {potential_root.message}"
                remediation = f"建议检查 {potential_root.source} 相关配置和资源"

                rc = RootCause(
                    alert_id=potential_root.alert_id,
                    category=category,
                    description=description,
                    confidence=round(confidence, 2),
                    remediation=remediation,
                )
                root_causes.append(rc)

            logger.debug(f"RootCauseAnalyzer: identified {len(root_causes)} root causes")
        except Exception as e:
            logger.error(f"RootCauseAnalyzer: _identify_root failed: {e}")
            root_causes = []
        return root_causes

    def generate_rca_report(self, root_causes: List[RootCause]) -> Dict[str, Any]:
        """生成RCA报告"""
        logger.info(f"RootCauseAnalyzer: generating RCA report, "
                    f"root_causes={len(root_causes)}")
        try:
            if not root_causes:
                return {"message": "暂无根因分析数据"}

            report: Dict[str, Any] = {
                "total_root_causes": len(root_causes),
                "root_causes": [
                    {
                        "cause_id": rc.cause_id,
                        "alert_id": rc.alert_id,
                        "category": rc.category,
                        "description": rc.description,
                        "confidence": rc.confidence,
                        "remediation": rc.remediation,
                    }
                    for rc in root_causes
                ],
                "highest_confidence": max(rc.confidence for rc in root_causes),
                "timestamp": time.time(),
            }
            logger.info(f"RootCauseAnalyzer: RCA report generated")
        except Exception as e:
            logger.error(f"RootCauseAnalyzer: generate_rca_report failed: {e}")
            report = {"error": str(e)}
        return report


class AlertRCAService:
    """告警与根因分析服务"""

    def __init__(self, alert_manager: Optional[AlertManager] = None,
                 rca_analyzer: Optional[RootCauseAnalyzer] = None):
        """初始化告警与根因分析服务"""
        self.alert_manager = alert_manager or AlertManager()
        self.rca_analyzer = rca_analyzer or RootCauseAnalyzer()
        self._rca_results: Dict[str, List[RootCause]] = {}
        logger.info("AlertRCAService initialized")

    def process_alert(self, severity: AlertSeverity, source: str,
                      message: str, metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """处理告警：创建告警并触发根因分析"""
        logger.info(f"AlertRCAService: processing alert, "
                    f"severity={severity.value}, source={source}")
        try:
            alert = self.alert_manager.create_alert(severity, source, message, metadata)
            # 触发根因分析
            active_alerts = self.alert_manager.get_active_alerts()
            root_causes = self.rca_analyzer.analyze(active_alerts)
            if root_causes:
                self._rca_results[alert.alert_id] = root_causes
            logger.info(f"AlertRCAService: alert processed, "
                        f"alert_id={alert.alert_id}, "
                        f"root_causes={len(root_causes)}")
        except Exception as e:
            logger.error(f"AlertRCAService: process_alert failed: {e}")
            alert = Alert(severity=severity, source=source, message=message)
        return alert

    def get_alerts(self, status: Optional[AlertStatus] = None) -> List[Alert]:
        """获取告警列表"""
        logger.debug(f"AlertRCAService: getting alerts, status={status}")
        if status is not None:
            return [a for a in self.alert_manager._alerts.values()
                    if a.status == status]
        return list(self.alert_manager._alerts.values())

    def get_rca(self, alert_id: str) -> Optional[List[RootCause]]:
        """获取根因分析结果"""
        logger.debug(f"AlertRCAService: getting RCA, alert_id={alert_id}")
        return self._rca_results.get(alert_id)
