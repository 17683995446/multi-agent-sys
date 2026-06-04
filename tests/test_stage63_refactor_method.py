"""
阶段63验收测试 - 方法原子化拆分重构
"""

import pytest
from src.architecture.refactor_method import (
    MethodComplexity,
    SplitStrategy,
    MethodAnalysis,
    MethodSplitter,
    MethodRefactorService,
)


class TestMethodComplexity:
    """测试方法复杂度枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert MethodComplexity.SIMPLE.value == "simple"
        assert MethodComplexity.MODERATE.value == "moderate"
        assert MethodComplexity.COMPLEX.value == "complex"
        assert MethodComplexity.HIGHLY_COMPLEX.value == "highly_complex"

    def test_all_complexities(self):
        """测试所有复杂度"""
        complexities = list(MethodComplexity)
        assert len(complexities) == 4


class TestSplitStrategy:
    """测试拆分策略枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert SplitStrategy.BY_RESPONSIBILITY.value == "by_responsibility"
        assert SplitStrategy.BY_PARAMETER.value == "by_parameter"
        assert SplitStrategy.BY_RETURN_VALUE.value == "by_return_value"
        assert SplitStrategy.BY_CONDITION.value == "by_condition"

    def test_all_strategies(self):
        """测试所有策略"""
        strategies = list(SplitStrategy)
        assert len(strategies) == 4


class TestMethodAnalysis:
    """测试方法分析结果"""

    def test_default_creation(self):
        """测试默认创建"""
        analysis = MethodAnalysis()
        assert analysis.method_name == ""
        assert analysis.complexity == MethodComplexity.SIMPLE
        assert analysis.line_count == 0
        assert analysis.responsibility_count == 0
        assert analysis.split_suggestions == []

    def test_custom_creation(self):
        """测试自定义创建"""
        analysis = MethodAnalysis(
            method_name="processData",
            complexity=MethodComplexity.COMPLEX,
            line_count=60,
            responsibility_count=3,
            split_suggestions=[{"strategy": "by_responsibility"}],
        )
        assert analysis.method_name == "processData"
        assert analysis.complexity == MethodComplexity.COMPLEX
        assert analysis.line_count == 60


class TestMethodSplitter:
    """测试方法拆分器"""

    def test_initialization(self):
        """测试初始化"""
        splitter = MethodSplitter()
        assert splitter._analyses == {}
        assert splitter._split_log == []

    def test_analyze_simple_method(self):
        """测试分析简单方法"""
        splitter = MethodSplitter()
        analysis = splitter.analyze_method("simple_func", {
            "line_count": 10,
            "responsibility_count": 1,
            "param_count": 2,
            "return_count": 1,
            "branch_count": 1,
        })
        assert analysis.method_name == "simple_func"
        assert analysis.complexity == MethodComplexity.SIMPLE
        assert len(analysis.split_suggestions) == 0

    def test_analyze_complex_method(self):
        """测试分析复杂方法"""
        splitter = MethodSplitter()
        analysis = splitter.analyze_method("complex_func", {
            "line_count": 80,
            "responsibility_count": 4,
            "param_count": 6,
            "return_count": 3,
            "branch_count": 8,
        })
        assert analysis.complexity in (MethodComplexity.COMPLEX, MethodComplexity.HIGHLY_COMPLEX)
        assert len(analysis.split_suggestions) > 0

    def test_analyze_moderate_method(self):
        """测试分析中等方法"""
        splitter = MethodSplitter()
        analysis = splitter.analyze_method("moderate_func", {
            "line_count": 25,
            "responsibility_count": 2,
            "param_count": 3,
            "return_count": 1,
            "branch_count": 2,
        })
        assert analysis.complexity in (
            MethodComplexity.MODERATE, MethodComplexity.COMPLEX
        )

    def test_analyze_highly_complex_method(self):
        """测试分析高度复杂方法"""
        splitter = MethodSplitter()
        analysis = splitter.analyze_method("mega_func", {
            "line_count": 100,
            "responsibility_count": 5,
            "param_count": 8,
            "return_count": 4,
            "branch_count": 12,
        })
        assert analysis.complexity == MethodComplexity.HIGHLY_COMPLEX
        assert len(analysis.split_suggestions) >= 3

    def test_analyze_method_default(self):
        """测试分析方法默认信息"""
        splitter = MethodSplitter()
        analysis = splitter.analyze_method("default_func")
        assert analysis.method_name == "default_func"
        assert analysis.complexity == MethodComplexity.SIMPLE

    def test_suggest_split(self):
        """测试提供拆分建议"""
        splitter = MethodSplitter()
        splitter.analyze_method("complex_func", {
            "line_count": 80,
            "responsibility_count": 4,
            "param_count": 6,
            "return_count": 3,
            "branch_count": 8,
        })
        suggestions = splitter.suggest_split("complex_func")
        assert len(suggestions) > 0

    def test_suggest_split_with_strategy(self):
        """测试按策略提供拆分建议"""
        splitter = MethodSplitter()
        splitter.analyze_method("complex_func", {
            "line_count": 80,
            "responsibility_count": 4,
            "param_count": 6,
            "return_count": 3,
            "branch_count": 8,
        })
        suggestions = splitter.suggest_split(
            "complex_func", SplitStrategy.BY_RESPONSIBILITY
        )
        for s in suggestions:
            assert s["strategy"] == "by_responsibility"

    def test_suggest_split_no_analysis(self):
        """测试无分析结果时提供建议"""
        splitter = MethodSplitter()
        suggestions = splitter.suggest_split("unknown_func")
        assert suggestions == []

    def test_suggest_split_simple_method(self):
        """测试简单方法无需拆分"""
        splitter = MethodSplitter()
        splitter.analyze_method("simple_func", {
            "line_count": 5,
            "responsibility_count": 1,
            "param_count": 1,
            "return_count": 1,
            "branch_count": 0,
        })
        suggestions = splitter.suggest_split("simple_func")
        assert suggestions == []

    def test_execute_split_by_responsibility(self):
        """测试按职责执行拆分"""
        splitter = MethodSplitter()
        splitter.analyze_method("complex_func", {
            "line_count": 80,
            "responsibility_count": 3,
            "param_count": 2,
            "return_count": 1,
            "branch_count": 6,
        })
        result = splitter.execute_split("complex_func", SplitStrategy.BY_RESPONSIBILITY)
        assert result["status"] == "completed"
        assert len(result["new_methods"]) == 3

    def test_execute_split_by_parameter(self):
        """测试按参数执行拆分"""
        splitter = MethodSplitter()
        splitter.analyze_method("complex_func", {
            "line_count": 80,
            "responsibility_count": 3,
            "param_count": 5,
            "return_count": 1,
            "branch_count": 6,
        })
        result = splitter.execute_split("complex_func", SplitStrategy.BY_PARAMETER)
        assert result["status"] == "completed"
        assert len(result["new_methods"]) == 2

    def test_execute_split_by_return_value(self):
        """测试按返回值执行拆分"""
        splitter = MethodSplitter()
        splitter.analyze_method("complex_func", {
            "line_count": 80,
            "responsibility_count": 3,
            "param_count": 2,
            "return_count": 2,
            "branch_count": 6,
        })
        result = splitter.execute_split("complex_func", SplitStrategy.BY_RETURN_VALUE)
        assert result["status"] == "completed"
        assert len(result["new_methods"]) == 2

    def test_execute_split_by_condition(self):
        """测试按条件执行拆分"""
        splitter = MethodSplitter()
        splitter.analyze_method("complex_func", {
            "line_count": 80,
            "responsibility_count": 3,
            "param_count": 2,
            "return_count": 1,
            "branch_count": 6,
        })
        result = splitter.execute_split("complex_func", SplitStrategy.BY_CONDITION)
        assert result["status"] == "completed"
        assert len(result["new_methods"]) == 2

    def test_execute_split_no_analysis(self):
        """测试无分析结果时执行拆分"""
        splitter = MethodSplitter()
        result = splitter.execute_split("unknown_func")
        assert result["status"] == "failed"

    def test_execute_split_simple_method(self):
        """测试简单方法无需拆分"""
        splitter = MethodSplitter()
        splitter.analyze_method("simple_func", {
            "line_count": 5,
            "responsibility_count": 1,
        })
        result = splitter.execute_split("simple_func")
        assert result["status"] == "skipped"

    def test_verify_split(self):
        """测试验证拆分结果"""
        splitter = MethodSplitter()
        splitter.analyze_method("complex_func", {
            "line_count": 80,
            "responsibility_count": 3,
            "param_count": 2,
            "return_count": 1,
            "branch_count": 6,
        })
        splitter.execute_split("complex_func", SplitStrategy.BY_RESPONSIBILITY)
        result = splitter.verify_split("complex_func")
        assert result["verified"] is True
        assert result["split_count"] == 1
        assert result["total_new_methods"] == 3


class TestMethodRefactorService:
    """测试方法重构服务"""

    def test_initialization(self):
        """测试初始化"""
        service = MethodRefactorService()
        assert service.splitter is not None

    def test_analyze(self):
        """测试分析"""
        service = MethodRefactorService()
        analysis = service.analyze("my_method", {
            "line_count": 60,
            "responsibility_count": 3,
        })
        assert analysis.method_name == "my_method"

    def test_split(self):
        """测试拆分"""
        service = MethodRefactorService()
        service.analyze("complex_method", {
            "line_count": 80,
            "responsibility_count": 3,
            "param_count": 2,
            "return_count": 1,
            "branch_count": 6,
        })
        result = service.split("complex_method", SplitStrategy.BY_RESPONSIBILITY)
        assert result["status"] == "completed"

    def test_get_analysis(self):
        """测试获取分析结果"""
        service = MethodRefactorService()
        service.analyze("test_method", {
            "line_count": 30,
            "responsibility_count": 2,
        })
        analysis = service.get_analysis("test_method")
        assert analysis is not None
        assert analysis.method_name == "test_method"

    def test_get_analysis_not_found(self):
        """测试获取不存在的分析结果"""
        service = MethodRefactorService()
        analysis = service.get_analysis("unknown_method")
        assert analysis is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
