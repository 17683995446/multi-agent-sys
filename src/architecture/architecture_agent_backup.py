"""
架构Agent模块

职责：依赖分析、边界锁定、架构方案输出

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import re
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class DependencyType(str, Enum):
    """依赖类型"""
    IMPORT = "import"
    CALL = "call"
    INHERIT = "inherit"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    SEMANTIC = "semantic"


class BoundaryType(str, Enum):
    """边界类型"""
    MODULE = "module"
    CLASS = "class"
    INTERFACE = "interface"
    SERVICE = "service"


@dataclass
class Dependency:
    """依赖关系"""
    dep_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_module: str = ""
    target_module: str = ""
    dep_type: DependencyType = DependencyType.IMPORT
    strength: float = 0.5  # 0.0-1.0
    reason: str = ""


@dataclass
class Interface:
    """接口定义"""
    interface_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    module: str
    methods: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    return_type: str = "Any"
    description: str = ""


@dataclass
class Boundary:
    """边界定义"""
    boundary_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    boundary_type: BoundaryType
    modules: List[str] = field(default_factory=list)
    interfaces: List[Interface] = field(default_factory=list)
    public_api: List[str] = field(default_factory=list)
    internal_components: List[str] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)


@dataclass
class ArchitectureSchema:
    """架构方案"""
    schema_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    boundaries: List[Boundary] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ArchitectureConfig:
    """架构Agent配置"""
    name: str
    analyze_imports: bool = True
    analyze_calls: bool = True
    analyze_semantic: bool = True
    detect_interfaces: bool = True
    output_code: bool = True
    schema_version: str = "1.0.0"


class SemanticDependencyAnalyzer:
    """语义依赖分析器"""
    
    def __init__(self):
        self.semantic_patterns = {
            "data_flow": [
                r"send.*data",
                r"receive.*data",
                r"fetch.*from",
                r"save.*to"
            ],
            "control_flow": [
                r"call.*method",
                r"invoke.*function",
                r"trigger.*action"
            ],
            "business_logic": [
                r"validate.*input",
                r"process.*request",
                r"handle.*event"
            ]
        }
    
    def analyze_semantic_dependencies(self, code: str, module: str) -> List[Dependency]:
        """分析语义依赖"""
        dependencies = []
        
        # 简单的语义关键词匹配
        semantic_keywords = {
            "data_flow": ["data", "input", "output", "stream"],
            "control_flow": ["call", "invoke", "execute"],
            "business_logic": ["validate", "process", "handle"]
        }
        
        for dep_type, keywords in semantic_keywords.items():
            for keyword in keywords:
                if keyword.lower() in code.lower():
                    dep = Dependency(
                        source_module=module,
                        target_module=f"{dep_type}_service",
                        dep_type=DependencyType.SEMANTIC,
                        strength=0.7,
                        reason=f"Semantic dependency via '{keyword}'"
                    )
                    dependencies.append(dep)
                    break
        
        return dependencies


class InterfaceDetector:
    """接口检测器"""
    
    def detect_interfaces(self, code: str, module: str) -> List[Interface]:
        """检测接口"""
        interfaces = []
        
        # 简单的函数签名提取
        function_pattern = r'def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\w+))?'
        matches = re.findall(function_pattern, code)
        
        for match in matches:
            func_name = match[0]
            params = match[1]
            return_type = match[2] if len(match) > 2 else "Any"
            
            interface = Interface(
                name=func_name,
                module=module,
                methods=[func_name],
                parameters=[p.strip() for p in params.split(',') if p.strip()],
                return_type=return_type
            )
            interfaces.append(interface)
        
        return interfaces


class BoundaryIdentifier:
    """边界识别器"""
    
    def identify_boundaries(self, interfaces: List[Interface], 
                          dependencies: List[Dependency]) -> List[Boundary]:
        """识别边界"""
        boundaries = []
        
        # 按模块分组接口
        module_interfaces: Dict[str, List[Interface]] = {}
        for interface in interfaces:
            if interface.module not in module_interfaces:
                module_interfaces[interface.module] = []
            module_interfaces[interface.module].append(interface)
        
        # 为每个模块创建边界
        for module_name, module_interfaces_list in module_interfaces.items():
            boundary = Boundary(
                name=module_name,
                boundary_type=BoundaryType.MODULE,
                modules=[module_name],
                interfaces=module_interfaces_list,
                public_api=[i.name for i in module_interfaces_list[:3]]
            )
            boundaries.append(boundary)
        
        # 添加服务边界
        if len(boundaries) > 1:
            service_boundary = Boundary(
                name="service_layer",
                boundary_type=BoundaryType.SERVICE,
                modules=[b.name for b in boundaries],
                interfaces=[],
                public_api=["service_interface"]
            )
            boundaries.append(service_boundary)
        
        return boundaries


class ArchitectureGenerator:
    """架构方案生成器"""
    
    def generate_documentation(self, schema: ArchitectureSchema) -> str:
        """生成文档"""
        lines = []
        
        lines.append("=" * 80)
        lines.append("ARCHITECTURE DESIGN")
        lines.append("=" * 80)
        lines.append(f"Schema Version: {schema.schema_version}")
        lines.append(f"Generated: {schema.generated_at.isoformat()}")
        lines.append("")
        
        # 边界
        lines.append("## Module Boundaries")
        for boundary in schema.boundaries:
            lines.append(f"\n### {boundary.name} ({boundary.boundary_type.value})")
            lines.append(f"Modules: {', '.join(boundary.modules)}")
            lines.append(f"Public API: {', '.join(boundary.public_api)}")
            lines.append(f"Internal Components: {len(boundary.internal_components)}")
        
        # 依赖
        lines.append("\n\n## Dependencies")
        for dep in schema.dependencies:
            lines.append(f"- {dep.source_module} -> {dep.target_module} ({dep.dep_type.value})")
        
        return "\n".join(lines)
    
    def generate_code(self, schema: ArchitectureSchema) -> Dict[str, str]:
        """生成代码"""
        code_files = {}
        
        # 生成接口文件
        interface_code = []
        interface_code.append("\"\"\"Interface Definitions\"\"\"")
        interface_code.append("")
        interface_code.append("from typing import Any, List")
        interface_code.append("")
        interface_code.append("")
        
        for boundary in schema.boundaries:
            for interface in boundary.interfaces:
                params = ", ".join(interface.parameters)
                interface_code.append(f"def {interface.name}({params}) -> {interface.return_type}:")
                interface_code.append(f'    """Interface {interface.name}""")
                interface_code.append("    pass")
                interface_code.append("")
        
        code_files["interfaces.py"] = "\n".join(interface_code)
        
        # 生成边界定义
        boundary_code = []
        boundary_code.append("\"\"\"Boundary Definitions\"\"\"")
        boundary_code.append("")
        boundary_code.append("from enum import Enum")
        boundary_code.append("")
        boundary_code.append("")
        
        for boundary in schema.boundaries:
            boundary_code.append(f"# Boundary: {boundary.name}")
            boundary_code.append(f"# Type: {boundary.boundary_type.value}")
            boundary_code.append(f"# Modules: {', '.join(boundary.modules)}")
            boundary_code.append("")
        
        code_files["boundaries.py"] = "\n".join(boundary_code)
        
        # 生成依赖图
        dep_code = []
        dep_code.append("\"\"\"Dependency Graph\"\"\"")
        dep_code.append("")
        dep_code.append("DEPENDENCIES = {")
        
        for dep in schema.dependencies:
            dep_code.append(f'    "{dep.source_module}": "{dep.target_module}",')
        
        dep_code.append("}")
        
        code_files["dependencies.py"] = "\n".join(dep_code)
        
        return code_files


class ArchitectureAgent:
    """架构Agent"""
    
    def __init__(self, config: ArchitectureConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.semantic_analyzer = SemanticDependencyAnalyzer()
        self.interface_detector = InterfaceDetector()
        self.boundary_identifier = BoundaryIdentifier()
        self.architecture_generator = ArchitectureGenerator()
        self.interfaces: List[Interface] = []
        self.dependencies: List[Dependency] = []
    
    def analyze_code(self, code: str, module_name: str) -> ArchitectureSchema:
        """分析代码并生成架构方案"""
        
        # 1. 语义依赖分析
        if self.config.analyze_semantic:
            sem_deps = self.semantic_analyzer.analyze_semantic_dependencies(code, module_name)
            self.dependencies.extend(sem_deps)
        
        # 2. 接口检测
        if self.config.detect_interfaces:
            interfaces = self.interface_detector.detect_interfaces(code, module_name)
            self.interfaces.extend(interfaces)
        
        # 3. 边界识别
        boundaries = self.boundary_identifier.identify_boundaries(
            self.interfaces,
            self.dependencies
        )
        
        # 4. 生成架构方案
        schema = ArchitectureSchema(
            name=f"Architecture for {module_name}",
            description=f"Auto-generated architecture schema",
            boundaries=boundaries,
            dependencies=self.dependencies,
            modules=[module_name]
        )
        
        return schema
    
    def generate_output(self, schema: ArchitectureSchema) -> Dict[str, Any]:
        """生成输出"""
        output = {
            "documentation": self.architecture_generator.generate_documentation(schema)
        }
        
        if self.config.output_code:
            output["code_files"] = self.architecture_generator.generate_code(schema)
        
        output["schema"] = {
            "schema_id": schema.schema_id,
            "name": schema.name,
            "boundaries": [
                {
                    "name": b.name,
                    "type": b.boundary_type.value,
                    "modules": b.modules,
                    "public_api": b.public_api
                }
                for b in schema.boundaries
            ],
            "dependencies": [
                {
                    "from": d.source_module,
                    "to": d.target_module,
                    "type": d.dep_type.value,
                    "strength": d.strength
                }
                for d in schema.dependencies
            ]
        }
        
        return output


# 全局架构Agent
_global_architecture_agent: Optional[ArchitectureAgent] = None


def get_architecture_agent(config: Optional[ArchitectureConfig] = None) -> ArchitectureAgent:
    """获取全局架构Agent"""
    global _global_architecture_agent
    if _global_architecture_agent is None:
        if config is None:
            config = ArchitectureConfig(name="ArchitectureAgent")
        _global_architecture_agent = ArchitectureAgent(config)
    return _global_architecture_agent


def reset_architecture_agent() -> None:
    """重置架构Agent"""
    global _global_architecture_agent
    _global_architecture_agent = None
