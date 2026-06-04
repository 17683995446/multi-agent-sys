"""
DAG任务调度器
职责：DAG构建、环检测、拓扑排序、节点执行调度
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class DAGNodeStatus(str, Enum):
    """DAG节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    """DAG节点"""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    task_fn: Optional[Callable] = None
    status: DAGNodeStatus = DAGNodeStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DAGEdge:
    """DAG边"""
    from_node: str = ""
    to_node: str = ""
    condition: Optional[str] = None


class DAG:
    """有向无环图"""

    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.edges: List[DAGEdge] = []
        logger.info("DAG初始化完成")

    def add_node(self, node: DAGNode) -> bool:
        """添加节点"""
        if node.node_id in self.nodes:
            logger.warning(f"节点已存在: node_id={node.node_id}")
            return False
        self.nodes[node.node_id] = node
        logger.info(f"添加节点: node_id={node.node_id}, name={node.name}")
        return True

    def add_edge(self, from_node: str, to_node: str, condition: Optional[str] = None) -> bool:
        """添加边"""
        if from_node not in self.nodes or to_node not in self.nodes:
            logger.warning(f"添加边失败: 节点不存在, from={from_node}, to={to_node}")
            return False
        edge = DAGEdge(from_node=from_node, to_node=to_node, condition=condition)
        self.edges.append(edge)
        if to_node not in self.nodes[from_node].dependencies:
            self.nodes[from_node].dependencies.append(to_node)
        logger.info(f"添加边: from={from_node}, to={to_node}")
        return True

    def validate_acyclic(self) -> bool:
        """验证无环（检测循环）"""
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            recursion_stack.add(node_id)
            successors = self.get_successors(node_id)
            for succ in successors:
                if succ not in visited:
                    if dfs(succ):
                        return True
                elif succ in recursion_stack:
                    return True
            recursion_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    logger.warning("检测到循环依赖")
                    return False

        logger.info("DAG验证通过: 无循环依赖")
        return True

    def get_roots(self) -> List[str]:
        """获取根节点（无前驱的节点）"""
        has_predecessor: Set[str] = set()
        for edge in self.edges:
            has_predecessor.add(edge.to_node)
        roots = [nid for nid in self.nodes if nid not in has_predecessor]
        logger.debug(f"获取根节点: roots={roots}")
        return roots

    def get_leaves(self) -> List[str]:
        """获取叶子节点（无后继的节点）"""
        has_successor: Set[str] = set()
        for edge in self.edges:
            has_successor.add(edge.from_node)
        leaves = [nid for nid in self.nodes if nid not in has_successor]
        logger.debug(f"获取叶子节点: leaves={leaves}")
        return leaves

    def topological_sort(self) -> Optional[List[str]]:
        """拓扑排序"""
        if not self.validate_acyclic():
            logger.warning("拓扑排序失败: 存在循环依赖")
            return None

        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        for edge in self.edges:
            in_degree[edge.to_node] = in_degree.get(edge.to_node, 0) + 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for succ in self.get_successors(node):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        logger.info(f"拓扑排序完成: order={result}")
        return result

    def get_successors(self, node_id: str) -> List[str]:
        """获取后继节点"""
        successors = [edge.to_node for edge in self.edges if edge.from_node == node_id]
        logger.debug(f"获取后继节点: node_id={node_id}, successors={successors}")
        return successors

    def get_predecessors(self, node_id: str) -> List[str]:
        """获取前驱节点"""
        predecessors = [edge.from_node for edge in self.edges if edge.to_node == node_id]
        logger.debug(f"获取前驱节点: node_id={node_id}, predecessors={predecessors}")
        return predecessors


class DAGScheduler:
    """DAG调度器"""

    def __init__(self, dag: Optional[DAG] = None):
        self.dag = dag or DAG()
        logger.info("DAGScheduler初始化完成")

    def execute(self) -> Dict[str, Any]:
        """执行DAG（按拓扑顺序运行节点，检查依赖）"""
        order = self.dag.topological_sort()
        if order is None:
            logger.error("执行失败: 无法获取拓扑排序")
            return {"success": False, "error": "存在循环依赖，无法执行"}

        results = {}
        failed = False
        for node_id in order:
            if failed:
                # 将下游节点标记为SKIPPED
                self.dag.nodes[node_id].status = DAGNodeStatus.SKIPPED
                results[node_id] = {"success": False, "error": "上游节点失败，跳过执行"}
                logger.info(f"跳过节点: node_id={node_id}, 原因=上游失败")
                continue
            result = self.execute_node(node_id)
            results[node_id] = result
            if self.dag.nodes[node_id].status == DAGNodeStatus.FAILED:
                logger.warning(f"节点执行失败，停止调度: node_id={node_id}")
                failed = True

        logger.info(f"DAG执行完成: nodes={len(results)}")
        return {"success": True, "results": results}

    def execute_node(self, node_id: str) -> Dict[str, Any]:
        """执行单个节点"""
        if node_id not in self.dag.nodes:
            logger.warning(f"执行节点失败: 节点不存在, node_id={node_id}")
            return {"success": False, "error": "节点不存在"}

        node = self.dag.nodes[node_id]

        # 检查前驱节点是否都已完成
        predecessors = self.dag.get_predecessors(node_id)
        for pred_id in predecessors:
            if pred_id in self.dag.nodes and self.dag.nodes[pred_id].status != DAGNodeStatus.SUCCESS:
                node.status = DAGNodeStatus.SKIPPED
                logger.info(f"节点跳过（前驱未完成）: node_id={node_id}")
                return {"success": False, "status": "skipped", "reason": "前驱节点未完成"}

        node.status = DAGNodeStatus.RUNNING
        logger.info(f"开始执行节点: node_id={node_id}, name={node.name}")

        try:
            if node.task_fn is not None:
                result = node.task_fn()
                node.status = DAGNodeStatus.SUCCESS
                logger.info(f"节点执行成功: node_id={node_id}")
                return {"success": True, "result": result}
            else:
                node.status = DAGNodeStatus.SUCCESS
                logger.info(f"节点执行成功（无任务函数）: node_id={node_id}")
                return {"success": True, "result": None}
        except Exception as e:
            node.status = DAGNodeStatus.FAILED
            logger.error(f"节点执行失败: node_id={node_id}, error={e}")
            return {"success": False, "error": str(e)}
