"""
阶段52验收测试：DAG任务调度器
"""

import pytest
from src.architecture.dag_scheduler import (
    DAGNodeStatus,
    DAGNode,
    DAGEdge,
    DAG,
    DAGScheduler,
)


class TestDAGNodeStatus:
    """测试DAG节点状态枚举"""

    def test_status_values(self):
        """测试节点状态枚举值"""
        assert DAGNodeStatus.PENDING.value == "pending"
        assert DAGNodeStatus.RUNNING.value == "running"
        assert DAGNodeStatus.SUCCESS.value == "success"
        assert DAGNodeStatus.FAILED.value == "failed"
        assert DAGNodeStatus.SKIPPED.value == "skipped"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(DAGNodeStatus)
        assert len(statuses) == 5


class TestDAGNode:
    """测试DAG节点"""

    def test_default_creation(self):
        """测试默认创建"""
        node = DAGNode()
        assert node.node_id != ""
        assert node.name == ""
        assert node.task_fn is None
        assert node.status == DAGNodeStatus.PENDING
        assert node.dependencies == []
        assert node.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        def my_task():
            return 42

        node = DAGNode(name="任务1", task_fn=my_task, metadata={"key": "value"})
        assert node.name == "任务1"
        assert node.task_fn is not None
        assert node.metadata["key"] == "value"


class TestDAGEdge:
    """测试DAG边"""

    def test_default_creation(self):
        """测试默认创建"""
        edge = DAGEdge()
        assert edge.from_node == ""
        assert edge.to_node == ""
        assert edge.condition is None

    def test_custom_creation(self):
        """测试自定义创建"""
        edge = DAGEdge(from_node="A", to_node="B", condition="x > 0")
        assert edge.from_node == "A"
        assert edge.to_node == "B"
        assert edge.condition == "x > 0"


class TestDAG:
    """测试DAG"""

    def test_add_node(self):
        """测试添加节点"""
        dag = DAG()
        node = DAGNode(node_id="n1", name="节点1")
        result = dag.add_node(node)
        assert result is True
        assert "n1" in dag.nodes

    def test_add_node_duplicate(self):
        """测试添加重复节点"""
        dag = DAG()
        node1 = DAGNode(node_id="n1", name="节点1")
        node2 = DAGNode(node_id="n1", name="节点1副本")
        dag.add_node(node1)
        result = dag.add_node(node2)
        assert result is False

    def test_add_edge(self):
        """测试添加边"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        result = dag.add_edge("n1", "n2")
        assert result is True
        assert len(dag.edges) == 1

    def test_add_edge_nonexistent_node(self):
        """测试添加边到不存在的节点"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        result = dag.add_edge("n1", "n999")
        assert result is False

    def test_validate_acyclic_no_cycle(self):
        """测试无环验证"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        dag.add_node(DAGNode(node_id="n3"))
        dag.add_edge("n1", "n2")
        dag.add_edge("n2", "n3")
        assert dag.validate_acyclic() is True

    def test_validate_acyclic_with_cycle(self):
        """测试有环验证"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        dag.add_node(DAGNode(node_id="n3"))
        dag.add_edge("n1", "n2")
        dag.add_edge("n2", "n3")
        dag.add_edge("n3", "n1")
        assert dag.validate_acyclic() is False

    def test_get_roots(self):
        """测试获取根节点"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        dag.add_node(DAGNode(node_id="n3"))
        dag.add_edge("n1", "n2")
        dag.add_edge("n1", "n3")
        roots = dag.get_roots()
        assert "n1" in roots
        assert "n2" not in roots

    def test_get_leaves(self):
        """测试获取叶子节点"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        dag.add_node(DAGNode(node_id="n3"))
        dag.add_edge("n1", "n2")
        dag.add_edge("n1", "n3")
        leaves = dag.get_leaves()
        assert "n2" in leaves
        assert "n3" in leaves
        assert "n1" not in leaves

    def test_topological_sort(self):
        """测试拓扑排序"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        dag.add_node(DAGNode(node_id="n3"))
        dag.add_edge("n1", "n2")
        dag.add_edge("n2", "n3")
        order = dag.topological_sort()
        assert order is not None
        assert order.index("n1") < order.index("n2")
        assert order.index("n2") < order.index("n3")

    def test_topological_sort_cyclic(self):
        """测试有环图拓扑排序"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        dag.add_edge("n1", "n2")
        dag.add_edge("n2", "n1")
        order = dag.topological_sort()
        assert order is None

    def test_get_successors(self):
        """测试获取后继节点"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        dag.add_node(DAGNode(node_id="n3"))
        dag.add_edge("n1", "n2")
        dag.add_edge("n1", "n3")
        successors = dag.get_successors("n1")
        assert "n2" in successors
        assert "n3" in successors

    def test_get_predecessors(self):
        """测试获取前驱节点"""
        dag = DAG()
        dag.add_node(DAGNode(node_id="n1"))
        dag.add_node(DAGNode(node_id="n2"))
        dag.add_edge("n1", "n2")
        predecessors = dag.get_predecessors("n2")
        assert "n1" in predecessors
        assert predecessors == dag.get_predecessors("n1") or "n1" not in dag.get_predecessors("n1")


class TestDAGScheduler:
    """测试DAG调度器"""

    def test_execute_simple(self):
        """测试简单执行"""
        dag = DAG()
        results = []

        def task1():
            results.append("task1")
            return "r1"

        def task2():
            results.append("task2")
            return "r2"

        n1 = DAGNode(node_id="n1", name="任务1", task_fn=task1)
        n2 = DAGNode(node_id="n2", name="任务2", task_fn=task2)
        dag.add_node(n1)
        dag.add_node(n2)
        dag.add_edge("n1", "n2")

        scheduler = DAGScheduler(dag)
        result = scheduler.execute()
        assert result["success"] is True
        assert results == ["task1", "task2"]

    def test_execute_parallel(self):
        """测试并行执行"""
        dag = DAG()
        results = []

        def task1():
            results.append("task1")
            return "r1"

        def task2():
            results.append("task2")
            return "r2"

        def task3():
            results.append("task3")
            return "r3"

        n1 = DAGNode(node_id="n1", name="任务1", task_fn=task1)
        n2 = DAGNode(node_id="n2", name="任务2", task_fn=task2)
        n3 = DAGNode(node_id="n3", name="任务3", task_fn=task3)
        dag.add_node(n1)
        dag.add_node(n2)
        dag.add_node(n3)
        dag.add_edge("n1", "n2")
        dag.add_edge("n1", "n3")

        scheduler = DAGScheduler(dag)
        result = scheduler.execute()
        assert result["success"] is True
        assert "task1" in results
        assert "task2" in results
        assert "task3" in results

    def test_execute_with_failure(self):
        """测试执行失败"""
        dag = DAG()

        def task_fail():
            raise RuntimeError("任务失败")

        n1 = DAGNode(node_id="n1", name="失败任务", task_fn=task_fail)
        n2 = DAGNode(node_id="n2", name="后续任务")
        dag.add_node(n1)
        dag.add_node(n2)
        dag.add_edge("n1", "n2")

        scheduler = DAGScheduler(dag)
        result = scheduler.execute()
        assert dag.nodes["n1"].status == DAGNodeStatus.FAILED
        assert dag.nodes["n2"].status == DAGNodeStatus.SKIPPED

    def test_execute_node_no_fn(self):
        """测试执行无任务函数的节点"""
        dag = DAG()
        n1 = DAGNode(node_id="n1", name="空任务")
        dag.add_node(n1)
        scheduler = DAGScheduler(dag)
        result = scheduler.execute_node("n1")
        assert result["success"] is True
        assert dag.nodes["n1"].status == DAGNodeStatus.SUCCESS

    def test_execute_node_nonexistent(self):
        """测试执行不存在的节点"""
        dag = DAG()
        scheduler = DAGScheduler(dag)
        result = scheduler.execute_node("nonexistent")
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
