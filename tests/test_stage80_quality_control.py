"""
阶段80验收测试 - 工程质量风控体系
"""

import pytest
from src.architecture.quality_control import (
    QualityDimension,
    QualityLevel,
    QualityMetric,
    QualityAssessment,
    QualityController,
    QualityControlService,
)


class TestQualityDimension:
    """测试质量维度枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert QualityDimension.RELIABILITY.value == "reliability"
        assert QualityDimension.MAINTAINABILITY.value == "maintainability"
        assert QualityDimension.EFFICIENCY.value == "efficiency"
        assert QualityDimension.SECURITY.value == "security"
        assert QualityDimension.USABILITY.value == "usability"

    def test_all_dimensions(self):
        """测试所有质量维度"""
        dimensions = list(QualityDimension)
        assert len(dimensions) == 5


class TestQualityLevel:
    """测试质量等级枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert QualityLevel.EXCELLENT.value == "excellent"
        assert QualityLevel.GOOD.value == "good"
        assert QualityLevel.ACCEPTABLE.value == "acceptable"
        assert QualityLevel.POOR.value == "poor"
        assert QualityLevel.CRITICAL.value == "critical"

    def test_all_levels(self):
        """测试所有质量等级"""
        levels = list(QualityLevel)
        assert len(levels) == 5


class TestQualityMetric:
    """测试质量指标"""

    def test_default_creation(self):
        """测试默认创建"""
        metric = QualityMetric()
        assert metric.dimension == QualityDimension.RELIABILITY
        assert metric.level == QualityLevel.GOOD
        assert metric.score == 80.0
        assert metric.description == ""
        assert metric.recommendations == []

    def test_custom_creation(self):
        """测试自定义创建"""
        metric = QualityMetric(
            dimension=QualityDimension.SECURITY,
            level=QualityLevel.CRITICAL,
            score=25.0,
            description="安全性严重不足",
            recommendations=["修复安全漏洞", "加强认证"],
        )
        assert metric.dimension == QualityDimension.SECURITY
        assert metric.level == QualityLevel.CRITICAL
        assert metric.score == 25.0
        assert len(metric.recommendations) == 2


class TestQualityAssessment:
    """测试质量评估"""

    def test_default_creation(self):
        """测试默认创建"""
        assessment = QualityAssessment()
        assert assessment.overall_score == 80.0
        assert assessment.metrics == []
        assert assessment.risk_areas == []
        assert assessment.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        assessment = QualityAssessment(
            overall_score=75.0,
            metrics=[QualityMetric()],
            risk_areas=["安全性不足"],
        )
        assert assessment.overall_score == 75.0
        assert len(assessment.metrics) == 1
        assert len(assessment.risk_areas) == 1


class TestQualityController:
    """测试质量控制器"""

    def test_initialization(self):
        """测试初始化"""
        controller = QualityController()
        assert controller._assessments == []

    def test_assess_good_project(self):
        """测试评估良好项目"""
        controller = QualityController()
        project_data = {
            "bug_count": 2,
            "crash_rate": 0.1,
            "test_pass_rate": 95.0,
            "code_complexity": 8,
            "doc_coverage": 70.0,
            "duplication_rate": 3.0,
            "avg_response_time": 200,
            "memory_usage": 40.0,
            "cpu_usage": 30.0,
            "vulnerability_count": 0,
            "auth_coverage": 95.0,
            "data_encryption": True,
        }
        assessment = controller.assess(project_data)
        assert assessment.overall_score >= 70.0
        assert len(assessment.metrics) == 4

    def test_assess_poor_project(self):
        """测试评估差项目"""
        controller = QualityController()
        project_data = {
            "bug_count": 30,
            "crash_rate": 8.0,
            "test_pass_rate": 50.0,
            "code_complexity": 40,
            "doc_coverage": 10.0,
            "duplication_rate": 25.0,
            "avg_response_time": 3000,
            "memory_usage": 90.0,
            "cpu_usage": 85.0,
            "vulnerability_count": 15,
            "auth_coverage": 30.0,
            "data_encryption": False,
        }
        assessment = controller.assess(project_data)
        assert assessment.overall_score < 60.0
        assert len(assessment.risk_areas) > 0

    def test_assess_reliability(self):
        """测试评估可靠性"""
        controller = QualityController()
        project_data = {"bug_count": 5, "crash_rate": 0.5, "test_pass_rate": 90.0}
        metric = controller._assess_reliability(project_data)
        assert metric.dimension == QualityDimension.RELIABILITY
        assert metric.score > 0

    def test_assess_reliability_high_bugs(self):
        """测试高Bug数可靠性评估"""
        controller = QualityController()
        project_data = {"bug_count": 25, "crash_rate": 6.0, "test_pass_rate": 70.0}
        metric = controller._assess_reliability(project_data)
        assert metric.score < 60.0
        assert len(metric.recommendations) > 0

    def test_assess_maintainability(self):
        """测试评估可维护性"""
        controller = QualityController()
        project_data = {"code_complexity": 15, "doc_coverage": 50.0, "duplication_rate": 8.0}
        metric = controller._assess_maintainability(project_data)
        assert metric.dimension == QualityDimension.MAINTAINABILITY
        assert metric.score > 0

    def test_assess_maintainability_poor(self):
        """测试差可维护性评估"""
        controller = QualityController()
        project_data = {"code_complexity": 35, "doc_coverage": 20.0, "duplication_rate": 20.0}
        metric = controller._assess_maintainability(project_data)
        assert metric.score < 60.0

    def test_assess_efficiency(self):
        """测试评估效率"""
        controller = QualityController()
        project_data = {"avg_response_time": 500, "memory_usage": 50.0, "cpu_usage": 40.0}
        metric = controller._assess_efficiency(project_data)
        assert metric.dimension == QualityDimension.EFFICIENCY
        assert metric.score > 0

    def test_assess_efficiency_poor(self):
        """测试差效率评估"""
        controller = QualityController()
        project_data = {"avg_response_time": 3000, "memory_usage": 90.0, "cpu_usage": 85.0}
        metric = controller._assess_efficiency(project_data)
        assert metric.score < 60.0

    def test_assess_security(self):
        """测试评估安全性"""
        controller = QualityController()
        project_data = {"vulnerability_count": 2, "auth_coverage": 85.0, "data_encryption": True}
        metric = controller._assess_security(project_data)
        assert metric.dimension == QualityDimension.SECURITY
        assert metric.score > 0

    def test_assess_security_critical(self):
        """测试严重安全性评估"""
        controller = QualityController()
        project_data = {"vulnerability_count": 15, "auth_coverage": 40.0, "data_encryption": False}
        metric = controller._assess_security(project_data)
        assert metric.score < 40.0
        assert metric.level == QualityLevel.CRITICAL

    def test_score_to_level(self):
        """测试分数到等级转换"""
        controller = QualityController()
        assert controller._score_to_level(95.0) == QualityLevel.EXCELLENT
        assert controller._score_to_level(80.0) == QualityLevel.GOOD
        assert controller._score_to_level(65.0) == QualityLevel.ACCEPTABLE
        assert controller._score_to_level(45.0) == QualityLevel.POOR
        assert controller._score_to_level(20.0) == QualityLevel.CRITICAL

    def test_generate_report(self):
        """测试生成报告"""
        controller = QualityController()
        controller.assess({"bug_count": 5, "crash_rate": 0.5, "test_pass_rate": 90.0,
                           "code_complexity": 10, "doc_coverage": 60.0, "duplication_rate": 5.0,
                           "avg_response_time": 300, "memory_usage": 50.0, "cpu_usage": 40.0,
                           "vulnerability_count": 1, "auth_coverage": 85.0, "data_encryption": True})
        report = controller.generate_report()
        assert "overall_score" in report
        assert "risk_areas" in report
        assert "metrics" in report
        assert "assessment_count" in report

    def test_generate_report_no_assessments(self):
        """测试无评估数据时生成报告"""
        controller = QualityController()
        report = controller.generate_report()
        assert "message" in report

    def test_get_risk_areas(self):
        """测试获取风险区域"""
        controller = QualityController()
        metrics = [
            QualityMetric(dimension=QualityDimension.SECURITY, score=30.0,
                          description="安全性差"),
            QualityMetric(dimension=QualityDimension.RELIABILITY, score=85.0,
                          description="可靠性良好"),
        ]
        risk_areas = controller.get_risk_areas(metrics)
        assert len(risk_areas) == 1
        assert "security" in risk_areas[0]

    def test_get_risk_areas_all_good(self):
        """测试所有指标良好时无风险"""
        controller = QualityController()
        metrics = [
            QualityMetric(dimension=QualityDimension.SECURITY, score=90.0),
            QualityMetric(dimension=QualityDimension.RELIABILITY, score=85.0),
        ]
        risk_areas = controller.get_risk_areas(metrics)
        assert len(risk_areas) == 0

    def test_multiple_assessments(self):
        """测试多次评估"""
        controller = QualityController()
        controller.assess({"bug_count": 5, "crash_rate": 0.5, "test_pass_rate": 90.0,
                           "code_complexity": 10, "doc_coverage": 60.0, "duplication_rate": 5.0,
                           "avg_response_time": 300, "memory_usage": 50.0, "cpu_usage": 40.0,
                           "vulnerability_count": 1, "auth_coverage": 85.0, "data_encryption": True})
        controller.assess({"bug_count": 20, "crash_rate": 5.0, "test_pass_rate": 60.0,
                           "code_complexity": 30, "doc_coverage": 20.0, "duplication_rate": 15.0,
                           "avg_response_time": 2000, "memory_usage": 80.0, "cpu_usage": 70.0,
                           "vulnerability_count": 10, "auth_coverage": 50.0, "data_encryption": False})
        assert len(controller._assessments) == 2


class TestQualityControlService:
    """测试质量风控服务"""

    def test_initialization(self):
        """测试初始化"""
        service = QualityControlService()
        assert service.controller is not None

    def test_initialization_with_controller(self):
        """测试使用自定义控制器初始化"""
        controller = QualityController()
        service = QualityControlService(controller=controller)
        assert service.controller is controller

    def test_assess(self):
        """测试执行评估"""
        service = QualityControlService()
        assessment = service.assess({"bug_count": 5, "crash_rate": 0.5, "test_pass_rate": 90.0,
                                     "code_complexity": 10, "doc_coverage": 60.0, "duplication_rate": 5.0,
                                     "avg_response_time": 300, "memory_usage": 50.0, "cpu_usage": 40.0,
                                     "vulnerability_count": 1, "auth_coverage": 85.0, "data_encryption": True})
        assert isinstance(assessment, QualityAssessment)
        assert assessment.overall_score > 0

    def test_get_assessment(self):
        """测试获取评估"""
        service = QualityControlService()
        service.assess({"bug_count": 5, "crash_rate": 0.5, "test_pass_rate": 90.0,
                        "code_complexity": 10, "doc_coverage": 60.0, "duplication_rate": 5.0,
                        "avg_response_time": 300, "memory_usage": 50.0, "cpu_usage": 40.0,
                        "vulnerability_count": 1, "auth_coverage": 85.0, "data_encryption": True})
        assessment = service.get_assessment()
        assert assessment is not None

    def test_get_assessment_empty(self):
        """测试无评估数据"""
        service = QualityControlService()
        assessment = service.get_assessment()
        assert assessment is None

    def test_get_report(self):
        """测试获取报告"""
        service = QualityControlService()
        service.assess({"bug_count": 5, "crash_rate": 0.5, "test_pass_rate": 90.0,
                        "code_complexity": 10, "doc_coverage": 60.0, "duplication_rate": 5.0,
                        "avg_response_time": 300, "memory_usage": 50.0, "cpu_usage": 40.0,
                        "vulnerability_count": 1, "auth_coverage": 85.0, "data_encryption": True})
        report = service.get_report()
        assert "overall_score" in report

    def test_get_risk_areas(self):
        """测试获取风险区域"""
        service = QualityControlService()
        service.assess({"bug_count": 30, "crash_rate": 8.0, "test_pass_rate": 50.0,
                        "code_complexity": 40, "doc_coverage": 10.0, "duplication_rate": 25.0,
                        "avg_response_time": 3000, "memory_usage": 90.0, "cpu_usage": 85.0,
                        "vulnerability_count": 15, "auth_coverage": 30.0, "data_encryption": False})
        risk_areas = service.get_risk_areas()
        assert isinstance(risk_areas, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
