"""
阶段99验收测试 - 系统自监控、自诊断、自优化
"""

import pytest
from src.architecture.self_optimize import (
    MonitorMetric,
    DiagnosisResult,
    SystemHealth,
    SelfMonitor,
    SelfDiagnoser,
    SelfOptimizer,
    SelfOptimizeService,
)


class TestMonitorMetric:
    """测试监控指标枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert MonitorMetric.CPU_USAGE.value == "cpu_usage"
        assert MonitorMetric.MEMORY_USAGE.value == "memory_usage"
        assert MonitorMetric.RESPONSE_TIME.value == "response_time"
        assert MonitorMetric.ERROR_RATE.value == "error_rate"
        assert MonitorMetric.THROUGHPUT.value == "throughput"

    def test_all_metrics(self):
        """测试所有指标"""
        metrics = list(MonitorMetric)
        assert len(metrics) == 5


class TestDiagnosisResult:
    """测试诊断结果枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert DiagnosisResult.HEALTHY.value == "healthy"
        assert DiagnosisResult.DEGRADED.value == "degraded"
        assert DiagnosisResult.UNSTABLE.value == "unstable"
        assert DiagnosisResult.CRITICAL.value == "critical"

    def test_all_results(self):
        """测试所有结果"""
        results = list(DiagnosisResult)
        assert len(results) == 4


class TestSystemHealth:
    """测试系统健康状态"""

    def test_default_creation(self):
        """测试默认创建"""
        health = SystemHealth()
        assert health.diagnosis == DiagnosisResult.HEALTHY
        assert health.metrics == {}
        assert health.issues == []
        assert health.recommendations == []
        assert health.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        health = SystemHealth(
            diagnosis=DiagnosisResult.DEGRADED,
            metrics={"cpu_usage": 85.0},
            issues=["CPU使用率过高"],
            recommendations=["增加CPU资源"],
        )
        assert health.diagnosis == DiagnosisResult.DEGRADED
        assert health.metrics["cpu_usage"] == 85.0
        assert len(health.issues) == 1
        assert len(health.recommendations) == 1


class TestSelfMonitor:
    """测试自监控器"""

    def test_initialization(self):
        """测试初始化"""
        monitor = SelfMonitor()
        assert len(monitor._history) == 0

    def test_monitor_healthy(self):
        """测试监控健康系统"""
        monitor = SelfMonitor()
        metrics = {
            "cpu_usage": 30.0,
            "memory_usage": 40.0,
            "response_time": 100.0,
            "error_rate": 1.0,
            "throughput": 500.0,
        }
        result = monitor.monitor(metrics)
        assert len(result["anomalies"]) == 0

    def test_monitor_cpu_warning(self):
        """测试监控CPU警告"""
        monitor = SelfMonitor()
        metrics = {"cpu_usage": 85.0}
        result = monitor.monitor(metrics)
        assert len(result["anomalies"]) >= 1
        assert result["anomalies"][0]["type"] == "warning"

    def test_monitor_cpu_critical(self):
        """测试监控CPU严重"""
        monitor = SelfMonitor()
        metrics = {"cpu_usage": 98.0}
        result = monitor.monitor(metrics)
        assert len(result["anomalies"]) >= 1
        assert result["anomalies"][0]["type"] == "critical"

    def test_monitor_memory_warning(self):
        """测试监控内存警告"""
        monitor = SelfMonitor()
        metrics = {"memory_usage": 90.0}
        result = monitor.monitor(metrics)
        assert len(result["anomalies"]) >= 1

    def test_monitor_throughput_warning(self):
        """测试监控吞吐量警告"""
        monitor = SelfMonitor()
        metrics = {"throughput": 80.0}
        result = monitor.monitor(metrics)
        assert len(result["anomalies"]) >= 1

    def test_monitor_throughput_critical(self):
        """测试监控吞吐量严重"""
        monitor = SelfMonitor()
        metrics = {"throughput": 30.0}
        result = monitor.monitor(metrics)
        assert len(result["anomalies"]) >= 1
        assert result["anomalies"][0]["type"] == "critical"

    def test_collect_metrics(self):
        """测试收集指标"""
        monitor = SelfMonitor()
        collected = monitor._collect_metrics({"cpu_usage": 50.0})
        assert "cpu_usage" in collected
        assert collected["cpu_usage"]["value"] == 50.0

    def test_check_thresholds(self):
        """测试检查阈值"""
        monitor = SelfMonitor()
        collected = {"cpu_usage": {"value": 85.0, "timestamp": 0}}
        results = monitor._check_thresholds(collected)
        assert "cpu_usage" in results
        assert results["cpu_usage"]["status"] == "warning"

    def test_detect_anomalies(self):
        """测试检测异常"""
        monitor = SelfMonitor()
        collected = {"cpu_usage": {"value": 98.0, "timestamp": 0}}
        anomalies = monitor._detect_anomalies(collected)
        assert len(anomalies) == 1
        assert anomalies[0]["type"] == "critical"

    def test_monitor_saves_history(self):
        """测试监控保存历史"""
        monitor = SelfMonitor()
        monitor.monitor({"cpu_usage": 50.0})
        assert len(monitor._history) == 1


class TestSelfDiagnoser:
    """测试自诊断器"""

    def test_initialization(self):
        """测试初始化"""
        diagnoser = SelfDiagnoser()
        assert len(diagnoser._diagnoses) == 0

    def test_diagnose_healthy(self):
        """测试诊断健康系统"""
        diagnoser = SelfDiagnoser()
        monitor_result = {"anomalies": [], "collected": {}}
        health = diagnoser.diagnose(monitor_result)
        assert health.diagnosis == DiagnosisResult.HEALTHY

    def test_diagnose_degraded(self):
        """测试诊断降级系统"""
        diagnoser = SelfDiagnoser()
        monitor_result = {
            "anomalies": [{"metric": "cpu_usage", "type": "warning", "description": "CPU偏高"}],
            "collected": {"cpu_usage": {"value": 85.0}},
        }
        health = diagnoser.diagnose(monitor_result)
        assert health.diagnosis == DiagnosisResult.DEGRADED

    def test_diagnose_unstable(self):
        """测试诊断不稳定系统"""
        diagnoser = SelfDiagnoser()
        monitor_result = {
            "anomalies": [
                {"metric": "cpu_usage", "type": "warning", "description": "CPU偏高"},
                {"metric": "memory_usage", "type": "warning", "description": "内存偏高"},
                {"metric": "response_time", "type": "warning", "description": "响应慢"},
            ],
            "collected": {},
        }
        health = diagnoser.diagnose(monitor_result)
        assert health.diagnosis == DiagnosisResult.UNSTABLE

    def test_diagnose_critical(self):
        """测试诊断严重系统"""
        diagnoser = SelfDiagnoser()
        monitor_result = {
            "anomalies": [{"metric": "cpu_usage", "type": "critical", "description": "CPU严重"}],
            "collected": {},
        }
        health = diagnoser.diagnose(monitor_result)
        assert health.diagnosis == DiagnosisResult.CRITICAL

    def test_analyze_symptoms(self):
        """测试分析症状"""
        diagnoser = SelfDiagnoser()
        anomalies = [{"metric": "cpu_usage", "type": "warning"}]
        symptoms = diagnoser._analyze_symptoms(anomalies)
        assert len(symptoms) == 1
        assert symptoms[0]["category"] == "resource"

    def test_identify_root_cause(self):
        """测试识别根因"""
        diagnoser = SelfDiagnoser()
        symptoms = [
            {"metric": "cpu_usage", "type": "warning", "category": "resource"},
            {"metric": "memory_usage", "type": "warning", "category": "resource"},
        ]
        root_cause = diagnoser._identify_root_cause(symptoms)
        assert root_cause == "resource"

    def test_assess_severity(self):
        """测试评估严重程度"""
        diagnoser = SelfDiagnoser()
        assert diagnoser._assess_severity([]) == DiagnosisResult.HEALTHY
        assert diagnoser._assess_severity([{"type": "warning"}]) == DiagnosisResult.DEGRADED
        assert diagnoser._assess_severity([{"type": "critical"}]) == DiagnosisResult.CRITICAL

    def test_diagnose_saves_result(self):
        """测试诊断保存结果"""
        diagnoser = SelfDiagnoser()
        diagnoser.diagnose({"anomalies": [], "collected": {}})
        assert len(diagnoser._diagnoses) == 1


class TestSelfOptimizer:
    """测试自优化器"""

    def test_initialization(self):
        """测试初始化"""
        optimizer = SelfOptimizer()
        assert len(optimizer._optimizations) == 0

    def test_optimize_healthy(self):
        """测试优化健康系统"""
        optimizer = SelfOptimizer()
        health = SystemHealth(diagnosis=DiagnosisResult.HEALTHY)
        result = optimizer.optimize(health)
        assert result["status"] == "healthy"
        assert result["improvement"] == 0.0

    def test_optimize_degraded(self):
        """测试优化降级系统"""
        optimizer = SelfOptimizer()
        health = SystemHealth(
            diagnosis=DiagnosisResult.DEGRADED,
            metrics={"cpu_usage": 85.0},
            issues=["CPU使用率偏高"],
        )
        result = optimizer.optimize(health)
        assert result["status"] == "optimized"
        assert len(result["actions"]) > 0

    def test_optimize_critical(self):
        """测试优化严重系统"""
        optimizer = SelfOptimizer()
        health = SystemHealth(
            diagnosis=DiagnosisResult.CRITICAL,
            metrics={"cpu_usage": 98.0, "memory_usage": 96.0},
            issues=["CPU严重过高", "内存严重过高"],
        )
        result = optimizer.optimize(health)
        assert result["status"] == "optimized"
        assert len(result["actions"]) > 0

    def test_apply_fix_cpu(self):
        """测试CPU修复"""
        optimizer = SelfOptimizer()
        fix = optimizer._apply_fix("CPU使用率过高")
        assert fix is not None
        assert "CPU" in fix["action"]

    def test_apply_fix_memory(self):
        """测试内存修复"""
        optimizer = SelfOptimizer()
        fix = optimizer._apply_fix("内存使用率过高")
        assert fix is not None
        assert "内存" in fix["action"]

    def test_apply_fix_response(self):
        """测试响应时间修复"""
        optimizer = SelfOptimizer()
        fix = optimizer._apply_fix("响应时间过长")
        assert fix is not None
        assert "响应" in fix["action"]

    def test_adjust_parameters(self):
        """测试参数调整"""
        optimizer = SelfOptimizer()
        adjustments = optimizer._adjust_parameters({"cpu_usage": 90.0, "memory_usage": 90.0})
        assert adjustments is not None
        assert "adjustments" in adjustments

    def test_adjust_parameters_normal(self):
        """测试正常参数无需调整"""
        optimizer = SelfOptimizer()
        adjustments = optimizer._adjust_parameters({"cpu_usage": 50.0, "memory_usage": 60.0})
        assert adjustments is None

    def test_rebalance_load(self):
        """测试负载均衡"""
        optimizer = SelfOptimizer()
        result = optimizer._rebalance_load({"cpu_usage": 90.0})
        assert result is not None
        assert result["type"] == "load_rebalance"

    def test_verify_improvement(self):
        """测试验证改进"""
        optimizer = SelfOptimizer()
        health = SystemHealth(diagnosis=DiagnosisResult.DEGRADED)
        actions = [{"type": "fix"}, {"type": "adjustment"}]
        improvement = optimizer.verify_improvement(health, actions)
        assert improvement > 0


class TestSelfOptimizeService:
    """测试自优化服务"""

    def test_initialization(self):
        """测试初始化"""
        service = SelfOptimizeService()
        assert service.monitor is not None
        assert service.diagnoser is not None
        assert service.optimizer is not None

    def test_run_health_check_healthy(self):
        """测试健康检查-健康"""
        service = SelfOptimizeService()
        metrics = {"cpu_usage": 30.0, "memory_usage": 40.0}
        health = service.run_health_check(metrics)
        assert health.diagnosis == DiagnosisResult.HEALTHY

    def test_run_health_check_degraded(self):
        """测试健康检查-降级"""
        service = SelfOptimizeService()
        metrics = {"cpu_usage": 85.0}
        health = service.run_health_check(metrics)
        assert health.diagnosis in (DiagnosisResult.DEGRADED, DiagnosisResult.UNSTABLE, DiagnosisResult.CRITICAL)

    def test_auto_optimize(self):
        """测试自动优化"""
        service = SelfOptimizeService()
        metrics = {"cpu_usage": 90.0, "memory_usage": 90.0}
        result = service.auto_optimize(metrics)
        assert "status" in result
        assert "actions" in result

    def test_get_health(self):
        """测试获取健康状态"""
        service = SelfOptimizeService()
        metrics = {"cpu_usage": 30.0}
        service.run_health_check(metrics)
        health = service.get_health()
        assert health is not None

    def test_get_health_before_check(self):
        """测试检查前获取健康状态"""
        service = SelfOptimizeService()
        health = service.get_health()
        assert health is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
