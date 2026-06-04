from __future__ import annotations

import ast
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class MethodType(str, Enum):
    """方法类型"""
    FUNCTION = "function"
    CLASS_METHOD = "class_method"
    STATIC_METHOD = "static_method"
    INSTANCE_METHOD = "instance_method"


class ResponsibilityCategory(str, Enum):
    """职责分类"""
    DATA_PROCESSING = "data_processing"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_FORMATTING = "output_formatting"
    ERROR_HANDLING = "error_handling"
    FILE_OPERATION = "file_operation"
    NETWORK_OPERATION = "network_operation"
    CALCULATION = "calculation"
    CONTROL_FLOW = "control_flow"
    LOGGING = "logging"
    INITIALIZATION = "initialization"
    CLEANUP = "cleanup"


class SplittingStrategy(str, Enum):
    """拆分策略"""
    BY_RESPONSIBILITY = "by_responsibility"
    BY_CODE_BLOCK = "by_code_block"
    BY_COMMENT = "by_comment"
    BY_SIZE = "by_size"


@dataclass
class Parameter:
    """参数信息"""
    name: str
    annotation: Optional[str] = None
    default_value: Optional[str] = None
    position: int = 0
    is_vararg: bool = False
    is_kwarg: bool = False
    is_kwonly: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "annotation": self.annotation,
            "default_value": self.default_value,
            "position": self.position,
            "is_vararg": self.is_vararg,
            "is_kwarg": self.is_kwarg,
            "is_kwonly": self.is_kwonly
        }


@dataclass
class CodeBlock:
    """代码块信息"""
    block_id: str
    start_line: int
    end_line: int
    content: str
    type: str = "unknown"
    responsibility: Optional[ResponsibilityCategory] = None
    used_variables: List[str] = field(default_factory=list)
    variables_declared: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "type": self.type,
            "responsibility": self.responsibility.value if self.responsibility else None,
            "used_variables": self.used_variables,
            "variables_declared": self.variables_declared
        }


@dataclass
class Responsibility:
    """职责信息"""
    responsibility_id: str
    category: ResponsibilityCategory
    description: str
    code_blocks: List[str] = field(default_factory=list)
    complexity: int = 1
    importance: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "responsibility_id": self.responsibility_id,
            "category": self.category.value,
            "description": self.description,
            "code_blocks": self.code_blocks,
            "complexity": self.complexity,
            "importance": self.importance
        }


@dataclass
class MethodInfo:
    """方法信息"""
    method_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    method_type: MethodType = MethodType.FUNCTION
    file_path: str = ""
    class_name: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    col_start: int = 0
    col_end: int = 0
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    code_content: str = ""
    line_count: int = 0
    code_blocks: List[CodeBlock] = field(default_factory=list)
    responsibilities: List[Responsibility] = field(default_factory=list)
    responsibility_count: int = 1
    cyclomatic_complexity: int = 1
    cognitive_complexity: int = 1
    max_nesting_depth: int = 0
    suggestions: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_id": self.method_id,
            "name": self.name,
            "method_type": self.method_type.value,
            "file_path": self.file_path,
            "class_name": self.class_name,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "col_start": self.col_start,
            "col_end": self.col_end,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type,
            "decorators": self.decorators,
            "docstring": self.docstring,
            "code_content": self.code_content,
            "line_count": self.line_count,
            "code_blocks": [cb.to_dict() for cb in self.code_blocks],
            "responsibilities": [r.to_dict() for r in self.responsibilities],
            "responsibility_count": self.responsibility_count,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "max_nesting_depth": self.max_nesting_depth,
            "suggestions": self.suggestions,
            "issues": self.issues
        }


@dataclass
class MethodSplit:
    """方法拆分结果"""
    original_method: MethodInfo
    new_methods: List[MethodInfo] = field(default_factory=list)
    applied_strategy: SplittingStrategy = SplittingStrategy.BY_RESPONSIBILITY
    description: str = ""
    validation_passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_method": self.original_method.to_dict(),
            "new_methods": [m.to_dict() for m in self.new_methods],
            "applied_strategy": self.applied_strategy.value,
            "description": self.description,
            "validation_passed": self.validation_passed
        }


@dataclass
class RefactorReport:
    """重构报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=datetime.now)
    file_path: str = ""
    total_methods: int = 0
    methods_analyzed: int = 0
    methods_requiring_refactor: int = 0
    methods_split: int = 0
    refactored_methods: List[MethodSplit] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("METHOD REFACTORING REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.generated_at.isoformat()}")
        lines.append(f"File: {self.file_path}")
        lines.append("-" * 80)
        lines.append(f"Total Methods: {self.total_methods}")
        lines.append(f"Analyzed: {self.methods_analyzed}")
        lines.append(f"Requiring Refactor: {self.methods_requiring_refactor}")
        lines.append(f"Successfully Split: {self.methods_split}")
        lines.append("-" * 80)
        
        for i, split in enumerate(self.refactored_methods, 1):
            lines.append(f"\n[{i}] {split.original_method.name}")
            lines.append(f"    Strategy: {split.applied_strategy.value}")
            lines.append(f"    Split into {len(split.new_methods)} methods")
            for new_method in split.new_methods:
                lines.append(f"      - {new_method.name}")
        
        if self.summary_stats:
            lines.append("\n" + "=" * 80)
            lines.append("SUMMARY STATISTICS")
            lines.append("=" * 80)
            for key, value in self.summary_stats.items():
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "file_path": self.file_path,
            "total_methods": self.total_methods,
            "methods_analyzed": self.methods_analyzed,
            "methods_requiring_refactor": self.methods_requiring_refactor,
            "methods_split": self.methods_split,
            "refactored_methods": [ms.to_dict() for ms in self.refactored_methods],
            "summary_stats": self.summary_stats
        }


class MethodScanner(ast.NodeVisitor):
    """方法扫描器 - AST遍历"""

    def __init__(self, file_path: str = ""):
        self.methods: List[MethodInfo] = []
        self.file_path: str = file_path
        self.current_class: Optional[str] = None
        self.source_lines: List[str] = []

    def scan(self, source_code: str, file_path: str = "") -> List[MethodInfo]:
        """扫描源代码"""
        if file_path:
            self.file_path = file_path
        self.methods.clear()
        self.current_class = None
        self.source_lines = source_code.split('\n')
        
        try:
            tree = ast.parse(source_code)
            self.visit(tree)
        except SyntaxError:
            pass
        
        return self.methods

    def scan_file(self, file_path: str) -> List[MethodInfo]:
        """扫描文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            return self.scan(source, file_path)
        except Exception:
            return []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """处理类定义"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """处理函数/方法定义"""
        method_info = self._parse_method(node)
        if method_info:
            self.methods.append(method_info)
        self.generic_visit(node)

    def _parse_method(self, node: ast.FunctionDef) -> Optional[MethodInfo]:
        """解析方法信息"""
        method_info = MethodInfo(
            name=node.name,
            file_path=self.file_path,
            class_name=self.current_class,
            line_start=node.lineno,
            line_end=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            col_start=node.col_offset,
            col_end=node.end_col_offset if hasattr(node, 'end_col_offset') else node.col_offset + len(node.name)
        )

        method_info.method_type = self._determine_method_type(node)
        method_info.decorators = self._parse_decorators(node)
        method_info.parameters = self._parse_parameters(node)
        method_info.return_type = self._parse_return_type(node)
        method_info.docstring = ast.get_docstring(node)
        method_info.code_content = self._extract_code_content(node)
        method_info.line_count = method_info.line_end - method_info.line_start + 1

        return method_info

    def _determine_method_type(self, node: ast.FunctionDef) -> MethodType:
        """确定方法类型"""
        if not self.current_class:
            return MethodType.FUNCTION
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == 'classmethod':
                    return MethodType.CLASS_METHOD
                if decorator.id == 'staticmethod':
                    return MethodType.STATIC_METHOD
        
        return MethodType.INSTANCE_METHOD

    def _parse_decorators(self, node: ast.FunctionDef) -> List[str]:
        """解析装饰器"""
        decorators = []
        for decorator in node.decorator_list:
            try:
                decorators.append(ast.unparse(decorator))
            except Exception:
                pass
        return decorators

    def _parse_parameters(self, node: ast.FunctionDef) -> List[Parameter]:
        """解析参数"""
        params = []
        
        position = 0
        for arg in node.args.args:
            param = Parameter(
                name=arg.arg,
                position=position,
                annotation=ast.unparse(arg.annotation) if arg.annotation else None
            )
            params.append(param)
            position += 1
        
        if node.args.vararg:
            param = Parameter(
                name=node.args.vararg.arg,
                position=position,
                is_vararg=True
            )
            params.append(param)
            position += 1
        
        for arg in node.args.kwonlyargs:
            param = Parameter(
                name=arg.arg,
                position=position,
                is_kwonly=True,
                annotation=ast.unparse(arg.annotation) if arg.annotation else None
            )
            params.append(param)
            position += 1
        
        if node.args.kwarg:
            param = Parameter(
                name=node.args.kwarg.arg,
                position=position,
                is_kwarg=True
            )
            params.append(param)
        
        return params

    def _parse_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        """解析返回类型"""
        if node.returns:
            try:
                return ast.unparse(node.returns)
            except Exception:
                pass
        return None

    def _extract_code_content(self, node: ast.FunctionDef) -> str:
        """提取方法代码内容"""
        start = node.lineno - 1
        end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
        return "\n".join(self.source_lines[start:end])


class ComplexityAnalyzer:
    """复杂度分析器"""

    def analyze_method(self, method_info: MethodInfo) -> MethodInfo:
        """分析方法复杂度"""
        try:
            tree = ast.parse(method_info.code_content)
            complexity_visitor = ComplexityVisitor()
            complexity_visitor.visit(tree)
            
            method_info.cyclomatic_complexity = complexity_visitor.cyclomatic_complexity
            method_info.cognitive_complexity = complexity_visitor.cognitive_complexity
            method_info.max_nesting_depth = complexity_visitor.max_nesting_depth
        except Exception:
            pass
        
        return method_info


class ComplexityVisitor(ast.NodeVisitor):
    """复杂度计算访问者"""

    def __init__(self):
        self.cyclomatic_complexity = 1
        self.cognitive_complexity = 0
        self.max_nesting_depth = 0
        self.current_nesting = 0

    def visit_If(self, node: ast.If) -> None:
        """处理If语句"""
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += (self.current_nesting + 1)
        self._handle_nesting(node)

    def visit_For(self, node: ast.For) -> None:
        """处理For循环"""
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += (self.current_nesting + 1)
        self._handle_nesting(node)

    def visit_While(self, node: ast.While) -> None:
        """处理While循环"""
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += (self.current_nesting + 1)
        self._handle_nesting(node)

    def visit_With(self, node: ast.With) -> None:
        """处理With语句"""
        self.cognitive_complexity += (self.current_nesting + 1)
        self._handle_nesting(node)

    def visit_Try(self, node: ast.Try) -> None:
        """处理Try语句"""
        self.cyclomatic_complexity += len(node.handlers)
        self.cognitive_complexity += (self.current_nesting + 1) * (1 + len(node.handlers))
        self._handle_nesting(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """处理布尔操作"""
        self.cyclomatic_complexity += len(node.values) - 1

    def _handle_nesting(self, node: ast.AST) -> None:
        """处理嵌套深度"""
        self.current_nesting += 1
        self.max_nesting_depth = max(self.max_nesting_depth, self.current_nesting)
        self.generic_visit(node)
        self.current_nesting -= 1


class ResponsibilityAnalyzer:
    """职责分析器"""

    RESPONSIBILITY_PATTERNS = {
        ResponsibilityCategory.INPUT_VALIDATION: [
            r'\.validate\b', r'\.check\b', r'\.is_valid\b', r'\bassert\b',
            r'raise.*Error.*invalid', r'not.*valid'
        ],
        ResponsibilityCategory.DATA_PROCESSING: [
            r'\.transform\b', r'\.process\b', r'\.convert\b', r'\.format\b',
            r'\.parse\b', r'\.extract\b', r'\.filter\b', r'\.map\b'
        ],
        ResponsibilityCategory.CALCULATION: [
            r'\bcalculate\b', r'\bcompute\b', r'\bcalculate\b', r'\bsum\b',
            r'\baverage\b', r'\bmin\b', r'\bmax\b', r'[\d+*/-]'
        ],
        ResponsibilityCategory.LOGGING: [
            r'\.log\b', r'\.info\b', r'\.debug\b', r'\.warn\b', r'\.error\b',
            r'\.critical\b', r'\.exception\b'
        ],
        ResponsibilityCategory.FILE_OPERATION: [
            r'\.open\b', r'\.read\b', r'\.write\b', r'\.close\b',
            r'\.save\b', r'\.load\b'
        ],
        ResponsibilityCategory.ERROR_HANDLING: [
            r'\bexcept\b', r'\btry\b', r'\bfinally\b',
            r'\.handle\b', r'\.recover\b'
        ]
    }

    def analyze_method(self, method_info: MethodInfo) -> MethodInfo:
        """分析方法职责"""
        method_info.code_blocks = self._extract_code_blocks(method_info)
        method_info.responsibilities = self._identify_responsibilities(method_info)
        method_info.responsibility_count = len(method_info.responsibilities)
        
        self._check_single_responsibility(method_info)
        
        return method_info

    def _extract_code_blocks(self, method_info: MethodInfo) -> List[CodeBlock]:
        """提取代码块"""
        blocks = []
        try:
            tree = ast.parse(method_info.code_content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While, ast.If, ast.Try, ast.With)):
                    block_id = f"block_{len(blocks)}"
                    block = CodeBlock(
                        block_id=block_id,
                        start_line=node.lineno,
                        end_line=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        content=self._extract_block_content(method_info, node),
                        type=type(node).__name__,
                        responsibility=self._guess_block_responsibility(node)
                    )
                    blocks.append(block)
        except Exception:
            pass
        return blocks

    def _extract_block_content(self, method_info: MethodInfo, node: ast.AST) -> str:
        """提取块内容"""
        start = max(0, node.lineno - 1)
        end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
        lines = method_info.code_content.split('\n')
        return '\n'.join(lines[start:end])

    def _guess_block_responsibility(self, node: ast.AST) -> Optional[ResponsibilityCategory]:
        """猜测块职责"""
        # 首先检查节点类型
        if isinstance(node, ast.Try):
            return ResponsibilityCategory.ERROR_HANDLING
        
        # 然后检查内容
        content = ast.dump(node)
        for category, patterns in self.RESPONSIBILITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return category
        
        # 为简单的If语句尝试分配默认职责
        if isinstance(node, ast.If):
            return ResponsibilityCategory.CONTROL_FLOW
            
        return None

    def _identify_responsibilities(self, method_info: MethodInfo) -> List[Responsibility]:
        """识别职责"""
        responsibilities = []
        category_counts: Dict[ResponsibilityCategory, int] = {}
        
        for block in method_info.code_blocks:
            if block.responsibility:
                category_counts[block.responsibility] = category_counts.get(block.responsibility, 0) + 1
        
        for category, count in category_counts.items():
            resp = Responsibility(
                responsibility_id=f"resp_{len(responsibilities)}",
                category=category,
                description=f"{category.value.capitalize()} responsibility",
                complexity=count,
                importance=count / max(1, len(method_info.code_blocks))
            )
            responsibilities.append(resp)
        
        # 如果没有识别到任何职责，添加一个默认职责
        if not responsibilities:
            resp = Responsibility(
                responsibility_id="resp_default",
                category=ResponsibilityCategory.DATA_PROCESSING,
                description="General method responsibility",
                complexity=1,
                importance=1.0
            )
            responsibilities.append(resp)
        
        return responsibilities

    def _check_single_responsibility(self, method_info: MethodInfo) -> None:
        """检查单一职责原则"""
        if method_info.responsibility_count > 1:
            method_info.issues.append(f"Method has {method_info.responsibility_count} responsibilities (should be 1)")
            method_info.suggestions.append("Consider splitting the method based on its responsibilities")
        
        if method_info.line_count > 30:
            method_info.issues.append(f"Method is too long ({method_info.line_count} lines)")
            method_info.suggestions.append("Consider breaking down into smaller methods")
        
        if method_info.cyclomatic_complexity > 10:
            method_info.issues.append(f"Cyclomatic complexity is too high ({method_info.cyclomatic_complexity})")
            method_info.suggestions.append("Consider reducing complexity by extracting methods")
        
        if method_info.max_nesting_depth > 3:
            method_info.issues.append(f"Nesting depth is too high ({method_info.max_nesting_depth})")
            method_info.suggestions.append("Consider extracting nested blocks into separate methods")


class MethodSplitter:
    """方法拆分器"""

    def split_method(self, method_info: MethodInfo, strategy: SplittingStrategy = SplittingStrategy.BY_RESPONSIBILITY) -> MethodSplit:
        """拆分方法"""
        result = MethodSplit(
            original_method=method_info,
            applied_strategy=strategy,
            description=f"Split using {strategy.value} strategy"
        )
        
        if strategy == SplittingStrategy.BY_RESPONSIBILITY:
            result.new_methods = self._split_by_responsibility(method_info)
        elif strategy == SplittingStrategy.BY_CODE_BLOCK:
            result.new_methods = self._split_by_code_block(method_info)
        elif strategy == SplittingStrategy.BY_COMMENT:
            result.new_methods = self._split_by_comment(method_info)
        elif strategy == SplittingStrategy.BY_SIZE:
            result.new_methods = self._split_by_size(method_info)
        
        return result

    def _split_by_responsibility(self, method_info: MethodInfo) -> List[MethodInfo]:
        """按职责拆分"""
        new_methods = []
        for resp in method_info.responsibilities:
            new_method = MethodInfo(
                name=f"{method_info.name}_{resp.category.value}",
                method_type=method_info.method_type,
                file_path=method_info.file_path,
                class_name=method_info.class_name,
                parameters=method_info.parameters.copy(),
                return_type=method_info.return_type,
                docstring=f"Auto-generated method for {resp.description}"
            )
            new_methods.append(new_method)
        
        return new_methods

    def _split_by_code_block(self, method_info: MethodInfo) -> List[MethodInfo]:
        """按代码块拆分"""
        new_methods = []
        for block in method_info.code_blocks:
            new_method = MethodInfo(
                name=f"{method_info.name}_block_{len(new_methods)}",
                method_type=method_info.method_type,
                file_path=method_info.file_path,
                class_name=method_info.class_name,
                code_content=block.content
            )
            new_methods.append(new_method)
        
        return new_methods

    def _split_by_comment(self, method_info: MethodInfo) -> List[MethodInfo]:
        """按注释拆分"""
        new_methods = []
        lines = method_info.code_content.split('\n')
        current_block: List[str] = []
        block_counter = 0
        
        for line in lines:
            if line.strip().startswith('#') and any(keyword in line.lower() for keyword in ['todo', 'note', 'section', 'split', '---']):
                if current_block:
                    new_method = self._create_method_from_block(current_block, method_info, block_counter)
                    new_methods.append(new_method)
                    block_counter += 1
                    current_block = []
            current_block.append(line)
        
        if current_block:
            new_method = self._create_method_from_block(current_block, method_info, block_counter)
            new_methods.append(new_method)
        
        return new_methods

    def _split_by_size(self, method_info: MethodInfo, max_lines: int = 30) -> List[MethodInfo]:
        """按大小拆分"""
        new_methods = []
        lines = method_info.code_content.split('\n')
        
        for i in range(0, len(lines), max_lines):
            block = lines[i:i+max_lines]
            new_method = self._create_method_from_block(block, method_info, i // max_lines)
            new_methods.append(new_method)
        
        return new_methods

    def _create_method_from_block(self, lines: List[str], original_method: MethodInfo, counter: int) -> MethodInfo:
        """从代码块创建新方法"""
        return MethodInfo(
            name=f"{original_method.name}_part_{counter}",
            method_type=original_method.method_type,
            file_path=original_method.file_path,
            class_name=original_method.class_name,
            code_content='\n'.join(lines),
            line_count=len(lines),
            parameters=original_method.parameters.copy()
        )


class MethodAnalyzer:
    """方法分析管理器"""

    def __init__(self):
        self.scanner = MethodScanner()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.responsibility_analyzer = ResponsibilityAnalyzer()
        self.splitter = MethodSplitter()

    def analyze_source(self, source_code: str, file_path: str = "") -> List[MethodInfo]:
        """分析源代码"""
        methods = self.scanner.scan(source_code, file_path)
        
        for method in methods:
            self.complexity_analyzer.analyze_method(method)
            self.responsibility_analyzer.analyze_method(method)
        
        return methods

    def analyze_file(self, file_path: str) -> List[MethodInfo]:
        """分析文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return self.analyze_source(f.read(), file_path)

    def generate_report(self, file_path: str) -> RefactorReport:
        """生成重构报告"""
        methods = self.analyze_file(file_path)
        
        report = RefactorReport(
            file_path=file_path,
            total_methods=len(methods),
            methods_analyzed=len(methods)
        )
        
        for method in methods:
            if method.issues:
                report.methods_requiring_refactor += 1
                if method.responsibility_count > 1:
                    split = self.splitter.split_method(method)
                    report.refactored_methods.append(split)
                    report.methods_split += 1
        
        report.summary_stats = {
            "avg_responsibilities": sum(m.responsibility_count for m in methods) / max(1, len(methods)),
            "avg_complexity": sum(m.cyclomatic_complexity for m in methods) / max(1, len(methods)),
            "max_line_count": max(m.line_count for m in methods) if methods else 0,
            "issues_found": sum(len(m.issues) for m in methods)
        }
        
        return report


_global_analyzer: Optional[MethodAnalyzer] = None


def get_method_analyzer() -> MethodAnalyzer:
    """获取全局方法分析器"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = MethodAnalyzer()
    return _global_analyzer


def reset_method_analyzer() -> None:
    """重置方法分析器"""
    global _global_analyzer
    _global_analyzer = None
