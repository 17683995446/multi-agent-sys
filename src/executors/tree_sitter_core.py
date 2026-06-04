from __future__ import annotations

import ast
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Iterator, Tuple
from dataclasses import dataclass


class Language(str, Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


@dataclass
class Point:
    """代码位置点"""
    row: int
    column: int


@dataclass
class Range:
    """代码范围"""
    start_point: Point
    end_point: Point
    start_byte: int
    end_byte: int


class SyntaxNode:
    """语法树节点"""
    
    def __init__(
        self,
        node_type: str,
        text: str,
        start_point: Point,
        end_point: Point,
        children: Optional[List[SyntaxNode]] = None,
        parent: Optional[SyntaxNode] = None
    ):
        self.type = node_type
        self.text = text
        self.start_point = start_point
        self.end_point = end_point
        self.children = children or []
        self.parent = parent
        self._fields: Dict[str, SyntaxNode] = {}
    
    @property
    def start_byte(self) -> int:
        return 0
    
    @property
    def end_byte(self) -> int:
        return len(self.text)
    
    def has_changes(self) -> bool:
        return False
    
    def has_error(self) -> bool:
        return False
    
    def is_missing(self) -> bool:
        return False
    
    def child_by_field_name(self, field_name: str) -> Optional[SyntaxNode]:
        return self._fields.get(field_name)
    
    def walk(self) -> TreeCursor:
        return TreeCursor(self)
    
    def __repr__(self) -> str:
        return f"SyntaxNode(type={self.type!r}, text={self.text[:20]!r})"


class TreeCursor:
    """树遍历光标"""
    
    def __init__(self, node: SyntaxNode):
        self._node = node
        self._stack: List[SyntaxNode] = [node]
    
    @property
    def node(self) -> SyntaxNode:
        return self._stack[-1]
    
    @property
    def current_field_name(self) -> Optional[str]:
        return None
    
    def goto_first_child(self) -> bool:
        if self.node.children:
            self._stack.append(self.node.children[0])
            return True
        return False
    
    def goto_next_sibling(self) -> bool:
        if len(self._stack) < 2:
            return False
        parent = self._stack[-2]
        current = self._stack[-1]
        try:
            idx = parent.children.index(current)
            if idx + 1 < len(parent.children):
                self._stack[-1] = parent.children[idx + 1]
                return True
        except ValueError:
            pass
        return False
    
    def goto_parent(self) -> bool:
        if len(self._stack) > 1:
            self._stack.pop()
            return True
        return False
    
    def reset(self, node: SyntaxNode) -> None:
        self._node = node
        self._stack = [node]


class Tree:
    """语法树"""
    
    def __init__(self, root_node: SyntaxNode, text: str):
        self.root_node = root_node
        self._text = text
    
    @property
    def text(self) -> str:
        return self._text
    
    def edit(self, *args, **kwargs) -> None:
        pass
    
    def walk(self) -> TreeCursor:
        return TreeCursor(self.root_node)


class Parser:
    """代码解析器"""
    
    def __init__(self, language: Language = Language.PYTHON):
        self.language = language
        self._parser_class = self._get_parser_class(language)
    
    def _get_parser_class(self, language: Language):
        parsers = {
            Language.PYTHON: PythonParser,
            Language.JAVASCRIPT: JavaScriptParser,
            Language.TYPESCRIPT: TypeScriptParser,
        }
        return parsers.get(language, PythonParser)
    
    def parse(self, text: bytes | str) -> Tree:
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        parser = self._parser_class()
        return parser.parse(text)


class BaseParser:
    """基础解析器"""
    
    def parse(self, text: str) -> Tree:
        raise NotImplementedError()


class PythonParser(BaseParser):
    """Python 代码解析器"""
    
    def parse(self, text: str) -> Tree:
        try:
            tree = ast.parse(text)
            root = self._convert_ast_node(tree, text)
            return Tree(root, text)
        except SyntaxError as e:
            return self._create_error_tree(text, e)
    
    def _convert_ast_node(self, node: ast.AST, text: str) -> SyntaxNode:
        lines = text.splitlines()
        start_lineno = getattr(node, "lineno", 1) - 1
        end_lineno = getattr(node, "end_lineno", start_lineno + 1) - 1
        start_col = getattr(node, "col_offset", 0)
        end_col = getattr(node, "end_col_offset", 0)
        
        if start_lineno < len(lines):
            line_text = lines[start_lineno]
            node_text = line_text[start_col:end_col] if end_col else line_text[start_col:]
        else:
            node_text = ""
        
        children = []
        for field_name, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                child = self._convert_ast_node(value, text)
                children.append(child)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        child = self._convert_ast_node(item, text)
                        children.append(child)
        
        return SyntaxNode(
            node_type=type(node).__name__,
            text=node_text,
            start_point=Point(start_lineno, start_col),
            end_point=Point(end_lineno, end_col),
            children=children
        )
    
    def _create_error_tree(self, text: str, error: SyntaxError) -> Tree:
        error_node = SyntaxNode(
            node_type="ERROR",
            text=str(error),
            start_point=Point(0, 0),
            end_point=Point(len(text.splitlines()), 0)
        )
        return Tree(error_node, text)


class JavaScriptParser(BaseParser):
    """JavaScript 代码解析器 (简化版)"""
    
    def parse(self, text: str) -> Tree:
        root = self._parse_javascript(text)
        return Tree(root, text)
    
    def _parse_javascript(self, text: str) -> SyntaxNode:
        lines = text.splitlines()
        
        children: List[SyntaxNode] = []
        function_pattern = re.compile(r'function\s+(\w+)')
        class_pattern = re.compile(r'class\s+(\w+)')
        var_pattern = re.compile(r'(?:var|let|const)\s+(\w+)')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            if function_match := function_pattern.search(line):
                children.append(SyntaxNode(
                    node_type="FunctionDeclaration",
                    text=line,
                    start_point=Point(i, 0),
                    end_point=Point(i, len(line))
                ))
            elif class_match := class_pattern.search(line):
                children.append(SyntaxNode(
                    node_type="ClassDeclaration",
                    text=line,
                    start_point=Point(i, 0),
                    end_point=Point(i, len(line))
                ))
            elif var_match := var_pattern.search(line):
                children.append(SyntaxNode(
                    node_type="VariableDeclaration",
                    text=line,
                    start_point=Point(i, 0),
                    end_point=Point(i, len(line))
                ))
        
        return SyntaxNode(
            node_type="Program",
            text=text,
            start_point=Point(0, 0),
            end_point=Point(len(lines), 0),
            children=children
        )


class TypeScriptParser(JavaScriptParser):
    """TypeScript 代码解析器"""
    
    def _parse_javascript(self, text: str) -> SyntaxNode:
        root = super()._parse_javascript(text)
        root.type = "Program"
        
        interface_pattern = re.compile(r'interface\s+(\w+)')
        type_pattern = re.compile(r'type\s+(\w+)')
        lines = text.splitlines()
        
        for i, line in enumerate(lines):
            line = line.strip()
            if interface_pattern.search(line):
                root.children.append(SyntaxNode(
                    node_type="InterfaceDeclaration",
                    text=line,
                    start_point=Point(i, 0),
                    end_point=Point(i, len(line))
                ))
            elif type_pattern.search(line):
                root.children.append(SyntaxNode(
                    node_type="TypeAliasDeclaration",
                    text=line,
                    start_point=Point(i, 0),
                    end_point=Point(i, len(line))
                ))
        
        return root


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, language: Language = Language.PYTHON):
        self.language = language
        self.parser = Parser(language)
    
    def analyze(self, code: str) -> Dict[str, Any]:
        tree = self.parser.parse(code)
        return {
            "language": self.language,
            "root_node": tree.root_node,
            "functions": self._extract_functions(tree),
            "classes": self._extract_classes(tree),
            "variables": self._extract_variables(tree),
        }
    
    def _extract_functions(self, tree: Tree) -> List[Dict[str, Any]]:
        functions: List[Dict[str, Any]] = []
        cursor = tree.walk()
        
        def visit():
            if cursor.node.type in ["FunctionDef", "AsyncFunctionDef", "FunctionDeclaration"]:
                functions.append({
                    "name": cursor.node.text,
                    "type": cursor.node.type,
                    "line": cursor.node.start_point.row,
                })
            if cursor.goto_first_child():
                visit()
                while cursor.goto_next_sibling():
                    visit()
                cursor.goto_parent()
        
        visit()
        return functions
    
    def _extract_classes(self, tree: Tree) -> List[Dict[str, Any]]:
        classes: List[Dict[str, Any]] = []
        cursor = tree.walk()
        
        def visit():
            if cursor.node.type in ["ClassDef", "ClassDeclaration"]:
                classes.append({
                    "name": cursor.node.text,
                    "type": cursor.node.type,
                    "line": cursor.node.start_point.row,
                })
            if cursor.goto_first_child():
                visit()
                while cursor.goto_next_sibling():
                    visit()
                cursor.goto_parent()
        
        visit()
        return classes
    
    def _extract_variables(self, tree: Tree) -> List[Dict[str, Any]]:
        variables: List[Dict[str, Any]] = []
        return variables
