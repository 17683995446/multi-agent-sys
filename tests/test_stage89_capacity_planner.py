"""
阶段89验收测试 - 智能容量规划与弹性伸缩
"""

import pytest
from src.architecture.capacity_planner import (
    ResourceType,
    ScalingAction,
    ResourceMetric,
    CapacityPlan,
    CapacityAnalyzer,
    CapacityPlanService,
)


class TestResourceType:
    """测试资源类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ResourceType.CPU.value == "cpu"
        assert ResourceType.MEMORY.value == "memory"
        assert ResourceType.DISK.value == "disk"
        assert ResourceType.NETWORK.value == "network"
        assert ResourceType.AGENTS.value == "agents"

    def test_all_types(self):
        """测试所有类型"""
        types = list(ResourceType)
        assert len(types) == 5


class TestScalingAction:
    """测试伸缩动作枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ScalingAction.SCALE_UP.value == "scale_up"
        assert ScalingAction.SCALE_DOWN.value == "scale_down"
        assert ScalingAction.MAINTAIN.value == "maintain"
        assert ScalingAction.EMERGENCY.value == "emergency"

    def test_all_actions(self):
        """测试所有动作"""
        actions = list(ScalingAction)
        assert len(actions) == 4


class TestResourceMetric:
    """测试资源指标"""

    def test_default_creation(self):
        """测试默认创建"""
        metric = ResourceMetric()
        assert metric.resource_type == ResourceType.CPU
        assert metric.current_usage == 0.0
        assert metric.peak_usage == 0.0
        assert metric.capacity == 100.0
        assert metric.utilization_pct == 0.0

    def test_custom_creation(self):
        """测试自定义创建"""
        metric = ResourceMetric(
            resource_type=ResourceType.MEMORY,
            current_usage=64.0,
            peak_usage=80.0,
            capacity=128.0,
            utilization_pct=50.0,
        )
        assert metric.resource_type == ResourceType.MEMORY
        assert metric.current_usage == 64.0
        assert metric.peak_usage == 80.0
        assert metric.capacity == 128.0
        assert metric.utilization_pct == 50.0

    def test_high_utilization(self):
        """测试高利用率"""
        metric = ResourceMetric(
            resource_type=ResourceType.CPU,
            current_usage=90.0,
            peak_usage=95.0,
            capacity=100.0,
            utilization_pct=90.0,
        )
        assert metric.utilization_pct == 90.0


class TestCapacityPlan:
    """测试容量规划"""

    def test_default_creation(self):
        """测试默认创建"""
        plan = CapacityPlan()
        assert plan.plan_id != ""
        assert plan.current_metrics == []
        assert plan.recommended_actions == []
        assert plan.estimated_cost == 0.0
        assert plan.risk_level == "low"

    def test_custom_creation(self):
        """测试自定义创建"""
        plan = CapacityPlan(
            current_metrics=[ResourceMetric(utilization_pct=85.0)],
            recommended_actions=[{"action": "scale_up"}],
            estimated_cost=100.0,
            risk_level="high",
        )
        assert len(plan.current_metrics) == 1
        assert len(plan.recommended_actions) == 1
        assert plan.estimated_cost == 100.0
        assert plan.risk_level == "high"

    def test_plan_id_unique(self):
        """测试规划ID唯一性"""
        p1 = CapacityPlan()
        p2 = CapacityPlan()
        assert p1.plan_id != p2.plan_id


class TestCapacityAnalyzer:
    """测试容量分析器"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = CapacityAnalyzer()
        assert len(analyzer._plans) == 0

    def test_analyze_low_utilization(self):
        """测试低利用率分析"""
        analyzer = CapacityAnalyzer()
        metrics = [
            ResourceMetric(
                resource_type=ResourceType.CPU,
                current_usage=20.0,
                peak_usage=30.0,
                capacity=100.0,
                utilization_pct=20.0,
            ),
        ]
        plan = analyzer.analyze(metrics)
        assert plan.risk_level == "low"
        assert len(plan.recommended_actions) == 1
        assert plan.recommended_actions[0]["action"] == ScalingAction.SCALE_DOWN.value

    def test_analyze_high_utilization(self):
        """测试高利用率分析"""
        analyzer = CapacityAnalyzer()
        metrics = [
            ResourceMetric(
                resource_type=ResourceType.CPU,
                current_usage=90.0,
                peak_usage=95.0,
                capacity=100.0,
                utilization_pct=90.0,
            ),
        ]
        plan = analyzer.analyze(metrics)
        assert plan.risk_level == "critical"
        assert len(plan.recommended_actions) == 1
        assert plan.recommended_actions[0]["action"] == ScalingAction.SCALE_UP.value

    def test_analyze_moderate_utilization(self):
        """测试中等利用率分析"""
        analyzer = CapacityAnalyzer()
        metrics = [
            ResourceMetric(
                resource_type=ResourceType.MEMORY,
                current_usage=60.0,
                peak_usage=70.0,
                capacity=100.0,
                utilization_pct=60.0,
            ),
        ]
        plan = analyzer.analyze(metrics)
        assert plan.recommended_actions[0]["action"] == ScalingAction.MAINTAIN.value

    def test_analyze_emergency(self):
        """测试紧急伸缩分析"""
        analyzer = CapacityAnalyzer()
        metrics = [
            ResourceMetric(
                resource_type=ResourceType.CPU,
                current_usage=98.0,
                peak_usage=99.0,
                capacity=100.0,
                utilization_pct=98.0,
            ),
        ]
        plan = analyzer.analyze(metrics)
        assert plan.risk_level == "critical"
        assert plan.recommended_actions[0]["action"] == ScalingAction.EMERGENCY.value

    def test_analyze_multiple_resources(self):
        """测试多资源分析"""
        analyzer = CapacityAnalyzer()
        metrics = [
            ResourceMetric(resource_type=ResourceType.CPU, current_usage=50.0,
                           peak_usage=60.0, capacity=100.0, utilization_pct=50.0),
            ResourceMetric(resource_type=ResourceType.MEMORY, current_usage=70.0,
                           peak_usage=80.0, capacity=100.0, utilization_pct=70.0),
            ResourceMetric(resource_type=ResourceType.DISK, current_usage=30.0,
                           peak_usage=40.0, capacity=100.0, utilization_pct=30.0),
        ]
        plan = analyzer.analyze(metrics)
        assert len(plan.recommended_actions) == 3
        assert len(plan.current_metrics) == 3

    def test_analyze_resource_usage(self):
        """测试分析资源使用"""
        analyzer = CapacityAnalyzer()
        metrics = [
            ResourceMetric(resource_type=ResourceType.CPU, current_usage=50.0,
                           peak_usage=70.0, capacity=100.0, utilization_pct=50.0),
        ]
        analysis = analyzer._analyze_resource_usage(metrics)
        assert "cpu" in analysis
        assert analysis["cpu"]["current_usage"] == 50.0
        assert analysis["cpu"]["headroom"] == 50.0

    def test_predict_demand(self):
        """测试预测需求"""
        analyzer = CapacityAnalyzer()
        analysis = {
            "cpu": {"current_usage": 50.0, "peak_usage": 70.0, "capacity": 100.0},
        }
        prediction = analyzer._predict_demand(analysis)
        assert "cpu" in prediction
        assert prediction["cpu"]["predicted_demand"] > 50.0

    def test_recommend_scaling(self):
        """测试推荐伸缩"""
        analyzer = CapacityAnalyzer()
        prediction = {
            "cpu": {"predicted_demand": 120.0, "growth_rate": 0.2},
        }
        metrics = [
            ResourceMetric(resource_type=ResourceType.CPU, current_usage=90.0,
                           peak_usage=95.0, capacity=100.0, utilization_pct=90.0),
        ]
        actions = analyzer._recommend_scaling(prediction, metrics)
        assert len(actions) == 1
        assert actions[0]["action"] == ScalingAction.SCALE_UP.value

    def test_generate_plan(self):
        """测试生成规划报告"""
        analyzer = CapacityAnalyzer()
        metrics = [
            ResourceMetric(resource_type=ResourceType.CPU, current_usage=50.0,
                           peak_usage=60.0, capacity=100.0, utilization_pct=50.0),
        ]
        plan = analyzer.analyze(metrics)
        report = analyzer.generate_plan(plan.plan_id)
        assert "plan_id" in report
        assert "risk_level" in report
        assert "metrics_summary" in report
        assert "recommended_actions" in report

    def test_generate_plan_not_found(self):
        """测试生成不存在的规划报告"""
        analyzer = CapacityAnalyzer()
        report = analyzer.generate_plan("nonexistent")
        assert "message" in report

    def test_analyze_saves_plan(self):
        """测试分析后保存规划"""
        analyzer = CapacityAnalyzer()
        metrics = [ResourceMetric(utilization_pct=50.0)]
        plan = analyzer.analyze(metrics)
        assert plan.plan_id in analyzer._plans


class TestCapacityPlanService:
    """测试容量规划服务"""

    def test_initialization(self):
        """测试初始化"""
        service = CapacityPlanService()
        assert service.analyzer is not None

    def test_initialization_with_analyzer(self):
        """测试使用自定义分析器初始化"""
        analyzer = CapacityAnalyzer()
        service = CapacityPlanService(analyzer=analyzer)
        assert service.analyzer is analyzer

    def test_analyze(self):
        """测试执行分析"""
        service = CapacityPlanService()
        metrics = [
            ResourceMetric(resource_type=ResourceType.CPU, current_usage=60.0,
                           peak_usage=70.0, capacity=100.0, utilization_pct=60.0),
        ]
        plan = service.analyze(metrics)
        assert isinstance(plan, CapacityPlan)
        assert len(plan.current_metrics) == 1

    def test_get_plan(self):
        """测试获取规划"""
        service = CapacityPlanService()
        metrics = [ResourceMetric(utilization_pct=50.0)]
        plan = service.analyze(metrics)
        result = service.get_plan(plan.plan_id)
        assert result is not None
        assert result.plan_id == plan.plan_id

    def test_get_plan_not_found(self):
        """测试获取不存在的规划"""
        service = CapacityPlanService()
        result = service.get_plan("nonexistent")
        assert result is None

    def test_get_recommendations(self):
        """测试获取伸缩推荐"""
        service = CapacityPlanService()
        metrics = [
            ResourceMetric(resource_type=ResourceType.CPU, current_usage=90.0,
                           peak_usage=95.0, capacity=100.0, utilization_pct=90.0),
        ]
        plan = service.analyze(metrics)
        recommendations = service.get_recommendations(plan.plan_id)
        assert len(recommendations) >= 1
        assert recommendations[0]["action"] == ScalingAction.SCALE_UP.value

    def test_get_recommendations_not_found(self):
        """测试获取不存在的推荐"""
        service = CapacityPlanService()
        recommendations = service.get_recommendations("nonexistent")
        assert recommendations == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
