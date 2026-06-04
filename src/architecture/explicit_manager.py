from __future__ import annotations

import ast
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.core import get_logger


logger = get_logger("explicit_manager")


class ImplicitStateType(str, Enum):
    """隐式状态类型"""
    GLOBAL_VARIABLE = "global_variable"
    MODULE_LEVEL_STATE = "module_level_state"
    CLASS_VARIABLE = "class_variable"
    CACHING_RESULT = "caching_result"
    SIDE_EFFECT = "side_effect"
    MAGIC_NUMBER = "magic_number"
    MAGIC_STRING = "magic_string"


@dataclass
class ImplicitState:
    """隐式状态记录"""
    state_type: ImplicitStateType
    location: str
    line_number: int
    description: str
    code_snippet: str
    severity: str = "medium"
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "state_type": self.state_type.value,
            "location": self.location,
            "line_number": self.line_number,
            "description": self.description,
            "code_snippet": self.code_snippet,
            "severity": self.severity,
            "suggestion": self.suggestion
        }


@dataclass
class TraceLink:
    """追溯链路"""
    trace_id: str
    source: str
    target: str
    relationship: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class ImplicitStateDetector:
    """隐式状态检测器"""

    IMPLICIT_PATTERNS = {
        ImplicitStateType.GLOBAL_VARIABLE: [
            r'^([A-Z_][A-Z0-9_]*)\s*=\s*[^=]',
            r'^global\s+[a-zA-Z_]'
        ],
        ImplicitStateType.MAGIC_NUMBER: [
            r'\b\d{1,4}\b(?!\s*[+\-*/%]\s*\d)'
        ],
        ImplicitStateType.MAGIC_STRING: [
            r'["\'][^"\']{0,50}["\']'
        ],
        ImplicitStateType.SIDE_EFFECT: [
            r'\bprint\s*\(',
            r'\bopen\s*\(',
            r'\beval\s*\(',
            r'\bexec\s*\('
        ]
    }

    def __init__(self):
        self.detected_states: List[ImplicitState] = []

    def detect_file(self, file_path: str) -> List[ImplicitState]:
        """检测文件中的隐式状态"""
        self.detected_states = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            self._detect_with_ast(file_path, source)
            self._detect_with_patterns(file_path, source)
        except Exception as e:
            logger.error(f"检测文件 {file_path} 失败: {e}")
        return self.detected_states

    def _detect_with_ast(self, file_path: str, source: str) -> None:
        """使用AST检测隐式状态"""
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                self._check_node(node, file_path, source)
        except SyntaxError:
            logger.warning(f"文件 {file_path} 存在语法错误")

    def _check_node(self, node: ast.AST, file_path: str, source: str) -> None:
        """检查AST节点"""
        if isinstance(node, ast.Global):
            for name in node.names:
                line_no = node.lineno
                line = self._get_line(source, line_no)
                self.detected_states.append(ImplicitState(
                    state_type=ImplicitStateType.GLOBAL_VARIABLE,
                    location=file_path,
                    line_number=line_no,
                    description=f"全局变量声明: {name}",
                    code_snippet=line,
                    severity="high",
                    suggestion=f"考虑使用参数传递或返回值替代全局变量 {name}"
                ))

        elif isinstance(node, ast.FunctionDef):
            for global_node in ast.walk(node):
                if isinstance(global_node, ast.Global):
                    for name in global_node.names:
                        line_no = global_node.lineno
                        line = self._get_line(source, line_no)
                        self.detected_states.append(ImplicitState(
                            state_type=ImplicitStateType.GLOBAL_VARIABLE,
                            location=file_path,
                            line_number=line_no,
                            description=f"函数内全局变量: {name}",
                            code_snippet=line,
                            severity="medium"
                        ))

        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    if isinstance(item.annotation, ast.Name) and item.annotation.id == "ClassVar":
                        continue
                    if not isinstance(item.value, (ast.Call, ast.BinOp, ast.Constant)):
                        line_no = item.lineno
                        line = self._get_line(source, line_no)
                        self.detected_states.append(ImplicitState(
                            state_type=ImplicitStateType.CLASS_VARIABLE,
                            location=file_path,
                            line_number=line_no,
                            description=f"类变量可能需要显式初始化: {item.target.id}",
                            code_snippet=line,
                            severity="low"
                        ))

    def _detect_with_patterns(self, file_path: str, source: str) -> None:
        """使用正则模式检测"""
        lines = source.split('\n')
        for line_no, line in enumerate(lines, start=1):
            for state_type, patterns in self.IMPLICIT_PATTERNS.items():
                if state_type == ImplicitStateType.MAGIC_NUMBER:
                    if self._is_magic_number(line):
                        self.detected_states.append(ImplicitState(
                            state_type=state_type,
                            location=file_path,
                            line_number=line_no,
                            description="可能使用魔数",
                            code_snippet=line.strip(),
                            severity="low",
                            suggestion="考虑定义常量替代魔数"
                        ))

                elif state_type == ImplicitStateType.SIDE_EFFECT:
                    for pattern in patterns:
                        if re.search(pattern, line):
                            func_name = re.search(r'(\w+)\s*\(', line)
                            if func_name:
                                self.detected_states.append(ImplicitState(
                                    state_type=state_type,
                                    location=file_path,
                                    line_number=line_no,
                                    description=f"可能的副作用: {func_name.group(1)}",
                                    code_snippet=line.strip(),
                                    severity="medium",
                                    suggestion="确保副作用是显式且可控的"
                                ))

    def _is_magic_number(self, line: str) -> bool:
        """判断是否为魔数"""
        magic_numbers = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                        '100', '1000', '3600', '24', '60', '365', '12', '30'}
        numbers = re.findall(r'\b\d+\b', line)
        for num in numbers:
            if num not in magic_numbers:
                return True
        return False

    def _get_line(self, source: str, line_no: int) -> str:
        """获取指定行"""
        lines = source.split('\n')
        if 0 < line_no <= len(lines):
            return lines[line_no - 1].strip()
        return ""


class ExplicitConverter:
    """显式化转换器"""

    def __init__(self):
        self.conversions: List[Dict[str, Any]] = []

    def convert_to_constant(self, code: str, name: str, value: Any) -> str:
        """将魔数转换为常量"""
        if isinstance(value, int):
            return f"{name} = {value}  # 常量定义"
        return f"{name} = {repr(value)}  # 常量定义"

    def convert_global_to_parameter(self, code: str, var_name: str) -> str:
        """将全局变量转换为函数参数"""
        lines = code.split('\n')
        result_lines = []
        for line in lines:
            if f'global {var_name}' in line:
                result_lines.append(f"# 已移除全局声明: {line.strip()}")
            else:
                result_lines.append(line)
        return '\n'.join(result_lines)

    def generate_explicit_state(self, implicit_state: ImplicitState) -> str:
        """为隐式状态生成显式代码"""
        if implicit_state.state_type == ImplicitStateType.MAGIC_NUMBER:
            return f"# 建议定义常量: YOUR_CONSTANT_NAME = {implicit_state.code_snippet.strip()}"
        elif implicit_state.state_type == ImplicitStateType.GLOBAL_VARIABLE:
            return f"# 建议: 使用依赖注入或返回值替代全局变量"
        elif implicit_state.state_type == ImplicitStateType.SIDE_EFFECT:
            return f"# 警告: 确认此副作用是预期的，并添加注释说明"
        return "# 需要人工审查"


class TraceChain:
    """追溯链"""

    def __init__(self):
        self.links: Dict[str, List[TraceLink]] = {}

    def add_link(self, source: str, target: str, relationship: str, metadata: Optional[Dict[str, Any]] = None) -> TraceLink:
        """添加链路"""
        trace_id = str(uuid.uuid4())
        link = TraceLink(
            trace_id=trace_id,
            source=source,
            target=target,
            relationship=relationship,
            metadata=metadata or {}
        )
        if source not in self.links:
            self.links[source] = []
        self.links[source].append(link)
        logger.debug(f"添加追溯链路: {source} -> {target} ({relationship})")
        return link

    def get_trace(self, source: str) -> List[TraceLink]:
        """获取从指定源的所有链路"""
        return self.links.get(source, [])

    def find_path(self, start: str, end: str) -> Optional[List[str]]:
        """查找从起点到终点的路径"""
        visited = set()
        path = []

        def dfs(current: str) -> bool:
            if current == end:
                path.append(current)
                return True
            if current in visited:
                return False
            visited.add(current)
            path.append(current)
            for link in self.links.get(current, []):
                if dfs(link.target):
                    return True
            path.pop()
            return False

        if dfs(start):
            return path
        return None

    def get_full_trace(self, entity: str) -> Dict[str, Any]:
        """获取完整追溯信息"""
        incoming = []
        outgoing = []

        for src, links in self.links.items():
            for link in links:
                if link.target == entity:
                    incoming.append(link.to_dict())
                if src == entity:
                    outgoing.append(link.to_dict())

        return {
            "entity": entity,
            "incoming_links": incoming,
            "outgoing_links": outgoing,
            "trace_count": len(incoming) + len(outgoing)
        }


class ExplicitRule:
    """显式化规范"""

    def __init__(self):
        self.rules: Dict[str, bool] = {
            "require_type_hints": True,
            "require_docstrings": True,
            "no_global_variables": False,
            "no_magic_numbers": True,
            "require_explicit_imports": True,
            "require_return_values": True
        }

    def enable_rule(self, rule_name: str) -> None:
        """启用规则"""
        if rule_name in self.rules:
            self.rules[rule_name] = True
            logger.info(f"启用显式化规则: {rule_name}")

    def disable_rule(self, rule_name: str) -> None:
        """禁用规则"""
        if rule_name in self.rules:
            self.rules[rule_name] = False
            logger.info(f"禁用显式化规则: {rule_name}")

    def is_enabled(self, rule_name: str) -> bool:
        """检查规则是否启用"""
        return self.rules.get(rule_name, False)

    def get_enabled_rules(self) -> List[str]:
        """获取所有启用的规则"""
        return [rule for rule, enabled in self.rules.items() if enabled]


class ExplicitChecker:
    """显式化检查器"""

    def __init__(self, rule: Optional[ExplicitRule] = None):
        self.rule = rule or ExplicitRule()
        self.violations: List[Dict[str, Any]] = []

    def check_file(self, file_path: str) -> List[Dict[str, Any]]:
        """检查文件显式化规范"""
        self.violations = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            self._check_type_hints(file_path, source)
            self._check_docstrings(file_path, source)
            self._check_magic_numbers(file_path, source)
        except Exception as e:
            logger.error(f"检查文件 {file_path} 失败: {e}")
        return self.violations

    def _check_type_hints(self, file_path: str, source: str) -> None:
        """检查类型提示"""
        if not self.rule.is_enabled("require_type_hints"):
            return

        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.returns is None and len(node.args.args) > 0:
                        self.violations.append({
                            "file": file_path,
                            "line": node.lineno,
                            "rule": "require_type_hints",
                            "message": f"函数 {node.name} 缺少返回类型注解",
                            "severity": "warning"
                        })
        except SyntaxError:
            pass

    def _check_docstrings(self, file_path: str, source: str) -> None:
        """检查文档字符串"""
        if not self.rule.is_enabled("require_docstrings"):
            return

        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        self.violations.append({
                            "file": file_path,
                            "line": node.lineno,
                            "rule": "require_docstrings",
                            "message": f"{node.__class__.__name__} {node.name} 缺少文档字符串",
                            "severity": "info"
                        })
        except SyntaxError:
            pass

    def _check_magic_numbers(self, file_path: str, source: str) -> None:
        """检查魔数"""
        if not self.rule.is_enabled("no_magic_numbers"):
            return

        detector = ImplicitStateDetector()
        states = detector.detect_file(file_path)
        for state in states:
            if state.state_type == ImplicitStateType.MAGIC_NUMBER:
                self.violations.append({
                    "file": file_path,
                    "line": state.line_number,
                    "rule": "no_magic_numbers",
                    "message": f"检测到魔数: {state.code_snippet}",
                    "severity": "warning"
                })


class ExplicitManager:
    """显式化管理器"""

    def __init__(self):
        self.detector = ImplicitStateDetector()
        self.converter = ExplicitConverter()
        self.trace_chain = TraceChain()
        self.checker = ExplicitChecker()
        self.logger = get_logger("explicit_manager")

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """扫描文件并返回分析结果"""
        implicit_states = self.detector.detect_file(file_path)
        violations = self.checker.check_file(file_path)

        return {
            "file": file_path,
            "implicit_states": [s.to_dict() for s in implicit_states],
            "violations": violations,
            "total_implicit": len(implicit_states),
            "total_violations": len(violations),
            "explicitness_score": self._calculate_score(len(implicit_states), len(violations))
        }

    def _calculate_score(self, implicit_count: int, violation_count: int) -> float:
        """计算显式化得分"""
        total = implicit_count + violation_count
        if total == 0:
            return 100.0
        return max(0.0, 100.0 - (implicit_count * 5 + violation_count * 2))

    def add_trace(self, source: str, target: str, relationship: str) -> None:
        """添加追溯链路"""
        self.trace_chain.add_link(source, target, relationship)

    def get_trace(self, entity: str) -> Dict[str, Any]:
        """获取追溯信息"""
        return self.trace_chain.get_full_trace(entity)


def create_explicit_manager() -> ExplicitManager:
    """创建显式化管理器"""
    return ExplicitManager()
