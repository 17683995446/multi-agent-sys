import pytest
from src.executors.ast_traversal import (
    ASTAnalyzer,
    BaseASTVisitor,
    EnhancedASTVisitor,
    UnifiedSyntaxAnalyzer,
    NodeType,
    CodeEntity,
    ASTAnalysisResult
)
from src.executors.tree_sitter_core import Language


class TestASTModule:
    """测试AST模块基础功能"""

    def test_ast_module_available(self):
        """测试AST模块可导入"""
        import ast
        assert ast is not None

    def test_parse_simple_code(self):
        """测试解析简单代码"""
        import ast
        tree = ast.parse("x = 1 + 2")
        assert tree is not None
        assert isinstance(tree, ast.Module)

    def test_node_visitor_basic(self):
        """测试基础访问者模式"""
        visitor = BaseASTVisitor()
        import ast
        tree = ast.parse("def test(): pass")
        visitor.visit(tree)
        assert len(visitor.result.functions) == 1
        assert visitor.result.functions[0].name == "test"


class TestASTAnalyzer:
    """测试AST分析器"""

    def test_init(self):
        """测试初始化"""
        analyzer = ASTAnalyzer()
        assert analyzer is not None

    def test_parse_code(self):
        """测试代码解析"""
        analyzer = ASTAnalyzer()
        code = """
def greet():
    return "Hello"
"""
        result = analyzer.parse(code).analyze()
        assert len(result.functions) == 1
        assert result.functions[0].name == "greet"

    def test_detect_variables(self):
        """测试变量识别"""
        analyzer = ASTAnalyzer()
        code = """
x = 10
y = "test"
def func():
    z = 20
"""
        result = analyzer.parse(code).analyze()
        variable_names = {v.name for v in result.variables}
        assert "x" in variable_names
        assert "y" in variable_names
        assert "z" in variable_names

    def test_detect_functions(self):
        """测试函数识别"""
        analyzer = ASTAnalyzer()
        code = """
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y
"""
        result = analyzer.parse(code).analyze()
        function_names = {f.name for f in result.functions}
        assert "add" in function_names
        assert "multiply" in function_names

    def test_detect_classes(self):
        """测试类识别"""
        analyzer = ASTAnalyzer()
        code = """
class Person:
    def __init__(self, name):
        self.name = name

class Car:
    def drive(self):
        pass
"""
        result = analyzer.parse(code).analyze()
        class_names = {c.name for c in result.classes}
        assert "Person" in class_names
        assert "Car" in class_names

    def test_detect_methods(self):
        """测试方法识别"""
        analyzer = ASTAnalyzer()
        code = """
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
"""
        result = analyzer.parse(code).analyze()
        method_names = {m.name for m in result.methods}
        assert "add" in method_names
        assert "subtract" in method_names

    def test_detect_imports(self):
        """测试导入识别"""
        analyzer = ASTAnalyzer()
        code = """
import os
import sys
from typing import List
"""
        result = analyzer.parse(code).analyze()
        import_names = {i.name for i in result.imports}
        assert "os" in import_names
        assert "sys" in import_names
        assert "typing.List" in import_names

    def test_get_entities_by_type(self):
        """测试按类型获取实体"""
        analyzer = ASTAnalyzer()
        code = "class Test: pass"
        analyzer.parse(code)
        classes = analyzer.get_entities_by_type(NodeType.CLASS)
        assert len(classes) == 1

    def test_dump_ast(self):
        """测试AST打印"""
        analyzer = ASTAnalyzer()
        analyzer.parse("x = 1")
        dump = analyzer.dump_ast()
        assert "Module" in dump
        assert "Assign" in dump


class TestEnhancedVisitor:
    """测试增强型访问者"""

    def test_detect_assignments(self):
        """测试赋值检测"""
        visitor = EnhancedASTVisitor()
        import ast
        code = """
x = 1
y = x + 2
z = y * 3
"""
        tree = ast.parse(code)
        visitor.visit(tree)
        assert len(visitor.assignments) >= 2

    def test_detect_call_sites(self):
        """测试调用点检测"""
        visitor = EnhancedASTVisitor()
        import ast
        code = """
def func():
    pass

func()
result = func()
"""
        tree = ast.parse(code)
        visitor.visit(tree)
        assert len(visitor.call_sites) >= 2


class TestUnifiedSyntaxAnalyzer:
    """测试统一语法分析器"""

    def test_init(self):
        """测试初始化"""
        analyzer = UnifiedSyntaxAnalyzer()
        assert analyzer is not None

    def test_analyze_with_ast(self):
        """测试使用AST分析"""
        analyzer = UnifiedSyntaxAnalyzer(Language.PYTHON)
        code = """
def test_func():
    x = 10
    return x
"""
        result = analyzer.analyze(code)
        assert result["engine"] == "ast"
        assert result["language"] == "python"
        assert len(result["functions"]) == 1
        assert len(result["variables"]) >= 1

    def test_switch_language(self):
        """测试语言切换"""
        analyzer = UnifiedSyntaxAnalyzer()
        analyzer.set_language(Language.JAVASCRIPT)
        assert analyzer.language == Language.JAVASCRIPT

    def test_switch_parser_mode(self):
        """测试解析器模式切换"""
        analyzer = UnifiedSyntaxAnalyzer()
        analyzer.set_parser_mode(use_tree_sitter=False)
        analyzer.set_parser_mode(use_tree_sitter=True)
        # 切换模式验证
        code = "function test() {}"
        result = analyzer.set_language(Language.JAVASCRIPT).set_parser_mode(True).analyze(code)
        assert result["engine"] == "tree-sitter"

    def test_ast_vs_tree_sitter(self):
        """测试两种解析器对比"""
        analyzer = UnifiedSyntaxAnalyzer(Language.PYTHON)
        code = """
class Test:
    def method(self):
        pass
"""
        # AST模式
        result_ast = analyzer.set_parser_mode(False).analyze(code)
        assert result_ast["engine"] == "ast"
        assert len(result_ast["classes"]) == 1


class TestCodeEntity:
    """测试代码实体"""

    def test_code_entity_creation(self):
        """测试创建代码实体"""
        entity = CodeEntity(
            name="test_var",
            type=NodeType.VARIABLE,
            line=5,
            column=10
        )
        assert entity.name == "test_var"
        assert entity.type == NodeType.VARIABLE
        assert entity.line == 5

    def test_code_entity_str(self):
        """测试代码实体字符串表示"""
        entity = CodeEntity(
            name="my_func",
            type=NodeType.FUNCTION,
            line=10,
            column=0
        )
        str_repr = str(entity)
        assert "my_func" in str_repr
        assert "function" in str_repr


class TestComplexScenarios:
    """测试复杂场景"""

    def test_nested_structures(self):
        """测试嵌套结构"""
        analyzer = ASTAnalyzer()
        code = """
class Outer:
    def outer_method(self):
        x = 1
        
        class Inner:
            def inner_method(self):
                y = 2
"""
        result = analyzer.parse(code).analyze()
        assert len(result.classes) == 2
        assert len(result.methods) == 2

    def test_multiple_classes_and_functions(self):
        """测试多类多函数"""
        analyzer = ASTAnalyzer()
        code = """
import math
from datetime import datetime

PI = 3.14

class Circle:
    def area(self, r):
        return PI * r * r

class Square:
    def area(self, s):
        return s * s

def calculate_sum(a, b):
    return a + b

def main():
    c = Circle()
    print(c.area(5))
"""
        result = analyzer.parse(code).analyze()
        assert len(result.classes) == 2
        assert len(result.functions) == 2
        assert len(result.imports) == 2

    def test_async_functions(self):
        """测试异步函数"""
        analyzer = ASTAnalyzer()
        code = """
async def fetch_data():
    pass

async def process_data():
    await fetch_data()
"""
        result = analyzer.parse(code).analyze()
        function_names = {f.name for f in result.functions}
        assert "fetch_data" in function_names
        assert "process_data" in function_names
