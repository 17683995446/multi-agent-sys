"""
需求拆解Agent模块

职责：需求层级分解、影响范围分析、标准Schema输出

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import re
import json
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class RequirementType(str, Enum):
    """需求类型"""
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    BUSINESS = "business"
    TECHNICAL = "technical"


class RequirementStatus(str, Enum):
    """需求状态"""
    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"


class ImpactLevel(str, Enum):
    """影响级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RequirementNode:
    """需求节点（层级结构）"""
    title: str
    description: str = ""
    req_type: RequirementType = RequirementType.FUNCTIONAL
    priority: int = 3  # 1=highest, 5=lowest
    status: RequirementStatus = RequirementStatus.DRAFT
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    estimated_effort: Optional[float] = None  # hours
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ImpactAnalysis:
    """影响分析"""
    requirement_id: str
    impacted_modules: List[str] = field(default_factory=list)
    impacted_files: List[str] = field(default_factory=list)
    impacted_functions: List[str] = field(default_factory=list)
    risk_level: ImpactLevel = ImpactLevel.MEDIUM
    complexity_level: ImpactLevel = ImpactLevel.MEDIUM
    dependencies_changed: List[str] = field(default_factory=list)
    analysis_notes: str = ""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class RequirementConfig:
    """需求Agent配置"""
    name: str
    max_depth: int = 5
    auto_decompose: bool = True
    enable_impact_analysis: bool = True
    schema_version: str = "1.0.0"
    keywords: List[str] = field(default_factory=list)


@dataclass
class DecompositionResult:
    """分解结果"""
    root_requirement: RequirementNode
    all_nodes: Dict[str, RequirementNode] = field(default_factory=dict)
    decomposition_levels: int = 0
    total_requirements: int = 0
    total_effort: Optional[float] = None


class HierarchicalDecomposer:
    """层级分解器（HTD）"""
    
    def __init__(self):
        self.keywords = [
            "must", "should", "shall", "can", "will",
            "display", "save", "load", "calculate", "validate",
            "feature", "function", "module", "component"
        ]
    
    def decompose(self, requirement: str, max_depth: int = 5) -> DecompositionResult:
        """自动分解需求"""
        root = RequirementNode(
            title=requirement[:100] if len(requirement) > 100 else requirement,
            description=requirement
        )
        
        result = DecompositionResult(
            root_requirement=root,
            all_nodes={root.node_id: root}
        )
        
        # 自动分解
        if max_depth > 1:
            self._decompose_recursive(root, result, 1, max_depth)
        
        # 更新统计
        result.total_requirements = len(result.all_nodes)
        result.decomposition_levels = self._calculate_depth(root, result.all_nodes)
        result.total_effort = self._sum_effort(result.all_nodes)
        
        return result
    
    def _decompose_recursive(self, node: RequirementNode, 
                           result: DecompositionResult, 
                           current_depth: int, max_depth: int) -> None:
        """递归分解"""
        if current_depth >= max_depth:
            return
        
        # 简单的关键词驱动分解
        sub_requirements = self._extract_sub_requirements(node.description)
        
        for sub_req in sub_requirements:
            child = RequirementNode(
                title=sub_req[:50] if len(sub_req) > 50 else sub_req,
                description=sub_req,
                parent_id=node.node_id,
                priority=node.priority
            )
            
            node.children.append(child.node_id)
            result.all_nodes[child.node_id] = child
            
            # 继续分解
            self._decompose_recursive(child, result, current_depth + 1, max_depth)
    
    def _extract_sub_requirements(self, text: str) -> List[str]:
        """从文本中提取子需求"""
        sub_reqs = []
        
        # 简单的句子分割
        sentences = re.split(r'[.!?;]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                # 检查是否包含关键词
                has_keyword = any(keyword.lower() in sentence.lower() 
                                 for keyword in self.keywords)
                if has_keyword:
                    sub_reqs.append(sentence)
        
        return sub_reqs[:3]  # 限制子需求数量
    
    def _calculate_depth(self, root: RequirementNode, 
                        all_nodes: Dict[str, RequirementNode]) -> int:
        """计算层级深度"""
        max_depth = 1
        
        def _depth(node_id: str, current: int) -> None:
            nonlocal max_depth
            node = all_nodes[node_id]
            max_depth = max(max_depth, current)
            for child_id in node.children:
                _depth(child_id, current + 1)
        
        _depth(root.node_id, 1)
        return max_depth
    
    def _sum_effort(self, all_nodes: Dict[str, RequirementNode]) -> float:
        """计算总工作量"""
        total = 0.0
        for node in all_nodes.values():
            if node.estimated_effort:
                total += node.estimated_effort
        return total


class ImpactAnalyzer:
    """影响分析器"""
    
    def __init__(self):
        # 简单的语义关键词映射
        self.semantic_keywords = {
            "database": ["data", "db", "repository", "model"],
            "api": ["api", "endpoint", "controller", "route"],
            "ui": ["ui", "display", "view", "screen", "component"],
            "business": ["business", "logic", "service", "manager"]
        }
    
    def analyze(self, requirement: RequirementNode, 
               context: Optional[Dict[str, Any]] = None) -> ImpactAnalysis:
        """语义分析影响范围"""
        analysis = ImpactAnalysis(
            requirement_id=requirement.node_id
        )
        
        # 分析需求描述
        text = requirement.title + " " + requirement.description
        text = text.lower()
        
        # 语义分析（关键词匹配）
        for module, keywords in self.semantic_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if module not in analysis.impacted_modules:
                        analysis.impacted_modules.append(module)
                    break
        
        # 基于模块推断文件和函数
        for module in analysis.impacted_modules:
            if module == "database":
                analysis.impacted_files.extend(["models.py", "database.py", "repositories.py"])
                analysis.impacted_functions.extend(["save", "load", "query"])
            elif module == "api":
                analysis.impacted_files.extend(["controllers.py", "routes.py", "api.py"])
                analysis.impacted_functions.extend(["handle_request", "send_response"])
            elif module == "ui":
                analysis.impacted_files.extend(["views.py", "components.py"])
                analysis.impacted_functions.extend(["render", "update_display"])
        
        # 风险评估
        analysis.risk_level = self._assess_risk(analysis.impacted_modules)
        analysis.complexity_level = self._assess_complexity(requirement)
        
        analysis.analysis_notes = f"Analyzed requirement with {len(analysis.impacted_modules)} impacted modules"
        
        return analysis
    
    def _assess_risk(self, modules: List[str]) -> ImpactLevel:
        """评估风险级别"""
        if len(modules) > 2:
            return ImpactLevel.HIGH
        elif len(modules) == 2:
            return ImpactLevel.MEDIUM
        return ImpactLevel.LOW
    
    def _assess_complexity(self, requirement: RequirementNode) -> ImpactLevel:
        """评估复杂度"""
        desc_length = len(requirement.description)
        
        if desc_length > 500:
            return ImpactLevel.HIGH
        elif desc_length > 200:
            return ImpactLevel.MEDIUM
        return ImpactLevel.LOW


class SchemaOutputGenerator:
    """Schema输出生成器"""
    
    def __init__(self, schema_version: str = "1.0.0"):
        self.schema_version = schema_version
    
    def generate_structured_text(self, result: DecompositionResult) -> str:
        """生成结构化文本"""
        lines = []
        
        lines.append("=" * 80)
        lines.append("REQUIREMENT DECOMPOSITION")
        lines.append("=" * 80)
        lines.append(f"Schema Version: {self.schema_version}")
        lines.append(f"Total Requirements: {result.total_requirements}")
        lines.append(f"Decomposition Levels: {result.decomposition_levels}")
        if result.total_effort:
            lines.append(f"Total Estimated Effort: {result.total_effort} hours")
        lines.append("")
        
        # 层级输出
        self._append_node_text(result.root_requirement, result.all_nodes, lines, 0)
        
        return "\n".join(lines)
    
    def generate_json_schema(self, result: DecompositionResult,
                           analysis: Optional[ImpactAnalysis] = None) -> Dict[str, Any]:
        """生成标准JSON Schema"""
        nodes_list = list(result.all_nodes.values())
        
        schema = {
            "schema_version": self.schema_version,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_requirements": result.total_requirements,
                "levels": result.decomposition_levels,
                "total_effort": result.total_effort
            },
            "requirements": [
                {
                    "node_id": node.node_id,
                    "title": node.title,
                    "description": node.description,
                    "type": node.req_type.value,
                    "priority": node.priority,
                    "status": node.status.value,
                    "parent_id": node.parent_id,
                    "children": node.children,
                    "estimated_effort": node.estimated_effort,
                    "acceptance_criteria": node.acceptance_criteria
                }
                for node in nodes_list
            ]
        }
        
        if analysis:
            schema["impact_analysis"] = {
                "analysis_id": analysis.analysis_id,
                "impacted_modules": analysis.impacted_modules,
                "impacted_files": analysis.impacted_files,
                "risk_level": analysis.risk_level.value,
                "complexity_level": analysis.complexity_level.value
            }
        
        return schema
    
    def _append_node_text(self, node: RequirementNode, 
                        all_nodes: Dict[str, RequirementNode], 
                        lines: List[str], indent: int) -> None:
        """递归添加节点文本"""
        indent_str = "  " * indent
        prefix = f"{'#' * (indent + 1)} "
        
        lines.append(f"{indent_str}{prefix}{node.title}")
        lines.append(f"{indent_str}  Type: {node.req_type.value}")
        lines.append(f"{indent_str}  Priority: {node.priority}")
        lines.append(f"{indent_str}  Status: {node.status.value}")
        
        if node.description:
            lines.append(f"{indent_str}  Description: {node.description[:100]}...")
        
        lines.append("")
        
        # 处理子节点
        for child_id in node.children:
            child_node = all_nodes[child_id]
            self._append_node_text(child_node, all_nodes, lines, indent + 1)


class RequirementAgent:
    """需求拆解Agent"""
    
    def __init__(self, config: RequirementConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.decomposer = HierarchicalDecomposer()
        self.impact_analyzer = ImpactAnalyzer()
        self.schema_generator = SchemaOutputGenerator(config.schema_version)
        self.requirements: Dict[str, RequirementNode] = {}
    
    def process_requirement(self, requirement_text: str) -> Dict[str, Any]:
        """完整处理需求"""
        # 1. 分解需求
        decomposition = self.decomposer.decompose(
            requirement_text,
            self.config.max_depth
        )
        
        # 保存所有节点
        for node_id, node in decomposition.all_nodes.items():
            self.requirements[node_id] = node
        
        result = {
            "decomposition": decomposition,
            "structured_text": self.schema_generator.generate_structured_text(decomposition),
            "json_schema": self.schema_generator.generate_json_schema(decomposition)
        }
        
        # 2. 影响分析
        if self.config.enable_impact_analysis:
            impact = self.impact_analyzer.analyze(decomposition.root_requirement)
            result["impact_analysis"] = impact
            result["json_schema"] = self.schema_generator.generate_json_schema(decomposition, impact)
        
        return result
    
    def get_requirement_by_id(self, node_id: str) -> Optional[RequirementNode]:
        """获取需求节点"""
        return self.requirements.get(node_id)


# 全局需求Agent
_global_requirement_agent: Optional[RequirementAgent] = None


def get_requirement_agent(config: Optional[RequirementConfig] = None) -> RequirementAgent:
    """获取全局需求Agent"""
    global _global_requirement_agent
    if _global_requirement_agent is None:
        if config is None:
            config = RequirementConfig(name="RequirementAgent")
        _global_requirement_agent = RequirementAgent(config)
    return _global_requirement_agent


def reset_requirement_agent() -> None:
    """重置需求Agent"""
    global _global_requirement_agent
    _global_requirement_agent = None
