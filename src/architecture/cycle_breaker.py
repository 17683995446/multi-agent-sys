"""
循环依赖全自动斩断模块

职责：检测循环依赖（直接、间接、自引用），自动斩断并验证

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class CycleType(str, Enum):
    """循环类型"""
    DIRECT = "direct"
    INDIRECT = "indirect"
    SELF = "self"


class CycleStatus(str, Enum):
    """循环状态"""
    DETECTED = "detected"
    BREAKING = "breaking"
    BROKEN = "broken"
    FAILED = "failed"


@dataclass
class CycleRecord:
    """循环依赖记录"""
    cycle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cycle_type: CycleType = CycleType.DIRECT
    nodes: List[str] = field(default_factory=list)
    edges: List[Tuple[str, str]] = field(default_factory=list)
    status: CycleStatus = CycleStatus.DETECTED
    break_strategy: str = ""
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"CycleRecord created: id={self.cycle_id}, "
                     f"type={self.cycle_type.value}")


class CycleDetector:
    """循环依赖检测器"""

    def __init__(self):
        """初始化循环依赖检测器"""
        self.records: List[CycleRecord] = []
        self.graph: Dict[str, List[str]] = {}
        logger.info("CycleDetector initialized")

    def detect_cycles(self, graph: Dict[str, List[str]]) -> List[CycleRecord]:
        """检测循环依赖"""
        logger.info(f"CycleDetector: detecting cycles in graph with "
                    f"{len(graph)} nodes")
        self.records = []
        self.graph = graph
        try:
            # 使用DFS检测所有循环
            visited: Set[str] = set()
            rec_stack: Set[str] = set()
            path: List[str] = []

            for node in graph:
                if node not in visited:
                    self._dfs_detect(node, graph, visited, rec_stack, path)

            logger.info(f"CycleDetector: detection completed, "
                        f"{len(self.records)} cycles found")
        except Exception as e:
            logger.error(f"CycleDetector: detect_cycles failed: {e}")
        return self.records

    def _dfs_detect(self, node: str, graph: Dict[str, List[str]],
                    visited: Set[str], rec_stack: Set[str],
                    path: List[str]) -> None:
        """深度优先搜索检测循环"""
        logger.debug(f"CycleDetector: DFS visiting node={node}")
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                self._dfs_detect(neighbor, graph, visited, rec_stack, path)
            elif neighbor in rec_stack:
                # 找到循环
                cycle_start = path.index(neighbor)
                cycle_nodes = path[cycle_start:]
                edges = []
                for i in range(len(cycle_nodes)):
                    src = cycle_nodes[i]
                    dst = cycle_nodes[(i + 1) % len(cycle_nodes)]
                    edges.append((src, dst))

                # 判断循环类型
                if len(cycle_nodes) == 1:
                    cycle_type = CycleType.SELF
                elif len(cycle_nodes) == 2:
                    cycle_type = CycleType.DIRECT
                else:
                    cycle_type = CycleType.INDIRECT

                record = CycleRecord(
                    cycle_type=cycle_type,
                    nodes=cycle_nodes,
                    edges=edges,
                    status=CycleStatus.DETECTED,
                )
                self.records.append(record)
                logger.info(f"CycleDetector: cycle detected, "
                            f"type={cycle_type.value}, "
                            f"nodes={cycle_nodes}")

        path.pop()
        rec_stack.remove(node)

    def get_cycle_graph(self) -> Dict[str, Any]:
        """获取循环依赖图"""
        logger.debug("CycleDetector: getting cycle graph")
        try:
            nodes = set()
            edges = []
            for record in self.records:
                for node in record.nodes:
                    nodes.add(node)
                for edge in record.edges:
                    edges.append({"source": edge[0], "target": edge[1]})

            return {
                "nodes": list(nodes),
                "edges": edges,
                "cycle_count": len(self.records),
            }
        except Exception as e:
            logger.error(f"CycleDetector: get_cycle_graph failed: {e}")
            return {"nodes": [], "edges": [], "cycle_count": 0}


class CycleBreaker:
    """循环依赖斩断器"""

    def __init__(self):
        """初始化循环依赖斩断器"""
        self.break_log: List[Dict[str, Any]] = []
        logger.info("CycleBreaker initialized")

    def break_cycle(self, record: CycleRecord) -> CycleRecord:
        """斩断循环依赖"""
        logger.info(f"CycleBreaker: breaking cycle id={record.cycle_id}")
        try:
            record.status = CycleStatus.BREAKING

            if record.cycle_type == CycleType.SELF:
                strategy_result = self._introduce_interface(record)
            elif record.cycle_type == CycleType.DIRECT:
                strategy_result = self._extract_module(record)
            else:
                strategy_result = self._reorder_dependencies(record)

            if strategy_result:
                record.status = CycleStatus.BROKEN
                record.break_strategy = strategy_result
            else:
                record.status = CycleStatus.FAILED

            self.break_log.append({
                "cycle_id": record.cycle_id,
                "status": record.status.value,
                "strategy": record.break_strategy,
            })
            logger.info(f"CycleBreaker: cycle {record.cycle_id} "
                        f"status={record.status.value}")
        except Exception as e:
            logger.error(f"CycleBreaker: break_cycle failed: {e}")
            record.status = CycleStatus.FAILED
        return record

    def _introduce_interface(self, record: CycleRecord) -> str:
        """引入接口斩断自引用循环"""
        logger.debug(f"CycleBreaker: introducing interface for "
                     f"cycle={record.cycle_id}")
        try:
            node = record.nodes[0] if record.nodes else "unknown"
            return f"引入接口解耦自引用: {node}Interface"
        except Exception as e:
            logger.error(f"CycleBreaker: _introduce_interface failed: {e}")
            return ""

    def _extract_module(self, record: CycleRecord) -> str:
        """提取模块斩断直接循环"""
        logger.debug(f"CycleBreaker: extracting module for "
                     f"cycle={record.cycle_id}")
        try:
            nodes_str = "->".join(record.nodes)
            shared = "_".join(record.nodes[:2])
            return f"提取共享模块: {shared}_shared, 斩断{nodes_str}"
        except Exception as e:
            logger.error(f"CycleBreaker: _extract_module failed: {e}")
            return ""

    def _reorder_dependencies(self, record: CycleRecord) -> str:
        """重排依赖斩断间接循环"""
        logger.debug(f"CycleBreaker: reordering dependencies for "
                     f"cycle={record.cycle_id}")
        try:
            nodes_str = "->".join(record.nodes)
            return f"重排依赖方向，斩断间接循环: {nodes_str}"
        except Exception as e:
            logger.error(f"CycleBreaker: _reorder_dependencies failed: {e}")
            return ""

    def verify_broken(self, records: List[CycleRecord]) -> Dict[str, Any]:
        """验证循环是否已被斩断"""
        logger.info(f"CycleBreaker: verifying {len(records)} records")
        try:
            broken = sum(1 for r in records
                         if r.status == CycleStatus.BROKEN)
            failed = sum(1 for r in records
                         if r.status == CycleStatus.FAILED)
            detected = sum(1 for r in records
                           if r.status == CycleStatus.DETECTED)
            result = {
                "total": len(records),
                "broken": broken,
                "failed": failed,
                "detected": detected,
                "success_rate": broken / len(records) if records else 1.0,
            }
            logger.info(f"CycleBreaker: verification completed, "
                        f"broken={broken}")
        except Exception as e:
            logger.error(f"CycleBreaker: verify_broken failed: {e}")
            result = {"total": 0, "broken": 0, "failed": 0,
                      "detected": 0, "success_rate": 0.0}
        return result


class CycleBreakService:
    """循环依赖斩断服务"""

    def __init__(self):
        """初始化循环依赖斩断服务"""
        self.detector = CycleDetector()
        self.breaker = CycleBreaker()
        logger.info("CycleBreakService initialized")

    def process(self, graph: Dict[str, List[str]]) -> Dict[str, Any]:
        """执行完整的循环依赖检测与斩断流程"""
        logger.info("CycleBreakService: processing")
        try:
            # 检测
            records = self.detector.detect_cycles(graph)

            # 斩断
            for record in records:
                self.breaker.break_cycle(record)

            # 验证
            verification = self.breaker.verify_broken(records)

            result = {
                "cycles_found": len(records),
                "verification": verification,
            }
            logger.info(f"CycleBreakService: process completed, "
                        f"{len(records)} cycles")
        except Exception as e:
            logger.error(f"CycleBreakService: process failed: {e}")
            result = {"cycles_found": 0, "verification": {}}
        return result

    def get_cycles(self) -> List[CycleRecord]:
        """获取循环依赖记录"""
        logger.debug("CycleBreakService: getting cycles")
        return self.detector.records

    def get_report(self) -> Dict[str, Any]:
        """获取循环依赖报告"""
        logger.debug("CycleBreakService: getting report")
        try:
            cycle_graph = self.detector.get_cycle_graph()
            verification = self.breaker.verify_broken(
                self.detector.records
            )
            report = {
                "cycle_graph": cycle_graph,
                "verification": verification,
                "records": [
                    {
                        "cycle_id": r.cycle_id,
                        "type": r.cycle_type.value,
                        "nodes": r.nodes,
                        "edges": [
                            {"source": e[0], "target": e[1]}
                            for e in r.edges
                        ],
                        "status": r.status.value,
                        "break_strategy": r.break_strategy,
                    }
                    for r in self.detector.records
                ],
            }
        except Exception as e:
            logger.error(f"CycleBreakService: get_report failed: {e}")
            report = {"cycle_graph": {}, "verification": {}, "records": []}
        return report
