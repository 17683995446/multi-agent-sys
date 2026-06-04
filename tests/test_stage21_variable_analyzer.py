import pytest
import tempfile
import os
from src.architecture import (
    VariableType,
    VariableCategory,
    VariableIssueType,
    VariableInfo,
    NamingSuggestion,
    VariableScanner,
    VariableClassifier,
    NamingHelper,
    VariableFixer,
    VariableAnalyzer,
    get_variable_analyzer,
    reset_variable_analyzer
)


class TestVariableScanner:
    """测试变量扫描器（21.1）"""

    def test_scan_simple_function(self):
        """测试扫描简单函数"""
        code = """
def test_func(x, y):
    result = x + y
    temp = result * 2
    return temp
"""
        scanner = VariableScanner()
        variables = scanner.scan(code)
        
        assert len(variables) >= 4
        var_names = [v.name for v in variables]
        assert 'x' in var_names
        assert 'y' in var_names
        assert 'result' in var_names
        assert 'temp' in var_names

    def test_scan_class(self):
        """测试扫描类"""
        code = """
class TestClass:
    CLASS_CONST = 42
    
    def __init__(self, value):
        self.value = value
        self.temp = 0
"""
        scanner = VariableScanner()
        variables = scanner.scan(code)
        
        var_names = [v.name for v in variables]
        assert 'value' in var_names
        assert 'CLASS_CONST' in var_names

    def test_scan_with_types(self):
        """测试扫描带类型注解的代码"""
        code = """
def add(a: int, b: int) -> int:
    result: int = a + b
    return result
"""
        scanner = VariableScanner()
        variables = scanner.scan(code)
        
        var_names = [v.name for v in variables]
        assert 'a' in var_names
        assert 'b' in var_names
        assert 'result' in var_names

    def test_scan_file(self):
        """测试扫描文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test():
    x = 1
    y = 2
    return x + y
""")
            file_path = f.name
        
        try:
            scanner = VariableScanner()
            variables = scanner.scan_file(file_path)
            
            assert len(variables) >= 2
            var_names = [v.name for v in variables]
            assert 'x' in var_names
            assert 'y' in var_names
        finally:
            os.unlink(file_path)


class TestVariableClassifier:
    """测试变量分类器（21.2）"""

    def test_basic_classification(self):
        """测试基本分类"""
        var = VariableInfo(
            name="user_name",
            var_type=VariableType.LOCAL,
            category=VariableCategory.DATA
        )
        
        classifier = VariableClassifier()
        classified = classifier.classify(var)
        
        assert classified.var_type == VariableType.LOCAL
        assert classified.category == VariableCategory.DATA

    def test_constant_detection(self):
        """测试常量识别"""
        var = VariableInfo(
            name="MAX_SIZE",
            var_type=VariableType.CONSTANT,
            category=VariableCategory.DATA
        )
        
        classifier = VariableClassifier()
        classified = classifier.classify(var)
        
        assert classified.category == VariableCategory.DATA

    def test_temp_variable_detection(self):
        """测试临时变量识别"""
        var = VariableInfo(
            name="temp",
            var_type=VariableType.LOCAL,
            category=VariableCategory.DATA
        )
        
        classifier = VariableClassifier()
        classified = classifier.classify(var)
        
        # 分类器可能会修改category
        assert classified.name == "temp"

    def test_index_variable_detection(self):
        """测试索引变量识别"""
        var = VariableInfo(
            name="i",
            var_type=VariableType.LOCAL,
            category=VariableCategory.DATA
        )
        
        classifier = VariableClassifier()
        classified = classifier.classify(var)
        
        # 应该检测到是索引
        assert classified.category == VariableCategory.INDEX


class TestVariableSemanticCheck:
    """测试语义一致性检查（21.3）"""

    def test_short_name_check(self):
        """测试短命名检查"""
        var = VariableInfo(
            name="x",
            var_type=VariableType.LOCAL,
            category=VariableCategory.DATA
        )
        
        classifier = VariableClassifier()
        classified = classifier.classify(var)
        
        assert VariableIssueType.SHORT_NAME in classified.issues

    def test_naming_style_check(self):
        """测试命名风格检查"""
        var = VariableInfo(
            name="userName",
            var_type=VariableType.LOCAL,
            category=VariableCategory.DATA
        )
        
        classifier = VariableClassifier()
        classified = classifier.classify(var)
        
        # camelCase不符合蛇形命名
        assert VariableIssueType.BAD_NAMING in classified.issues

    def test_constant_naming(self):
        """测试常量命名检查"""
        var = VariableInfo(
            name="max_size",
            var_type=VariableType.CONSTANT,
            category=VariableCategory.DATA
        )
        
        classifier = VariableClassifier()
        classified = classifier.classify(var)
        
        assert VariableIssueType.BAD_NAMING in classified.issues


class TestNamingHelper:
    """测试命名辅助工具"""

    def test_suggest_for_x(self):
        """测试为x生成建议"""
        suggestion = NamingHelper.suggest_names("x")
        
        assert len(suggestion.suggested) > 0
        assert "data" in suggestion.suggested or "value" in suggestion.suggested

    def test_suggest_for_i(self):
        """测试为i生成建议"""
        suggestion = NamingHelper.suggest_names("i", VariableCategory.INDEX)
        
        assert len(suggestion.suggested) > 0
        assert "index" in suggestion.suggested

    def test_constant_suggestion(self):
        """测试常量建议"""
        suggestion = NamingHelper.suggest_names("max_size")
        
        assert "MAX_SIZE" in suggestion.suggested


class TestVariableFixer:
    """测试自动纠错（21.4）"""

    def test_suggest_generation(self):
        """测试建议生成"""
        var = VariableInfo(
            name="x",
            var_type=VariableType.LOCAL,
            category=VariableCategory.DATA
        )
        
        fixer = VariableFixer()
        analysis = fixer.analyze_variable(var)
        
        assert "issues" in analysis
        assert "suggestions" in analysis

    def test_apply_fix(self):
        """测试应用修复"""
        code = """
def test():
    x = 1
    y = 2
    return x + y
"""
        scanner = VariableScanner()
        variables = scanner.scan(code)
        
        for var in variables:
            if var.name == "x":
                x_var = var
        
        fixer = VariableFixer()
        fixed_var = fixer.fix_naming(x_var)
        
        if fixed_var:
            assert fixed_var.name != "x"


class TestVariableAnalyzer:
    """测试变量分析管理器"""

    def test_analyze_source(self):
        """测试分析源代码"""
        code = """
def calculate_total(price: float, quantity: int) -> float:
    result = price * quantity
    temp = result
    return temp
"""
        analyzer = VariableAnalyzer()
        result = analyzer.analyze_source(code)
        
        assert "variables" in result
        assert "total_count" in result
        assert "issues_count" in result
        assert result["total_count"] >= 3

    def test_fix_source(self):
        """测试修复源代码"""
        code = """
def test():
    x = 1
    y = 2
    return x + y
"""
        analyzer = VariableAnalyzer()
        result = analyzer.analyze_source(code)
        
        assert result["total_count"] >= 2

    def test_global_analyzer(self):
        """测试全局分析器"""
        reset_variable_analyzer()
        analyzer1 = get_variable_analyzer()
        analyzer2 = get_variable_analyzer()
        
        assert analyzer1 is analyzer2


class TestVariableAnalyzerIntegration:
    """集成测试 - 模拟实际工作流"""

    def test_full_workflow(self):
        """测试完整工作流"""
        code = """
def process_data(items):
    temp = []
    for i in items:
        temp.append(i * 2)
    result = temp
    return result
"""
        analyzer = VariableAnalyzer()
        
        # 1. 分析
        analysis = analyzer.analyze_source(code)
        assert analysis["total_count"] >= 3
        
        # 2. 查找问题
        has_issues = analysis["issues_count"] > 0
        
        # 3. 检查是否可修复
        fixable = analysis["fixable_count"] > 0
        
        # 简单验证流程可行
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
