import pytest
from src.executors.tree_sitter_core import (
    Language, Parser, PythonParser, JavaScriptParser, TypeScriptParser,
    CodeAnalyzer, SyntaxNode, Tree, TreeCursor, Point
)


class TestTreeSitterCore:
    """测试 Tree-sitter 核心功能"""
    
    def test_language_enum(self):
        """测试语言枚举"""
        assert Language.PYTHON == "python"
        assert Language.JAVASCRIPT == "javascript"
        assert Language.TYPESCRIPT == "typescript"
    
    def test_point_creation(self):
        """测试位置点创建"""
        point = Point(row=0, column=10)
        assert point.row == 0
        assert point.column == 10
    
    def test_syntax_node_creation(self):
        """测试语法节点创建"""
        node = SyntaxNode(
            node_type="FunctionDef",
            text="def test():",
            start_point=Point(0, 0),
            end_point=Point(0, 10)
        )
        assert node.type == "FunctionDef"
        assert node.text == "def test():"
        assert node.start_point.row == 0
        assert node.end_point.row == 0
    
    def test_tree_creation(self):
        """测试语法树创建"""
        root = SyntaxNode(
            node_type="Module",
            text="test code",
            start_point=Point(0, 0),
            end_point=Point(1, 0)
        )
        tree = Tree(root, "test code")
        assert tree.root_node == root
        assert tree.text == "test code"
    
    def test_tree_cursor(self):
        """测试树遍历光标"""
        root = SyntaxNode(
            node_type="Module",
            text="",
            start_point=Point(0, 0),
            end_point=Point(0, 0)
        )
        child = SyntaxNode(
            node_type="FunctionDef",
            text="def test():",
            start_point=Point(0, 0),
            end_point=Point(0, 10)
        )
        root.children.append(child)
        
        cursor = TreeCursor(root)
        assert cursor.node == root
        assert cursor.goto_first_child()
        assert cursor.node == child
        assert cursor.goto_parent()
        assert cursor.node == root


class TestPythonParser:
    """测试 Python 解析器"""
    
    def test_python_parser_init(self):
        """测试 Python 解析器初始化"""
        parser = PythonParser()
        assert parser is not None
    
    def test_parse_simple_python(self):
        """测试解析简单 Python 代码"""
        code = """def hello():
    return "world"
"""
        parser = PythonParser()
        tree = parser.parse(code)
        assert tree.root_node is not None
        assert tree.text == code
    
    def test_parser_api(self):
        """测试 Parser API"""
        parser = Parser(Language.PYTHON)
        assert parser.language == Language.PYTHON
        
        code = "x = 1 + 2"
        tree = parser.parse(code)
        assert tree is not None
    
    def test_parse_python_with_class(self):
        """测试解析包含类的 Python 代码"""
        code = """class Test:
    def method(self):
        pass
"""
        parser = PythonParser()
        tree = parser.parse(code)
        assert tree.root_node is not None


class TestJavaScriptParser:
    """测试 JavaScript 解析器"""
    
    def test_javascript_parser_init(self):
        """测试 JavaScript 解析器初始化"""
        parser = JavaScriptParser()
        assert parser is not None
    
    def test_parse_javascript_function(self):
        """测试解析 JavaScript 函数"""
        code = """function hello() {
    return "world";
}
"""
        parser = JavaScriptParser()
        tree = parser.parse(code)
        assert tree.root_node is not None
        assert len(tree.root_node.children) > 0
    
    def test_parse_javascript_class(self):
        """测试解析 JavaScript 类"""
        code = """class Test {
    method() {}
}
"""
        parser = JavaScriptParser()
        tree = parser.parse(code)
        assert tree.root_node is not None


class TestTypeScriptParser:
    """测试 TypeScript 解析器"""
    
    def test_typescript_parser_init(self):
        """测试 TypeScript 解析器初始化"""
        parser = TypeScriptParser()
        assert parser is not None
    
    def test_parse_typescript_interface(self):
        """测试解析 TypeScript 接口"""
        code = """interface User {
    name: string;
    age: number;
}
"""
        parser = TypeScriptParser()
        tree = parser.parse(code)
        assert tree.root_node is not None
    
    def test_parse_typescript_type(self):
        """测试解析 TypeScript 类型别名"""
        code = "type Status = 'active' | 'inactive';"
        parser = TypeScriptParser()
        tree = parser.parse(code)
        assert tree.root_node is not None


class TestCodeAnalyzer:
    """测试代码分析器"""
    
    def test_analyzer_init(self):
        """测试分析器初始化"""
        analyzer = CodeAnalyzer(Language.PYTHON)
        assert analyzer.language == Language.PYTHON
        assert analyzer.parser is not None
    
    def test_analyze_python_code(self):
        """测试分析 Python 代码"""
        code = """def greet():
    print("hello")

class Person:
    pass
"""
        analyzer = CodeAnalyzer(Language.PYTHON)
        result = analyzer.analyze(code)
        assert result["language"] == Language.PYTHON
        assert "functions" in result
        assert "classes" in result
    
    def test_analyze_javascript_code(self):
        """测试分析 JavaScript 代码"""
        code = """function add(a, b) {
    return a + b;
}
"""
        analyzer = CodeAnalyzer(Language.JAVASCRIPT)
        result = analyzer.analyze(code)
        assert result["language"] == Language.JAVASCRIPT


class TestMultiLanguageSwitching:
    """测试多语言切换"""
    
    def test_switch_python_to_javascript(self):
        """测试从 Python 切换到 JavaScript"""
        parser = Parser(Language.PYTHON)
        assert parser.language == Language.PYTHON
        
        parser = Parser(Language.JAVASCRIPT)
        assert parser.language == Language.JAVASCRIPT
    
    def test_switch_javascript_to_typescript(self):
        """测试从 JavaScript 切换到 TypeScript"""
        parser = Parser(Language.JAVASCRIPT)
        assert parser.language == Language.JAVASCRIPT
        
        parser = Parser(Language.TYPESCRIPT)
        assert parser.language == Language.TYPESCRIPT
    
    def test_analyze_multiple_languages(self):
        """测试分析多种语言代码"""
        python_code = "x = 1"
        js_code = "let x = 1;"
        
        analyzer = CodeAnalyzer(Language.PYTHON)
        py_result = analyzer.analyze(python_code)
        assert py_result["language"] == Language.PYTHON
        
        analyzer = CodeAnalyzer(Language.JAVASCRIPT)
        js_result = analyzer.analyze(js_code)
        assert js_result["language"] == Language.JAVASCRIPT


class TestTreeTraversal:
    """测试语法树遍历"""
    
    def test_cursor_traversal(self):
        """测试光标遍历"""
        code = """def f1():
    pass

def f2():
    pass
"""
        parser = Parser(Language.PYTHON)
        tree = parser.parse(code)
        cursor = tree.walk()
        
        assert cursor.node is not None
        assert hasattr(cursor, "goto_first_child")
        assert hasattr(cursor, "goto_next_sibling")
        assert hasattr(cursor, "goto_parent")
    
    def test_walk_method(self):
        """测试 walk 方法"""
        code = "x = 1"
        parser = Parser(Language.PYTHON)
        tree = parser.parse(code)
        
        cursor = tree.walk()
        assert cursor is not None
        assert isinstance(cursor, TreeCursor)
