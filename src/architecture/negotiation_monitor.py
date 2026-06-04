"""
协商性能监控与可视化
职责：性能指标采集、协商监控、瓶颈检测、报告生成
"""

import uuid
import time
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """指标类型"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ACCEPTANCE_RATE = "acceptance_rate"
    CONCESSION_RATE = "concession_rate"
    DEADLOCK_RATE = "deadlock_rate"


@dataclass
class MetricRecord:
    """指标记录"""
    metric_type: MetricType = MetricType.LATENCY
    value: float = 0.0
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"MetricRecord created: type={self.metric_type}, value={self.value}")


class PerformanceMetrics:
    """性能指标集合"""

    def __init__(self):
        self.records: List[MetricRecord] = []
        logger.info("PerformanceMetrics initialized")

    def add_metric(self, metric_type: MetricType, value: float,
                   session_id: str = "", metadata: Optional[Dict[str, Any]] = None) -> MetricRecord:
        """添加指标记录"""
        # 输入验证
        if not isinstance(metric_type, MetricType):
            logger.warning(f"add_metric: invalid metric_type={metric_type}")
            raise ValueError(f"无效的指标类型: {metric_type}")

        # 业务逻辑
        try:
            record = MetricRecord(
                metric_type=metric_type,
                value=value,
                session_id=session_id,
                metadata=metadata or {},
            )
            self.records.append(record)
            logger.info(f"PerformanceMetrics: added {metric_type.value}={value} for session={session_id[:8] if session_id else 'N/A'}")
        except Exception as e:
            # 异常处理
            logger.error(f"PerformanceMetrics: add_metric failed: {e}")
            raise

        # 返回结果
        return record

    def get_metrics(self, metric_type: Optional[MetricType] = None,
                    session_id: Optional[str] = None) -> List[MetricRecord]:
        """获取指标记录"""
        # 业务逻辑
        try:
            result = self.records
            if metric_type is not None:
                result = [r for r in result if r.metric_type == metric_type]
            if session_id is not None:
                result = [r for r in result if r.session_id == session_id]
            logger.debug(f"PerformanceMetrics: get_metrics returned {len(result)} records")
        except Exception as e:
            # 异常处理
            logger.error(f"PerformanceMetrics: get_metrics failed: {e}")
            return []

        # 返回结果
        return result

    def get_average(self, metric_type: MetricType,
                    session_id: Optional[str] = None) -> float:
        """获取指标平均值"""
        # 输入验证
        records = self.get_metrics(metric_type=metric_type, session_id=session_id)

        # 业务逻辑
        if not records:
            logger.debug(f"PerformanceMetrics: no records for {metric_type.value}")
            return 0.0

        total = sum(r.value for r in records)
        avg = total / len(records)
        logger.debug(f"PerformanceMetrics: average {metric_type.value}={avg:.4f}")

        # 返回结果
        return avg

    def get_trend(self, metric_type: MetricType,
                  session_id: Optional[str] = None) -> str:
        """获取指标趋势"""
        # 输入验证
        records = self.get_metrics(metric_type=metric_type, session_id=session_id)

        # 业务逻辑
        try:
            if len(records) < 2:
                logger.debug(f"PerformanceMetrics: not enough data for trend")
                return "stable"

            # 比较前半段和后半段的平均值
            mid = len(records) // 2
            first_half_avg = sum(r.value for r in records[:mid]) / mid
            second_half_avg = sum(r.value for r in records[mid:]) / (len(records) - mid)

            diff = second_half_avg - first_half_avg
            threshold = first_half_avg * 0.1 if first_half_avg != 0 else 0.01

            if diff > threshold:
                trend = "increasing"
            elif diff < -threshold:
                trend = "decreasing"
            else:
                trend = "stable"

            logger.debug(f"PerformanceMetrics: trend for {metric_type.value} = {trend}")
        except Exception as e:
            # 异常处理
            logger.error(f"PerformanceMetrics: get_trend failed: {e}")
            return "stable"

        # 返回结果
        return trend


class NegotiationMonitor:
    """协商监控器"""

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.monitoring: bool = False
        logger.info("NegotiationMonitor initialized")

    def record_metric(self, session_id: str, metric_type: MetricType,
                      value: float, metadata: Optional[Dict[str, Any]] = None) -> MetricRecord:
        """记录指标"""
        # 输入验证
        if not session_id:
            logger.warning("record_metric: session_id is empty")
            raise ValueError("session_id不能为空")

        # 业务逻辑
        try:
            if session_id not in self.metrics:
                self.metrics[session_id] = PerformanceMetrics()
                self.sessions[session_id] = {
                    "start_time": time.time(),
                    "metric_count": 0,
                }

            record = self.metrics[session_id].add_metric(
                metric_type=metric_type,
                value=value,
                session_id=session_id,
                metadata=metadata or {},
            )
            self.sessions[session_id]["metric_count"] += 1
            logger.info(f"NegotiationMonitor: recorded {metric_type.value}={value} "
                       f"for session={session_id[:8]}")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationMonitor: record_metric failed: {e}")
            raise

        # 返回结果
        return record

    def get_session_metrics(self, session_id: str,
                            metric_type: Optional[MetricType] = None) -> List[MetricRecord]:
        """获取会话指标"""
        # 输入验证
        if not session_id or session_id not in self.metrics:
            logger.debug(f"NegotiationMonitor: session={session_id[:8] if session_id else 'N/A'} not found")
            return []

        # 业务逻辑 + 返回结果
        return self.metrics[session_id].get_metrics(metric_type=metric_type)

    def get_performance_summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """获取性能摘要"""
        # 业务逻辑
        try:
            if session_id:
                if session_id not in self.metrics:
                    return {"session_id": session_id, "metrics": {}}
                pm = self.metrics[session_id]
                summary = {
                    "session_id": session_id,
                    "metrics": {},
                }
                for mt in MetricType:
                    records = pm.get_metrics(metric_type=mt)
                    if records:
                        summary["metrics"][mt.value] = {
                            "count": len(records),
                            "average": pm.get_average(mt),
                            "trend": pm.get_trend(mt),
                            "latest": records[-1].value,
                        }
                logger.debug(f"NegotiationMonitor: summary for session={session_id[:8]}")
                return summary
            else:
                # 全部会话摘要
                summary = {
                    "total_sessions": len(self.sessions),
                    "sessions": {},
                }
                for sid in self.metrics:
                    summary["sessions"][sid] = self.get_performance_summary(sid)
                logger.debug(f"NegotiationMonitor: global summary, {len(self.sessions)} sessions")
                return summary
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationMonitor: get_performance_summary failed: {e}")
            return {"error": str(e)}

    def detect_bottleneck(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """检测瓶颈"""
        # 业务逻辑
        try:
            bottlenecks = []
            target_sessions = [session_id] if session_id else list(self.metrics.keys())

            for sid in target_sessions:
                if sid not in self.metrics:
                    continue

                pm = self.metrics[sid]

                # 检查高延迟
                avg_latency = pm.get_average(MetricType.LATENCY, session_id=sid)
                if avg_latency > 1000.0:  # 超过1000ms视为瓶颈
                    bottlenecks.append({
                        "session_id": sid,
                        "type": "high_latency",
                        "metric": MetricType.LATENCY.value,
                        "value": avg_latency,
                        "threshold": 1000.0,
                    })

                # 检查低吞吐量
                avg_throughput = pm.get_average(MetricType.THROUGHPUT, session_id=sid)
                if avg_throughput > 0 and avg_throughput < 1.0:  # 低于1 ops/s
                    bottlenecks.append({
                        "session_id": sid,
                        "type": "low_throughput",
                        "metric": MetricType.THROUGHPUT.value,
                        "value": avg_throughput,
                        "threshold": 1.0,
                    })

                # 检查高死锁率
                avg_deadlock = pm.get_average(MetricType.DEADLOCK_RATE, session_id=sid)
                if avg_deadlock > 0.5:  # 超过50%死锁率
                    bottlenecks.append({
                        "session_id": sid,
                        "type": "high_deadlock_rate",
                        "metric": MetricType.DEADLOCK_RATE.value,
                        "value": avg_deadlock,
                        "threshold": 0.5,
                    })

                # 检查低接受率
                avg_acceptance = pm.get_average(MetricType.ACCEPTANCE_RATE, session_id=sid)
                if avg_acceptance > 0 and avg_acceptance < 0.2:
                    bottlenecks.append({
                        "session_id": sid,
                        "type": "low_acceptance_rate",
                        "metric": MetricType.ACCEPTANCE_RATE.value,
                        "value": avg_acceptance,
                        "threshold": 0.2,
                    })

            if bottlenecks:
                logger.warning(f"NegotiationMonitor: detected {len(bottlenecks)} bottleneck(s)")
            else:
                logger.debug(f"NegotiationMonitor: no bottlenecks detected")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationMonitor: detect_bottleneck failed: {e}")
            return []

        # 返回结果
        return bottlenecks


class MetricsReporter:
    """指标报告器"""

    def __init__(self):
        logger.info("MetricsReporter initialized")

    def generate_text_report(self, summary: Dict[str, Any]) -> str:
        """生成文本报告"""
        # 输入验证
        if not summary:
            logger.debug("generate_text_report: empty summary")
            return "无监控数据"

        # 业务逻辑
        try:
            lines = []
            lines.append("=" * 50)
            lines.append("协商性能监控报告")
            lines.append("=" * 50)

            if "total_sessions" in summary:
                lines.append(f"总会话数: {summary['total_sessions']}")
                for sid, s_data in summary.get("sessions", {}).items():
                    lines.append(f"\n--- 会话: {sid[:8]} ---")
                    for metric_name, metric_data in s_data.get("metrics", {}).items():
                        lines.append(f"  {metric_name}: 平均={metric_data.get('average', 0):.2f}, "
                                    f"趋势={metric_data.get('trend', 'N/A')}, "
                                    f"最新={metric_data.get('latest', 0):.2f}")
            elif "metrics" in summary:
                lines.append(f"会话: {summary.get('session_id', 'N/A')[:8]}")
                for metric_name, metric_data in summary.get("metrics", {}).items():
                    lines.append(f"  {metric_name}: 平均={metric_data.get('average', 0):.2f}, "
                                f"趋势={metric_data.get('trend', 'N/A')}, "
                                f"最新={metric_data.get('latest', 0):.2f}")

            lines.append("=" * 50)
            report = "\n".join(lines)
            logger.debug("MetricsReporter: text report generated")
        except Exception as e:
            # 异常处理
            logger.error(f"MetricsReporter: generate_text_report failed: {e}")
            return f"报告生成失败: {e}"

        # 返回结果
        return report

    def generate_json_report(self, summary: Dict[str, Any]) -> str:
        """生成JSON报告"""
        # 输入验证
        if not summary:
            logger.debug("generate_json_report: empty summary")
            return "{}"

        # 业务逻辑
        try:
            report = json.dumps(summary, indent=2, ensure_ascii=False, default=str)
            logger.debug("MetricsReporter: JSON report generated")
        except Exception as e:
            # 异常处理
            logger.error(f"MetricsReporter: generate_json_report failed: {e}")
            return '{"error": "报告生成失败"}'

        # 返回结果
        return report

    def generate_timeline(self, records: List[MetricRecord]) -> List[Dict[str, Any]]:
        """生成时间线"""
        # 输入验证
        if not records:
            logger.debug("generate_timeline: no records")
            return []

        # 业务逻辑
        try:
            timeline = []
            for record in sorted(records, key=lambda r: r.timestamp):
                timeline.append({
                    "timestamp": record.timestamp,
                    "metric_type": record.metric_type.value,
                    "value": record.value,
                    "session_id": record.session_id,
                })
            logger.debug(f"MetricsReporter: timeline generated with {len(timeline)} entries")
        except Exception as e:
            # 异常处理
            logger.error(f"MetricsReporter: generate_timeline failed: {e}")
            return []

        # 返回结果
        return timeline


class NegotiationMonitorService:
    """协商监控服务"""

    def __init__(self):
        self.monitor = NegotiationMonitor()
        self.reporter = MetricsReporter()
        self._monitoring: bool = False
        logger.info("NegotiationMonitorService initialized")

    def start_monitoring(self, session_id: str = "") -> bool:
        """开始监控"""
        # 业务逻辑
        try:
            self._monitoring = True
            if session_id:
                if session_id not in self.monitor.metrics:
                    self.monitor.metrics[session_id] = PerformanceMetrics()
                    self.monitor.sessions[session_id] = {
                        "start_time": time.time(),
                        "metric_count": 0,
                    }
            logger.info(f"NegotiationMonitorService: monitoring started"
                       f"{', session=' + session_id[:8] if session_id else ''}")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationMonitorService: start_monitoring failed: {e}")
            return False

        # 返回结果
        return True

    def stop_monitoring(self) -> bool:
        """停止监控"""
        # 业务逻辑
        try:
            self._monitoring = False
            logger.info("NegotiationMonitorService: monitoring stopped")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationMonitorService: stop_monitoring failed: {e}")
            return False

        # 返回结果
        return True

    def get_report(self, session_id: Optional[str] = None,
                   format: str = "text") -> Any:
        """获取报告"""
        # 业务逻辑
        try:
            summary = self.monitor.get_performance_summary(session_id)

            if format == "json":
                report = self.reporter.generate_json_report(summary)
            elif format == "timeline":
                if session_id:
                    records = self.monitor.get_session_metrics(session_id)
                else:
                    records = []
                    for pm in self.monitor.metrics.values():
                        records.extend(pm.records)
                report = self.reporter.generate_timeline(records)
            else:
                report = self.reporter.generate_text_report(summary)

            logger.info(f"NegotiationMonitorService: report generated, format={format}")
        except Exception as e:
            # 异常处理
            logger.error(f"NegotiationMonitorService: get_report failed: {e}")
            return None

        # 返回结果
        return report


_global_monitor_service: Optional[NegotiationMonitorService] = None


def get_monitor_service() -> NegotiationMonitorService:
    """获取全局监控服务"""
    global _global_monitor_service
    if _global_monitor_service is None:
        _global_monitor_service = NegotiationMonitorService()
    return _global_monitor_service


def reset_monitor_service() -> None:
    """重置全局监控服务"""
    global _global_monitor_service
    _global_monitor_service = None
