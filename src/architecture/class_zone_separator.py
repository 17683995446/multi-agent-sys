"""
类原子三区分离模块

职责：将类的成员分离为三个区域
1. 常量区 - Constants Zone（静态常量、配置常量）
2. 状态区 - State Zone（类变量、实例变量）
3. 方法区 - Methods Zone（构造方法、业务方法、工具方法）

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


class ZoneType(str, Enum):
    """类区域类型"""
    CONSTANTS = "constants"  # 常量区
    STATE = "state"         # 状态区
    METHODS = "methods"     # 方法区
    UNKNOWN = "unknown"    # 未知区


class MethodGroupType(str, Enum):
    """方法分组类型"""
    CONSTRUCTOR = "constructor"  # 构造方法
    BUSINESS = "business"       # 业务方法
    UTILITY = "utility"         # 工具方法
    PROPERTY = "property"       # 属性访问方法
    UNKNOWN = "unknown"        # 未知方法


class ConstantType(str, Enum):
    """常量类型"""
    STATIC = "static"     # 静态常量
    CONFIG = "config"    # 配置常量
    MAGIC = "magic"      # 魔法常量


class StateType(str, Enum):
    """状态类型"""
    CLASS = "class"     # 类变量
    INSTANCE = "instance"  # 实例变量


@dataclass
class ClassConstant:
    """类常量"""
    name: str
    value: str
    constant_type: ConstantType = ConstantType.STATIC
    line_start: int = 0
    line_end: int = 0
    documentation: Optional[str] = None


@dataclass
class ClassState:
    """类状态"""
    name: str
    state_type: StateType = StateType.INSTANCE
    initial_value: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    documentation: Optional[str] = None


@dataclass
class ClassMethod:
    """类方法"""
    name: str
    method_group: MethodGroupType = MethodGroupType.UNKNOWN
    is_class_method: bool = False
    is_static_method: bool = False
    is_property: bool = False
    line_start: int = 0
    line_end: int = 0
    code_content: str = ""
    documentation: Optional[str] = None


@dataclass
class ClassZone:
    """类区域"""
    zone_type: ZoneType
    items: List[Any] = field(default_factory=list)
    documentation: Optional[str] = None


@dataclass
class ClassStructure:
    """类结构"""
    class_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_code: str = ""
    class_name: str = ""
    bases: List[str] = field(default_factory=list)
    documentation: Optional[str] = None
    zones: Dict[ZoneType, ClassZone] = field(default_factory=dict)
    validation_passed: bool = True
    issues: List[str] = field(default_factory=list)

    def get_zone(self, zone_type: ZoneType) -> Optional[ClassZone]:
        """获取指定类型的区域"""
        return self.zones.get(zone_type)

    def has_zone(self, zone_type: ZoneType) -> bool:
        """检查是否存在指定类型的区域"""
        return zone_type in self.zones


@dataclass
class RefactoredClass:
    """重构后的类"""
    class_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_structure: ClassStructure = None
    refactored_code: str = ""
    generation_time: datetime = field(default_factory=datetime.now)
    applied_zones: List[ZoneType] = field(default_factory=list)
    validation_result: Dict[str, Any] = field(default_factory=dict)


class ClassZoneIdentifier:
    """类区域识别器"""

    CONSTANT_PATTERNS = [
        r'^[A-Z_]+$',  # 全大写带下划线
    ]

    def _is_constant(self, name: str, value: ast.expr) -> bool:
        """判断是否为常量"""
        # 检查命名模式
        if re.match(r'^[A-Z_][A-Z0-9_]*$', name):
            return True
        
        # 检查是否为字面量（兼容不同 Python 版本）
        if hasattr(ast, 'Constant') and isinstance(value, ast.Constant):
            return True
        # 兼容旧版本
        if hasattr(ast, 'NameConstant') and isinstance(value, ast.NameConstant):
            return True
        if hasattr(ast, 'Str') and isinstance(value, ast.Str):
            return True
        if hasattr(ast, 'Num') and isinstance(value, ast.Num):
            return True
        
        # 检查魔术常量（__xxx__）
        if name.startswith('__') and name.endswith('__'):
            return True
        
        return False

    def _identify_constant_type(self, name: str, value: ast.expr) -> ConstantType:
        """识别常量类型"""
        if name.startswith('__') and name.endswith('__'):
            return ConstantType.MAGIC
        
        if name.upper() == name and '_' in name:
            if 'CONFIG' in name or 'SETTING' in name:
                return ConstantType.CONFIG
            return ConstantType.STATIC
        
        return ConstantType.STATIC

    def identify_constants(self, node: ast.ClassDef) -> List[ClassConstant]:
        """识别类常量"""
        constants = []
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if self._is_constant(target.id, item.value):
                            try:
                                value_str = ast.unparse(item.value) if hasattr(ast, 'unparse') else repr(item.value)
                            except:
                                value_str = repr(item.value)
                            
                            constant = ClassConstant(
                                name=target.id,
                                value=value_str,
                                constant_type=self._identify_constant_type(target.id, item.value),
                                line_start=item.lineno,
                                line_end=item.end_lineno if hasattr(item, 'end_lineno') else item.lineno
                            )
                            constants.append(constant)
        
        return constants

    def identify_state(self, node: ast.ClassDef) -> List[ClassState]:
        """识别类状态"""
        states = []
        
        # 识别类变量
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # 如果是全大写带下划线，那它是常量，不是状态
                        if not re.match(r'^[A-Z_][A-Z0-9_]*$', target.id):
                            try:
                                value_str = ast.unparse(item.value) if hasattr(ast, 'unparse') else None
                            except:
                                value_str = None
                            
                            state = ClassState(
                                name=target.id,
                                state_type=StateType.CLASS,
                                initial_value=value_str,
                                line_start=item.lineno,
                                line_end=item.end_lineno if hasattr(item, 'end_lineno') else item.lineno
                            )
                            states.append(state)
        
        # 识别实例变量（在__init__等方法中）
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == '__init__':
                    for stmt in item.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                    state = ClassState(
                                        name=target.attr,
                                        state_type=StateType.INSTANCE,
                                        line_start=stmt.lineno,
                                        line_end=stmt.end_lineno if hasattr(stmt, 'end_lineno') else stmt.lineno
                                    )
                                    states.append(state)
        
        return states

    def identify_methods(self, node: ast.ClassDef) -> List[ClassMethod]:
        """识别类方法"""
        methods = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method = ClassMethod(
                    name=item.name,
                    line_start=item.lineno,
                    line_end=item.end_lineno if hasattr(item, 'end_lineno') else item.lineno
                )
                
                # 检查装饰器
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name):
                        if decorator.id == 'classmethod':
                            method.is_class_method = True
                        elif decorator.id == 'staticmethod':
                            method.is_static_method = True
                        elif decorator.id == 'property':
                            method.is_property = True
                
                # 确定方法分组
                if item.name == '__init__':
                    method.method_group = MethodGroupType.CONSTRUCTOR
                elif method.is_property:
                    method.method_group = MethodGroupType.PROPERTY
                elif item.name.startswith('_'):
                    method.method_group = MethodGroupType.UTILITY
                else:
                    method.method_group = MethodGroupType.BUSINESS
                
                methods.append(method)
        
        return methods


class ClassStructureAnalyzer:
    """类结构分析器"""

    def __init__(self):
        self.identifier = ClassZoneIdentifier()

    def analyze_structure(self, class_code: str) -> ClassStructure:
        """分析类结构"""
        structure = ClassStructure(original_code=class_code)
        
        try:
            tree = ast.parse(class_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    structure.class_name = node.name
                    structure.bases = [ast.unparse(base) if hasattr(ast, 'unparse') else base.id for base in node.bases]
                    structure.documentation = ast.get_docstring(node)
                    
                    # 识别各区域
                    constants = self.identifier.identify_constants(node)
                    states = self.identifier.identify_state(node)
                    methods = self.identifier.identify_methods(node)
                    
                    # 创建区域
                    structure.zones[ZoneType.CONSTANTS] = ClassZone(
                        zone_type=ZoneType.CONSTANTS,
                        items=constants
                    )
                    
                    structure.zones[ZoneType.STATE] = ClassZone(
                        zone_type=ZoneType.STATE,
                        items=states
                    )
                    
                    structure.zones[ZoneType.METHODS] = ClassZone(
                        zone_type=ZoneType.METHODS,
                        items=methods
                    )
        
        except Exception as e:
            structure.validation_passed = False
            structure.issues.append(f"Failed to analyze class structure: {str(e)}")
        
        return structure


class ClassZoneTemplate:
    """类区域模板"""

    @staticmethod
    def get_template(
        class_name: str,
        bases: List[str],
        documentation: Optional[str],
        zones: Dict[ZoneType, ClassZone]
    ) -> str:
        """生成三区分离的类代码"""
        lines = []
        
        # 类定义
        if documentation:
            lines.append(f'class {class_name}({", ".join(bases)}):')
            lines.append(f'    """{documentation}"""')
        else:
            lines.append(f'class {class_name}({", ".join(bases)}):')
            lines.append(f'    """{class_name} class"""')
        
        # 常量区
        constants_zone = zones.get(ZoneType.CONSTANTS)
        if constants_zone and constants_zone.items:
            lines.append("")
            lines.append("    # === CONSTANTS ZONE ===")
            for const in constants_zone.items:
                if const.constant_type == ConstantType.MAGIC:
                    continue  # 跳过魔术常量
                if const.documentation:
                    lines.append(f'    # {const.documentation}')
                lines.append(f'    {const.name} = {const.value}')
        
        # 状态区
        state_zone = zones.get(ZoneType.STATE)
        if state_zone and state_zone.items:
            lines.append("")
            lines.append("    # === STATE ZONE ===")
            # 先放类变量
            class_vars = [s for s in state_zone.items if s.state_type == StateType.CLASS]
            for state in class_vars:
                if state.documentation:
                    lines.append(f'    # {state.documentation}')
                if state.initial_value:
                    lines.append(f'    {state.name} = {state.initial_value}')
                else:
                    lines.append(f'    {state.name} = None')
        
        # 方法区
        methods_zone = zones.get(ZoneType.METHODS)
        if methods_zone and methods_zone.items:
            # 按分组组织
            constructor_methods = [m for m in methods_zone.items if m.method_group == MethodGroupType.CONSTRUCTOR]
            business_methods = [m for m in methods_zone.items if m.method_group == MethodGroupType.BUSINESS]
            utility_methods = [m for m in methods_zone.items if m.method_group == MethodGroupType.UTILITY]
            property_methods = [m for m in methods_zone.items if m.method_group == MethodGroupType.PROPERTY]
            
            if constructor_methods:
                lines.append("")
                lines.append("    # === METHODS ZONE - Constructor ===")
                for method in constructor_methods:
                    lines.append(f"    def {method.name}(...):")
                    lines.append("        pass")
            
            if property_methods:
                lines.append("")
                lines.append("    # === METHODS ZONE - Properties ===")
                for method in property_methods:
                    lines.append(f"    @property")
                    lines.append(f"    def {method.name}(...):")
                    lines.append("        pass")
            
            if business_methods:
                lines.append("")
                lines.append("    # === METHODS ZONE - Business ===")
                for method in business_methods:
                    decorators = []
                    if method.is_class_method:
                        decorators.append("@classmethod")
                    if method.is_static_method:
                        decorators.append("@staticmethod")
                    
                    for dec in decorators:
                        lines.append(f"    {dec}")
                    lines.append(f"    def {method.name}(...):")
                    lines.append("        pass")
            
            if utility_methods:
                lines.append("")
                lines.append("    # === METHODS ZONE - Utility ===")
                for method in utility_methods:
                    decorators = []
                    if method.is_class_method:
                        decorators.append("@classmethod")
                    if method.is_static_method:
                        decorators.append("@staticmethod")
                    
                    for dec in decorators:
                        lines.append(f"    {dec}")
                    lines.append(f"    def {method.name}(...):")
                    lines.append("        pass")
        
        return "\n".join(lines)


class ClassZoneValidator:
    """类区域验证器"""

    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """验证语法正确性"""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"

    def validate_three_zone_structure(self, code: str) -> Tuple[bool, List[str]]:
        """验证三区结构"""
        issues = []
        
        required_zones = [ZoneType.CONSTANTS, ZoneType.STATE, ZoneType.METHODS]
        required_markers = {
            ZoneType.CONSTANTS: "=== CONSTANTS ZONE ===",
            ZoneType.STATE: "=== STATE ZONE ===",
            ZoneType.METHODS: "=== METHODS ZONE ==="
        }
        
        for zone in required_zones:
            marker = required_markers[zone]
            if marker not in code:
                issues.append(f"Missing required zone marker: {marker}")
        
        if not issues:
            return True, []
        return False, issues


class ClassZoneRefactorEngine:
    """类三区分离重构引擎"""
    
    def __init__(self):
        self.analyzer = ClassStructureAnalyzer()
        self.template = ClassZoneTemplate()
        self.validator = ClassZoneValidator()

    def refactor_class(self, class_code: str, validate: bool = True) -> RefactoredClass:
        """重构类为三区分离结构"""
        refactored = RefactoredClass()
        
        structure = self.analyzer.analyze_structure(class_code)
        refactored.original_structure = structure
        
        if not structure.validation_passed:
            refactored.validation_result["success"] = False
            refactored.validation_result["errors"] = structure.issues
            return refactored
        
        refactored.refactored_code = self.template.get_template(
            structure.class_name,
            structure.bases,
            structure.documentation,
            structure.zones
        )
        
        refactored.applied_zones = list(structure.zones.keys())
        
        if validate:
            syntax_valid, error = self.validator.validate_syntax(refactored.refactored_code)
            refactored.validation_result["syntax_valid"] = syntax_valid
            if error:
                refactored.validation_result["syntax_error"] = error
            
            if syntax_valid:
                structure_valid, structure_issues = self.validator.validate_three_zone_structure(
                    refactored.refactored_code
                )
                refactored.validation_result["structure_valid"] = structure_valid
                refactored.validation_result["structure_issues"] = structure_issues
        
        return refactored


_global_engine: Optional[ClassZoneRefactorEngine] = None


def get_class_zone_refactor_engine() -> ClassZoneRefactorEngine:
    """获取全局类区域重构引擎"""
    global _global_engine
    if _global_engine is None:
        _global_engine = ClassZoneRefactorEngine()
    return _global_engine


def reset_class_zone_refactor_engine() -> None:
    """重置类区域重构引擎"""
    global _global_engine
    _global_engine = None
