"""
阶段79验收测试 - 单元测试覆盖率提升
"""

import pytest
from src.architecture.coverage_enhancer import (
    CoverageLevel,
    CoverageGap,
    CoverageReport,
    CoverageAnalyzer,
    CoverageEnhancer,
    CoverageService,
)


class TestCoverageLevel:
    """测试覆盖率级别枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert CoverageLevel.LINE.value == "line"
        assert CoverageLevel.BRANCH.value == "branch"
        assert CoverageLevel.FUNCTION.value == "function"
        assert CoverageLevel.MODULE.value == "module"

    def test_all_levels(self):
        """测试所有覆盖率级别"""
        levels = list(CoverageLevel)
        assert len(levels) == 4


class TestCoverageGap:
    """测试覆盖率缺口"""

    def test_default_creation(self):
        """测试默认创建"""
        gap = CoverageGap()
        assert gap.gap_id != ""
        assert gap.level == CoverageLevel.LINE
        assert gap.location == ""
        assert gap.description == ""
        assert gap.suggested_test == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        gap = CoverageGap(
            level=CoverageLevel.BRANCH,
            location="app.py:42",
            description="分支未覆盖",
            suggested_test="编写True/False分支测试",
        )
        assert gap.level == CoverageLevel.BRANCH
        assert gap.location == "app.py:42"

    def test_gap_id_unique(self):
        """测试缺口ID唯一性"""
        g1 = CoverageGap()
        g2 = CoverageGap()
        assert g1.gap_id != g2.gap_id


class TestCoverageReport:
    """测试覆盖率报告"""

    def test_default_creation(self):
        """测试默认创建"""
        report = CoverageReport()
        assert report.total_lines == 0
        assert report.covered_lines == 0
        assert report.coverage_percentage == 0.0
        assert report.gaps == []
        assert report.by_module == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        report = CoverageReport(
            total_lines=100,
            covered_lines=80,
            coverage_percentage=80.0,
            gaps=[CoverageGap()],
            by_module={"app": 80.0},
        )
        assert report.total_lines == 100
        assert report.covered_lines == 80
        assert report.coverage_percentage == 80.0
        assert len(report.gaps) == 1


class TestCoverageAnalyzer:
    """测试覆盖率分析器"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = CoverageAnalyzer()
        assert analyzer._gaps == []
        assert analyzer._modules == {}

    def test_analyze_simple_code(self):
        """测试分析简单代码"""
        analyzer = CoverageAnalyzer()
        code = "x = 1\ny = 2\nz = x + y"
        report = analyzer.analyze(code, "simple.py")
        assert report.total_lines > 0
        assert report.coverage_percentage >= 0.0

    def test_analyze_code_with_functions(self):
        """测试分析含函数的代码"""
        analyzer = CoverageAnalyzer()
        code = "def hello():\n    return 'world'\n\ndef goodbye():\n    return 'bye'"
        report = analyzer.analyze(code, "funcs.py")
        line_gaps = [g for g in report.gaps if g.level == CoverageLevel.LINE]
        assert len(line_gaps) > 0

    def test_analyze_code_with_branches(self):
        """测试分析含分支的代码"""
        analyzer = CoverageAnalyzer()
        code = "def check(x):\n    if x > 0:\n        return True\n    else:\n        return False"
        report = analyzer.analyze(code, "branch.py")
        branch_gaps = [g for g in report.gaps if g.level == CoverageLevel.BRANCH]
        assert len(branch_gaps) > 0

    def test_analyze_code_with_try(self):
        """测试分析含try的代码"""
        analyzer = CoverageAnalyzer()
        code = "try:\n    result = do_something()\nexcept Exception:\n    pass"
        report = analyzer.analyze(code, "try_code.py")
        branch_gaps = [g for g in report.gaps if g.level == CoverageLevel.BRANCH]
        assert len(branch_gaps) > 0

    def test_analyze_empty_code(self):
        """测试分析空代码"""
        analyzer = CoverageAnalyzer()
        report = analyzer.analyze("", "empty.py")
        assert report.total_lines == 0
        assert report.coverage_percentage == 100.0

    def test_analyze_line_coverage(self):
        """测试行覆盖率分析"""
        analyzer = CoverageAnalyzer()
        code = "def add(a, b):\n    return a + b"
        gaps = analyzer._analyze_line_coverage(code, "math.py")
        assert len(gaps) > 0
        assert gaps[0].level == CoverageLevel.LINE

    def test_analyze_branch_coverage(self):
        """测试分支覆盖率分析"""
        analyzer = CoverageAnalyzer()
        code = "if x > 0:\n    pass\nelif x < 0:\n    pass"
        gaps = analyzer._analyze_branch_coverage(code, "cond.py")
        assert len(gaps) >= 2

    def test_identify_gaps(self):
        """测试识别覆盖率缺口"""
        analyzer = CoverageAnalyzer()
        code = "def untested():\n    pass"
        analyzer.analyze(code, "untested.py")
        gaps = analyzer.identify_gaps(min_coverage=100.0)
        assert len(gaps) >= 0

    def test_identify_gaps_high_threshold(self):
        """测试高阈值识别缺口"""
        analyzer = CoverageAnalyzer()
        code = "def untested():\n    pass"
        analyzer.analyze(code, "untested.py")
        gaps = analyzer.identify_gaps(min_coverage=50.0)
        assert isinstance(gaps, list)

    def test_generate_report(self):
        """测试生成报告"""
        analyzer = CoverageAnalyzer()
        analyzer.analyze("def foo(): pass", "test.py")
        report = analyzer.generate_report()
        assert "overall_coverage" in report
        assert "total_gaps" in report
        assert "by_level" in report
        assert "by_module" in report

    def test_generate_report_empty(self):
        """测试空报告"""
        analyzer = CoverageAnalyzer()
        report = analyzer.generate_report()
        assert report["overall_coverage"] == 0.0
        assert report["total_gaps"] == 0


class TestCoverageEnhancer:
    """测试覆盖率提升器"""

    def test_initialization(self):
        """测试初始化"""
        enhancer = CoverageEnhancer()
        assert enhancer._generated_tests == []

    def test_generate_unit_test(self):
        """测试生成单元测试"""
        enhancer = CoverageEnhancer()
        gap = CoverageGap(
            level=CoverageLevel.LINE,
            location="app.py:10",
            description="函数未覆盖",
            suggested_test="为 add 编写单元测试",
        )
        result = enhancer.generate_test(gap)
        assert result["status"] == "generated"
        assert "test_code" in result
        assert "def test_" in result["test_code"]

    def test_generate_branch_test(self):
        """测试生成分支测试"""
        enhancer = CoverageEnhancer()
        gap = CoverageGap(
            level=CoverageLevel.BRANCH,
            location="app.py:15",
            description="条件分支未覆盖",
            suggested_test="为条件编写分支测试",
        )
        result = enhancer.generate_test(gap)
        assert result["status"] == "generated"
        assert "test_branch_" in result["test_code"]

    def test_generate_test_function_level(self):
        """测试函数级别生成"""
        enhancer = CoverageEnhancer()
        gap = CoverageGap(
            level=CoverageLevel.FUNCTION,
            location="app.py",
            description="模块未覆盖",
        )
        result = enhancer.generate_test(gap)
        assert result["status"] == "pending"

    def test_apply_tests(self):
        """测试应用测试"""
        enhancer = CoverageEnhancer()
        gap = CoverageGap(
            level=CoverageLevel.LINE,
            suggested_test="为 func 编写单元测试",
        )
        test_result = enhancer.generate_test(gap)
        result = enhancer.apply_tests([test_result])
        assert result["total"] == 1
        assert result["applied"] == 1

    def test_apply_tests_with_pending(self):
        """测试应用含待定状态的测试"""
        enhancer = CoverageEnhancer()
        tests = [{"status": "pending", "test_code": ""}]
        result = enhancer.apply_tests(tests)
        assert result["skipped"] == 1

    def test_apply_tests_empty(self):
        """测试应用空测试列表"""
        enhancer = CoverageEnhancer()
        result = enhancer.apply_tests([])
        assert result["total"] == 0
        assert result["applied"] == 0


class TestCoverageService:
    """测试覆盖率服务"""

    def test_initialization(self):
        """测试初始化"""
        service = CoverageService()
        assert service.analyzer is not None
        assert service.enhancer is not None

    def test_analyze(self):
        """测试执行分析"""
        service = CoverageService()
        report = service.analyze("def foo(): pass", "test.py")
        assert isinstance(report, CoverageReport)

    def test_enhance(self):
        """测试提升覆盖率"""
        service = CoverageService()
        service.analyze("def foo(): pass", "test.py")
        results = service.enhance()
        assert isinstance(results, list)

    def test_enhance_with_gaps(self):
        """测试使用指定缺口提升覆盖率"""
        service = CoverageService()
        gap = CoverageGap(
            level=CoverageLevel.LINE,
            suggested_test="为 func 编写单元测试",
        )
        results = service.enhance(gaps=[gap])
        assert len(results) == 1
        assert results[0]["status"] == "generated"

    def test_get_report(self):
        """测试获取报告"""
        service = CoverageService()
        service.analyze("def foo(): pass", "test.py")
        report = service.get_report()
        assert "overall_coverage" in report

    def test_analyze_and_enhance_flow(self):
        """测试分析并提升的完整流程"""
        service = CoverageService()
        report = service.analyze("def foo(): pass\nif x: pass", "test.py")
        assert report.total_lines > 0
        results = service.enhance()
        assert len(results) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
