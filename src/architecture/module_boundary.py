"""
模块边界识别模块

职责：识别和分析模块的边界，包括目录边界、语义边界、公共接口等

基于第一性原理：简单、单一、可追溯、可组合
"""

from __future__ import annotations

import ast
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class InterfaceType(str, Enum):
    """接口类型"""
    PUBLIC = "public"       # 公共接口
    PRIVATE = "private"     # 私有接口
    PROTECTED = "protected" # 受保护接口
    MAGIC = "magic"        # 魔术接口


class BoundaryType(str, Enum):
    """边界类型"""
    DIRECTORY = "directory"  # 目录边界
    SEMANTIC = "semantic"     # 语义边界


class ModuleInterface:
    """模块接口"""
    def __init__(
        self,
        name: str,
        interface_type: InterfaceType,
        location: str,
        is_exported: bool = False
    ):
        self.name = name
        self.interface_type = interface_type
        self.location = location
        self.is_exported = is_exported


class ModuleBoundary:
    """模块边界"""
    def __init__(
        self,
        boundary_id: str,
        module_name: str,
        boundary_type: BoundaryType,
        path: str,
        interfaces: List[ModuleInterface],
        dependencies: List[str]
    ):
        self.boundary_id = boundary_id
        self.module_name = module_name
        self.boundary_type = boundary_type
        self.path = path
        self.interfaces = interfaces
        self.dependencies = dependencies


@dataclass
class ModuleInfo:
    """模块信息"""
    module_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    module_name: str = ""
    module_path: str = ""
    module_type: str = "directory"
    is_package: bool = False
    __all__: List[str] = field(default_factory=list)
    public_classes: List[str] = field(default_factory=list)
    public_functions: List[str] = field(default_factory=list)
    public_constants: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)


@dataclass
class BoundaryReport:
    """边界报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=datetime.now)
    module_info: Optional[ModuleInfo] = None
    boundaries: List[ModuleBoundary] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    
    def to_text(self) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("MODULE BOUNDARY ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {self.generated_at.isoformat()}")
        
        if self.module_info:
            lines.append(f"\nModule: {self.module_info.module_name}")
            lines.append(f"Path: {self.module_info.module_path}")
            lines.append(f"Type: {self.module_info.module_type}")
            lines.append(f"Is Package: {self.module_info.is_package}")
            
            lines.append("\n--- Public Interface ---")
            lines.append(f"Classes: {', '.join(self.module_info.public_classes) or 'None'}")
            lines.append(f"Functions: {', '.join(self.module_info.public_functions) or 'None'}")
            lines.append(f"Constants: {', '.join(self.module_info.public_constants) or 'None'}")
            
            lines.append("\n--- Dependencies ---")
            lines.append(f"Depends on: {', '.join(self.module_info.dependencies) or 'None'}")
            lines.append(f"Depended by: {', '.join(self.module_info.dependents) or 'None'}")
        
        if self.issues:
            lines.append("\n--- Issues ---")
            for issue in self.issues:
                lines.append(f"  - {issue}")
        
        return "\n".join(lines)


class DirectoryBoundaryDetector:
    """目录边界检测器"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
    
    def detect_boundaries(self) -> List[ModuleBoundary]:
        """检测所有模块边界"""
        boundaries = []
        
        for py_file in self.root_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                module_name = self._get_module_name(py_file.parent)
                boundary = self._create_boundary_from_dir(py_file.parent, module_name)
                if boundary:
                    boundaries.append(boundary)
        
        return boundaries
    
    def _get_module_name(self, path: Path) -> str:
        """获取模块名称"""
        try:
            relative = path.relative_to(self.root_path)
            return ".".join(relative.parts)
        except ValueError:
            return path.name
    
    def _create_boundary_from_dir(self, dir_path: Path, module_name: str) -> Optional[ModuleBoundary]:
        """从目录创建边界"""
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            return None
        
        # 读取 __all__ 列表
        __all__ = self._read_all(init_file)
        
        # 分析模块接口
        interfaces = self._extract_interfaces(dir_path, __all__)
        
        # 检测依赖
        dependencies = self._extract_dependencies(dir_path)
        
        return ModuleBoundary(
            boundary_id=str(uuid.uuid4()),
            module_name=module_name,
            boundary_type=BoundaryType.DIRECTORY,
            path=str(dir_path),
            interfaces=interfaces,
            dependencies=dependencies
        )
    
    def _read_all(self, init_file: Path) -> List[str]:
        """读取 __all__ 列表"""
        try:
            with open(init_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "__all__":
                            if isinstance(node.value, (ast.List, ast.Tuple)):
                                return [
                                    ast.literal_eval(elt) if isinstance(elt, (ast.Str, ast.Constant))
                                    else str(elt)
                                    for elt in node.value.elts
                                ]
            return []
        except Exception:
            return []
    
    def _extract_interfaces(self, dir_path: Path, __all__: List[str]) -> List[ModuleInterface]:
        """提取模块接口"""
        interfaces = []
        
        # 分析 __init__.py 中的导出
        init_file = dir_path / "__init__.py"
        if init_file.exists():
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            if __all__ and alias.name in __all__:
                                interface = ModuleInterface(
                                    name=alias.name,
                                    interface_type=InterfaceType.PUBLIC,
                                    location=str(init_file),
                                    is_exported=True
                                )
                                interfaces.append(interface)
            except Exception:
                pass
        
        return interfaces
    
    def _extract_dependencies(self, dir_path: Path) -> List[str]:
        """提取模块依赖"""
        dependencies = []
        
        for py_file in dir_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            dep = alias.name.split('.')[0]
                            if dep not in dependencies and not dep.startswith('_'):
                                dependencies.append(dep)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dep = node.module.split('.')[0]
                            if dep not in dependencies and not dep.startswith('_'):
                                dependencies.append(dep)
            except Exception:
                pass
        
        return dependencies


class SemanticBoundaryDetector:
    """语义边界检测器"""
    
    def __init__(self):
        self.module_patterns = [
            r'^controllers?/',
            r'^services?/',
            r'^models?/',
            r'^views?/',
            r'^utils?/',
            r'^helpers?/',
            r'^managers?/',
            r'^handlers?/',
        ]
    
    def detect_boundaries(self, source_code: str, module_name: str) -> ModuleBoundary:
        """检测语义边界"""
        interfaces = self._extract_public_api(source_code)
        dependencies = self._extract_dependencies(source_code)
        
        return ModuleBoundary(
            boundary_id=str(uuid.uuid4()),
            module_name=module_name,
            boundary_type=BoundaryType.SEMANTIC,
            path=f"semantic:{module_name}",
            interfaces=interfaces,
            dependencies=dependencies
        )
    
    def _extract_public_api(self, source_code: str) -> List[ModuleInterface]:
        """提取公共 API"""
        interfaces = []
        
        try:
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                # 公共类
                if isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):
                        interface = ModuleInterface(
                            name=node.name,
                            interface_type=InterfaceType.PUBLIC,
                            location=f"line {node.lineno}"
                        )
                        interfaces.append(interface)
                
                # 公共函数
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith('_'):
                        interface = ModuleInterface(
                            name=node.name,
                            interface_type=InterfaceType.PUBLIC,
                            location=f"line {node.lineno}"
                        )
                        interfaces.append(interface)
                
                # 魔术方法
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith('__') and node.name.endswith('__'):
                        interface = ModuleInterface(
                            name=node.name,
                            interface_type=InterfaceType.MAGIC,
                            location=f"line {node.lineno}"
                        )
                        interfaces.append(interface)
        except Exception:
            pass
        
        return interfaces
    
    def _extract_dependencies(self, source_code: str) -> List[str]:
        """提取依赖"""
        dependencies = []
        
        try:
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep = alias.name.split('.')[0]
                        if dep not in dependencies and not dep.startswith('_'):
                            dependencies.append(dep)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dep = node.module.split('.')[0]
                        if dep not in dependencies and not dep.startswith('_'):
                            dependencies.append(dep)
        except Exception:
            pass
        
        return dependencies


class InterfaceRecognizer:
    """接口识别器"""
    
    def __init__(self):
        self.public_pattern = r'^[A-Z][a-zA-Z0-9]*$'
        self.private_pattern = r'^_[A-Z]?.*'
        self.protected_pattern = r'^_[a-z].*'
        self.magic_pattern = r'^__.*__$'
    
    def recognize(self, name: str) -> InterfaceType:
        """识别接口类型"""
        if re.match(self.magic_pattern, name):
            return InterfaceType.MAGIC
        elif re.match(self.public_pattern, name):
            return InterfaceType.PUBLIC
        elif re.match(self.protected_pattern, name):
            return InterfaceType.PROTECTED
        else:
            return InterfaceType.PRIVATE
    
    def is_public(self, name: str) -> bool:
        """判断是否为公共接口"""
        return self.recognize(name) == InterfaceType.PUBLIC


class BoundaryValidator:
    """边界验证器"""
    
    def __init__(self):
        self.max_public_interfaces = 20
        self.max_dependencies = 10
    
    def validate_boundary(self, boundary: ModuleBoundary) -> Tuple[bool, List[str]]:
        """验证边界"""
        issues = []
        
        # 检查公共接口数量
        public_count = sum(1 for i in boundary.interfaces if i.interface_type == InterfaceType.PUBLIC)
        if public_count > self.max_public_interfaces:
            issues.append(f"模块 {boundary.module_name} 有 {public_count} 个公共接口，超过建议限制 {self.max_public_interfaces}")
        
        # 检查依赖数量
        if len(boundary.dependencies) > self.max_dependencies:
            issues.append(f"模块 {boundary.module_name} 有 {len(boundary.dependencies)} 个依赖，超过建议限制 {self.max_dependencies}")
        
        # 检查循环依赖（如果提供了完整信息）
        # 这里简化处理，实际应该检查完整的依赖图
        
        return len(issues) == 0, issues


class BoundaryReporter:
    """边界报告生成器"""
    
    def generate_text_report(self, report: BoundaryReport) -> str:
        """生成文本报告"""
        return report.to_text()
    
    def generate_json_report(self, report: BoundaryReport) -> Dict[str, Any]:
        """生成 JSON 报告"""
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "module_info": {
                "module_name": report.module_info.module_name if report.module_info else None,
                "module_path": report.module_info.module_path if report.module_info else None,
                "public_classes": report.module_info.public_classes if report.module_info else [],
                "public_functions": report.module_info.public_functions if report.module_info else [],
                "dependencies": report.module_info.dependencies if report.module_info else [],
            },
            "boundaries": [
                {
                    "boundary_id": b.boundary_id,
                    "module_name": b.module_name,
                    "boundary_type": b.boundary_type.value,
                    "path": b.path,
                    "interfaces": [{"name": i.name, "type": i.interface_type.value} for i in b.interfaces],
                    "dependencies": b.dependencies
                }
                for b in report.boundaries
            ],
            "issues": report.issues,
            "validation_results": report.validation_results
        }


class ModuleBoundaryAnalyzer:
    """模块边界分析器"""
    
    def __init__(self, root_path: str = ""):
        self.root_path = root_path
        self.directory_detector = DirectoryBoundaryDetector(root_path) if root_path else None
        self.semantic_detector = SemanticBoundaryDetector()
        self.interface_recognizer = InterfaceRecognizer()
        self.validator = BoundaryValidator()
        self.reporter = BoundaryReporter()
    
    def analyze_module(self, module_path: str, module_name: str = "") -> BoundaryReport:
        """分析模块"""
        report = BoundaryReport()
        
        # 如果有目录路径，使用目录检测
        if self.directory_detector and os.path.isdir(module_path):
            boundaries = self.directory_detector.detect_boundaries()
            report.boundaries.extend(boundaries)
            
            if boundaries:
                # 获取第一个匹配的模块信息
                boundary = boundaries[0]
                report.module_info = self._extract_module_info(boundary)
        
        # 否则使用语义检测
        elif os.path.isfile(module_path):
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                boundary = self.semantic_detector.detect_boundaries(source_code, module_name or os.path.basename(module_path))
                report.boundaries.append(boundary)
                report.module_info = self._extract_module_info(boundary)
            except Exception as e:
                report.issues.append(f"Failed to analyze file: {e}")
        
        # 验证边界
        for boundary in report.boundaries:
            is_valid, issues = self.validator.validate_boundary(boundary)
            report.issues.extend(issues)
            report.validation_results[boundary.boundary_id] = {
                "valid": is_valid,
                "issues": issues
            }
        
        return report
    
    def _extract_module_info(self, boundary: ModuleBoundary) -> ModuleInfo:
        """提取模块信息"""
        info = ModuleInfo(
            module_name=boundary.module_name,
            module_path=boundary.path,
            dependencies=boundary.dependencies
        )
        
        for interface in boundary.interfaces:
            if interface.interface_type == InterfaceType.PUBLIC:
                if interface.name[0].isupper():
                    info.public_classes.append(interface.name)
                else:
                    info.public_functions.append(interface.name)
        
        return info


_global_analyzer: Optional[ModuleBoundaryAnalyzer] = None


def get_module_boundary_analyzer(root_path: str = "") -> ModuleBoundaryAnalyzer:
    """获取全局模块边界分析器"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = ModuleBoundaryAnalyzer(root_path)
    return _global_analyzer


def reset_module_boundary_analyzer() -> None:
    """重置模块边界分析器"""
    global _global_analyzer
    _global_analyzer = None
