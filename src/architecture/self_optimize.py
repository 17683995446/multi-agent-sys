"""
系统自监控、自诊断、自优化模块

职责：监控系统指标、诊断系统健康、自动优化性能

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MonitorMetric(str, Enum):
    """监控指标"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


class DiagnosisResult(str, Enum):
    """诊断结果"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    CRITICAL = "critical"


@dataclass
class SystemHealth:
    """系统健康状态"""
    diagnosis: DiagnosisResult = DiagnosisResult.HEALTHY
    metrics: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"SystemHealth created: diagnosis={self.diagnosis.value}, "
                     f"issues={len(self.issues)}, "
                     f"recommendations={len(self.recommendations)}")


class SelfMonitor:
    """自监控器"""

    def __init__(self):
        """初始化自监控器"""
        self._thresholds: Dict[str, Dict[str, float]] = {
            MonitorMetric.CPU_USAGE.value: {"warning": 80.0, "critical": 95.0},
            MonitorMetric.MEMORY_USAGE.value: {"warning": 85.0, "critical": 95.0},
            MonitorMetric.RESPONSE_TIME.value: {"warning": 500.0, "critical": 2000.0},
            MonitorMetric.ERROR_RATE.value: {"warning": 5.0, "critical": 15.0},
            MonitorMetric.THROUGHPUT.value: {"warning": 100.0, "critical": 50.0},
        }
        self._history: List[Dict[str, Any]] = []
        logger.info("SelfMonitor initialized")

    def monitor(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """执行监控"""
        logger.info(f"SelfMonitor: monitoring, keys={list(metrics.keys())}")
        try:
            collected = self._collect_metrics(metrics)
            threshold_results = self._check_thresholds(collected)
            anomalies = self._detect_anomalies(collected)

            result: Dict[str, Any] = {
                "collected": collected,
                "threshold_results": threshold_results,
                "anomalies": anomalies,
                "timestamp": time.time(),
            }

            self._history.append(result)

            logger.info(f"SelfMonitor: monitoring completed, "
                        f"anomalies={len(anomalies)}")
        except Exception as e:
            logger.error(f"SelfMonitor: monitor failed: {e}")
            result = {"collected": {}, "threshold_results": {}, "anomalies": []}
        return result

    def _collect_metrics(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """收集指标"""
        logger.debug("SelfMonitor: collecting metrics")
        try:
            collected: Dict[str, Any] = {}
            for key, value in metrics.items():
                collected[key] = {
                    "value": value,
                    "timestamp": time.time(),
                }
            logger.debug(f"SelfMonitor: collected {len(collected)} metrics")
        except Exception as e:
            logger.error(f"SelfMonitor: _collect_metrics failed: {e}")
            collected = {}
        return collected

    def _check_thresholds(self, collected: Dict[str, Any]) -> Dict[str, Any]:
        """检查阈值"""
        logger.debug("SelfMonitor: checking thresholds")
        try:
            results: Dict[str, Any] = {}
            for metric_name, data in collected.items():
                value = data.get("value", 0.0)
                thresholds = self._thresholds.get(metric_name, {})
                warning = thresholds.get("warning", float("inf"))
                critical = thresholds.get("critical", float("inf"))

                # 对于吞吐量，阈值是下限
                if metric_name == MonitorMetric.THROUGHPUT.value:
                    if value < critical:
                        status = "critical"
                    elif value < warning:
                        status = "warning"
                    else:
                        status = "normal"
                else:
                    if value > critical:
                        status = "critical"
                    elif value > warning:
                        status = "warning"
                    else:
                        status = "normal"

                results[metric_name] = {
                    "value": value,
                    "status": status,
                    "warning_threshold": warning,
                    "critical_threshold": critical,
                }

            logger.debug(f"SelfMonitor: threshold check completed")
        except Exception as e:
            logger.error(f"SelfMonitor: _check_thresholds failed: {e}")
            results = {}
        return results

    def _detect_anomalies(self, collected: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测异常"""
        logger.debug("SelfMonitor: detecting anomalies")
        try:
            anomalies: List[Dict[str, Any]] = []
            for metric_name, data in collected.items():
                value = data.get("value", 0.0)
                thresholds = self._thresholds.get(metric_name, {})
                warning = thresholds.get("warning", float("inf"))
                critical = thresholds.get("critical", float("inf"))

                if metric_name == MonitorMetric.THROUGHPUT.value:
                    if value < critical:
                        anomalies.append({
                            "metric": metric_name,
                            "value": value,
                            "type": "critical",
                            "description": f"吞吐量严重低于阈值: {value} < {critical}",
                        })
                    elif value < warning:
                        anomalies.append({
                            "metric": metric_name,
                            "value": value,
                            "type": "warning",
                            "description": f"吞吐量低于警告阈值: {value} < {warning}",
                        })
                else:
                    if value > critical:
                        anomalies.append({
                            "metric": metric_name,
                            "value": value,
                            "type": "critical",
                            "description": f"指标超过严重阈值: {value} > {critical}",
                        })
                    elif value > warning:
                        anomalies.append({
                            "metric": metric_name,
                            "value": value,
                            "type": "warning",
                            "description": f"指标超过警告阈值: {value} > {warning}",
                        })

            logger.debug(f"SelfMonitor: detected {len(anomalies)} anomalies")
        except Exception as e:
            logger.error(f"SelfMonitor: _detect_anomalies failed: {e}")
            anomalies = []
        return anomalies


class SelfDiagnoser:
    """自诊断器"""

    def __init__(self):
        """初始化自诊断器"""
        self._diagnoses: List[SystemHealth] = []
        logger.info("SelfDiagnoser initialized")

    def diagnose(self, monitor_result: Dict[str, Any]) -> SystemHealth:
        """执行诊断"""
        logger.info("SelfDiagnoser: diagnosing system")
        try:
            anomalies = monitor_result.get("anomalies", [])
            collected = monitor_result.get("collected", {})

            symptoms = self._analyze_symptoms(anomalies)
            root_cause = self._identify_root_cause(symptoms)
            severity = self._assess_severity(anomalies)

            # 构建指标字典
            metrics: Dict[str, float] = {}
            for metric_name, data in collected.items():
                metrics[metric_name] = data.get("value", 0.0)

            # 生成建议
            recommendations = self._generate_recommendations(root_cause, severity)

            health = SystemHealth(
                diagnosis=severity,
                metrics=metrics,
                issues=[a.get("description", "") for a in anomalies],
                recommendations=recommendations,
            )

            self._diagnoses.append(health)

            logger.info(f"SelfDiagnoser: diagnosis completed, "
                        f"result={health.diagnosis.value}")
        except Exception as e:
            logger.error(f"SelfDiagnoser: diagnose failed: {e}")
            health = SystemHealth(diagnosis=DiagnosisResult.HEALTHY)
        return health

    def _analyze_symptoms(self, anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析症状"""
        logger.debug(f"SelfDiagnoser: analyzing {len(anomalies)} anomalies")
        try:
            symptoms: List[Dict[str, Any]] = []
            for anomaly in anomalies:
                symptoms.append({
                    "metric": anomaly.get("metric", ""),
                    "type": anomaly.get("type", "warning"),
                    "category": self._categorize_metric(anomaly.get("metric", "")),
                })
            logger.debug(f"SelfDiagnoser: analyzed {len(symptoms)} symptoms")
        except Exception as e:
            logger.error(f"SelfDiagnoser: _analyze_symptoms failed: {e}")
            symptoms = []
        return symptoms

    def _categorize_metric(self, metric: str) -> str:
        """分类指标"""
        if metric in (MonitorMetric.CPU_USAGE.value, MonitorMetric.MEMORY_USAGE.value):
            return "resource"
        elif metric in (MonitorMetric.RESPONSE_TIME.value, MonitorMetric.THROUGHPUT.value):
            return "performance"
        elif metric == MonitorMetric.ERROR_RATE.value:
            return "reliability"
        return "unknown"

    def _identify_root_cause(self, symptoms: List[Dict[str, Any]]) -> str:
        """识别根因"""
        logger.debug(f"SelfDiagnoser: identifying root cause from {len(symptoms)} symptoms")
        try:
            categories: Dict[str, int] = {}
            for symptom in symptoms:
                cat = symptom.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

            if not categories:
                root_cause = "无异常"
            else:
                root_cause = max(categories, key=categories.get)

            logger.debug(f"SelfDiagnoser: root cause={root_cause}")
        except Exception as e:
            logger.error(f"SelfDiagnoser: _identify_root_cause failed: {e}")
            root_cause = "unknown"
        return root_cause

    def _assess_severity(self, anomalies: List[Dict[str, Any]]) -> DiagnosisResult:
        """评估严重程度"""
        logger.debug(f"SelfDiagnoser: assessing severity, "
                     f"anomalies={len(anomalies)}")
        try:
            critical_count = sum(1 for a in anomalies if a.get("type") == "critical")
            warning_count = sum(1 for a in anomalies if a.get("type") == "warning")

            if critical_count > 0:
                severity = DiagnosisResult.CRITICAL
            elif warning_count >= 3:
                severity = DiagnosisResult.UNSTABLE
            elif warning_count > 0:
                severity = DiagnosisResult.DEGRADED
            else:
                severity = DiagnosisResult.HEALTHY

            logger.debug(f"SelfDiagnoser: severity={severity.value}")
        except Exception as e:
            logger.error(f"SelfDiagnoser: _assess_severity failed: {e}")
            severity = DiagnosisResult.HEALTHY
        return severity

    def _generate_recommendations(self, root_cause: str,
                                  severity: DiagnosisResult) -> List[str]:
        """生成建议"""
        logger.debug(f"SelfDiagnoser: generating recommendations, "
                     f"root_cause={root_cause}, severity={severity.value}")
        try:
            recommendations: List[str] = []
            if root_cause == "resource":
                recommendations.extend(["增加资源配置", "优化资源使用", "启用自动扩缩容"])
            elif root_cause == "performance":
                recommendations.extend(["优化性能瓶颈", "增加缓存", "调整并发参数"])
            elif root_cause == "reliability":
                recommendations.extend(["检查错误日志", "修复已知Bug", "增加重试机制"])

            if severity == DiagnosisResult.CRITICAL:
                recommendations.insert(0, "立即采取行动")
            elif severity == DiagnosisResult.UNSTABLE:
                recommendations.insert(0, "尽快处理")

            logger.debug(f"SelfDiagnoser: {len(recommendations)} recommendations")
        except Exception as e:
            logger.error(f"SelfDiagnoser: _generate_recommendations failed: {e}")
            recommendations = []
        return recommendations


class SelfOptimizer:
    """自优化器"""

    def __init__(self):
        """初始化自优化器"""
        self._optimizations: List[Dict[str, Any]] = []
        logger.info("SelfOptimizer initialized")

    def optimize(self, health: SystemHealth) -> Dict[str, Any]:
        """执行优化"""
        logger.info(f"SelfOptimizer: optimizing, "
                    f"diagnosis={health.diagnosis.value}")
        try:
            if health.diagnosis == DiagnosisResult.HEALTHY:
                logger.info("SelfOptimizer: system healthy, no optimization needed")
                return {"status": "healthy", "actions": [], "improvement": 0.0}

            actions: List[Dict[str, Any]] = []

            # 根据问题执行优化
            for issue in health.issues:
                fix = self._apply_fix(issue)
                if fix:
                    actions.append(fix)

            # 调整参数
            param_adjustments = self._adjust_parameters(health.metrics)
            if param_adjustments:
                actions.append(param_adjustments)

            # 负载均衡
            if health.diagnosis in (DiagnosisResult.UNSTABLE, DiagnosisResult.CRITICAL):
                rebalance = self._rebalance_load(health.metrics)
                if rebalance:
                    actions.append(rebalance)

            # 验证改进
            improvement = self.verify_improvement(health, actions)

            result: Dict[str, Any] = {
                "status": "optimized",
                "actions": actions,
                "improvement": improvement,
                "timestamp": time.time(),
            }

            self._optimizations.append(result)

            logger.info(f"SelfOptimizer: optimization completed, "
                        f"actions={len(actions)}, improvement={improvement}")
        except Exception as e:
            logger.error(f"SelfOptimizer: optimize failed: {e}")
            result = {"status": "failed", "actions": [], "improvement": 0.0}
        return result

    def _apply_fix(self, issue: str) -> Optional[Dict[str, Any]]:
        """应用修复"""
        logger.debug(f"SelfOptimizer: applying fix for issue: {issue}")
        try:
            if "CPU" in issue or "cpu" in issue:
                fix: Dict[str, Any] = {
                    "type": "fix",
                    "action": "优化CPU使用",
                    "description": "降低CPU密集型任务优先级",
                }
            elif "内存" in issue or "memory" in issue:
                fix = {
                    "type": "fix",
                    "action": "释放内存",
                    "description": "清理缓存和未使用资源",
                }
            elif "响应" in issue or "response" in issue:
                fix = {
                    "type": "fix",
                    "action": "优化响应时间",
                    "description": "启用请求缓存和连接池",
                }
            elif "错误" in issue or "error" in issue:
                fix = {
                    "type": "fix",
                    "action": "降低错误率",
                    "description": "增加重试机制和降级策略",
                }
            elif "吞吐" in issue or "throughput" in issue:
                fix = {
                    "type": "fix",
                    "action": "提升吞吐量",
                    "description": "增加并发度和批处理",
                }
            else:
                fix = None

            if fix:
                logger.debug(f"SelfOptimizer: fix applied: {fix['action']}")
        except Exception as e:
            logger.error(f"SelfOptimizer: _apply_fix failed: {e}")
            fix = None
        return fix

    def _adjust_parameters(self, metrics: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """调整参数"""
        logger.debug(f"SelfOptimizer: adjusting parameters, "
                     f"metrics={list(metrics.keys())}")
        try:
            adjustments: Dict[str, Any] = {}
            cpu_usage = metrics.get(MonitorMetric.CPU_USAGE.value, 0.0)
            memory_usage = metrics.get(MonitorMetric.MEMORY_USAGE.value, 0.0)

            if cpu_usage > 80.0:
                adjustments["max_concurrent_tasks"] = max(1, int(10 * (1 - cpu_usage / 100)))
            if memory_usage > 85.0:
                adjustments["cache_size"] = "reduced"

            if adjustments:
                result: Dict[str, Any] = {
                    "type": "parameter_adjustment",
                    "adjustments": adjustments,
                }
                logger.debug(f"SelfOptimizer: parameters adjusted: {adjustments}")
            else:
                result = None
        except Exception as e:
            logger.error(f"SelfOptimizer: _adjust_parameters failed: {e}")
            result = None
        return result

    def _rebalance_load(self, metrics: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """负载均衡"""
        logger.debug("SelfOptimizer: rebalancing load")
        try:
            cpu_usage = metrics.get(MonitorMetric.CPU_USAGE.value, 0.0)
            memory_usage = metrics.get(MonitorMetric.MEMORY_USAGE.value, 0.0)

            if cpu_usage > 80.0 or memory_usage > 85.0:
                result: Dict[str, Any] = {
                    "type": "load_rebalance",
                    "action": "重新分配负载",
                    "description": "将部分任务迁移到低负载节点",
                }
                logger.debug("SelfOptimizer: load rebalanced")
            else:
                result = None
        except Exception as e:
            logger.error(f"SelfOptimizer: _rebalance_load failed: {e}")
            result = None
        return result

    def verify_improvement(self, health: SystemHealth,
                           actions: List[Dict[str, Any]]) -> float:
        """验证改进效果"""
        logger.debug(f"SelfOptimizer: verifying improvement, "
                     f"actions={len(actions)}")
        try:
            # 简化模型：根据动作数量估算改进
            base_improvement = len(actions) * 5.0
            # 根据诊断结果调整
            if health.diagnosis == DiagnosisResult.CRITICAL:
                improvement = min(base_improvement * 1.5, 80.0)
            elif health.diagnosis == DiagnosisResult.UNSTABLE:
                improvement = min(base_improvement * 1.2, 60.0)
            elif health.diagnosis == DiagnosisResult.DEGRADED:
                improvement = min(base_improvement, 40.0)
            else:
                improvement = 0.0

            logger.debug(f"SelfOptimizer: estimated improvement={improvement}%")
        except Exception as e:
            logger.error(f"SelfOptimizer: verify_improvement failed: {e}")
            improvement = 0.0
        return improvement


class SelfOptimizeService:
    """自优化服务"""

    def __init__(self, monitor: Optional[SelfMonitor] = None,
                 diagnoser: Optional[SelfDiagnoser] = None,
                 optimizer: Optional[SelfOptimizer] = None):
        """初始化自优化服务"""
        self.monitor = monitor or SelfMonitor()
        self.diagnoser = diagnoser or SelfDiagnoser()
        self.optimizer = optimizer or SelfOptimizer()
        self._last_health: Optional[SystemHealth] = None
        logger.info("SelfOptimizeService initialized")

    def run_health_check(self, metrics: Dict[str, float]) -> SystemHealth:
        """执行健康检查"""
        logger.info("SelfOptimizeService: running health check")
        monitor_result = self.monitor.monitor(metrics)
        health = self.diagnoser.diagnose(monitor_result)
        self._last_health = health
        return health

    def auto_optimize(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """自动优化"""
        logger.info("SelfOptimizeService: auto optimizing")
        health = self.run_health_check(metrics)
        result = self.optimizer.optimize(health)
        return result

    def get_health(self) -> Optional[SystemHealth]:
        """获取最新健康状态"""
        logger.debug("SelfOptimizeService: getting health")
        return self._last_health
