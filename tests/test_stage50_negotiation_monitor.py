"""
阶段50验收测试：协商性能监控与可视化
"""

import pytest
import time
import json

from src.architecture.negotiation_monitor import (
    MetricType, MetricRecord,
    PerformanceMetrics, NegotiationMonitor, MetricsReporter, NegotiationMonitorService,
    get_monitor_service, reset_monitor_service
)


class TestMetricType:
    """测试指标类型枚举"""

    def test_metric_values(self):
        """测试指标枚举值"""
        assert MetricType.LATENCY.value == "latency"
        assert MetricType.THROUGHPUT.value == "throughput"
        assert MetricType.ACCEPTANCE_RATE.value == "acceptance_rate"
        assert MetricType.CONCESSION_RATE.value == "concession_rate"
        assert MetricType.DEADLOCK_RATE.value == "deadlock_rate"

    def test_all_metrics(self):
        """测试所有指标"""
        metrics = list(MetricType)
        assert len(metrics) == 5


class TestMetricRecord:
    """测试指标记录"""

    def test_default_creation(self):
        """测试默认创建"""
        record = MetricRecord()
        assert record.metric_type == MetricType.LATENCY
        assert record.value == 0.0
        assert record.timestamp > 0
        assert record.session_id == ""
        assert record.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        record = MetricRecord(
            metric_type=MetricType.THROUGHPUT,
            value=42.5,
            session_id="s1",
            metadata={"agent": "a1"},
        )
        assert record.metric_type == MetricType.THROUGHPUT
        assert record.value == 42.5
        assert record.session_id == "s1"
        assert record.metadata["agent"] == "a1"


class TestPerformanceMetrics:
    """测试性能指标集合"""

    def test_initial_state(self):
        """测试初始状态"""
        pm = PerformanceMetrics()
        assert len(pm.records) == 0

    def test_add_metric(self):
        """测试添加指标"""
        pm = PerformanceMetrics()
        record = pm.add_metric(MetricType.LATENCY, 100.0, session_id="s1")
        assert record.metric_type == MetricType.LATENCY
        assert record.value == 100.0
        assert len(pm.records) == 1

    def test_add_multiple_metrics(self):
        """测试添加多个指标"""
        pm = PerformanceMetrics()
        pm.add_metric(MetricType.LATENCY, 100.0)
        pm.add_metric(MetricType.THROUGHPUT, 50.0)
        pm.add_metric(MetricType.LATENCY, 200.0)
        assert len(pm.records) == 3

    def test_add_metric_invalid_type(self):
        """测试添加无效指标类型"""
        pm = PerformanceMetrics()
        with pytest.raises(ValueError):
            pm.add_metric("invalid_type", 100.0)

    def test_get_metrics_all(self):
        """测试获取所有指标"""
        pm = PerformanceMetrics()
        pm.add_metric(MetricType.LATENCY, 100.0, session_id="s1")
        pm.add_metric(MetricType.THROUGHPUT, 50.0, session_id="s1")
        records = pm.get_metrics()
        assert len(records) == 2

    def test_get_metrics_by_type(self):
        """测试按类型获取指标"""
        pm = PerformanceMetrics()
        pm.add_metric(MetricType.LATENCY, 100.0, session_id="s1")
        pm.add_metric(MetricType.THROUGHPUT, 50.0, session_id="s1")
        pm.add_metric(MetricType.LATENCY, 200.0, session_id="s1")
        records = pm.get_metrics(metric_type=MetricType.LATENCY)
        assert len(records) == 2

    def test_get_metrics_by_session(self):
        """测试按会话获取指标"""
        pm = PerformanceMetrics()
        pm.add_metric(MetricType.LATENCY, 100.0, session_id="s1")
        pm.add_metric(MetricType.LATENCY, 200.0, session_id="s2")
        records = pm.get_metrics(session_id="s1")
        assert len(records) == 1
        assert records[0].value == 100.0

    def test_get_average(self):
        """测试获取平均值"""
        pm = PerformanceMetrics()
        pm.add_metric(MetricType.LATENCY, 100.0)
        pm.add_metric(MetricType.LATENCY, 200.0)
        pm.add_metric(MetricType.LATENCY, 300.0)
        avg = pm.get_average(MetricType.LATENCY)
        assert avg == pytest.approx(200.0, abs=0.01)

    def test_get_average_no_records(self):
        """测试无记录时的平均值"""
        pm = PerformanceMetrics()
        avg = pm.get_average(MetricType.LATENCY)
        assert avg == 0.0

    def test_get_average_by_session(self):
        """测试按会话获取平均值"""
        pm = PerformanceMetrics()
        pm.add_metric(MetricType.LATENCY, 100.0, session_id="s1")
        pm.add_metric(MetricType.LATENCY, 200.0, session_id="s1")
        pm.add_metric(MetricType.LATENCY, 900.0, session_id="s2")
        avg = pm.get_average(MetricType.LATENCY, session_id="s1")
        assert avg == pytest.approx(150.0, abs=0.01)

    def test_get_trend_increasing(self):
        """测试上升趋势"""
        pm = PerformanceMetrics()
        for i in range(10):
            pm.add_metric(MetricType.THROUGHPUT, float(i * 10))
        trend = pm.get_trend(MetricType.THROUGHPUT)
        assert trend == "increasing"

    def test_get_trend_decreasing(self):
        """测试下降趋势"""
        pm = PerformanceMetrics()
        for i in range(10):
            pm.add_metric(MetricType.LATENCY, float(100 - i * 10))
        trend = pm.get_trend(MetricType.LATENCY)
        assert trend == "decreasing"

    def test_get_trend_stable(self):
        """测试稳定趋势"""
        pm = PerformanceMetrics()
        for i in range(10):
            pm.add_metric(MetricType.LATENCY, 50.0)
        trend = pm.get_trend(MetricType.LATENCY)
        assert trend == "stable"

    def test_get_trend_insufficient_data(self):
        """测试数据不足时的趋势"""
        pm = PerformanceMetrics()
        pm.add_metric(MetricType.LATENCY, 100.0)
        trend = pm.get_trend(MetricType.LATENCY)
        assert trend == "stable"


class TestNegotiationMonitor:
    """测试协商监控器"""

    def test_initial_state(self):
        """测试初始状态"""
        monitor = NegotiationMonitor()
        assert len(monitor.metrics) == 0
        assert len(monitor.sessions) == 0
        assert monitor.monitoring == False

    def test_record_metric(self):
        """测试记录指标"""
        monitor = NegotiationMonitor()
        record = monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        assert record.metric_type == MetricType.LATENCY
        assert record.value == 100.0
        assert "s1" in monitor.metrics
        assert monitor.sessions["s1"]["metric_count"] == 1

    def test_record_metric_empty_session(self):
        """测试空会话ID记录指标"""
        monitor = NegotiationMonitor()
        with pytest.raises(ValueError):
            monitor.record_metric("", MetricType.LATENCY, 100.0)

    def test_record_multiple_metrics(self):
        """测试记录多个指标"""
        monitor = NegotiationMonitor()
        monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        monitor.record_metric("s1", MetricType.THROUGHPUT, 50.0)
        monitor.record_metric("s1", MetricType.ACCEPTANCE_RATE, 0.8)
        assert monitor.sessions["s1"]["metric_count"] == 3

    def test_get_session_metrics(self):
        """测试获取会话指标"""
        monitor = NegotiationMonitor()
        monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        monitor.record_metric("s1", MetricType.THROUGHPUT, 50.0)
        records = monitor.get_session_metrics("s1")
        assert len(records) == 2

    def test_get_session_metrics_by_type(self):
        """测试按类型获取会话指标"""
        monitor = NegotiationMonitor()
        monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        monitor.record_metric("s1", MetricType.THROUGHPUT, 50.0)
        records = monitor.get_session_metrics("s1", metric_type=MetricType.LATENCY)
        assert len(records) == 1
        assert records[0].value == 100.0

    def test_get_session_metrics_not_found(self):
        """测试获取不存在的会话指标"""
        monitor = NegotiationMonitor()
        records = monitor.get_session_metrics("nonexistent")
        assert records == []

    def test_get_performance_summary_single_session(self):
        """测试获取单会话性能摘要"""
        monitor = NegotiationMonitor()
        monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        monitor.record_metric("s1", MetricType.LATENCY, 200.0)
        summary = monitor.get_performance_summary("s1")
        assert summary["session_id"] == "s1"
        assert "latency" in summary["metrics"]
        assert summary["metrics"]["latency"]["count"] == 2

    def test_get_performance_summary_all_sessions(self):
        """测试获取全部会话性能摘要"""
        monitor = NegotiationMonitor()
        monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        monitor.record_metric("s2", MetricType.THROUGHPUT, 50.0)
        summary = monitor.get_performance_summary()
        assert summary["total_sessions"] == 2
        assert "s1" in summary["sessions"]
        assert "s2" in summary["sessions"]

    def test_get_performance_summary_not_found(self):
        """测试获取不存在的会话摘要"""
        monitor = NegotiationMonitor()
        summary = monitor.get_performance_summary("nonexistent")
        assert "metrics" in summary

    def test_detect_bottleneck_high_latency(self):
        """测试检测高延迟瓶颈"""
        monitor = NegotiationMonitor()
        for _ in range(5):
            monitor.record_metric("s1", MetricType.LATENCY, 1500.0)
        bottlenecks = monitor.detect_bottleneck("s1")
        assert len(bottlenecks) >= 1
        assert any(b["type"] == "high_latency" for b in bottlenecks)

    def test_detect_bottleneck_low_throughput(self):
        """测试检测低吞吐量瓶颈"""
        monitor = NegotiationMonitor()
        for _ in range(5):
            monitor.record_metric("s1", MetricType.THROUGHPUT, 0.5)
        bottlenecks = monitor.detect_bottleneck("s1")
        assert len(bottlenecks) >= 1
        assert any(b["type"] == "low_throughput" for b in bottlenecks)

    def test_detect_bottleneck_high_deadlock(self):
        """测试检测高死锁率瓶颈"""
        monitor = NegotiationMonitor()
        for _ in range(5):
            monitor.record_metric("s1", MetricType.DEADLOCK_RATE, 0.8)
        bottlenecks = monitor.detect_bottleneck("s1")
        assert len(bottlenecks) >= 1
        assert any(b["type"] == "high_deadlock_rate" for b in bottlenecks)

    def test_detect_bottleneck_low_acceptance(self):
        """测试检测低接受率瓶颈"""
        monitor = NegotiationMonitor()
        for _ in range(5):
            monitor.record_metric("s1", MetricType.ACCEPTANCE_RATE, 0.1)
        bottlenecks = monitor.detect_bottleneck("s1")
        assert len(bottlenecks) >= 1
        assert any(b["type"] == "low_acceptance_rate" for b in bottlenecks)

    def test_detect_bottleneck_no_issues(self):
        """测试无瓶颈"""
        monitor = NegotiationMonitor()
        monitor.record_metric("s1", MetricType.LATENCY, 50.0)
        monitor.record_metric("s1", MetricType.THROUGHPUT, 100.0)
        monitor.record_metric("s1", MetricType.ACCEPTANCE_RATE, 0.8)
        bottlenecks = monitor.detect_bottleneck("s1")
        assert len(bottlenecks) == 0

    def test_detect_bottleneck_all_sessions(self):
        """测试检测所有会话瓶颈"""
        monitor = NegotiationMonitor()
        for _ in range(5):
            monitor.record_metric("s1", MetricType.LATENCY, 1500.0)
        for _ in range(5):
            monitor.record_metric("s2", MetricType.LATENCY, 50.0)
        bottlenecks = monitor.detect_bottleneck()
        assert len(bottlenecks) >= 1


class TestMetricsReporter:
    """测试指标报告器"""

    def test_generate_text_report(self):
        """测试生成文本报告"""
        reporter = MetricsReporter()
        summary = {
            "session_id": "s1",
            "metrics": {
                "latency": {
                    "count": 5,
                    "average": 120.0,
                    "trend": "stable",
                    "latest": 100.0,
                },
            },
        }
        report = reporter.generate_text_report(summary)
        assert "协商性能监控报告" in report
        assert "latency" in report

    def test_generate_text_report_empty(self):
        """测试生成空文本报告"""
        reporter = MetricsReporter()
        report = reporter.generate_text_report({})
        assert report == "无监控数据"

    def test_generate_text_report_multi_session(self):
        """测试生成多会话文本报告"""
        reporter = MetricsReporter()
        summary = {
            "total_sessions": 2,
            "sessions": {
                "s1": {"metrics": {"latency": {"count": 3, "average": 100.0, "trend": "stable", "latest": 90.0}}},
                "s2": {"metrics": {"throughput": {"count": 2, "average": 50.0, "trend": "increasing", "latest": 60.0}}},
            },
        }
        report = reporter.generate_text_report(summary)
        assert "总会话数: 2" in report

    def test_generate_json_report(self):
        """测试生成JSON报告"""
        reporter = MetricsReporter()
        summary = {"session_id": "s1", "metrics": {"latency": {"count": 5, "average": 120.0}}}
        report = reporter.generate_json_report(summary)
        parsed = json.loads(report)
        assert parsed["session_id"] == "s1"
        assert "latency" in parsed["metrics"]

    def test_generate_json_report_empty(self):
        """测试生成空JSON报告"""
        reporter = MetricsReporter()
        report = reporter.generate_json_report({})
        assert report == "{}"

    def test_generate_timeline(self):
        """测试生成时间线"""
        reporter = MetricsReporter()
        records = [
            MetricRecord(metric_type=MetricType.LATENCY, value=100.0, timestamp=1.0, session_id="s1"),
            MetricRecord(metric_type=MetricType.LATENCY, value=200.0, timestamp=2.0, session_id="s1"),
        ]
        timeline = reporter.generate_timeline(records)
        assert len(timeline) == 2
        assert timeline[0]["value"] == 100.0
        assert timeline[1]["value"] == 200.0

    def test_generate_timeline_empty(self):
        """测试生成空时间线"""
        reporter = MetricsReporter()
        timeline = reporter.generate_timeline([])
        assert timeline == []

    def test_generate_timeline_sorted(self):
        """测试时间线排序"""
        reporter = MetricsReporter()
        records = [
            MetricRecord(metric_type=MetricType.LATENCY, value=200.0, timestamp=2.0),
            MetricRecord(metric_type=MetricType.LATENCY, value=100.0, timestamp=1.0),
        ]
        timeline = reporter.generate_timeline(records)
        assert timeline[0]["value"] == 100.0
        assert timeline[1]["value"] == 200.0


class TestNegotiationMonitorService:
    """测试协商监控服务"""

    def setup_method(self):
        reset_monitor_service()

    def test_initial_state(self):
        """测试初始状态"""
        service = NegotiationMonitorService()
        assert service._monitoring == False

    def test_start_monitoring(self):
        """测试开始监控"""
        service = NegotiationMonitorService()
        result = service.start_monitoring("s1")
        assert result == True
        assert service._monitoring == True
        assert "s1" in service.monitor.metrics

    def test_start_monitoring_no_session(self):
        """测试开始监控（无指定会话）"""
        service = NegotiationMonitorService()
        result = service.start_monitoring()
        assert result == True
        assert service._monitoring == True

    def test_stop_monitoring(self):
        """测试停止监控"""
        service = NegotiationMonitorService()
        service.start_monitoring()
        result = service.stop_monitoring()
        assert result == True
        assert service._monitoring == False

    def test_get_report_text(self):
        """测试获取文本报告"""
        service = NegotiationMonitorService()
        service.start_monitoring("s1")
        service.monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        report = service.get_report(session_id="s1", format="text")
        assert report is not None
        assert "协商性能监控报告" in report

    def test_get_report_json(self):
        """测试获取JSON报告"""
        service = NegotiationMonitorService()
        service.start_monitoring("s1")
        service.monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        report = service.get_report(session_id="s1", format="json")
        assert report is not None
        parsed = json.loads(report)
        assert "session_id" in parsed

    def test_get_report_timeline(self):
        """测试获取时间线报告"""
        service = NegotiationMonitorService()
        service.start_monitoring("s1")
        service.monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        service.monitor.record_metric("s1", MetricType.LATENCY, 200.0)
        report = service.get_report(session_id="s1", format="timeline")
        assert report is not None
        assert len(report) == 2

    def test_get_report_no_data(self):
        """测试无数据时获取报告"""
        service = NegotiationMonitorService()
        report = service.get_report(session_id="nonexistent", format="text")
        assert report is not None

    def test_global_service(self):
        """测试全局服务"""
        service1 = get_monitor_service()
        service2 = get_monitor_service()
        assert service1 is service2
        reset_monitor_service()
        service3 = get_monitor_service()
        assert service3 is not service1

    def test_full_monitoring_workflow(self):
        """测试完整监控工作流"""
        service = NegotiationMonitorService()

        # 1. 开始监控
        service.start_monitoring("s1")

        # 2. 记录指标
        service.monitor.record_metric("s1", MetricType.LATENCY, 100.0)
        service.monitor.record_metric("s1", MetricType.THROUGHPUT, 50.0)
        service.monitor.record_metric("s1", MetricType.ACCEPTANCE_RATE, 0.8)

        # 3. 获取摘要
        summary = service.monitor.get_performance_summary("s1")
        assert "latency" in summary["metrics"]
        assert "throughput" in summary["metrics"]
        assert "acceptance_rate" in summary["metrics"]

        # 4. 检测瓶颈
        bottlenecks = service.monitor.detect_bottleneck("s1")
        assert len(bottlenecks) == 0  # 正常指标，无瓶颈

        # 5. 生成报告
        text_report = service.get_report(session_id="s1", format="text")
        assert "协商性能监控报告" in text_report

        json_report = service.get_report(session_id="s1", format="json")
        parsed = json.loads(json_report)
        assert parsed["session_id"] == "s1"

        # 6. 停止监控
        service.stop_monitoring()
        assert service._monitoring == False
