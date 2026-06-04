"""
质量门禁系统
职责：质量指标管理、门禁评估、质量报告生成
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class GateStatus(str, Enum):
    """门禁状态"""
    OPEN = "open"
    CLOSED = "closed"
    CONDITIONAL = "conditional"


@dataclass
class QualityMetric:
    """质量指标"""
    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    value: float = 0.0
    threshold: float = 0.0
    passed: bool = False

    def __post_init__(self):
        logger.debug(f"QualityMetric created: id={self.metric_id}, name={self.name}, "
                    f"value={self.value}, threshold={self.threshold}")


@dataclass
class QualityGate:
    """质量门禁"""
    gate_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    metrics: List[QualityMetric] = field(default_factory=list)
    status: GateStatus = GateStatus.OPEN
    condition: str = ""

    def __post_init__(self):
        logger.debug(f"QualityGate created: id={self.gate_id}, name={self.name}")


class QualityGateEvaluator:
    """质量门禁评估器"""

    def __init__(self):
        self.gates: Dict[str, QualityGate] = {}
        logger.info("QualityGateEvaluator initialized")

    def create_gate(self, name: str = "", condition: str = "") -> QualityGate:
        """创建质量门禁"""
        try:
            gate = QualityGate(name=name, condition=condition)
            self.gates[gate.gate_id] = gate
            logger.info(f"QualityGateEvaluator: created gate id={gate.gate_id}, name={name}")
        except Exception as e:
            logger.error(f"QualityGateEvaluator: create_gate failed: {e}")
            raise

        return gate

    def add_metric(self, gate_id: str, name: str = "", value: float = 0.0,
                   threshold: float = 0.0) -> Optional[QualityMetric]:
        """向门禁添加质量指标"""
        if gate_id not in self.gates:
            logger.warning(f"QualityGateEvaluator: gate_id={gate_id} not found")
            return None

        try:
            metric = QualityMetric(
                name=name,
                value=value,
                threshold=threshold,
                passed=value >= threshold,
            )
            self.gates[gate_id].metrics.append(metric)
            logger.info(f"QualityGateEvaluator: added metric name={name} to gate={gate_id}, "
                       f"value={value}, threshold={threshold}, passed={metric.passed}")
        except Exception as e:
            logger.error(f"QualityGateEvaluator: add_metric failed: {e}")
            return None

        return metric

    def evaluate_gate(self, gate_id: str) -> Optional[GateStatus]:
        """评估单个门禁"""
        if gate_id not in self.gates:
            logger.warning(f"QualityGateEvaluator: gate_id={gate_id} not found")
            return None

        try:
            gate = self.gates[gate_id]

            if not gate.metrics:
                gate.status = GateStatus.OPEN
                logger.debug(f"QualityGateEvaluator: gate={gate_id} has no metrics, status=OPEN")
                return gate.status

            # 重新评估每个指标
            for metric in gate.metrics:
                metric.passed = metric.value >= metric.threshold

            all_passed = all(m.passed for m in gate.metrics)
            failed_count = sum(1 for m in gate.metrics if not m.passed)

            if all_passed:
                gate.status = GateStatus.OPEN
            elif failed_count == len(gate.metrics):
                gate.status = GateStatus.CLOSED
            else:
                gate.status = GateStatus.CONDITIONAL

            logger.info(f"QualityGateEvaluator: evaluated gate={gate_id}, "
                       f"status={gate.status.value}, "
                       f"passed={sum(1 for m in gate.metrics if m.passed)}/{len(gate.metrics)}")
        except Exception as e:
            logger.error(f"QualityGateEvaluator: evaluate_gate failed: {e}")
            return None

        return gate.status

    def evaluate_all(self) -> Dict[str, GateStatus]:
        """评估所有门禁"""
        try:
            results: Dict[str, GateStatus] = {}
            for gate_id in self.gates:
                status = self.evaluate_gate(gate_id)
                if status is not None:
                    results[gate_id] = status

            logger.info(f"QualityGateEvaluator: evaluated all gates, count={len(results)}")
        except Exception as e:
            logger.error(f"QualityGateEvaluator: evaluate_all failed: {e}")
            return {}

        return results


class QualityGateService:
    """质量门禁服务"""

    def __init__(self):
        self.evaluator = QualityGateEvaluator()
        logger.info("QualityGateService initialized")

    def check_quality(self, gate_id: str) -> Dict[str, Any]:
        """检查质量"""
        try:
            status = self.evaluator.evaluate_gate(gate_id)
            if status is None:
                logger.warning(f"QualityGateService: gate={gate_id} not found")
                return {"gate_id": gate_id, "status": "not_found", "passed": False}

            gate = self.evaluator.gates[gate_id]
            result = {
                "gate_id": gate_id,
                "status": status.value,
                "passed": status == GateStatus.OPEN,
                "metrics": [
                    {
                        "name": m.name,
                        "value": m.value,
                        "threshold": m.threshold,
                        "passed": m.passed,
                    }
                    for m in gate.metrics
                ],
            }
            logger.info(f"QualityGateService: quality check gate={gate_id}, "
                       f"status={status.value}")
        except Exception as e:
            logger.error(f"QualityGateService: check_quality failed: {e}")
            return {"gate_id": gate_id, "status": "error", "passed": False}

        return result

    def get_gate_status(self, gate_id: str) -> Optional[GateStatus]:
        """获取门禁状态"""
        if gate_id not in self.evaluator.gates:
            logger.debug(f"QualityGateService: gate={gate_id} not found")
            return None

        status = self.evaluator.gates[gate_id].status
        logger.debug(f"QualityGateService: gate={gate_id}, status={status.value}")
        return status

    def get_quality_report(self) -> Dict[str, Any]:
        """获取质量报告"""
        try:
            all_statuses = self.evaluator.evaluate_all()
            report = {
                "total_gates": len(self.evaluator.gates),
                "open": sum(1 for s in all_statuses.values() if s == GateStatus.OPEN),
                "closed": sum(1 for s in all_statuses.values() if s == GateStatus.CLOSED),
                "conditional": sum(1 for s in all_statuses.values() if s == GateStatus.CONDITIONAL),
                "gates": {},
            }

            for gate_id, gate in self.evaluator.gates.items():
                report["gates"][gate_id] = {
                    "name": gate.name,
                    "status": gate.status.value,
                    "metric_count": len(gate.metrics),
                    "passed_metrics": sum(1 for m in gate.metrics if m.passed),
                }

            logger.info(f"QualityGateService: quality report, "
                       f"total={report['total_gates']}, "
                       f"open={report['open']}, closed={report['closed']}, "
                       f"conditional={report['conditional']}")
        except Exception as e:
            logger.error(f"QualityGateService: get_quality_report failed: {e}")
            return {"total_gates": 0, "open": 0, "closed": 0, "conditional": 0, "gates": {}}

        return report
