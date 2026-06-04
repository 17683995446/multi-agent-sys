"""
阶段82验收测试 - 自动识别高风险/烂代码模块
"""

import pytest
from src.architecture.risk_identifier import (
    RiskCategory,
    RiskLevel,
    RiskIndicator,
    RiskIdentifier,
    RiskIdentifyService,
)


class TestRiskCategory:
    """测试风险类别枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RiskCategory.HIGH_COMPLEXITY.value == "high_complexity"
        assert RiskCategory.LOW_COVERAGE.value == "low_coverage"
        assert RiskCategory.FREQUENT_CHANGES.value == "frequent_changes"
        assert RiskCategory.MANY_BUGS.value == "many_bugs"
        assert RiskCategory.TIGHT_COUPLING.value == "tight_coupling"

    def test_all_categories(self):
        """测试所有风险类别"""
        categories = list(RiskCategory)
        assert len(categories) == 5


class TestRiskLevel:
    """测试风险等级枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_all_levels(self):
        """测试所有风险等级"""
        levels = list(RiskLevel)
        assert len(levels) == 4


class TestRiskIndicator:
    """测试风险指标"""

    def test_default_creation(self):
        """测试默认创建"""
        indicator = RiskIndicator()
        assert indicator.indicator_id != ""
        assert indicator.category == RiskCategory.HIGH_COMPLEXITY
        assert indicator.level == RiskLevel.MEDIUM
        assert indicator.module_path == ""
        assert indicator.description == ""
        assert indicator.metrics == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        indicator = RiskIndicator(
            category=RiskCategory.MANY_BUGS,
            level=RiskLevel.CRITICAL,
            module_path="src/core/engine.py",
            description="Bug数量极多",
            metrics={"bug_count": 20},
        )
        assert indicator.category == RiskCategory.MANY_BUGS
        assert indicator.level == RiskLevel.CRITICAL
        assert indicator.module_path == "src/core/engine.py"
        assert indicator.metrics["bug_count"] == 20

    def test_unique_ids(self):
        """测试唯一ID"""
        ind1 = RiskIndicator()
        ind2 = RiskIndicator()
        assert ind1.indicator_id != ind2.indicator_id


class TestRiskIdentifier:
    """测试风险识别器"""

    def _make_project_data(self, complexity=5, coverage=80.0, changes=5,
                           coupling=2, bugs=1):
        """构造测试项目数据"""
        return {
            "modules": {
                "src/core/engine.py": {
                    "cyclomatic_complexity": complexity,
                    "test_coverage": coverage,
                    "change_count": changes,
                    "coupling_score": coupling,
                    "bug_count": bugs,
                }
            }
        }

    def test_initialization(self):
        """测试初始化"""
        identifier = RiskIdentifier()
        assert identifier._indicators == []

    def test_identify_healthy_project(self):
        """测试识别健康项目"""
        identifier = RiskIdentifier()
        data = self._make_project_data(complexity=5, coverage=90.0, changes=3,
                                        coupling=2, bugs=1)
        indicators = identifier.identify(data)
        assert len(indicators) == 0

    def test_identify_high_complexity_critical(self):
        """测试识别极高复杂度"""
        identifier = RiskIdentifier()
        data = self._make_project_data(complexity=35)
        indicators = identifier.identify(data)
        complexity_indicators = [i for i in indicators if i.category == RiskCategory.HIGH_COMPLEXITY]
        assert len(complexity_indicators) == 1
        assert complexity_indicators[0].level == RiskLevel.CRITICAL

    def test_identify_high_complexity_high(self):
        """测试识别高复杂度"""
        identifier = RiskIdentifier()
        data = self._make_project_data(complexity=25)
        indicators = identifier.identify(data)
        complexity_indicators = [i for i in indicators if i.category == RiskCategory.HIGH_COMPLEXITY]
        assert len(complexity_indicators) == 1
        assert complexity_indicators[0].level == RiskLevel.HIGH

    def test_identify_high_complexity_medium(self):
        """测试识别中等复杂度"""
        identifier = RiskIdentifier()
        data = self._make_project_data(complexity=15)
        indicators = identifier.identify(data)
        complexity_indicators = [i for i in indicators if i.category == RiskCategory.HIGH_COMPLEXITY]
        assert len(complexity_indicators) == 1
        assert complexity_indicators[0].level == RiskLevel.MEDIUM

    def test_identify_low_coverage_critical(self):
        """测试识别极低覆盖率"""
        identifier = RiskIdentifier()
        data = self._make_project_data(coverage=20.0)
        indicators = identifier.identify(data)
        coverage_indicators = [i for i in indicators if i.category == RiskCategory.LOW_COVERAGE]
        assert len(coverage_indicators) == 1
        assert coverage_indicators[0].level == RiskLevel.CRITICAL

    def test_identify_low_coverage_high(self):
        """测试识别低覆盖率"""
        identifier = RiskIdentifier()
        data = self._make_project_data(coverage=40.0)
        indicators = identifier.identify(data)
        coverage_indicators = [i for i in indicators if i.category == RiskCategory.LOW_COVERAGE]
        assert len(coverage_indicators) == 1
        assert coverage_indicators[0].level == RiskLevel.HIGH

    def test_identify_frequent_changes(self):
        """测试识别频繁变更"""
        identifier = RiskIdentifier()
        data = self._make_project_data(changes=60)
        indicators = identifier.identify(data)
        change_indicators = [i for i in indicators if i.category == RiskCategory.FREQUENT_CHANGES]
        assert len(change_indicators) == 1
        assert change_indicators[0].level == RiskLevel.CRITICAL

    def test_identify_tight_coupling(self):
        """测试识别紧耦合"""
        identifier = RiskIdentifier()
        data = self._make_project_data(coupling=25)
        indicators = identifier.identify(data)
        coupling_indicators = [i for i in indicators if i.category == RiskCategory.TIGHT_COUPLING]
        assert len(coupling_indicators) == 1
        assert coupling_indicators[0].level == RiskLevel.CRITICAL

    def test_identify_many_bugs(self):
        """测试识别大量Bug"""
        identifier = RiskIdentifier()
        data = self._make_project_data(bugs=20)
        indicators = identifier.identify(data)
        bug_indicators = [i for i in indicators if i.category == RiskCategory.MANY_BUGS]
        assert len(bug_indicators) == 1
        assert bug_indicators[0].level == RiskLevel.CRITICAL

    def test_identify_multiple_risks(self):
        """测试识别多种风险"""
        identifier = RiskIdentifier()
        data = self._make_project_data(complexity=35, coverage=20.0,
                                        changes=60, coupling=25, bugs=20)
        indicators = identifier.identify(data)
        assert len(indicators) == 5

    def test_check_complexity_empty_modules(self):
        """测试空模块复杂度检查"""
        identifier = RiskIdentifier()
        indicators = identifier._check_complexity({})
        assert indicators == []

    def test_generate_risk_report(self):
        """测试生成风险报告"""
        identifier = RiskIdentifier()
        data = self._make_project_data(complexity=35, bugs=20)
        identifier.identify(data)
        report = identifier.generate_risk_report()
        assert "overall_level" in report
        assert "total_indicators" in report
        assert "by_category" in report
        assert "by_level" in report
        assert "indicators" in report

    def test_generate_risk_report_critical(self):
        """测试生成严重风险报告"""
        identifier = RiskIdentifier()
        data = self._make_project_data(complexity=35, coverage=20.0, bugs=20)
        identifier.identify(data)
        report = identifier.generate_risk_report()
        assert report["overall_level"] == RiskLevel.CRITICAL.value

    def test_generate_risk_report_no_indicators(self):
        """测试无风险指标时生成报告"""
        identifier = RiskIdentifier()
        report = identifier.generate_risk_report()
        assert report["total_indicators"] == 0
        assert report["overall_level"] == RiskLevel.LOW.value


class TestRiskIdentifyService:
    """测试风险识别服务"""

    def test_initialization(self):
        """测试初始化"""
        service = RiskIdentifyService()
        assert service.identifier is not None

    def test_initialization_with_identifier(self):
        """测试使用自定义识别器初始化"""
        identifier = RiskIdentifier()
        service = RiskIdentifyService(identifier=identifier)
        assert service.identifier is identifier

    def test_identify(self):
        """测试执行风险识别"""
        service = RiskIdentifyService()
        data = {
            "modules": {
                "src/core.py": {
                    "cyclomatic_complexity": 35,
                    "test_coverage": 20.0,
                    "change_count": 60,
                    "coupling_score": 25,
                    "bug_count": 20,
                }
            }
        }
        indicators = service.identify(data)
        assert len(indicators) == 5

    def test_get_risks_all(self):
        """测试获取所有风险"""
        service = RiskIdentifyService()
        data = {
            "modules": {
                "src/core.py": {
                    "cyclomatic_complexity": 35,
                    "test_coverage": 90.0,
                    "change_count": 3,
                    "coupling_score": 2,
                    "bug_count": 0,
                }
            }
        }
        service.identify(data)
        risks = service.get_risks()
        assert len(risks) == 1

    def test_get_risks_by_level(self):
        """测试按等级获取风险"""
        service = RiskIdentifyService()
        data = {
            "modules": {
                "src/core.py": {
                    "cyclomatic_complexity": 35,
                    "test_coverage": 20.0,
                    "change_count": 3,
                    "coupling_score": 2,
                    "bug_count": 0,
                }
            }
        }
        service.identify(data)
        critical_risks = service.get_risks(RiskLevel.CRITICAL)
        assert len(critical_risks) == 2

    def test_get_report(self):
        """测试获取风险报告"""
        service = RiskIdentifyService()
        data = {
            "modules": {
                "src/core.py": {
                    "cyclomatic_complexity": 35,
                    "test_coverage": 90.0,
                    "change_count": 3,
                    "coupling_score": 2,
                    "bug_count": 0,
                }
            }
        }
        service.identify(data)
        report = service.get_report()
        assert "overall_level" in report
        assert "total_indicators" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
