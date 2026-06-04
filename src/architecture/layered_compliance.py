"""
模块分层合规校验模块

职责：定义层级结构，校验层级依赖，生成合规报告，提供修复建议

基于第一性原理：简单、单一、可追溯、可组合
"""

from __future__ import annotations

import ast
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class LayerType(str, Enum):
    """层级类型"""
    INPUT = "input_layer"  # 输入收敛层
    BUSINESS = "business_layer"  # 业务逻辑层
    DATA = "data_layer"  # 数据访问层
    UTILITY = "utility_layer"  # 工具层
    INFRA = "infra_layer"  # 基础设施层


@dataclass
class LayerDefinition:
    """层级定义"""
    layer_type: LayerType
    layer_name: str
    layer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    allowed_dependencies: List[LayerType] = field(default_factory=list)
    forbidden_dependencies: List[LayerType] = field(default_factory=list)
    directory_patterns: List[str] = field(default_factory=list)


@dataclass
class Violation:
    """违规记录"""
    violation_type: str
    layer_from: Optional[LayerType]
    layer_to: Optional[LayerType]
    module_from: str
    module_to: str
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    line_number: int = 0
    file_path: str = ""
    severity: str = "medium"
    description: str = ""


@dataclass
class FixSuggestion:
    """修复建议"""
    target_module: str
    suggestion_type: str
    description: str
    suggestion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: int = 2
    before_code: str = ""
    after_code: str = ""


@dataclass
class ComplianceReport:
    """合规报告"""
    total_modules: int = 0
    compliant_modules: int = 0
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=datetime.now)
    violations: List[Violation] = field(default_factory=list)
    suggestions: List[FixSuggestion] = field(default_factory=list)


class LayeredArchitecture:
    """分层架构定义"""
    
    def __init__(self):
        self.layers: List[LayerDefinition] = []
        self._initialize_default_layers()
    
    def _initialize_default_layers(self):
        """初始化默认的分层架构"""
        # 输入层 - UI、API接口
        input_layer = LayerDefinition(
            layer_type=LayerType.INPUT,
            layer_name="输入收敛层",
            description="负责用户输入和外部接口",
            allowed_dependencies=[LayerType.BUSINESS, LayerType.UTILITY, LayerType.INFRA],
            directory_patterns=["controllers", "api", "handlers", "views"]
        )
        
        # 业务逻辑层
        business_layer = LayerDefinition(
            layer_type=LayerType.BUSINESS,
            layer_name="业务逻辑层",
            description="核心业务逻辑和服务",
            allowed_dependencies=[LayerType.DATA, LayerType.UTILITY, LayerType.INFRA],
            directory_patterns=["services", "business", "use_cases"]
        )
        
        # 数据访问层
        data_layer = LayerDefinition(
            layer_type=LayerType.DATA,
            layer_name="数据访问层",
            description="数据库访问、缓存、文件系统等",
            allowed_dependencies=[LayerType.UTILITY, LayerType.INFRA],
            directory_patterns=["repositories", "models", "dao", "database"]
        )
        
        # 工具层
        utility_layer = LayerDefinition(
            layer_type=LayerType.UTILITY,
            layer_name="工具层",
            description="通用工具、帮助类、配置等",
            allowed_dependencies=[LayerType.INFRA],
            directory_patterns=["utils", "helpers", "common", "config"]
        )
        
        # 基础设施层
        infra_layer = LayerDefinition(
            layer_type=LayerType.INFRA,
            layer_name="基础设施层",
            description="底层基础设施，无依赖",
            allowed_dependencies=[],
            directory_patterns=["infra", "core", "foundation"]
        )
        
        self.layers.extend([input_layer, business_layer, data_layer, utility_layer, infra_layer])
    
    def get_layer_by_module(self, module_name: str) -> Optional[LayerDefinition]:
        """根据模块名确定其所属层级"""
        for layer in self.layers:
            for pattern in layer.directory_patterns:
                if pattern in module_name.lower():
                    return layer
        return None
    
    def get_layer_by_type(self, layer_type: LayerType) -> Optional[LayerDefinition]:
        """根据层级类型获取层级定义"""
        for layer in self.layers:
            if layer.layer_type == layer_type:
                return layer
        return None
    
    def is_dependency_allowed(self, from_layer: LayerType, to_layer: LayerType) -> bool:
        """检查依赖是否允许"""
        from_layer_def = self.get_layer_by_type(from_layer)
        if not from_layer_def:
            return False
        
        if to_layer in from_layer_def.allowed_dependencies:
            return True
        
        # 检查层级顺序，上层依赖下层通常允许
        layer_order = [
            LayerType.INPUT,
            LayerType.BUSINESS,
            LayerType.DATA,
            LayerType.UTILITY,
            LayerType.INFRA
        ]
        
        if layer_order.index(from_layer) < layer_order.index(to_layer):
            return True
        
        return False


class LayeredArchitectureValidator:
    """分层架构合规校验器"""
    
    def __init__(self, architecture: LayeredArchitecture):
        self.architecture = architecture
        self.violations: List[Violation] = []
        self.suggestions: List[FixSuggestion] = []
    
    def validate_file(self, file_path: str) -> List[Violation]:
        """校验单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            return self.validate_source(source_code, file_path)
        except Exception:
            return []
    
    def validate_source(self, source_code: str, file_path: str) -> List[Violation]:
        """校验源代码"""
        violations: List[Violation] = []
        
        try:
            tree = ast.parse(source_code)
            
            module_name = Path(file_path).stem
            from_layer = self.architecture.get_layer_by_module(module_name)
            
            # 分析导入语句
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep_module = alias.name.split('.')[0]
                        to_layer = self.architecture.get_layer_by_module(dep_module)
                        
                        if from_layer and to_layer:
                            if not self.architecture.is_dependency_allowed(from_layer.layer_type, to_layer.layer_type):
                                violation = Violation(
                                    violation_type="invalid_dependency",
                                    layer_from=from_layer.layer_type,
                                    layer_to=to_layer.layer_type,
                                    module_from=module_name,
                                    module_to=dep_module,
                                    line_number=node.lineno,
                                    file_path=file_path,
                                    severity="medium",
                                    description=f"{from_layer.layer_name} 不能依赖 {to_layer.layer_name}"
                                )
                                violations.append(violation)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dep_module = node.module.split('.')[0]
                        to_layer = self.architecture.get_layer_by_module(dep_module)
                        
                        if from_layer and to_layer:
                            if not self.architecture.is_dependency_allowed(from_layer.layer_type, to_layer.layer_type):
                                violation = Violation(
                                    violation_type="invalid_dependency",
                                    layer_from=from_layer.layer_type,
                                    layer_to=to_layer.layer_type,
                                    module_from=module_name,
                                    module_to=dep_module,
                                    line_number=node.lineno,
                                    file_path=file_path,
                                    severity="medium",
                                    description=f"{from_layer.layer_name} 不能依赖 {to_layer.layer_name}"
                                )
                                violations.append(violation)
        
        except Exception:
            pass
        
        self.violations.extend(violations)
        return violations
    
    def validate_directory(self, directory: str) -> ComplianceReport:
        """校验整个目录"""
        self.violations.clear()
        self.suggestions.clear()
        
        dir_path = Path(directory)
        total_files = 0
        files_without_violations = 0
        
        for py_file in dir_path.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
            
            total_files += 1
            file_violations = self.validate_file(str(py_file))
            
            if not file_violations:
                files_without_violations += 1
        
        # 生成修复建议
        self._generate_suggestions()
        
        return ComplianceReport(
            total_modules=total_files,
            compliant_modules=files_without_violations,
            violations=self.violations.copy(),
            suggestions=self.suggestions.copy()
        )
    
    def _generate_suggestions(self):
        """生成修复建议"""
        for violation in self.violations:
            suggestion = FixSuggestion(
                target_module=violation.module_from,
                suggestion_type="dependency_fix",
                description=f"建议重构 {violation.module_from} 对 {violation.module_to} 的依赖",
                priority=2
            )
            self.suggestions.append(suggestion)


class ComplianceReporter:
    """合规报告生成器"""
    
    def generate_text_report(self, report: ComplianceReport) -> str:
        """生成文本报告"""
        lines: List[str] = []
        lines.append("=" * 80)
        lines.append("模块分层合规校验报告")
        lines.append("=" * 80)
        lines.append(f"生成时间: {report.generated_at.isoformat()}")
        lines.append(f"总模块数: {report.total_modules}")
        lines.append(f"合规模块数: {report.compliant_modules}")
        lines.append(f"违规数: {len(report.violations)}")
        lines.append("")
        
        if report.violations:
            lines.append("--- 违规详情 ---")
            for i, violation in enumerate(report.violations, 1):
                lines.append(f"违规 {i}:")
                lines.append(f"  类型: {violation.violation_type}")
                lines.append(f"  从 {violation.module_from} ({violation.layer_from})")
                lines.append(f"  到 {violation.module_to} ({violation.layer_to})")
                lines.append(f"  文件: {violation.file_path}:{violation.line_number}")
                lines.append(f"  描述: {violation.description}")
                lines.append("")
        
        if report.suggestions:
            lines.append("--- 修复建议 ---")
            for i, suggestion in enumerate(report.suggestions, 1):
                lines.append(f"建议 {i}:")
                lines.append(f"  模块: {suggestion.target_module}")
                lines.append(f"  类型: {suggestion.suggestion_type}")
                lines.append(f"  描述: {suggestion.description}")
                lines.append("")
        
        return "\n".join(lines)
    
    def generate_json_report(self, report: ComplianceReport) -> Dict[str, Any]:
        """生成 JSON 报告"""
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "total_modules": report.total_modules,
            "compliant_modules": report.compliant_modules,
            "compliance_rate": report.compliant_modules / max(report.total_modules, 1),
            "violations": [
                {
                    "violation_id": v.violation_id,
                    "violation_type": v.violation_type,
                    "layer_from": v.layer_from.value if v.layer_from else None,
                    "layer_to": v.layer_to.value if v.layer_to else None,
                    "module_from": v.module_from,
                    "module_to": v.module_to,
                    "severity": v.severity,
                    "file_path": v.file_path,
                    "line_number": v.line_number
                }
                for v in report.violations
            ],
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "target_module": s.target_module,
                    "suggestion_type": s.suggestion_type,
                    "description": s.description
                }
                for s in report.suggestions
            ]
        }


class LayeredArchitectureAnalyzer:
    """分层架构分析引擎"""
    
    def __init__(self):
        self.architecture = LayeredArchitecture()
        self.validator = LayeredArchitectureValidator(self.architecture)
        self.reporter = ComplianceReporter()
    
    def analyze_directory(self, directory: str) -> ComplianceReport:
        """分析目录的分层合规性"""
        return self.validator.validate_directory(directory)


_global_analyzer: Optional[LayeredArchitectureAnalyzer] = None


def get_layered_architecture_analyzer() -> LayeredArchitectureAnalyzer:
    """获取全局分层架构分析器"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = LayeredArchitectureAnalyzer()
    return _global_analyzer


def reset_layered_architecture_analyzer() -> None:
    """重置分层架构分析器"""
    global _global_analyzer
    _global_analyzer = None
