"""
智能容量规划与弹性伸缩模块

职责：分析资源使用情况、预测需求、推荐伸缩策略、生成容量规划

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    AGENTS = "agents"


class ScalingAction(str, Enum):
    """伸缩动作"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    EMERGENCY = "emergency"


@dataclass
class ResourceMetric:
    """资源指标"""
    resource_type: ResourceType = ResourceType.CPU
    current_usage: float = 0.0
    peak_usage: float = 0.0
    capacity: float = 100.0
    utilization_pct: float = 0.0

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"ResourceMetric created: type={self.resource_type.value}, "
                     f"current={self.current_usage}, utilization={self.utilization_pct}%")


@dataclass
class CapacityPlan:
    """容量规划"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_metrics: List[ResourceMetric] = field(default_factory=list)
    recommended_actions: List[Dict[str, Any]] = field(default_factory=list)
    estimated_cost: float = 0.0
    risk_level: str = "low"

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"CapacityPlan created: plan_id={self.plan_id}, "
                     f"metrics={len(self.current_metrics)}, "
                     f"actions={len(self.recommended_actions)}")


class CapacityAnalyzer:
    """容量分析器"""

    def __init__(self):
        """初始化容量分析器"""
        self._plans: Dict[str, CapacityPlan] = {}
        logger.info("CapacityAnalyzer initialized")

    def analyze(self, metrics: List[ResourceMetric]) -> CapacityPlan:
        """分析资源指标，生成容量规划"""
        logger.info(f"CapacityAnalyzer: analyzing {len(metrics)} metrics")
        try:
            # 1. 分析资源使用
            usage_analysis = self._analyze_resource_usage(metrics)
            # 2. 预测需求
            demand_prediction = self._predict_demand(usage_analysis)
            # 3. 推荐伸缩
            actions = self._recommend_scaling(demand_prediction, metrics)

            # 计算风险等级
            risk_level = "low"
            for metric in metrics:
                if metric.utilization_pct >= 90.0:
                    risk_level = "critical"
                    break
                elif metric.utilization_pct > 75.0:
                    risk_level = "high"

            # 计算预估成本
            estimated_cost = sum(
                a.get("estimated_cost", 0.0) for a in actions
            )

            plan = CapacityPlan(
                current_metrics=metrics,
                recommended_actions=actions,
                estimated_cost=estimated_cost,
                risk_level=risk_level,
            )
            self._plans[plan.plan_id] = plan

            logger.info(f"CapacityAnalyzer: plan generated, "
                        f"plan_id={plan.plan_id}, "
                        f"risk_level={risk_level}, "
                        f"actions={len(actions)}")
        except Exception as e:
            logger.error(f"CapacityAnalyzer: analyze failed: {e}")
            plan = CapacityPlan(current_metrics=metrics)
        return plan

    def _analyze_resource_usage(self, metrics: List[ResourceMetric]) -> Dict[str, Any]:
        """分析资源使用情况"""
        logger.debug(f"CapacityAnalyzer: analyzing resource usage, "
                     f"metrics={len(metrics)}")
        try:
            analysis: Dict[str, Any] = {}
            for metric in metrics:
                analysis[metric.resource_type.value] = {
                    "current_usage": metric.current_usage,
                    "peak_usage": metric.peak_usage,
                    "capacity": metric.capacity,
                    "utilization_pct": metric.utilization_pct,
                    "headroom": metric.capacity - metric.current_usage,
                }
            logger.debug(f"CapacityAnalyzer: resource usage analysis completed")
        except Exception as e:
            logger.error(f"CapacityAnalyzer: _analyze_resource_usage failed: {e}")
            analysis = {}
        return analysis

    def _predict_demand(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """预测资源需求"""
        logger.debug(f"CapacityAnalyzer: predicting demand, "
                     f"resources={len(analysis)}")
        try:
            prediction: Dict[str, Any] = {}
            for resource_type, data in analysis.items():
                current = data.get("current_usage", 0.0)
                peak = data.get("peak_usage", 0.0)
                # 简单预测：基于当前和峰值估算未来需求
                predicted = max(current * 1.2, peak * 1.1)
                prediction[resource_type] = {
                    "predicted_demand": predicted,
                    "growth_rate": 0.2 if current > 0 else 0.0,
                }
            logger.debug(f"CapacityAnalyzer: demand prediction completed")
        except Exception as e:
            logger.error(f"CapacityAnalyzer: _predict_demand failed: {e}")
            prediction = {}
        return prediction

    def _recommend_scaling(self, prediction: Dict[str, Any],
                           metrics: List[ResourceMetric]) -> List[Dict[str, Any]]:
        """推荐伸缩策略"""
        logger.debug(f"CapacityAnalyzer: recommending scaling, "
                     f"predictions={len(prediction)}")
        try:
            actions: List[Dict[str, Any]] = []
            for metric in metrics:
                resource_type = metric.resource_type.value
                pred = prediction.get(resource_type, {})
                predicted_demand = pred.get("predicted_demand", 0.0)

                if metric.utilization_pct > 95.0:
                    action = ScalingAction.EMERGENCY
                    estimated_cost = 100.0
                elif metric.utilization_pct > 85.0:
                    action = ScalingAction.SCALE_UP
                    estimated_cost = (predicted_demand - metric.capacity) * 0.5
                    if estimated_cost < 0:
                        estimated_cost = 50.0
                elif metric.utilization_pct < 30.0:
                    action = ScalingAction.SCALE_DOWN
                    estimated_cost = -20.0
                else:
                    action = ScalingAction.MAINTAIN
                    estimated_cost = 0.0

                actions.append({
                    "resource_type": resource_type,
                    "action": action.value,
                    "current_utilization": metric.utilization_pct,
                    "predicted_demand": predicted_demand,
                    "estimated_cost": max(0.0, estimated_cost),
                })

            logger.debug(f"CapacityAnalyzer: scaling recommendations completed, "
                         f"actions={len(actions)}")
        except Exception as e:
            logger.error(f"CapacityAnalyzer: _recommend_scaling failed: {e}")
            actions = []
        return actions

    def generate_plan(self, plan_id: str) -> Dict[str, Any]:
        """生成容量规划报告"""
        logger.info(f"CapacityAnalyzer: generating plan, plan_id={plan_id}")
        try:
            plan = self._plans.get(plan_id)
            if plan is None:
                return {"message": "未找到容量规划"}

            report: Dict[str, Any] = {
                "plan_id": plan.plan_id,
                "risk_level": plan.risk_level,
                "estimated_cost": plan.estimated_cost,
                "metrics_summary": [
                    {
                        "resource_type": m.resource_type.value,
                        "current_usage": m.current_usage,
                        "peak_usage": m.peak_usage,
                        "capacity": m.capacity,
                        "utilization_pct": m.utilization_pct,
                    }
                    for m in plan.current_metrics
                ],
                "recommended_actions": plan.recommended_actions,
                "timestamp": time.time(),
            }
            logger.info(f"CapacityAnalyzer: plan generated, plan_id={plan_id}")
        except Exception as e:
            logger.error(f"CapacityAnalyzer: generate_plan failed: {e}")
            report = {"error": str(e)}
        return report


class CapacityPlanService:
    """容量规划服务"""

    def __init__(self, analyzer: Optional[CapacityAnalyzer] = None):
        """初始化容量规划服务"""
        self.analyzer = analyzer or CapacityAnalyzer()
        logger.info("CapacityPlanService initialized")

    def analyze(self, metrics: List[ResourceMetric]) -> CapacityPlan:
        """执行容量分析"""
        logger.info("CapacityPlanService: analyzing capacity")
        return self.analyzer.analyze(metrics)

    def get_plan(self, plan_id: str) -> Optional[CapacityPlan]:
        """获取容量规划"""
        logger.debug(f"CapacityPlanService: getting plan, plan_id={plan_id}")
        return self.analyzer._plans.get(plan_id)

    def get_recommendations(self, plan_id: str) -> List[Dict[str, Any]]:
        """获取伸缩推荐"""
        logger.debug(f"CapacityPlanService: getting recommendations, "
                     f"plan_id={plan_id}")
        plan = self.analyzer._plans.get(plan_id)
        if plan is None:
            return []
        return plan.recommended_actions
