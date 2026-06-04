from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from src.core import get_logger, MAESError


logger = get_logger("dag_validator")


class DependencyViolationType(Enum):
    """依赖违规类型"""
    CIRCULAR_DEPENDENCY = "circular_dependency"
    REVERSE_DEPENDENCY = "reverse_dependency"
    UNDECLARED_DEPENDENCY = "undeclared_dependency"


@dataclass
class DependencyViolation:
    """依赖违规记录"""
    violation_type: DependencyViolationType
    nodes: List[str]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.violation_type.value}] {self.message} (nodes: {self.nodes})"


class DAGError(MAESError):
    """DAG相关错误"""
    def __init__(self, message: str, violations: Optional[List[DependencyViolation]] = None, details: Optional[Dict] = None):
        super().__init__(message, code="E010", details=details)
        self.violations = violations or []


class DirectedAcyclicGraph:
    """有向无环图（DAG）"""

    def __init__(self):
        self.graph: Dict[str, Set[str]] = {}
        self.in_degree: Dict[str, int] = {}
        self.all_nodes: Set[str] = set()

    def add_node(self, node: str) -> None:
        """添加节点"""
        if node not in self.graph:
            self.graph[node] = set()
            self.in_degree[node] = 0
            self.all_nodes.add(node)

    def add_edge(self, from_node: str, to_node: str) -> None:
        """添加边（from_node -> to_node）"""
        self.add_node(from_node)
        self.add_node(to_node)
        
        if to_node not in self.graph[from_node]:
            self.graph[from_node].add(to_node)
            self.in_degree[to_node] += 1

    def has_cycle(self) -> Tuple[bool, Optional[List[str]]]:
        """
        检测是否存在环
        返回: (是否有环, 环的节点列表如果存在)
        """
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> Optional[List[str]]:
            if node not in visited:
                visited.add(node)
                recursion_stack.add(node)
                path.append(node)

                for neighbor in self.graph.get(node, []):
                    if neighbor not in visited:
                        cycle = dfs(neighbor)
                        if cycle:
                            return cycle
                    elif neighbor in recursion_stack:
                        # 找到环
                        idx = path.index(neighbor)
                        return path[idx:] + [neighbor]

            if node in recursion_stack:
                recursion_stack.remove(node)
                path.pop()
            return None

        for node in self.all_nodes:
            cycle = dfs(node)
            if cycle:
                return True, cycle
        return False, None

    def topological_sort(self) -> Optional[List[str]]:
        """
        拓扑排序
        返回: 拓扑排序后的节点列表，如果有环则返回None
        """
        has_cycle, cycle = self.has_cycle()
        if has_cycle:
            logger.warning(f"检测到循环依赖: {cycle}")
            return None

        temp_in_degree = self.in_degree.copy()
        queue = deque([node for node in self.all_nodes if temp_in_degree[node] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in self.graph.get(node, []):
                temp_in_degree[neighbor] -= 1
                if temp_in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result if len(result) == len(self.all_nodes) else None

    def get_dependencies(self, node: str) -> Set[str]:
        """获取节点的依赖（节点指向的其他节点）"""
        return self.graph.get(node, set())

    def get_dependents(self, node: str) -> Set[str]:
        """获取依赖该节点的其他节点"""
        dependents = set()
        for n, neighbors in self.graph.items():
            if node in neighbors:
                dependents.add(n)
        return dependents


class LayeredDAGValidator:
    """分层DAG单向依赖校验器"""

    def __init__(self, layer_order: Optional[List[str]] = None):
        """
        初始化分层DAG校验器
        layer_order: 层级顺序，前面的层级不能依赖后面的层级
        """
        self.layer_order = layer_order or ["input_layer", "scheduler", "agents", "executors"]
        self.dag = DirectedAcyclicGraph()
        self.node_layers: Dict[str, str] = {}
        self.violations: List[DependencyViolation] = []

    def register_node(self, node: str, layer: str) -> None:
        """注册节点及其所属层级"""
        if layer not in self.layer_order:
            logger.warning(f"未知层级: {layer}，已知层级: {self.layer_order}")
        self.node_layers[node] = layer
        self.dag.add_node(node)

    def add_dependency(self, from_node: str, to_node: str) -> None:
        """
        添加依赖关系
        from_node 依赖 to_node，即 from_node -> to_node
        """
        self.dag.add_edge(from_node, to_node)

    def validate(self, strict: bool = True) -> Tuple[bool, List[DependencyViolation]]:
        """
        执行完整验证
        strict: 是否严格模式，发现违规立即抛出异常
        返回: (是否通过, 违规列表)
        """
        self.violations = []
        
        # 1. 检测循环依赖
        self._check_circular_dependencies()
        
        # 2. 检测单向依赖规则
        self._check_layer_dependencies()
        
        # 报告违规
        if self.violations:
            self._report_violations()
            if strict:
                raise DAGError("DAG依赖校验失败", violations=self.violations)
        
        is_valid = len(self.violations) == 0
        return is_valid, self.violations

    def _check_circular_dependencies(self) -> None:
        """检测循环依赖"""
        has_cycle, cycle = self.dag.has_cycle()
        if has_cycle and cycle:
            violation = DependencyViolation(
                violation_type=DependencyViolationType.CIRCULAR_DEPENDENCY,
                nodes=cycle,
                message=f"检测到循环依赖: {' -> '.join(cycle)}",
                details={"cycle": cycle}
            )
            self.violations.append(violation)

    def _check_layer_dependencies(self) -> None:
        """检测层级单向依赖规则"""
        layer_index = {layer: idx for idx, layer in enumerate(self.layer_order)}
        
        for from_node, to_nodes in self.dag.graph.items():
            from_layer = self.node_layers.get(from_node)
            if from_layer not in layer_index:
                continue
                
            for to_node in to_nodes:
                to_layer = self.node_layers.get(to_node)
                if to_layer not in layer_index:
                    continue
                    
                # 检查是否违反单向依赖（高层级不能依赖低层级）
                if layer_index[from_layer] > layer_index[to_layer]:
                    violation = DependencyViolation(
                        violation_type=DependencyViolationType.REVERSE_DEPENDENCY,
                        nodes=[from_node, to_node],
                        message=f"层级依赖违规: {from_node}({from_layer}) 不能依赖 {to_node}({to_layer})",
                        details={
                            "from_node": from_node,
                            "from_layer": from_layer,
                            "to_node": to_node,
                            "to_layer": to_layer
                        }
                    )
                    self.violations.append(violation)

    def _report_violations(self) -> None:
        """报告违规情况"""
        logger.error(f"DAG校验发现 {len(self.violations)} 个违规:")
        for i, violation in enumerate(self.violations, 1):
            logger.error(f"  {i}. {violation}")

    def get_topological_order(self) -> Optional[List[str]]:
        """获取拓扑排序"""
        return self.dag.topological_sort()

    def get_violations(self) -> List[DependencyViolation]:
        """获取所有违规"""
        return self.violations


class RuntimeDependencyMonitor:
    """运行时依赖监视器"""

    def __init__(self, validator: LayeredDAGValidator):
        self.validator = validator
        self.runtime_dependencies: List[Tuple[str, str]] = []
        self.logger = get_logger("runtime_monitor")

    def record_dependency(self, from_node: str, to_node: str) -> None:
        """记录运行时依赖"""
        self.runtime_dependencies.append((from_node, to_node))
        
        # 立即检查
        try:
            temp_validator = LayeredDAGValidator(self.validator.layer_order)
            # 复制节点和层级
            for node, layer in self.validator.node_layers.items():
                temp_validator.register_node(node, layer)
            # 复制已有的依赖
            for f_node, t_nodes in self.validator.dag.graph.items():
                for t_node in t_nodes:
                    temp_validator.add_dependency(f_node, t_node)
            # 添加新依赖
            temp_validator.add_dependency(from_node, to_node)
            # 验证
            temp_validator.validate(strict=True)
            self.logger.debug(f"运行时依赖验证通过: {from_node} -> {to_node}")
        except DAGError as e:
            self.logger.error(f"运行时依赖违规: {e}")
            raise


def create_module_dependency_validator() -> LayeredDAGValidator:
    """
    创建模块依赖验证器
    基于项目四层架构：input_layer -> scheduler -> agents -> executors
    """
    validator = LayeredDAGValidator([
        "input_layer",
        "scheduler",
        "agents",
        "executors",
        "architecture"
    ])
    
    # 注册架构模块
    validator.register_node("input_layer", "input_layer")
    validator.register_node("scheduler", "scheduler")
    validator.register_node("agents", "agents")
    validator.register_node("executors", "executors")
    validator.register_node("architecture", "architecture")
    
    return validator
