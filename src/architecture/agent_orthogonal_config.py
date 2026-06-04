"""
Agent正交职责配置系统
职责：职责矩阵定义、无重叠验证、无空缺验证、分工文档
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class AgentType(str, Enum):
    """Agent类型"""
    CONTROL = "control"
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    DEVELOPMENT = "development"
    REVIEW = "review"
    DEBUG = "debug"
    TEST = "test"
    DOC = "doc"


class ResponsibilityCategory(str, Enum):
    """职责分类"""
    DECISION = "decision"
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    DOCUMENTATION = "documentation"
    OPERATION = "operation"


@dataclass
class Responsibility:
    """职责定义"""
    resp_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: ResponsibilityCategory = ResponsibilityCategory.ANALYSIS
    primary_agent: AgentType = None
    secondary_agents: List[AgentType] = field(default_factory=list)
    required: bool = True


@dataclass
class AgentCapability:
    """Agent能力"""
    capability_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    responsibility: str = ""


@dataclass
class AgentRole:
    """Agent角色定义"""
    agent_type: AgentType
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    capabilities: List[AgentCapability] = field(default_factory=list)
    responsibilities: List[Responsibility] = field(default_factory=list)


@dataclass
class ResponsibilityMatrix:
    """职责矩阵"""
    matrix_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agents: List[AgentRole] = field(default_factory=list)
    responsibilities: List[Responsibility] = field(default_factory=list)
    overlap_checks: List[Dict] = field(default_factory=list)
    gap_checks: List[Dict] = field(default_factory=list)


class ResponsibilityMatrixBuilder:
    """职责矩阵构建器"""
    
    def __init__(self):
        self.matrix = ResponsibilityMatrix()
    
    def add_agent(self, agent_type: AgentType, name: str, description: str) -> AgentRole:
        """添加Agent"""
        role = AgentRole(
            agent_type=agent_type,
            name=name,
            description=description
        )
        self.matrix.agents.append(role)
        return role
    
    def add_responsibility(self, name: str, description: str, 
                          primary_agent: AgentType, 
                          secondary_agents: List[AgentType] = None,
                          category: ResponsibilityCategory = ResponsibilityCategory.ANALYSIS,
                          required: bool = True) -> Responsibility:
        """添加职责"""
        resp = Responsibility(
            name=name,
            description=description,
            category=category,
            primary_agent=primary_agent,
            secondary_agents=secondary_agents or [],
            required=required
        )
        self.matrix.responsibilities.append(resp)
        
        for agent in self.matrix.agents:
            if agent.agent_type == primary_agent:
                agent.responsibilities.append(resp)
        
        return resp
    
    def build(self) -> ResponsibilityMatrix:
        """构建矩阵"""
        return self.matrix


class OverlapDetector:
    """重叠检测器"""
    
    @staticmethod
    def detect_overlaps(matrix: ResponsibilityMatrix) -> List[Dict]:
        """检测职责重叠"""
        overlaps = []
        
        primary_assignments = {}
        for resp in matrix.responsibilities:
            if resp.primary_agent:
                if resp.primary_agent not in primary_assignments:
                    primary_assignments[resp.primary_agent] = []
                primary_assignments[resp.primary_agent].append(resp)
        
        for agent_type, resps in primary_assignments.items():
            for i, resp1 in enumerate(resps):
                for j, resp2 in enumerate(resps[i+1:], i+1):
                    similarity = OverlapDetector._check_similarity(resp1, resp2)
                    if similarity > 0.7:
                        overlaps.append({
                            "agent_type": agent_type,
                            "resp1": resp1.name,
                            "resp2": resp2.name,
                            "similarity": similarity
                        })
        
        matrix.overlap_checks = overlaps
        return overlaps
    
    @staticmethod
    def _check_similarity(resp1: Responsibility, resp2: Responsibility) -> float:
        """检查职责相似度"""
        if resp1.category == resp2.category:
            keywords1 = set(resp1.name.lower().split())
            keywords2 = set(resp2.name.lower().split())
            intersection = len(keywords1 & keywords2)
            union = len(keywords1 | keywords2)
            return intersection / union if union > 0 else 0
        return 0.0
    
    @staticmethod
    def has_overlap(matrix: ResponsibilityMatrix) -> bool:
        """检查是否有重叠"""
        if not matrix.overlap_checks:
            OverlapDetector.detect_overlaps(matrix)
        return len(matrix.overlap_checks) > 0


class GapDetector:
    """空缺检测器"""
    
    @staticmethod
    def detect_gaps(matrix: ResponsibilityMatrix, required_categories: List[ResponsibilityCategory] = None) -> List[Dict]:
        """检测职责空缺"""
        gaps = []
        
        if required_categories is None:
            required_categories = list(ResponsibilityCategory)
        
        agent_types = set(agent.agent_type for agent in matrix.agents)
        
        for category in required_categories:
            covered = False
            for resp in matrix.responsibilities:
                if resp.category == category and resp.required:
                    covered = True
                    break
            
            if not covered:
                gaps.append({
                    "category": category,
                    "status": "uncovered",
                    "description": f"没有职责覆盖 {category} 分类"
                })
        
        for agent_type in agent_types:
            agent_resps = [
                r for r in matrix.responsibilities 
                if r.primary_agent == agent_type
            ]
            if len(agent_resps) == 0:
                gaps.append({
                    "agent_type": agent_type,
                    "status": "no_responsibility",
                    "description": f"Agent {agent_type} 没有主职责"
                })
        
        matrix.gap_checks = gaps
        return gaps
    
    @staticmethod
    def has_gap(matrix: ResponsibilityMatrix, required_categories: List[ResponsibilityCategory] = None) -> bool:
        """检查是否有空缺"""
        if not matrix.gap_checks:
            GapDetector.detect_gaps(matrix, required_categories)
        return len(matrix.gap_checks) > 0


class ResponsibilityDocumentGenerator:
    """职责文档生成器"""
    
    @staticmethod
    def generate_markdown_document(matrix: ResponsibilityMatrix) -> str:
        """生成Markdown格式的分工文档"""
        lines = []
        lines.append("# Agent职责分工文档")
        lines.append("")
        lines.append("## 1. Agent角色列表")
        lines.append("")
        
        for agent in matrix.agents:
            lines.append(f"### {agent.agent_type.value.capitalize()} Agent")
            lines.append(f"- **名称**: {agent.name}")
            lines.append(f"- **描述**: {agent.description}")
            lines.append("- **主职责**:")
            for resp in agent.responsibilities:
                lines.append(f"  - {resp.name}: {resp.description}")
            lines.append("")
        
        lines.append("## 2. 职责矩阵")
        lines.append("")
        
        lines.append("| 职责名称 | 主负责人 | 次负责人 | 分类 | 是否必需 |")
        lines.append("|---------|---------|---------|------|---------|")
        
        for resp in matrix.responsibilities:
            primary = resp.primary_agent.value if resp.primary_agent else "-"
            secondaries = ", ".join(a.value for a in resp.secondary_agents) or "-"
            required = "✓" if resp.required else "○"
            lines.append(f"| {resp.name} | {primary} | {secondaries} | {resp.category.value} | {required} |")
        
        lines.append("")
        lines.append("## 3. 验证结果")
        lines.append("")
        
        lines.append("### 重叠检测")
        if matrix.overlap_checks:
            lines.append("⚠️ **检测到潜在重叠**:")
            for ov in matrix.overlap_checks:
                lines.append(f"- {ov['agent_type']}: {ov['resp1']} ↔ {ov['resp2']} (相似度: {ov['similarity']:.2f})")
        else:
            lines.append("✓ **无职责重叠**")
        
        lines.append("")
        
        lines.append("### 空缺检测")
        if matrix.gap_checks:
            lines.append("⚠️ **检测到职责空缺**:")
            for gap in matrix.gap_checks:
                lines.append(f"- {gap.get('category', gap.get('agent_type'))}: {gap['description']}")
        else:
            lines.append("✓ **无职责空缺**")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_visual_matrix(matrix: ResponsibilityMatrix) -> str:
        """生成可视化矩阵"""
        lines = []
        lines.append("```")
        lines.append("       " + " ".join(f"{a.agent_type.value[:3]:4}" for a in matrix.agents))
        
        for resp in matrix.responsibilities:
            row = f"{resp.name[:12]:12}"
            for agent in matrix.agents:
                if agent.agent_type == resp.primary_agent:
                    row += " P   "
                elif agent.agent_type in resp.secondary_agents:
                    row += " S   "
                else:
                    row += " -   "
            lines.append(row)
        
        lines.append("```")
        return "\n".join(lines)


class AgentOrthogonalConfig:
    """Agent正交配置系统"""
    
    def __init__(self):
        self.responsibility_matrix = None
    
    def initialize_standard_matrix(self) -> ResponsibilityMatrix:
        """初始化标准的职责矩阵"""
        builder = ResponsibilityMatrixBuilder()
        
        builder.add_agent(AgentType.CONTROL, "总控Agent", "全局协调、任务收口")
        builder.add_agent(AgentType.REQUIREMENT, "需求Agent", "HTD分解、影响分析")
        builder.add_agent(AgentType.ARCHITECTURE, "架构Agent", "依赖分析、边界锁定")
        builder.add_agent(AgentType.DEVELOPMENT, "开发Agent", "代码生成、修改、重构")
        builder.add_agent(AgentType.REVIEW, "评审Agent", "原子校验、规范检查")
        builder.add_agent(AgentType.DEBUG, "缺陷排查Agent", "日志解析、堆栈定位")
        builder.add_agent(AgentType.TEST, "测试Agent", "用例生成、回归测试")
        builder.add_agent(AgentType.DOC, "文档Agent", "文档生成、归档、同步")
        
        builder.add_responsibility(
            "全局决策", "全局协调和任务决策",
            AgentType.CONTROL,
            category=ResponsibilityCategory.DECISION,
            required=True
        )
        
        builder.add_responsibility(
            "需求分解", "HTD层级任务分解",
            AgentType.REQUIREMENT,
            category=ResponsibilityCategory.ANALYSIS,
            required=True
        )
        
        builder.add_responsibility(
            "架构设计", "依赖分析和边界锁定",
            AgentType.ARCHITECTURE,
            category=ResponsibilityCategory.ANALYSIS,
            required=True
        )
        
        builder.add_responsibility(
            "代码实现", "代码生成、修改、重构",
            AgentType.DEVELOPMENT,
            category=ResponsibilityCategory.IMPLEMENTATION,
            required=True
        )
        
        builder.add_responsibility(
            "代码评审", "原子校验和规范检查",
            AgentType.REVIEW,
            category=ResponsibilityCategory.VALIDATION,
            required=True
        )
        
        builder.add_responsibility(
            "缺陷排查", "日志解析和堆栈定位",
            AgentType.DEBUG,
            category=ResponsibilityCategory.OPERATION,
            required=True
        )
        
        builder.add_responsibility(
            "测试执行", "用例生成和回归测试",
            AgentType.TEST,
            category=ResponsibilityCategory.VALIDATION,
            required=True
        )
        
        builder.add_responsibility(
            "文档管理", "文档生成、归档、同步",
            AgentType.DOC,
            category=ResponsibilityCategory.DOCUMENTATION,
            required=True
        )
        
        self.responsibility_matrix = builder.build()
        
        OverlapDetector.detect_overlaps(self.responsibility_matrix)
        GapDetector.detect_gaps(self.responsibility_matrix)
        
        return self.responsibility_matrix
    
    def verify_config(self) -> Tuple[bool, Dict]:
        """验证配置"""
        if not self.responsibility_matrix:
            return False, {"error": "No matrix initialized"}
        
        has_overlap = OverlapDetector.has_overlap(self.responsibility_matrix)
        has_gap = GapDetector.has_gap(self.responsibility_matrix)
        
        valid = not has_overlap and not has_gap
        
        return valid, {
            "overlap_count": len(self.responsibility_matrix.overlap_checks),
            "gap_count": len(self.responsibility_matrix.gap_checks),
            "overlaps": self.responsibility_matrix.overlap_checks,
            "gaps": self.responsibility_matrix.gap_checks
        }
    
    def generate_documentation(self) -> str:
        """生成完整的分工文档"""
        doc = ResponsibilityDocumentGenerator.generate_markdown_document(self.responsibility_matrix)
        visual = ResponsibilityDocumentGenerator.generate_visual_matrix(self.responsibility_matrix)
        return doc + "\n\n## 可视化矩阵\n" + visual


_global_config: Optional[AgentOrthogonalConfig] = None


def get_agent_config() -> AgentOrthogonalConfig:
    """获取全局配置"""
    global _global_config
    if _global_config is None:
        _global_config = AgentOrthogonalConfig()
        _global_config.initialize_standard_matrix()
    return _global_config


def reset_agent_config() -> None:
    """重置全局配置"""
    global _global_config
    _global_config = None
