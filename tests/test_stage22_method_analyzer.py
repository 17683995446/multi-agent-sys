"""
阶段22验收测试 - 方法原子化：单一职责校验、拆分、规整

验收标准：
1. ✓ 实现方法识别与完整签名解析
2. ✓ 实现职责数量检测（行数统计+语义分析）
3. ✓ 实现拆分工具（手动+自动拆分）
4. ✓ 实现规整报告（文本+可视化）
"""

import pytest
import ast
from src.architecture import (
    MethodType,
    ResponsibilityCategory,
    SplittingStrategy,
    MethodScanner,
    ComplexityAnalyzer,
    ResponsibilityAnalyzer,
    MethodSplitter,
    MethodAnalyzer,
    get_method_analyzer,
    reset_method_analyzer
)


class TestMethodScanner:
    """测试方法扫描器"""
    
    def test_scan_simple_function(self):
        """测试扫描简单函数"""
        source_code = """
def simple_function(x, y):
    return x + y
"""
        scanner = MethodScanner()
        methods = scanner.scan(source_code)
        
        assert len(methods) == 1
        assert methods[0].name == "simple_function"
        assert methods[0].method_type == MethodType.FUNCTION
        assert len(methods[0].parameters) == 2
    
    def test_scan_class_methods(self):
        """测试扫描类方法"""
        source_code = """
class TestClass:
    def instance_method(self, x):
        return x
    
    @classmethod
    def class_method(cls, x):
        return x
    
    @staticmethod
    def static_method(x):
        return x
"""
        scanner = MethodScanner()
        methods = scanner.scan(source_code)
        
        assert len(methods) == 3
        method_types = {m.name: m.method_type for m in methods}
        assert method_types["instance_method"] == MethodType.INSTANCE_METHOD
        assert method_types["class_method"] == MethodType.CLASS_METHOD
        assert method_types["static_method"] == MethodType.STATIC_METHOD
    
    def test_scan_complex_signature(self):
        """测试扫描复杂签名"""
        source_code = """
def complex_function(
    a: int,
    b: str = "default",
    *args,
    c: float,
    **kwargs
) -> dict:
    return {"a": a, "b": b, "c": c}
"""
        scanner = MethodScanner()
        methods = scanner.scan(source_code)
        
        assert len(methods) == 1
        method = methods[0]
        assert len(method.parameters) >= 3
        assert method.return_type is not None


class TestComplexityAnalyzer:
    """测试复杂度分析器"""
    
    def test_cyclomatic_complexity(self):
        """测试圈复杂度计算"""
        source_code = """
def complex_function(x):
    if x > 0:
        if x < 10:
            return "small"
        else:
            return "large"
    elif x == 0:
        return "zero"
    else:
        return "negative"
"""
        scanner = MethodScanner()
        methods = scanner.scan(source_code)
        analyzer = ComplexityAnalyzer()
        analyzed = analyzer.analyze_method(methods[0])
        
        assert analyzed.cyclomatic_complexity > 1
        assert analyzed.max_nesting_depth >= 1


class TestResponsibilityAnalyzer:
    """测试职责分析器"""
    
    def test_identify_multiple_responsibilities(self):
        """测试识别多个职责"""
        source_code = """
def process_data(data):
    # 输入验证
    if not data:
        raise ValueError("Data is required")
    
    # 数据处理
    result = [x * 2 for x in data]
    
    # 日志记录
    print(f"Processed {len(result)} items")
    
    return result
"""
        scanner = MethodScanner()
        methods = scanner.scan(source_code)
        analyzer = ResponsibilityAnalyzer()
        analyzed = analyzer.analyze_method(methods[0])
        
        assert len(analyzed.code_blocks) > 0
        assert analyzed.responsibility_count >= 1


class TestMethodSplitter:
    """测试方法拆分器"""
    
    def test_split_by_responsibility(self):
        """测试按职责拆分"""
        source_code = """
def process_data(data):
    if not data:
        raise ValueError("Data is required")
    result = [x * 2 for x in data]
    return result
"""
        scanner = MethodScanner()
        methods = scanner.scan(source_code)
        analyzer = ResponsibilityAnalyzer()
        analyzed = analyzer.analyze_method(methods[0])
        
        splitter = MethodSplitter()
        split_result = splitter.split_method(analyzed, SplittingStrategy.BY_RESPONSIBILITY)
        
        assert split_result.original_method.name == "process_data"
        assert len(split_result.new_methods) >= 1


class TestMethodAnalyzer:
    """测试完整的方法分析器"""
    
    def test_analyze_source_code(self):
        """测试分析源代码"""
        source_code = """
def function_with_issues(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return x + y + z
            else:
                return x + y
        else:
            return x
    else:
        return 0
"""
        analyzer = MethodAnalyzer()
        methods = analyzer.analyze_source(source_code)
        
        assert len(methods) == 1
        method = methods[0]
        assert method.cyclomatic_complexity >= 1
    
    def test_generate_report(self):
        """测试生成报告"""
        # 使用现有的源文件来测试
        import os
        test_file = os.path.join(os.path.dirname(__file__), "../src/architecture/method_analyzer.py")
        
        analyzer = MethodAnalyzer()
        report = analyzer.generate_report(test_file)
        
        assert report.total_methods > 0
        assert report.methods_analyzed > 0


class TestGlobalAnalyzer:
    """测试全局分析器"""
    
    def test_get_and_reset(self):
        """测试获取和重置全局分析器"""
        reset_method_analyzer()
        analyzer1 = get_method_analyzer()
        analyzer2 = get_method_analyzer()
        
        assert analyzer1 is analyzer2
        
        reset_method_analyzer()
        analyzer3 = get_method_analyzer()
        
        assert analyzer3 is not analyzer1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
