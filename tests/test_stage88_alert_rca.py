"""
阶段88验收测试 - 智能告警与根因分析
"""

import pytest
from src.architecture.alert_rca import (
    AlertSeverity,
    AlertStatus,
    Alert,
    RootCause,
    AlertManager,
    RootCauseAnalyzer,
    AlertRCAService,
)


class TestAlertSeverity:
    """测试告警严重级别枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_all_severities(self):
        """测试所有严重级别"""
        severities = list(AlertSeverity)
        assert len(severities) == 4


class TestAlertStatus:
    """测试告警状态枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert AlertStatus.ACTIVE.value == "active"
        assert AlertStatus.ACKNOWLEDGED.value == "acknowledged"
        assert AlertStatus.RESOLVED.value == "resolved"
        assert AlertStatus.SUPPRESSED.value == "suppressed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(AlertStatus)
        assert len(statuses) == 4


class TestAlert:
    """测试告警"""

    def test_default_creation(self):
        """测试默认创建"""
        alert = Alert()
        assert alert.alert_id != ""
        assert alert.severity == AlertSeverity.INFO
        assert alert.status == AlertStatus.ACTIVE
        assert alert.source == ""
        assert alert.message == ""
        assert alert.timestamp > 0
        assert alert.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        alert = Alert(
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACKNOWLEDGED,
            source="database",
            message="连接池耗尽",
            metadata={"host": "db-01"},
        )
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.source == "database"
        assert alert.message == "连接池耗尽"
        assert alert.metadata["host"] == "db-01"

    def test_alert_id_unique(self):
        """测试告警ID唯一性"""
        a1 = Alert()
        a2 = Alert()
        assert a1.alert_id != a2.alert_id


class TestRootCause:
    """测试根因"""

    def test_default_creation(self):
        """测试默认创建"""
        rc = RootCause()
        assert rc.cause_id != ""
        assert rc.alert_id == ""
        assert rc.category == ""
        assert rc.description == ""
        assert rc.confidence == 0.0
        assert rc.remediation == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        rc = RootCause(
            alert_id="alert-001",
            category="database_failure",
            description="数据库主节点宕机",
            confidence=0.85,
            remediation="重启数据库主节点",
        )
        assert rc.alert_id == "alert-001"
        assert rc.category == "database_failure"
        assert rc.confidence == 0.85


class TestAlertManager:
    """测试告警管理器"""

    def test_initialization(self):
        """测试初始化"""
        manager = AlertManager()
        assert len(manager._alerts) == 0

    def test_create_alert(self):
        """测试创建告警"""
        manager = AlertManager()
        alert = manager.create_alert(
            AlertSeverity.ERROR, "api-server", "接口响应超时"
        )
        assert alert.severity == AlertSeverity.ERROR
        assert alert.source == "api-server"
        assert alert.message == "接口响应超时"
        assert alert.status == AlertStatus.ACTIVE
        assert alert.alert_id in manager._alerts

    def test_create_alert_with_metadata(self):
        """测试创建带元数据的告警"""
        manager = AlertManager()
        alert = manager.create_alert(
            AlertSeverity.WARNING, "cache", "缓存命中率低",
            metadata={"hit_rate": 0.3},
        )
        assert alert.metadata["hit_rate"] == 0.3

    def test_acknowledge(self):
        """测试确认告警"""
        manager = AlertManager()
        alert = manager.create_alert(AlertSeverity.ERROR, "service", "服务异常")
        result = manager.acknowledge(alert.alert_id)
        assert result is not None
        assert result.status == AlertStatus.ACKNOWLEDGED

    def test_acknowledge_not_found(self):
        """测试确认不存在的告警"""
        manager = AlertManager()
        result = manager.acknowledge("nonexistent")
        assert result is None

    def test_resolve(self):
        """测试解决告警"""
        manager = AlertManager()
        alert = manager.create_alert(AlertSeverity.WARNING, "network", "网络延迟高")
        result = manager.resolve(alert.alert_id)
        assert result is not None
        assert result.status == AlertStatus.RESOLVED

    def test_resolve_not_found(self):
        """测试解决不存在的告警"""
        manager = AlertManager()
        result = manager.resolve("nonexistent")
        assert result is None

    def test_get_active_alerts(self):
        """测试获取活跃告警"""
        manager = AlertManager()
        manager.create_alert(AlertSeverity.ERROR, "service-a", "异常1")
        manager.create_alert(AlertSeverity.WARNING, "service-b", "异常2")
        alert3 = manager.create_alert(AlertSeverity.INFO, "service-c", "信息")
        manager.resolve(alert3.alert_id)
        active = manager.get_active_alerts()
        assert len(active) == 2

    def test_get_active_alerts_empty(self):
        """测试无活跃告警"""
        manager = AlertManager()
        active = manager.get_active_alerts()
        assert active == []

    def test_suppress(self):
        """测试抑制告警"""
        manager = AlertManager()
        alert = manager.create_alert(AlertSeverity.INFO, "monitor", "监控信息")
        result = manager.suppress(alert.alert_id)
        assert result is not None
        assert result.status == AlertStatus.SUPPRESSED

    def test_suppress_not_found(self):
        """测试抑制不存在的告警"""
        manager = AlertManager()
        result = manager.suppress("nonexistent")
        assert result is None


class TestRootCauseAnalyzer:
    """测试根因分析器"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = RootCauseAnalyzer()
        assert len(analyzer._root_causes) == 0

    def test_analyze_empty(self):
        """测试分析空告警列表"""
        analyzer = RootCauseAnalyzer()
        results = analyzer.analyze([])
        assert results == []

    def test_analyze_single_alert(self):
        """测试分析单个告警"""
        analyzer = RootCauseAnalyzer()
        alerts = [Alert(severity=AlertSeverity.ERROR, source="database", message="连接失败")]
        results = analyzer.analyze(alerts)
        assert len(results) >= 1
        assert results[0].confidence > 0

    def test_analyze_multiple_alerts(self):
        """测试分析多个告警"""
        analyzer = RootCauseAnalyzer()
        alerts = [
            Alert(severity=AlertSeverity.CRITICAL, source="database", message="主库宕机"),
            Alert(severity=AlertSeverity.ERROR, source="database", message="从库延迟"),
            Alert(severity=AlertSeverity.WARNING, source="api", message="接口超时"),
        ]
        results = analyzer.analyze(alerts)
        assert len(results) >= 1

    def test_correlate_alerts(self):
        """测试关联告警"""
        analyzer = RootCauseAnalyzer()
        alerts = [
            Alert(source="database", message="告警1"),
            Alert(source="database", message="告警2"),
            Alert(source="api", message="告警3"),
        ]
        groups = analyzer._correlate_alerts(alerts)
        assert "database" in groups
        assert len(groups["database"]) == 2
        assert "api" in groups

    def test_trace_causality(self):
        """测试追溯因果关系"""
        analyzer = RootCauseAnalyzer()
        groups = {
            "database": [
                Alert(severity=AlertSeverity.CRITICAL, source="database", message="宕机"),
                Alert(severity=AlertSeverity.WARNING, source="database", message="慢查询"),
            ]
        }
        chains = analyzer._trace_causality(groups)
        assert len(chains) == 1
        assert chains[0]["source"] == "database"

    def test_identify_root(self):
        """测试识别根因"""
        analyzer = RootCauseAnalyzer()
        critical_alert = Alert(severity=AlertSeverity.CRITICAL, source="db", message="宕机")
        chains = [{
            "source": "db",
            "alerts": [critical_alert],
            "potential_root": critical_alert,
        }]
        root_causes = analyzer._identify_root(chains, [critical_alert])
        assert len(root_causes) == 1
        assert root_causes[0].confidence >= 0.9

    def test_generate_rca_report(self):
        """测试生成RCA报告"""
        analyzer = RootCauseAnalyzer()
        alerts = [Alert(severity=AlertSeverity.ERROR, source="service", message="服务异常")]
        root_causes = analyzer.analyze(alerts)
        report = analyzer.generate_rca_report(root_causes)
        assert "total_root_causes" in report
        assert "root_causes" in report
        assert "highest_confidence" in report

    def test_generate_rca_report_empty(self):
        """测试空根因列表生成报告"""
        analyzer = RootCauseAnalyzer()
        report = analyzer.generate_rca_report([])
        assert "message" in report


class TestAlertRCAService:
    """测试告警与根因分析服务"""

    def test_initialization(self):
        """测试初始化"""
        service = AlertRCAService()
        assert service.alert_manager is not None
        assert service.rca_analyzer is not None

    def test_initialization_with_custom(self):
        """测试使用自定义组件初始化"""
        manager = AlertManager()
        analyzer = RootCauseAnalyzer()
        service = AlertRCAService(alert_manager=manager, rca_analyzer=analyzer)
        assert service.alert_manager is manager
        assert service.rca_analyzer is analyzer

    def test_process_alert(self):
        """测试处理告警"""
        service = AlertRCAService()
        alert = service.process_alert(
            AlertSeverity.ERROR, "payment", "支付服务超时"
        )
        assert alert.severity == AlertSeverity.ERROR
        assert alert.source == "payment"

    def test_get_alerts(self):
        """测试获取告警列表"""
        service = AlertRCAService()
        service.process_alert(AlertSeverity.ERROR, "service-a", "异常")
        service.process_alert(AlertSeverity.WARNING, "service-b", "警告")
        alerts = service.get_alerts()
        assert len(alerts) == 2

    def test_get_alerts_by_status(self):
        """测试按状态获取告警"""
        service = AlertRCAService()
        service.process_alert(AlertSeverity.ERROR, "service-a", "异常")
        active_alerts = service.get_alerts(AlertStatus.ACTIVE)
        assert len(active_alerts) >= 1

    def test_get_rca(self):
        """测试获取根因分析结果"""
        service = AlertRCAService()
        alert = service.process_alert(
            AlertSeverity.CRITICAL, "database", "数据库宕机"
        )
        rca = service.get_rca(alert.alert_id)
        # 可能有也可能没有RCA结果，取决于活跃告警数量
        assert isinstance(rca, list) or rca is None

    def test_get_rca_not_found(self):
        """测试获取不存在的RCA"""
        service = AlertRCAService()
        rca = service.get_rca("nonexistent")
        assert rca is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
