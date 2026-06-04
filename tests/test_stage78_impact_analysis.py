"""
阶段78验收测试 - 回归影响范围精准分析
"""

import pytest
from src.architecture.impact_analysis import (
    ImpactLevel,
    ImpactArea,
    ImpactRecord,
    ImpactAnalyzer,
    ImpactAnalysisService,
)


class TestImpactLevel:
    """测试影响级别枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ImpactLevel.NONE.value == "none"
        assert ImpactLevel.LOW.value == "low"
        assert ImpactLevel.MEDIUM.value == "medium"
        assert ImpactLevel.HIGH.value == "high"
        assert ImpactLevel.CRITICAL.value == "critical"

    def test_all_levels(self):
        """测试所有影响级别"""
        levels = list(ImpactLevel)
        assert len(levels) == 5


class TestImpactArea:
    """测试影响领域枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ImpactArea.FUNCTIONALITY.value == "functionality"
        assert ImpactArea.PERFORMANCE.value == "performance"
        assert ImpactArea.SECURITY.value == "security"
        assert ImpactArea.COMPATIBILITY.value == "compatibility"
        assert ImpactArea.MAINTAINABILITY.value == "maintainability"

    def test_all_areas(self):
        """测试所有影响领域"""
        areas = list(ImpactArea)
        assert len(areas) == 5


class TestImpactRecord:
    """测试影响记录"""

    def test_default_creation(self):
        """测试默认创建"""
        record = ImpactRecord()
        assert record.impact_id != ""
        assert record.area == ImpactArea.FUNCTIONALITY
        assert record.level == ImpactLevel.MEDIUM
        assert record.affected_components == []
        assert record.description == ""
        assert record.mitigation == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        record = ImpactRecord(
            area=ImpactArea.SECURITY,
            level=ImpactLevel.HIGH,
            affected_components=["auth.py", "user.py"],
            description="安全影响",
            mitigation="加强认证",
        )
        assert record.area == ImpactArea.SECURITY
        assert record.level == ImpactLevel.HIGH
        assert len(record.affected_components) == 2

    def test_impact_id_unique(self):
        """测试影响ID唯一性"""
        r1 = ImpactRecord()
        r2 = ImpactRecord()
        assert r1.impact_id != r2.impact_id


class TestImpactAnalyzer:
    """测试影响分析器"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = ImpactAnalyzer()
        assert analyzer._impacts == []
        assert analyzer._dependency_map == {}

    def test_analyze_change(self):
        """测试分析变更"""
        analyzer = ImpactAnalyzer()
        impacts = analyzer.analyze_change(
            "修复登录Bug", ["src/auth.py"])
        assert len(impacts) > 0
        assert any(i.area == ImpactArea.FUNCTIONALITY for i in impacts)

    def test_analyze_change_refactor(self):
        """测试分析重构变更"""
        analyzer = ImpactAnalyzer()
        impacts = analyzer.analyze_change(
            "重构用户模块", ["src/user.py"])
        functional_impacts = [i for i in impacts if i.area == ImpactArea.FUNCTIONALITY]
        assert len(functional_impacts) > 0
        assert functional_impacts[0].level == ImpactLevel.HIGH

    def test_analyze_change_fix(self):
        """测试分析修复变更"""
        analyzer = ImpactAnalyzer()
        impacts = analyzer.analyze_change(
            "修复空指针异常", ["src/utils.py"])
        functional_impacts = [i for i in impacts if i.area == ImpactArea.FUNCTIONALITY]
        assert len(functional_impacts) > 0
        assert functional_impacts[0].level == ImpactLevel.LOW

    def test_analyze_change_performance(self):
        """测试分析性能影响"""
        analyzer = ImpactAnalyzer()
        impacts = analyzer.analyze_change(
            "优化循环查询", ["src/query.py"])
        perf_impacts = [i for i in impacts if i.area == ImpactArea.PERFORMANCE]
        assert len(perf_impacts) > 0

    def test_analyze_change_cache(self):
        """测试分析缓存变更"""
        analyzer = ImpactAnalyzer()
        impacts = analyzer.analyze_change(
            "修改缓存策略", ["src/cache.py"])
        perf_impacts = [i for i in impacts if i.area == ImpactArea.PERFORMANCE]
        assert len(perf_impacts) > 0
        assert perf_impacts[0].level == ImpactLevel.HIGH

    def test_trace_dependencies(self):
        """测试追踪依赖关系"""
        analyzer = ImpactAnalyzer()
        deps = analyzer._trace_dependencies(["src/auth.py"])
        assert "src/auth.py" in deps
        assert len(deps["src/auth.py"]) > 0

    def test_assess_functional_impact(self):
        """测试评估功能影响"""
        analyzer = ImpactAnalyzer()
        deps = {"src/app.py": ["src/utils.py"]}
        impacts = analyzer._assess_functional_impact(
            "新增功能", ["src/app.py"], deps)
        assert len(impacts) > 0
        assert impacts[0].area == ImpactArea.FUNCTIONALITY

    def test_assess_performance_impact_with_keywords(self):
        """测试评估性能影响（含关键词）"""
        analyzer = ImpactAnalyzer()
        deps = {"src/app.py": []}
        impacts = analyzer._assess_performance_impact(
            "优化查询循环", ["src/app.py"], deps)
        assert len(impacts) > 0

    def test_assess_performance_impact_no_keywords(self):
        """测试评估性能影响（无关键词）"""
        analyzer = ImpactAnalyzer()
        deps = {"src/app.py": []}
        impacts = analyzer._assess_performance_impact(
            "修改UI样式", ["src/app.py"], deps)
        assert len(impacts) == 0

    def test_generate_report(self):
        """测试生成报告"""
        analyzer = ImpactAnalyzer()
        analyzer.analyze_change("修复Bug", ["src/app.py"])
        report = analyzer.generate_report()
        assert "total_impacts" in report
        assert "by_area" in report
        assert "by_level" in report
        assert "overall_level" in report
        assert report["total_impacts"] > 0

    def test_generate_report_empty(self):
        """测试空报告"""
        analyzer = ImpactAnalyzer()
        report = analyzer.generate_report()
        assert report["total_impacts"] == 0
        assert report["overall_level"] == "低"

    def test_multiple_analyses(self):
        """测试多次分析"""
        analyzer = ImpactAnalyzer()
        analyzer.analyze_change("修复Bug", ["src/a.py"])
        analyzer.analyze_change("重构模块", ["src/b.py"])
        assert len(analyzer._impacts) >= 2


class TestImpactAnalysisService:
    """测试影响分析服务"""

    def test_initialization(self):
        """测试初始化"""
        service = ImpactAnalysisService()
        assert service.analyzer is not None

    def test_initialization_with_analyzer(self):
        """测试使用自定义分析器初始化"""
        analyzer = ImpactAnalyzer()
        service = ImpactAnalysisService(analyzer=analyzer)
        assert service.analyzer is analyzer

    def test_analyze(self):
        """测试执行分析"""
        service = ImpactAnalysisService()
        impacts = service.analyze("修复Bug", ["src/app.py"])
        assert len(impacts) > 0

    def test_get_impacts(self):
        """测试获取影响记录"""
        service = ImpactAnalysisService()
        service.analyze("修复Bug", ["src/app.py"])
        impacts = service.get_impacts()
        assert len(impacts) > 0

    def test_get_impacts_by_area(self):
        """测试按领域获取影响记录"""
        service = ImpactAnalysisService()
        service.analyze("修复Bug", ["src/app.py"])
        impacts = service.get_impacts(area=ImpactArea.FUNCTIONALITY)
        assert all(i.area == ImpactArea.FUNCTIONALITY for i in impacts)

    def test_get_impacts_by_level(self):
        """测试按级别获取影响记录"""
        service = ImpactAnalysisService()
        service.analyze("修复Bug", ["src/app.py"])
        impacts = service.get_impacts(level=ImpactLevel.LOW)
        assert all(i.level == ImpactLevel.LOW for i in impacts)

    def test_get_report(self):
        """测试获取报告"""
        service = ImpactAnalysisService()
        service.analyze("修复Bug", ["src/app.py"])
        report = service.get_report()
        assert "total_impacts" in report

    def test_get_impacts_empty(self):
        """测试空影响记录"""
        service = ImpactAnalysisService()
        impacts = service.get_impacts()
        assert impacts == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
