from __future__ import annotations

import ast
import re
import keyword
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Callable


class VariableType(str, Enum):
    """变量类型分类"""
    LOCAL = "local"
    PARAMETER = "parameter"
    GLOBAL = "global"
    CONSTANT = "constant"
    CLASS_VAR = "class_var"
    INSTANCE_VAR = "instance_var"


class VariableCategory(str, Enum):
    """变量语义分类"""
    DATA = "data"
    CONTROL = "control"
    STATE = "state"
    TEMPORARY = "temporary"
    CONFIG = "config"
    OUTPUT = "output"
    INDEX = "index"


class VariableIssueType(str, Enum):
    """变量问题类型"""
    SHORT_NAME = "short_name"
    BAD_NAMING = "bad_naming"
    TYPE_MISMATCH = "type_mismatch"
    UNUSED = "unused"
    MAGIC_NUMBER = "magic_number"
    AMBIGUOUS = "ambiguous"
    SHADOWING = "shadowing"


@dataclass
class VariableInfo:
    """变量信息"""
    var_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    var_type: VariableType = VariableType.LOCAL
    category: VariableCategory = VariableCategory.DATA
    scope: str = ""
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    col_start: int = 0
    col_end: int = 0
    type_annotation: Optional[str] = None
    assigned_type: Optional[str] = None
    used_in: List[int] = field(default_factory=list)
    assigned: bool = False
    redefined: bool = False
    issues: List[VariableIssueType] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    original_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "var_id": self.var_id,
            "name": self.name,
            "var_type": self.var_type.value,
            "category": self.category.value,
            "scope": self.scope,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "type_annotation": self.type_annotation,
            "assigned_type": self.assigned_type,
            "assigned": self.assigned,
            "redefined": self.redefined,
            "issues": [i.value for i in self.issues],
            "suggestions": self.suggestions
        }


@dataclass
class NamingSuggestion:
    """命名建议"""
    original: str
    suggested: List[str]
    reason: str


class VariableScanner(ast.NodeVisitor):
    """变量扫描器 - AST遍历"""

    def __init__(self, file_path: str = ""):
        self.variables: Dict[str, VariableInfo] = {}
        self.current_scopes: List[str] = []
        self.file_path: str = file_path
        self._var_counter: int = 0

    def scan(self, source_code: str, file_path: str = "") -> List[VariableInfo]:
        """扫描源代码"""
        if file_path:
            self.file_path = file_path
        self.variables.clear()
        self.current_scopes = []
        self._var_counter = 0
        
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
        except SyntaxError as e:
            pass
        
        return list(self.variables.values())

    def scan_file(self, file_path: str) -> List[VariableInfo]:
        """扫描文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            return self.scan(source, file_path)
        except Exception as e:
            return []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """处理函数定义"""
        scope_name = f"function_{node.name}"
        self.current_scopes.append(scope_name)
        
        for i, arg in enumerate(node.args.args):
            self._add_parameter(arg, i)
        
        self.generic_visit(node)
        self.current_scopes.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """处理类定义"""
        scope_name = f"class_{node.name}"
        self.current_scopes.append(scope_name)
        
        self.generic_visit(node)
        self.current_scopes.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        """处理赋值语句"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._add_variable(
                    target.id,
                    node,
                    self._guess_category(target.id),
                    VariableType.LOCAL
                )
        
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """处理名称引用"""
        if isinstance(node.ctx, ast.Store):
            if self._in_class_scope():
                var_type = VariableType.INSTANCE_VAR
            else:
                var_type = VariableType.LOCAL
            
            self._add_variable(
                node.id,
                node,
                self._guess_category(node.id),
                var_type
            )
        
        elif isinstance(node.ctx, ast.Load):
            var_id = f"{'.'.join(self.current_scopes)}::{node.id}"
            if var_id in self.variables:
                self.variables[var_id].used_in.append(node.lineno)
        
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        """处理全局声明"""
        for name in node.names:
            var_id = f"global::{name}"
            if var_id in self.variables:
                self.variables[var_id].var_type = VariableType.GLOBAL
        
        self.generic_visit(node)

    def _add_variable(self, name: str, node: ast.AST, category: VariableCategory, var_type: VariableType) -> None:
        """添加变量信息"""
        scope = "::".join(self.current_scopes) if self.current_scopes else "global"
        var_id = f"{scope}::{name}"
        
        if var_id in self.variables:
            self.variables[var_id].redefined = True
            self.variables[var_id].used_in.append(node.lineno)
            return
        
        type_annotation = self._extract_type_annotation(node)
        assigned_type = self._guess_assigned_type(node)
        
        self.variables[var_id] = VariableInfo(
            name=name,
            var_type=var_type,
            category=category,
            scope=scope,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            col_start=node.col_offset,
            col_end=node.end_col_offset if hasattr(node, 'end_col_offset') else node.col_offset + len(name),
            type_annotation=type_annotation,
            assigned_type=assigned_type,
            assigned=True
        )

    def _add_parameter(self, arg: ast.arg, index: int) -> None:
        """添加函数参数"""
        scope = "::".join(self.current_scopes)
        var_id = f"{scope}::{arg.arg}"
        
        type_annotation = None
        if arg.annotation:
            type_annotation = ast.unparse(arg.annotation)
        
        self.variables[var_id] = VariableInfo(
            name=arg.arg,
            var_type=VariableType.PARAMETER,
            category=self._guess_category(arg.arg),
            scope=scope,
            file_path=self.file_path,
            line_start=arg.lineno,
            line_end=arg.end_lineno if hasattr(arg, 'end_lineno') else arg.lineno,
            col_start=arg.col_offset,
            col_end=arg.end_col_offset if hasattr(arg, 'end_col_offset') else arg.col_offset + len(arg.arg),
            type_annotation=type_annotation
        )

    def _guess_category(self, name: str) -> VariableCategory:
        """猜测量语义分类"""
        name_lower = name.lower()
        
        if name_lower in ['temp', 'tmp', 'x', 'y', 'z', 'i', 'j', 'k']:
            return VariableCategory.TEMPORARY
        
        if name_lower in ['i', 'j', 'k', 'index', 'idx', 'count', 'iter']:
            return VariableCategory.INDEX
        
        if name_lower in ['config', 'settings', 'opts', 'params']:
            return VariableCategory.CONFIG
        
        if name_lower in ['result', 'output', 'return', 'ret']:
            return VariableCategory.OUTPUT
        
        if name_lower in ['flag', 'status', 'state', 'enabled', 'disabled']:
            return VariableCategory.STATE
        
        return VariableCategory.DATA

    def _extract_type_annotation(self, node: ast.AST) -> Optional[str]:
        """提取类型注解"""
        if isinstance(node, ast.AnnAssign):
            return ast.unparse(node.annotation)
        return None

    def _guess_assigned_type(self, node: ast.AST) -> Optional[str]:
        """猜测赋值类型"""
        if isinstance(node, ast.Assign):
            value = node.value
            if isinstance(value, ast.Constant):
                return type(value.value).__name__
            elif isinstance(value, ast.List):
                return "list"
            elif isinstance(value, ast.Dict):
                return "dict"
            elif isinstance(value, ast.Tuple):
                return "tuple"
            elif isinstance(value, ast.Set):
                return "set"
            elif isinstance(value, ast.Call):
                if isinstance(value.func, ast.Name):
                    return value.func.id
        return None

    def _in_class_scope(self) -> bool:
        """判断是否在类作用域中"""
        return any(scope.startswith("class_") for scope in self.current_scopes)


class VariableClassifier:
    """变量分类器 - 基本+语义分类"""

    def __init__(self):
        self._naming_rules: Dict[str, re.Pattern] = {
            'constant': re.compile(r'^[A-Z][A-Z0-9_]*$'),
            'private': re.compile(r'^_[a-z][a-z0-9_]*$'),
            'snake_case': re.compile(r'^[a-z][a-z0-9_]*$'),
            'camel_case': re.compile(r'^[a-z][a-zA-Z0-9]*$')
        }

    def classify(self, var: VariableInfo) -> VariableInfo:
        """执行完整分类"""
        var = self._check_naming_style(var)
        var = self._check_semantic_category(var)
        var = self._check_type_consistency(var)
        var = self._detect_issues(var)
        return var

    def _check_naming_style(self, var: VariableInfo) -> VariableInfo:
        """检查命名风格"""
        if var.var_type == VariableType.CONSTANT:
            if not self._naming_rules['constant'].match(var.name):
                var.issues.append(VariableIssueType.BAD_NAMING)
                var.suggestions.append(f"Consider naming as {var.name.upper()}")
        
        elif var.name.startswith('_'):
            if not self._naming_rules['private'].match(var.name):
                var.issues.append(VariableIssueType.BAD_NAMING)
        
        elif not self._naming_rules['snake_case'].match(var.name):
            var.issues.append(VariableIssueType.BAD_NAMING)
        
        return var

    def _check_semantic_category(self, var: VariableInfo) -> VariableInfo:
        """检查语义分类是否合适"""
        # 识别索引变量
        if var.name in ['i', 'j', 'k', 'index', 'idx', 'counter', 'iter']:
            var.category = VariableCategory.INDEX
        
        # 检查短名
        if len(var.name) == 1:
            if var.var_type != VariableType.PARAMETER or var.name not in ['i', 'j', 'k']:
                var.issues.append(VariableIssueType.SHORT_NAME)
                var.suggestions.append(f"Use a more descriptive name instead of '{var.name}'")
        
        if len(var.name) <= 2 and var.name not in ['id', 'is', 'of', 'to']:
            var.issues.append(VariableIssueType.SHORT_NAME)
            var.suggestions.append("Use a more descriptive name")
        
        return var

    def _check_type_consistency(self, var: VariableInfo) -> VariableInfo:
        """检查类型一致性"""
        if var.type_annotation and var.assigned_type:
            if self._types_incompatible(var.type_annotation, var.assigned_type):
                var.issues.append(VariableIssueType.TYPE_MISMATCH)
                var.suggestions.append(f"Type annotation {var.type_annotation} may not match assigned {var.assigned_type}")
        return var

    def _detect_issues(self, var: VariableInfo) -> VariableInfo:
        """检测其他问题"""
        if keyword.iskeyword(var.name):
            var.issues.append(VariableIssueType.AMBIGUOUS)
            var.suggestions.append("Avoid using Python keywords as variable names")
        
        if not var.used_in and var.var_type == VariableType.LOCAL:
            var.issues.append(VariableIssueType.UNUSED)
            var.suggestions.append("Consider removing unused variable")
        
        if re.match(r'^\d+$', var.name):
            var.issues.append(VariableIssueType.MAGIC_NUMBER)
            var.suggestions.append("Avoid using numeric-only variable names")
        
        return var

    def _types_incompatible(self, type1: str, type2: str) -> bool:
        """简单的类型兼容性检查"""
        numeric = ['int', 'float', 'complex']
        sequences = ['list', 'tuple', 'set']
        
        if type1 in numeric and type2 in numeric:
            return False
        if type1 in sequences and type2 in sequences:
            return False
        if type1 in ['str', 'bytes'] and type2 in ['str', 'bytes']:
            return False
        
        return type1.lower() != type2.lower()


class NamingHelper:
    """命名辅助工具"""

    @staticmethod
    def suggest_names(name: str, category: Optional[VariableCategory] = None) -> NamingSuggestion:
        """生成命名建议"""
        suggestions: List[str] = []
        reason = ""
        
        if len(name) == 1:
            replacements = {
                'x': ['data', 'value', 'item'],
                'i': ['index', 'idx', 'counter'],
                'j': ['inner_index', 'j_index'],
                'k': ['loop_counter', 'iterator'],
                'y': ['secondary', 'alt_value'],
                'z': ['tertiary', 'other_val']
            }
            if name in replacements:
                suggestions.extend(replacements[name])
                reason = "Single-letter variable names can be ambiguous"
        
        # 常量检查基于名字而不是category
        if name.isupper() or ('_' in name and name[0].isalpha()):
            if not name.isupper():
                suggestions.append(name.upper())
                reason = "Constants should be in ALL_CAPS"
        
        if not suggestions:
            snake_case = NamingHelper._to_snake_case(name)
            if snake_case != name:
                suggestions.append(snake_case)
        
        if not suggestions:
            if category == VariableCategory.TEMPORARY:
                suggestions.append(f"temp_{name}")
                suggestions.append(f"tmp_{name}")
        
        return NamingSuggestion(
            original=name,
            suggested=suggestions,
            reason=reason
        )

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """转换为蛇形命名"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class VariableFixer:
    """自动纠错工具 - 建议+自动修复"""

    def __init__(self):
        self.classifier = VariableClassifier()
        self.naming_helper = NamingHelper()

    def analyze_variable(self, var: VariableInfo) -> Dict[str, Any]:
        """分析变量并生成建议"""
        var = self.classifier.classify(var)
        
        return {
            "var_id": var.var_id,
            "name": var.name,
            "issues": var.issues,
            "suggestions": var.suggestions,
            "can_fix_automatically": self._can_fix_automatically(var)
        }

    def fix_naming(self, var: VariableInfo) -> Optional[VariableInfo]:
        """尝试自动修复命名"""
        if VariableIssueType.SHORT_NAME in var.issues or VariableIssueType.BAD_NAMING in var.issues:
            suggestion = self.naming_helper.suggest_names(var.name, var.category)
            if suggestion.suggested:
                var.name = suggestion.suggested[0]
                var.suggestions = [f"Renamed from '{suggestion.original}'"]
                return var
        return None

    def fix_in_code(self, source_code: str, variables: List[VariableInfo]) -> Tuple[str, List[Dict[str, Any]]]:
        """在源码中应用修复"""
        lines = source_code.split('\n')
        changes: List[Dict[str, Any]] = []
        
        for var in variables:
            if self._can_fix_automatically(var):
                if VariableIssueType.SHORT_NAME in var.issues or VariableIssueType.BAD_NAMING in var.issues:
                    fix = self.fix_naming(var)
                    if fix:
                        line_idx = var.line_start - 1
                        if 0 <= line_idx < len(lines):
                            old_line = lines[line_idx]
                            new_line = self._replace_var_in_line(old_line, var.name, fix.name)
                            if new_line != old_line:
                                lines[line_idx] = new_line
                                changes.append({
                                    "old": old_line,
                                    "new": new_line,
                                    "var": var.name,
                                    "replacement": fix.name
                                })
        
        return '\n'.join(lines), changes

    def _replace_var_in_line(self, line: str, old_name: str, new_name: str) -> str:
        """在单行中替换变量名"""
        pattern = r'\b' + re.escape(old_name) + r'\b'
        return re.sub(pattern, new_name, line)

    def _can_fix_automatically(self, var: VariableInfo) -> bool:
        """判断是否可以自动修复"""
        return VariableIssueType.SHORT_NAME in var.issues or VariableIssueType.BAD_NAMING in var.issues


class VariableAnalyzer:
    """变量分析管理器 - 整合扫描、分类、纠错"""

    def __init__(self):
        self.scanner = VariableScanner()
        self.classifier = VariableClassifier()
        self.fixer = VariableFixer()

    def analyze_source(self, source_code: str, file_path: str = "") -> Dict[str, Any]:
        """分析源代码"""
        variables = self.scanner.scan(source_code, file_path)
        
        analyzed_vars: List[VariableInfo] = []
        for var in variables:
            analyzed = self.classifier.classify(var)
            analyzed_vars.append(analyzed)
        
        issues_count = sum(len(var.issues) for var in analyzed_vars)
        fixable_count = sum(1 for var in analyzed_vars if self.fixer._can_fix_automatically(var))
        
        return {
            "variables": [v.to_dict() for v in analyzed_vars],
            "total_count": len(analyzed_vars),
            "issues_count": issues_count,
            "fixable_count": fixable_count
        }

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析文件"""
        return self.analyze_source(open(file_path, 'r', encoding='utf-8').read(), file_path)

    def fix_file(self, file_path: str) -> Dict[str, Any]:
        """修复文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        variables = self.scanner.scan(source, file_path)
        
        for var in variables:
            self.classifier.classify(var)
        
        fixed_source, changes = self.fixer.fix_in_code(source, variables)
        
        return {
            "file_path": file_path,
            "changes_count": len(changes),
            "changes": changes,
            "fixed_source": fixed_source
        }


_global_analyzer: Optional[VariableAnalyzer] = None


def get_variable_analyzer() -> VariableAnalyzer:
    """获取变量分析器"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = VariableAnalyzer()
    return _global_analyzer


def reset_variable_analyzer() -> None:
    """重置变量分析器"""
    global _global_analyzer
    _global_analyzer = None
