"""
类单一能力校验、解耦重构模块

职责：评估类的耦合度和内聚度，检测违规并提供解耦建议和执行方案

基于第一性原理：简单、单一、可追溯、可组合
"""

from __future__ import annotations

import ast
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class IssueType(str, Enum):
    """违规类型"""
    TOO_MANY_METHODS = "too_many_methods"
    TOO_MANY_FIELDS = "too_many_fields"
    HIGH_COUPLING = "high_coupling"
    LOW_COHESION = "low_cohesion"
    GOD_CLASS = "god_class"
    DATA_CLUMP = "data_clump"
    FEATURE_ENVY = "feature_envy"


class IssueSeverity(str, Enum):
    """违规严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CohesionMetric:
    """内聚度度量"""
    type: str = "cohesion"
    value: float = 0.0
    interpretation: str = "unknown"
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CouplingMetric:
    """耦合度度量"""
    type: str = "coupling"
    afferent_coupling: int = 0
    efferent_coupling: int = 0
    instability: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ClassViolation:
    """类违规"""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    issue_type: IssueType = IssueType.LOW_COHESION
    severity: IssueSeverity = IssueSeverity.WARNING
    description: str = ""
    location: str = ""
    line_number: int = 0
    impact: str = ""
    suggestion: str = ""


@dataclass
class RefactoringSuggestion:
    """重构建议"""
    suggestion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    description: str = ""
    priority: int = 0
    estimated_effort: str = ""
    affected_components: List[str] = field(default_factory=list)
    before_example: str = ""
    after_example: str = ""


@dataclass
class RefactoringAction:
    """重构动作"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    description: str = ""
    status: str = "pending"
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ClassAnalysisResult:
    """类分析结果"""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    class_name: str = ""
    cohesion: CohesionMetric = field(default_factory=CohesionMetric)
    coupling: CouplingMetric = field(default_factory=CouplingMetric)
    violations: List[ClassViolation] = field(default_factory=list)
    suggestions: List[RefactoringSuggestion] = field(default_factory=list)
    analysis_date: datetime = field(default_factory=datetime.now)
    is_valid: bool = True


class CohesionAnalyzer:
    """内聚度分析器"""
    
    DEFAULT_THRESHOLDS = {
        "LCOM4_high": 0.8,
        "LCOM4_medium": 0.6,
        "method_count_high": 20,
        "field_count_high": 15,
    }
    
    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
    
    def analyze(self, class_node: ast.ClassDef) -> CohesionMetric:
        """分析类的内聚度"""
        metric = CohesionMetric()
        
        # 计算方法和字段数量
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        fields = self._extract_fields(class_node)
        
        metric.value = self._calculate_lcom4(methods, fields)
        metric.interpretation = self._interpret_cohesion(metric.value)
        
        # 检查问题
        if len(methods) > self.thresholds["method_count_high"]:
            metric.issues.append(f"类有 {len(methods)} 个方法，可能职责过多")
        
        if len(fields) > self.thresholds["field_count_high"]:
            metric.issues.append(f"类有 {len(fields)} 个字段，可能数据过多")
        
        # 添加建议
        if metric.value < 0.3:
            metric.recommendations.append("内聚度较高，保持当前架构")
        elif metric.value < 0.6:
            metric.recommendations.append("内聚度适中，可考虑轻微拆分")
        else:
            metric.recommendations.append("内聚度较低，建议拆分为多个单一职责类")
        
        return metric
    
    def _extract_fields(self, class_node: ast.ClassDef) -> Set[str]:
        """提取类的字段"""
        fields = set()
        
        # 检查类级别的字段
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        fields.add(target.id)
        
        # 检查实例字段
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if (isinstance(target, ast.Attribute) and 
                                isinstance(target.value, ast.Name) and 
                                target.value.id == 'self'):
                                fields.add(target.attr)
        
        return fields
    
    def _calculate_lcom4(self, methods: List[ast.FunctionDef], fields: Set[str]) -> float:
        """计算 LCOM4 内聚度指标"""
        if not methods or not fields:
            return 0.0
        
        # 方法使用字段的图
        method_field_map = {}
        for method in methods:
            used_fields = self._find_fields_used(method, fields)
            method_field_map[method.name] = used_fields
        
        # 计算相关的方法组数量
        method_groups = self._find_method_groups(method_field_map)
        total_methods = len(methods)
        
        if total_methods <= 1:
            return 0.0
        
        # LCOM4 = 分组数量 - 1，如果所有方法都相关，则 LCOM4 = 0
        return (len(method_groups) - 1) / max(1, total_methods - 1)
    
    def _find_fields_used(self, method: ast.FunctionDef, fields: Set[str]) -> Set[str]:
        """找到方法使用的字段"""
        used = set()
        
        for node in ast.walk(method):
            if (isinstance(node, ast.Attribute) and 
                isinstance(node.value, ast.Name) and 
                node.value.id == 'self' and 
                node.attr in fields):
                used.add(node.attr)
        
        return used
    
    def _find_method_groups(self, method_field_map: Dict[str, Set[str]]) -> List[Set[str]]:
        """找到通过字段关联的方法组"""
        if not method_field_map:
            return []
        
        # 使用并查集算法
        parent = {name: name for name in method_field_map}
        
        def find(u):
            while parent[u] != u:
                parent[u] = parent[parent[u]]
                u = parent[u]
            return u
        
        def union(u, v):
            u_root = find(u)
            v_root = find(v)
            if u_root != v_root:
                parent[v_root] = u_root
        
        # 构建共享字段的方法关系
        for name1, fields1 in method_field_map.items():
            for name2, fields2 in method_field_map.items():
                if name1 != name2 and fields1 & fields2:
                    union(name1, name2)
        
        # 收集分组
        groups = {}
        for name in method_field_map:
            root = find(name)
            if root not in groups:
                groups[root] = set()
            groups[root].add(name)
        
        return list(groups.values())
    
    def _interpret_cohesion(self, value: float) -> str:
        """解释内聚度值"""
        if value < 0.3:
            return "高内聚"
        elif value < 0.6:
            return "中内聚"
        else:
            return "低内聚"


class CouplingAnalyzer:
    """耦合度分析器"""
    
    def analyze(self, class_node: ast.ClassDef, all_classes: Optional[List[str]] = None) -> CouplingMetric:
        """分析类的耦合度"""
        metric = CouplingMetric()
        
        # 简单计算导入关系作为初步耦合度量
        imports = self._extract_imports(class_node)
        metric.efferent_coupling = len(imports)
        
        metric.issues = []
        if metric.efferent_coupling > 5:
            metric.issues.append(f"类依赖了 {metric.efferent_coupling} 个模块，耦合度可能过高")
        
        # 计算不稳定性
        total_coupling = metric.afferent_coupling + metric.efferent_coupling
        if total_coupling > 0:
            metric.instability = metric.efferent_coupling / total_coupling
        
        if metric.instability > 0.8:
            metric.recommendations.append("类稳定性较低，建议减少依赖或增加职责")
        elif metric.instability < 0.2:
            metric.recommendations.append("类稳定性较高，适合作为基础组件")
        
        return metric
    
    def _extract_imports(self, class_node: ast.ClassDef) -> Set[str]:
        """提取类中的导入"""
        imports = set()
        
        # 查找所有 Name 节点作为可能的依赖
        for node in ast.walk(class_node):
            if isinstance(node, ast.Name):
                if node.id[0].isupper():  # 可能是类名
                    imports.add(node.id)
        
        return imports


class ViolationDetector:
    """违规检测器"""
    
    DEFAULT_RULES = {
        "max_methods": 20,
        "max_fields": 15,
        "min_cohesion": 0.3,
    }
    
    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        self.rules = rules or self.DEFAULT_RULES
    
    def detect(self, class_node: ast.ClassDef, cohesion: CohesionMetric, 
              coupling: CouplingMetric) -> List[ClassViolation]:
        """检测违规"""
        violations = []
        
        # 检查方法数量
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > self.rules["max_methods"]:
            violations.append(ClassViolation(
                issue_type=IssueType.TOO_MANY_METHODS,
                severity=IssueSeverity.WARNING,
                description=f"类有 {len(methods)} 个方法，超过建议限制",
                location=class_node.name,
                line_number=class_node.lineno if hasattr(class_node, 'lineno') else 0,
                impact="可能导致类职责过多，难以维护",
                suggestion="考虑拆分为多个类"
            ))
        
        # 检查内聚度
        if cohesion.value > self.rules["min_cohesion"]:
            violations.append(ClassViolation(
                issue_type=IssueType.LOW_COHESION,
                severity=IssueSeverity.ERROR,
                description=f"类内聚度 {cohesion.value:.2f} 较低",
                location=class_node.name,
                line_number=class_node.lineno if hasattr(class_node, 'lineno') else 0,
                impact="类可能承担了过多职责",
                suggestion="按职责拆分为多个类"
            ))
        
        # 检查耦合度
        if coupling.efferent_coupling > 5:
            violations.append(ClassViolation(
                issue_type=IssueType.HIGH_COUPLING,
                severity=IssueSeverity.WARNING,
                description=f"类依赖了 {coupling.efferent_coupling} 个模块",
                location=class_node.name,
                line_number=class_node.lineno if hasattr(class_node, 'lineno') else 0,
                impact="依赖过多，模块变化会影响该类",
                suggestion="考虑减少依赖或使用依赖注入"
            ))
        
        return violations


class SuggestionGenerator:
    """建议生成器"""
    
    def generate(self, violations: List[ClassViolation]) -> List[RefactoringSuggestion]:
        """生成重构建议"""
        suggestions = []
        
        for violation in violations:
            if violation.issue_type == IssueType.TOO_MANY_METHODS:
                suggestions.append(RefactoringSuggestion(
                    type="extract_class",
                    description=f"从 {violation.location} 中提取类",
                    priority=2,
                    estimated_effort="medium",
                    affected_components=[violation.location],
                    before_example="class LargeClass(...)",
                    after_example="class SmallerClass(...)"
                ))
            elif violation.issue_type == IssueType.LOW_COHESION:
                suggestions.append(RefactoringSuggestion(
                    type="split_class",
                    description=f"按职责拆分 {violation.location}",
                    priority=1,
                    estimated_effort="high",
                    affected_components=[violation.location],
                    before_example="class MixedClass(...)",
                    after_example="class ResponsibilityA(...) class ResponsibilityB(...)"
                ))
            elif violation.issue_type == IssueType.HIGH_COUPLING:
                suggestions.append(RefactoringSuggestion(
                    type="reduce_dependencies",
                    description=f"减少 {violation.location} 的依赖",
                    priority=3,
                    estimated_effort="medium",
                    affected_components=[violation.location],
                    before_example="import many_modules",
                    after_example="import fewer_modules"
                ))
        
        return suggestions


class DecouplingExecutor:
    """解耦执行器"""
    
    def __init__(self):
        self.actions: List[RefactoringAction] = []
    
    def execute(self, suggestion: RefactoringSuggestion) -> RefactoringAction:
        """执行重构建议（模拟）"""
        action = RefactoringAction(
            type=suggestion.type,
            description=suggestion.description,
            status="completed"
        )
        self.actions.append(action)
        return action
    
    def batch_execute(self, suggestions: List[RefactoringSuggestion]) -> List[RefactoringAction]:
        """批量执行重构建议"""
        return [self.execute(suggestion) for suggestion in suggestions]


class ClassDecouplingAnalyzer:
    """类解耦分析器"""
    
    def __init__(self):
        self.cohesion_analyzer = CohesionAnalyzer()
        self.coupling_analyzer = CouplingAnalyzer()
        self.violation_detector = ViolationDetector()
        self.suggestion_generator = SuggestionGenerator()
        self.executor = DecouplingExecutor()
    
    def analyze(self, class_code: str) -> ClassAnalysisResult:
        """完整分析类"""
        result = ClassAnalysisResult()
        
        try:
            tree = ast.parse(class_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result.class_name = node.name
                    result.cohesion = self.cohesion_analyzer.analyze(node)
                    result.coupling = self.coupling_analyzer.analyze(node)
                    result.violations = self.violation_detector.detect(
                        node, result.cohesion, result.coupling
                    )
                    result.suggestions = self.suggestion_generator.generate(result.violations)
                    break
        except Exception as e:
            result.is_valid = False
            print(f"Error analyzing class: {e}")
        
        return result
    
    def refactor(self, analysis_result: ClassAnalysisResult, original_code: str) -> Tuple[str, List[RefactoringAction]]:
        """执行重构（模拟）"""
        actions = self.executor.batch_execute(analysis_result.suggestions)
        return original_code, actions


_global_analyzer: Optional[ClassDecouplingAnalyzer] = None


def get_class_decoupling_analyzer() -> ClassDecouplingAnalyzer:
    """获取全局类解耦分析器"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = ClassDecouplingAnalyzer()
    return _global_analyzer


def reset_class_decoupling_analyzer() -> None:
    """重置类解耦分析器"""
    global _global_analyzer
    _global_analyzer = None
