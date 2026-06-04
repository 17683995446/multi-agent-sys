"""
评审Agent模块
职责：四级原子校验、规范检查、评审报告生成

基于第一性原理：简单、单一、可追溯、可组合
"""

import re
import ast
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class ReviewSeverity(str, Enum):
    """问题严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReviewCategory(str, Enum):
    """评审类别"""
    NAMING = "naming"
    STYLE = "style"
    STRUCTURE = "structure"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BEST_PRACTICES = "best_practices"
    ATOM_VERIFICATION = "atom_verification"


class AtomLevel(str, Enum):
    """原子层级"""
    VARIABLE = "variable"
    METHOD = "method"
    CLASS = "class"
    MODULE = "module"


@dataclass
class ReviewIssue:
    """评审问题"""
    issue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: ReviewSeverity = ReviewSeverity.WARNING
    category: ReviewCategory = ReviewCategory.STYLE
    title: str = ""
    description: str = ""
    location: str = ""
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggested_fix: str = ""
    atom_level: Optional[AtomLevel] = None


@dataclass
class AtomVerification:
    """原子验证"""
    atom_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    atom_level: AtomLevel = AtomLevel.VARIABLE
    name: str = ""
    is_valid: bool = False
    issues: List[ReviewIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ReviewConfig:
    """评审Agent配置"""
    name: str
    check_naming: bool = True
    check_style: bool = True
    check_structure: bool = True
    check_performance: bool = True
    check_security: bool = True
    check_best_practices: bool = True
    enable_atom_verification: bool = True
    enable_atom_level_1: bool = True
    enable_atom_level_2: bool = True
    enable_atom_level_3: bool = True
    enable_atom_level_4: bool = True


@dataclass
class ReviewReport:
    """评审报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reviewed_files: List[str] = field(default_factory=list)
    total_issues: int = 0
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    issues: List[ReviewIssue] = field(default_factory=list)
    atom_verifications: List[AtomVerification] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class NamingChecker:
    """命名检查器"""
    
    def __init__(self):
        self.patterns = {
            'snake_case': r'^[a-z][a-z0-9_]*$',
            'PascalCase': r'^[A-Z][a-zA-Z0-9]*$',
            'CONSTANT_CASE': r'^[A-Z][A-Z0-9_]*$',
        }
    
    def check_variable_naming(self, name: str, line: Optional[int] = None) -> List[ReviewIssue]:
        """检查变量命名"""
        issues = []
        
        if not re.match(self.patterns['snake_case'], name):
            issues.append(ReviewIssue(
                severity=ReviewSeverity.WARNING,
                category=ReviewCategory.NAMING,
                title=f"变量命名不符合规范: {name}",
                description=f"变量名应使用snake_case格式",
                line_number=line,
                suggested_fix=f"重命名为符合snake_case的名称，如 '{name.lower().replace(' ', '_')}'",
                atom_level=AtomLevel.VARIABLE
            ))
        
        return issues
    
    def check_function_naming(self, name: str, line: Optional[int] = None) -> List[ReviewIssue]:
        """检查函数命名"""
        issues = []
        
        if not re.match(self.patterns['snake_case'], name):
            issues.append(ReviewIssue(
                severity=ReviewSeverity.WARNING,
                category=ReviewCategory.NAMING,
                title=f"函数命名不符合规范: {name}",
                description=f"函数名应使用snake_case格式",
                line_number=line,
                suggested_fix=f"重命名为符合snake_case的名称",
                atom_level=AtomLevel.METHOD
            ))
        
        return issues
    
    def check_class_naming(self, name: str, line: Optional[int] = None) -> List[ReviewIssue]:
        """检查类命名"""
        issues = []
        
        if not re.match(self.patterns['PascalCase'], name):
            issues.append(ReviewIssue(
                severity=ReviewSeverity.WARNING,
                category=ReviewCategory.NAMING,
                title=f"类命名不符合规范: {name}",
                description=f"类名应使用PascalCase格式",
                line_number=line,
                suggested_fix=f"重命名为符合PascalCase的名称",
                atom_level=AtomLevel.CLASS
            ))
        
        return issues
    
    def check_constant_naming(self, name: str, line: Optional[int] = None) -> List[ReviewIssue]:
        """检查常量命名"""
        issues = []
        
        if not re.match(self.patterns['CONSTANT_CASE'], name):
            issues.append(ReviewIssue(
                severity=ReviewSeverity.WARNING,
                category=ReviewCategory.NAMING,
                title=f"常量命名不符合规范: {name}",
                description=f"常量名应使用CONSTANT_CASE格式",
                line_number=line,
                suggested_fix=f"重命名为符合CONSTANT_CASE的名称",
                atom_level=AtomLevel.VARIABLE
            ))
        
        return issues


class StyleChecker:
    """代码风格检查器"""
    
    def __init__(self):
        self.line_length_limit = 88
        self.max_nesting_depth = 4
    
    def check_line_length(self, content: str) -> List[ReviewIssue]:
        """检查行长度"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if len(line) > self.line_length_limit:
                issues.append(ReviewIssue(
                    severity=ReviewSeverity.WARNING,
                    category=ReviewCategory.STYLE,
                    title=f"行过长: {len(line)}字符",
                    description=f"行超过{self.line_length_limit}字符限制",
                    line_number=line_num,
                    suggested_fix="将长行拆分为多行"
                ))
        
        return issues
    
    def check_indentation(self, content: str) -> List[ReviewIssue]:
        """检查缩进"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.lstrip()
            if stripped_line:
                indent = len(line) - len(stripped_line)
                if indent % 4 != 0:
                    issues.append(ReviewIssue(
                        severity=ReviewSeverity.WARNING,
                        category=ReviewCategory.STYLE,
                        title=f"缩进不规范: {indent}空格",
                        description=f"缩进应为4的倍数",
                        line_number=line_num,
                        suggested_fix="调整为4的倍数"
                    ))
        
        return issues


class AtomVerifier:
    """原子验证器"""
    
    def __init__(self):
        self.naming_checker = NamingChecker()
    
    def verify_variable(self, name: str, value: Optional[Any] = None) -> AtomVerification:
        """验证变量原子"""
        verification = AtomVerification(
            atom_level=AtomLevel.VARIABLE,
            name=name
        )
        
        issues = self.naming_checker.check_variable_naming(name)
        
        if len(name) < 2:
            issues.append(ReviewIssue(
                severity=ReviewSeverity.WARNING,
                category=ReviewCategory.NAMING,
                title=f"变量名过短: {name}",
                description="变量名应具有描述性",
                atom_level=AtomLevel.VARIABLE
            ))
        
        verification.issues = issues
        verification.is_valid = len(issues) == 0
        
        return verification
    
    def verify_method(self, name: str, params: List[str] = None) -> AtomVerification:
        """验证方法原子"""
        verification = AtomVerification(
            atom_level=AtomLevel.METHOD,
            name=name
        )
        
        issues = self.naming_checker.check_function_naming(name)
        
        if params and len(params) > 10:
            issues.append(ReviewIssue(
                severity=ReviewSeverity.WARNING,
                category=ReviewCategory.BEST_PRACTICES,
                title=f"函数参数过多: {len(params)}",
                description="建议参数不超过10个，可考虑封装为对象",
                atom_level=AtomLevel.METHOD
            ))
        
        verification.issues = issues
        verification.is_valid = len(issues) == 0
        
        return verification
    
    def verify_class(self, name: str) -> AtomVerification:
        """验证类原子"""
        verification = AtomVerification(
            atom_level=AtomLevel.CLASS,
            name=name
        )
        
        issues = self.naming_checker.check_class_naming(name)
        
        verification.issues = issues
        verification.is_valid = len(issues) == 0
        
        return verification


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self):
        self.naming_checker = NamingChecker()
        self.style_checker = StyleChecker()
        self.atom_verifier = AtomVerifier()
    
    def analyze_content(self, content: str, file_path: str = "") -> List[ReviewIssue]:
        """分析代码内容"""
        issues = []
        
        issues.extend(self.style_checker.check_line_length(content))
        issues.extend(self.style_checker.check_indentation(content))
        
        try:
            tree = ast.parse(content)
            visitor = CodeReviewVisitor()
            visitor.visit(tree)
            issues.extend(visitor.issues)
        except SyntaxError:
            pass
        
        return issues
    
    def verify_atoms(self, content: str, config: ReviewConfig) -> List[AtomVerification]:
        """验证四级原子"""
        verifications = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if config.enable_atom_level_1:
                        verifications.append(self.atom_verifier.verify_variable(node.id))
                
                if isinstance(node, ast.FunctionDef):
                    if config.enable_atom_level_2:
                        verifications.append(self.atom_verifier.verify_method(
                            node.name,
                            [arg.arg for arg in node.args.args]
                        ))
                
                if isinstance(node, ast.ClassDef):
                    if config.enable_atom_level_3:
                        verifications.append(self.atom_verifier.verify_class(node.name))
        except SyntaxError:
            pass
        
        return verifications


class CodeReviewVisitor(ast.NodeVisitor):
    """代码评审访问者"""
    
    def __init__(self):
        self.issues: List[ReviewIssue] = []
    
    def visit_FunctionDef(self, node):
        """访问函数定义"""
        if len(node.body) > 50:
            self.issues.append(ReviewIssue(
                severity=ReviewSeverity.WARNING,
                category=ReviewCategory.BEST_PRACTICES,
                title=f"函数过长: {node.name}",
                description=f"函数有{len(node.body)}行，建议拆分为小函数",
                line_number=node.lineno,
                atom_level=AtomLevel.METHOD
            ))
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """访问类定义"""
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        if method_count > 20:
            self.issues.append(ReviewIssue(
                severity=ReviewSeverity.WARNING,
                category=ReviewCategory.STRUCTURE,
                title=f"类方法过多: {node.name}",
                description=f"类有{method_count}个方法，考虑拆分",
                line_number=node.lineno,
                atom_level=AtomLevel.CLASS
            ))
        
        self.generic_visit(node)


class ReviewAgent:
    """评审Agent"""
    
    def __init__(self, config: ReviewConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.code_analyzer = CodeAnalyzer()
        self.reports: List[ReviewReport] = []
    
    def review_code(self, content: str, file_path: str = "") -> ReviewReport:
        """评审代码"""
        report = ReviewReport(
            reviewed_files=[file_path] if file_path else []
        )
        
        issues = self.code_analyzer.analyze_content(content, file_path)
        report.issues = issues
        
        if self.config.enable_atom_verification:
            report.atom_verifications = self.code_analyzer.verify_atoms(content, self.config)
            for verification in report.atom_verifications:
                report.issues.extend(verification.issues)
        
        report.total_issues = len(report.issues)
        report.critical_count = sum(1 for i in report.issues if i.severity == ReviewSeverity.CRITICAL)
        report.error_count = sum(1 for i in report.issues if i.severity == ReviewSeverity.ERROR)
        report.warning_count = sum(1 for i in report.issues if i.severity == ReviewSeverity.WARNING)
        report.info_count = sum(1 for i in report.issues if i.severity == ReviewSeverity.INFO)
        
        self.reports.append(report)
        
        return report
    
    def generate_report_text(self, report: ReviewReport) -> str:
        """生成评审报告文本"""
        lines = []
        
        lines.append("=" * 80)
        lines.append("代码评审报告")
        lines.append("=" * 80)
        lines.append(f"生成时间: {report.created_at.isoformat()}")
        lines.append(f"评审文件: {', '.join(report.reviewed_files)}")
        lines.append(f"总问题数: {report.total_issues}")
        lines.append(f"严重: {report.critical_count}")
        lines.append(f"错误: {report.error_count}")
        lines.append(f"警告: {report.warning_count}")
        lines.append(f"信息: {report.info_count}")
        lines.append("")
        
        lines.append("问题详情:")
        for issue in sorted(report.issues, key=lambda x: (x.severity, x.line_number or 0)):
            severity_str = f"[{issue.severity.upper()}]"
            location_str = f"行 {issue.line_number}" if issue.line_number else ""
            lines.append(f"\n{severity_str} {issue.category} - {issue.title}")
            if issue.description:
                lines.append(f"  描述: {issue.description}")
            if location_str:
                lines.append(f"  位置: {location_str}")
            if issue.suggested_fix:
                lines.append(f"  建议: {issue.suggested_fix}")
        
        lines.append("\n" + "=" * 80)
        lines.append("四级原子验证:")
        lines.append("=" * 80)
        
        level_groups: Dict[AtomLevel, List[AtomVerification]] = {}
        for verification in report.atom_verifications:
            if verification.atom_level not in level_groups:
                level_groups[verification.atom_level] = []
            level_groups[verification.atom_level].append(verification)
        
        for level, verifications in level_groups.items():
            valid_count = sum(1 for v in verifications if v.is_valid)
            lines.append(f"\n{level.value.upper()} 层: {valid_count}/{len(verifications)} 有效")
        
        lines.append("\n" + "=" * 80)
        
        return "\n".join(lines)


_global_review_agent: Optional[ReviewAgent] = None


def get_review_agent(config: Optional[ReviewConfig] = None) -> ReviewAgent:
    """获取全局评审Agent"""
    global _global_review_agent
    if _global_review_agent is None:
        if config is None:
            config = ReviewConfig(name="ReviewAgent")
        _global_review_agent = ReviewAgent(config)
    return _global_review_agent


def reset_review_agent() -> None:
    """重置评审Agent"""
    global _global_review_agent
    _global_review_agent = None
