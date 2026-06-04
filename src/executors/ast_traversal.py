from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from .tree_sitter_core import Language


class NodeType(Enum):
    """AST节点类型"""
    VARIABLE = "variable"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    IMPORT = "import"
    ASSIGNMENT = "assignment"
    EXPRESSION = "expression"
    STATEMENT = "statement"
    MODULE = "module"


@dataclass
class CodeEntity:
    """代码实体信息"""
    name: str
    type: NodeType
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    parent_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.type.value}:{self.name} @{self.line}:{self.column}"


@dataclass
class ASTAnalysisResult:
    """AST分析结果"""
    variables: List[CodeEntity] = field(default_factory=list)
    functions: List[CodeEntity] = field(default_factory=list)
    classes: List[CodeEntity] = field(default_factory=list)
    methods: List[CodeEntity] = field(default_factory=list)
    imports: List[CodeEntity] = field(default_factory=list)
    all_entities: List[CodeEntity] = field(default_factory=list)


class BaseASTVisitor(ast.NodeVisitor):
    """基础AST访问者"""

    def __init__(self):
        self.result = ASTAnalysisResult()
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None

    def visit_Module(self, node: ast.Module) -> Any:
        """访问模块节点"""
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        """访问函数定义"""
        entity = CodeEntity(
            name=node.name,
            type=NodeType.METHOD if self.current_class else NodeType.FUNCTION,
            line=node.lineno,
            column=node.col_offset,
            end_line=getattr(node, "end_lineno", None),
            end_column=getattr(node, "end_col_offset", None),
            parent_name=self.current_class
        )
        if self.current_class:
            self.result.methods.append(entity)
        else:
            self.result.functions.append(entity)
        self.result.all_entities.append(entity)
        
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        """访问类定义"""
        entity = CodeEntity(
            name=node.name,
            type=NodeType.CLASS,
            line=node.lineno,
            column=node.col_offset,
            end_line=getattr(node, "end_lineno", None),
            end_column=getattr(node, "end_col_offset", None)
        )
        self.result.classes.append(entity)
        self.result.all_entities.append(entity)
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Name(self, node: ast.Name) -> Any:
        """访问名称节点（变量等）"""
        if isinstance(node.ctx, ast.Store):
            entity = CodeEntity(
                name=node.id,
                type=NodeType.VARIABLE,
                line=node.lineno,
                column=node.col_offset,
                parent_name=self.current_class or self.current_function
            )
            self.result.variables.append(entity)
            self.result.all_entities.append(entity)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> Any:
        """访问导入语句"""
        for alias in node.names:
            entity = CodeEntity(
                name=alias.name,
                type=NodeType.IMPORT,
                line=node.lineno,
                column=node.col_offset
            )
            self.result.imports.append(entity)
            self.result.all_entities.append(entity)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        """访问从...导入语句"""
        module = node.module or ""
        for alias in node.names:
            entity = CodeEntity(
                name=f"{module}.{alias.name}" if module else alias.name,
                type=NodeType.IMPORT,
                line=node.lineno,
                column=node.col_offset
            )
            self.result.imports.append(entity)
            self.result.all_entities.append(entity)
        self.generic_visit(node)


class EnhancedASTVisitor(BaseASTVisitor):
    """增强型AST访问者，支持更多特性"""

    def __init__(self):
        super().__init__()
        self.assignments: List[CodeEntity] = []
        self.call_sites: List[Dict[str, Any]] = []

    def visit_Assign(self, node: ast.Assign) -> Any:
        """访问赋值语句"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                entity = CodeEntity(
                    name=target.id,
                    type=NodeType.ASSIGNMENT,
                    line=node.lineno,
                    column=node.col_offset,
                    parent_name=self.current_class or self.current_function
                )
                self.assignments.append(entity)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        """访问函数调用"""
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        if func_name:
            self.call_sites.append({
                "name": func_name,
                "line": node.lineno,
                "column": node.col_offset,
                "args_count": len(node.args)
            })
        self.generic_visit(node)


class ASTAnalyzer:
    """AST分析器"""

    def __init__(self):
        self.source_code: str = ""
        self.tree: Optional[ast.Module] = None

    def parse(self, source_code: str) -> ASTAnalyzer:
        """解析源代码"""
        self.source_code = source_code
        try:
            self.tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error: {e}") from e
        return self

    def analyze(self) -> ASTAnalysisResult:
        """执行完整AST分析"""
        if not self.tree:
            raise ValueError("No source code parsed. Call parse() first.")
        
        visitor = EnhancedASTVisitor()
        visitor.visit(self.tree)
        return visitor.result

    def get_entities_by_type(self, node_type: NodeType) -> List[CodeEntity]:
        """按类型获取实体"""
        result = self.analyze()
        type_map = {
            NodeType.VARIABLE: result.variables,
            NodeType.FUNCTION: result.functions,
            NodeType.CLASS: result.classes,
            NodeType.METHOD: result.methods,
            NodeType.IMPORT: result.imports
        }
        return type_map.get(node_type, [])

    def dump_ast(self, indent: int = 2) -> str:
        """打印AST结构"""
        if not self.tree:
            raise ValueError("No source code parsed. Call parse() first.")
        return ast.dump(self.tree, indent=indent)


class UnifiedSyntaxAnalyzer:
    """统一语法分析器（支持AST和Tree-sitter）"""

    def __init__(self, language: Language = Language.PYTHON):
        self.language = language
        self.ast_analyzer = ASTAnalyzer()
        self._use_tree_sitter: bool = False

    def set_language(self, language: Language) -> UnifiedSyntaxAnalyzer:
        """设置语言"""
        self.language = language
        return self

    def set_parser_mode(self, use_tree_sitter: bool = False) -> UnifiedSyntaxAnalyzer:
        """设置解析器模式"""
        self._use_tree_sitter = use_tree_sitter
        return self

    def analyze(self, source_code: str) -> Dict[str, Any]:
        """统一分析接口"""
        if self.language == Language.PYTHON and not self._use_tree_sitter:
            return self._analyze_with_ast(source_code)
        else:
            return self._analyze_with_tree_sitter(source_code)

    def _analyze_with_ast(self, source_code: str) -> Dict[str, Any]:
        """使用AST分析（Python专用）"""
        try:
            result = self.ast_analyzer.parse(source_code).analyze()
            return {
                "engine": "ast",
                "language": "python",
                "variables": [{"name": e.name, "line": e.line} for e in result.variables],
                "functions": [{"name": e.name, "line": e.line} for e in result.functions],
                "classes": [{"name": e.name, "line": e.line} for e in result.classes],
                "methods": [{"name": e.name, "line": e.line} for e in result.methods],
                "imports": [{"name": e.name, "line": e.line} for e in result.imports],
                "total_entities": len(result.all_entities)
            }
        except Exception as e:
            return {"engine": "ast", "error": str(e)}

    def _analyze_with_tree_sitter(self, source_code: str) -> Dict[str, Any]:
        """使用Tree-sitter分析"""
        from .tree_sitter_core import CodeAnalyzer as TSCodeAnalyzer
        ts_analyzer = TSCodeAnalyzer(self.language)
        ts_result = ts_analyzer.analyze(source_code)
        return {
            "engine": "tree-sitter",
            "language": self.language.value,
            "variables": [],
            "functions": ts_result.get("functions", []),
            "classes": ts_result.get("classes", []),
            "methods": [],
            "imports": [],
            "total_entities": len(ts_result.get("functions", [])) + len(ts_result.get("classes", []))
        }
