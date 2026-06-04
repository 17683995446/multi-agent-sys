"""
模块循环依赖检测模块

职责：构建依赖图、检测循环依赖、报告循环路径、提供斩断方案

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


class DependencyType(str, Enum):
    """依赖类型"""
    IMPORT = "import"
    FROM_IMPORT = "from_import"
    CALL = "call"
    REFERENCE = "reference"


@dataclass
class Dependency:
    """依赖关系"""
    from_module: str
    to_module: str
    dep_type: DependencyType = DependencyType.IMPORT
    line_number: int = 0
    file_path: str = ""


@dataclass
class CyclePath:
    """循环路径"""
    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    modules: List[str] = field(default_factory=list)
    severity: str = "medium"
    impact: str = ""
    suggestions: List[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """依赖图"""
    graph_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nodes: Set[str] = field(default_factory=set)
    edges: List[Dependency] = field(default_factory=list)
    adjacency: Dict[str, List[str]] = field(default_factory=dict)
    reverse_adjacency: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class CycleReport:
    """循环依赖报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=datetime.now)
    total_cycles: int = 0
    cycles: List[CyclePath] = field(default_factory=list)
    dependency_graph: Optional[DependencyGraph] = None


class DependencyGraphBuilder:
    """依赖图构建器"""
    
    def __init__(self, root_path: str = ""):
        self.root_path = Path(root_path) if root_path else Path.cwd()
        self.graph = DependencyGraph()
        self.module_mapping: Dict[str, Path] = {}
    
    def build_from_directory(self, directory: str) -> DependencyGraph:
        """从目录构建依赖图"""
        dir_path = Path(directory)
        self._scan_directory(dir_path)
        self._parse_all_files()
        return self.graph
    
    def build_from_code(self, source_code: str, module_name: str) -> DependencyGraph:
        """从代码构建依赖图"""
        self._parse_source(source_code, module_name, "")
        return self.graph
    
    def _scan_directory(self, dir_path: Path):
        """扫描目录中的 Python 文件"""
        if dir_path.is_file():
            files = [dir_path]
        else:
            files = list(dir_path.rglob("*.py"))
        
        for file_path in files:
            if file_path.name.startswith('.'):
                continue
            
            module_name = self._file_to_module_name(file_path)
            self.module_mapping[module_name] = file_path
            self.graph.nodes.add(module_name)
            if module_name not in self.graph.adjacency:
                self.graph.adjacency[module_name] = []
            if module_name not in self.graph.reverse_adjacency:
                self.graph.reverse_adjacency[module_name] = []
    
    def _file_to_module_name(self, file_path: Path) -> str:
        """将文件路径转换为模块名"""
        try:
            relative_path = file_path.relative_to(self.root_path)
            parts = list(relative_path.parts)
            if parts[-1] == "__init__.py":
                parts.pop()
            else:
                parts[-1] = parts[-1][:-3]  # Remove .py
            return ".".join(parts)
        except ValueError:
            return file_path.stem
    
    def _parse_all_files(self):
        """解析所有找到的 Python 文件"""
        for module_name, file_path in self.module_mapping.items():
            self._parse_file(file_path, module_name)
    
    def _parse_file(self, file_path: Path, module_name: str):
        """解析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            self._parse_source(source_code, module_name, str(file_path))
        except Exception:
            pass
    
    def _parse_source(self, source_code: str, module_name: str, file_path: str):
        """解析源代码提取依赖"""
        try:
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                # 处理 import 语句
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep_name = alias.name.split('.')[0]
                        if dep_name in self.module_mapping:
                            self._add_edge(module_name, dep_name, DependencyType.IMPORT, file_path, node.lineno)
                
                # 处理 from ... import 语句
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_parts = node.module.split('.')
                        # 尝试匹配完整模块名或子模块
                        for i in range(len(module_parts), 0, -1):
                            partial_name = '.'.join(module_parts[:i])
                            if partial_name in self.module_mapping:
                                self._add_edge(module_name, partial_name, DependencyType.FROM_IMPORT, file_path, node.lineno)
                                break
                
                # 处理函数调用，可能发现间接引用
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        # 检查是否是另一个模块中的名称
                        if hasattr(node.func, 'id') and node.func.id[0].isupper():
                            pass  # 类名暂时跳过
        except Exception:
            pass
    
    def _add_edge(self, from_mod: str, to_mod: str, dep_type: DependencyType, file_path: str, line_no: int):
        """添加依赖边"""
        if from_mod == to_mod:
            return
        
        dependency = Dependency(
            from_module=from_mod,
            to_module=to_mod,
            dep_type=dep_type,
            line_number=line_no,
            file_path=file_path
        )
        self.graph.edges.append(dependency)
        
        if to_mod not in self.graph.adjacency[from_mod]:
            self.graph.adjacency[from_mod].append(to_mod)
        
        if from_mod not in self.graph.reverse_adjacency[to_mod]:
            self.graph.reverse_adjacency[to_mod].append(from_mod)


class CycleDetector:
    """循环依赖检测器 - 使用 Tarjan 算法"""
    
    def detect_cycles(self, graph: DependencyGraph) -> List[CyclePath]:
        """检测图中的所有循环"""
        cycles: List[CyclePath] = []
        index = 0
        indices: Dict[str, int] = {}
        lowlink: Dict[str, int] = {}
        on_stack: Dict[str, bool] = {}
        stack: List[str] = []
        
        for node in graph.nodes:
            if node not in indices:
                self._tarjan(
                    node, graph, index, indices, lowlink, on_stack, stack, cycles
                )
        
        return cycles
    
    def _tarjan(self, node: str, graph: DependencyGraph, index: int, 
                indices: Dict[str, int], lowlink: Dict[str, int],
                on_stack: Dict[str, bool], stack: List[str],
                cycles: List[CyclePath]):
        """Tarjan 强连通分量算法"""
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack[node] = True
        
        if node in graph.adjacency:
            for neighbor in graph.adjacency[node]:
                if neighbor not in indices:
                    index = self._tarjan(
                        neighbor, graph, index, indices, lowlink, on_stack, stack, cycles
                    )
                    lowlink[node] = min(lowlink[node], lowlink[neighbor])
                elif on_stack.get(neighbor, False):
                    lowlink[node] = min(lowlink[node], indices[neighbor])
        
        if lowlink[node] == indices[node]:
            scc: List[str] = []
            while True:
                member = stack.pop()
                on_stack[member] = False
                scc.append(member)
                if member == node:
                    break
            
            if len(scc) > 1:
                cycle_path = self._extract_cycle_from_scc(scc, graph)
                if cycle_path:
                    cycles.append(cycle_path)
        
        return index
    
    def _extract_cycle_from_scc(self, scc: List[str], graph: DependencyGraph) -> Optional[CyclePath]:
        """从强连通分量中提取具体的循环路径"""
        if len(scc) < 2:
            return None
        
        # 尝试寻找简单路径
        start_node = scc[0]
        visited: Set[str] = set()
        path: List[str] = []
        
        def dfs(current: str) -> Optional[List[str]]:
            if current in path:
                cycle_start = path.index(current)
                return path[cycle_start:]
            if current in visited:
                return None
            
            visited.add(current)
            path.append(current)
            
            if current in graph.adjacency:
                for neighbor in graph.adjacency[current]:
                    if neighbor in scc:
                        result = dfs(neighbor)
                        if result:
                            return result
            
            path.pop()
            return None
        
        cycle = dfs(start_node)
        
        if not cycle:
            # 如果找不到简单路径，直接使用 SCC
            cycle = scc + [scc[0]]
        
        cycle_path = CyclePath(
            modules=cycle,
            severity=self._calculate_severity(cycle),
            impact=self._calculate_impact(cycle)
        )
        
        return cycle_path
    
    def _calculate_severity(self, cycle: List[str]) -> str:
        """计算循环严重程度"""
        length = len(cycle)
        if length <= 2:
            return "critical"
        elif length <= 4:
            return "high"
        elif length <= 6:
            return "medium"
        return "low"
    
    def _calculate_impact(self, cycle: List[str]) -> str:
        """计算循环影响"""
        if len(cycle) <= 2:
            return "模块间紧密耦合，难以重构"
        elif len(cycle) <= 4:
            return "中等耦合，需要谨慎处理"
        return "轻度耦合，影响较小"


class CycleBreaker:
    """循环依赖斩断方案生成器"""
    
    def generate_suggestions(self, cycle: CyclePath, graph: DependencyGraph) -> List[str]:
        """生成斩断方案建议"""
        suggestions: List[str] = []
        
        # 按模块依赖数量排序，找出最佳断点
        break_points = self._find_best_break_points(cycle.modules, graph)
        
        for point in break_points:
            from_mod, to_mod = point
            suggestions.append(f"建议断开 {from_mod} 对 {to_mod} 的依赖")
            suggestions.append(f"  方案 1: 将 {to_mod} 中被 {from_mod} 使用的功能提取到独立模块")
            suggestions.append(f"  方案 2: 使用依赖注入模式，降低直接依赖")
            suggestions.append(f"  方案 3: 使用事件驱动或观察者模式，解耦两者")
        
        return suggestions
    
    def _find_best_break_points(self, cycle: List[str], graph: DependencyGraph) -> List[Tuple[str, str]]:
        """找出最佳的断点位置"""
        break_points: List[Tuple[str, str]] = []
        
        for i in range(len(cycle) - 1):
            from_mod = cycle[i]
            to_mod = cycle[i + 1]
            
            # 计算该边的权重（影响范围）
            weight = self._calculate_edge_weight(from_mod, to_mod, graph)
            break_points.append((from_mod, to_mod, weight))
        
        # 按权重排序（越小越容易断）
        break_points.sort(key=lambda x: x[2])
        
        return [(bp[0], bp[1]) for bp in break_points]
    
    def _calculate_edge_weight(self, from_mod: str, to_mod: str, graph: DependencyGraph) -> int:
        """计算边的权重（影响范围）"""
        weight = 0
        
        # 计算该边的使用频率
        for dep in graph.edges:
            if dep.from_module == from_mod and dep.to_module == to_mod:
                weight += 1
        
        # 增加反向依赖权重（安全访问）
        if hasattr(graph, 'reverse_adjacency'):
            if to_mod in graph.reverse_adjacency and from_mod in graph.reverse_adjacency[to_mod]:
                weight += 10
        
        return weight


class CycleReporter:
    """循环依赖报告生成器"""
    
    def generate_text_report(self, report: CycleReport) -> str:
        """生成文本报告"""
        lines: List[str] = []
        lines.append("=" * 80)
        lines.append("CYCLE DEPENDENCY DETECTION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {report.generated_at.isoformat()}")
        lines.append(f"Total Cycles Found: {report.total_cycles}")
        lines.append("")
        
        for i, cycle in enumerate(report.cycles, 1):
            lines.append(f"=== Cycle {i} (Severity: {cycle.severity}) ===")
            lines.append(f"  Path: {' -> '.join(cycle.modules)}")
            lines.append(f"  Impact: {cycle.impact}")
            
            if cycle.suggestions:
                lines.append("  Suggestions:")
                for suggestion in cycle.suggestions:
                    lines.append(f"    - {suggestion}")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_json_report(self, report: CycleReport) -> Dict[str, Any]:
        """生成 JSON 报告"""
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "total_cycles": report.total_cycles,
            "cycles": [
                {
                    "cycle_id": c.cycle_id,
                    "modules": c.modules,
                    "severity": c.severity,
                    "impact": c.impact,
                    "suggestions": c.suggestions
                }
                for c in report.cycles
            ]
        }


class CycleDependencyAnalyzer:
    """循环依赖分析器 - 整合所有功能"""
    
    def __init__(self, root_path: str = ""):
        self.root_path = root_path
        self.builder = DependencyGraphBuilder(root_path)
        self.detector = CycleDetector()
        self.breaker = CycleBreaker()
        self.reporter = CycleReporter()
    
    def analyze_directory(self, directory: str) -> CycleReport:
        """分析目录中的循环依赖"""
        graph = self.builder.build_from_directory(directory)
        return self._generate_report(graph)
    
    def analyze_code(self, source_code: str, module_name: str) -> CycleReport:
        """分析代码（用于测试）"""
        graph = self.builder.build_from_code(source_code, module_name)
        return self._generate_report(graph)
    
    def _generate_report(self, graph: DependencyGraph) -> CycleReport:
        """生成完整报告"""
        cycles = self.detector.detect_cycles(graph)
        
        # 为每个循环添加建议
        for cycle in cycles:
            cycle.suggestions = self.breaker.generate_suggestions(cycle, graph)
        
        report = CycleReport(
            total_cycles=len(cycles),
            cycles=cycles,
            dependency_graph=graph
        )
        
        return report


_global_analyzer: Optional[CycleDependencyAnalyzer] = None


def get_cycle_dependency_analyzer(root_path: str = "") -> CycleDependencyAnalyzer:
    """获取全局循环依赖分析器"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = CycleDependencyAnalyzer(root_path)
    return _global_analyzer


def reset_cycle_dependency_analyzer() -> None:
    """重置循环依赖分析器"""
    global _global_analyzer
    _global_analyzer = None
