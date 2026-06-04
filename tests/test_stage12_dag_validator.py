import pytest
from src.architecture import (
    DirectedAcyclicGraph,
    LayeredDAGValidator,
    RuntimeDependencyMonitor,
    DependencyViolation,
    DependencyViolationType,
    DAGError,
    create_module_dependency_validator
)


class TestDirectedAcyclicGraph:
    """测试DAG基础功能"""

    def test_add_node_and_edge(self):
        """测试添加节点和边"""
        dag = DirectedAcyclicGraph()
        dag.add_node("A")
        dag.add_node("B")
        dag.add_edge("A", "B")
        
        assert "A" in dag.all_nodes
        assert "B" in dag.all_nodes
        assert "B" in dag.graph["A"]

    def test_no_cycle(self):
        """测试无环图"""
        dag = DirectedAcyclicGraph()
        dag.add_edge("A", "B")
        dag.add_edge("B", "C")
        dag.add_edge("A", "C")
        
        has_cycle, cycle = dag.has_cycle()
        assert has_cycle is False
        assert cycle is None

    def test_has_cycle(self):
        """测试有环图"""
        dag = DirectedAcyclicGraph()
        dag.add_edge("A", "B")
        dag.add_edge("B", "C")
        dag.add_edge("C", "A")
        
        has_cycle, cycle = dag.has_cycle()
        assert has_cycle is True
        assert cycle is not None
        assert len(cycle) >= 3

    def test_topological_sort(self):
        """测试拓扑排序"""
        dag = DirectedAcyclicGraph()
        dag.add_edge("A", "B")
        dag.add_edge("B", "C")
        dag.add_edge("A", "C")
        
        result = dag.topological_sort()
        assert result is not None
        assert "A" in result
        assert "B" in result
        assert "C" in result
        assert result.index("A") < result.index("B")
        assert result.index("B") < result.index("C")

    def test_topological_sort_cyclic(self):
        """测试有环图的拓扑排序"""
        dag = DirectedAcyclicGraph()
        dag.add_edge("A", "B")
        dag.add_edge("B", "A")
        
        result = dag.topological_sort()
        assert result is None

    def test_get_dependencies(self):
        """测试获取依赖"""
        dag = DirectedAcyclicGraph()
        dag.add_edge("A", "B")
        dag.add_edge("A", "C")
        
        assert dag.get_dependencies("A") == {"B", "C"}
        assert dag.get_dependencies("B") == set()

    def test_get_dependents(self):
        """测试获取依赖者"""
        dag = DirectedAcyclicGraph()
        dag.add_edge("A", "B")
        dag.add_edge("C", "B")
        
        assert dag.get_dependents("B") == {"A", "C"}
        assert dag.get_dependents("A") == set()


class TestLayeredDAGValidator:
    """测试分层DAG校验器"""

    def test_validate_valid_dag(self):
        """测试有效的DAG验证"""
        validator = LayeredDAGValidator(["layer1", "layer2", "layer3"])
        validator.register_node("A", "layer1")
        validator.register_node("B", "layer2")
        validator.register_node("C", "layer3")
        validator.add_dependency("A", "B")
        validator.add_dependency("B", "C")
        
        is_valid, violations = validator.validate(strict=False)
        assert is_valid is True
        assert len(violations) == 0

    def test_validate_circular_dependency(self):
        """测试循环依赖检测"""
        validator = LayeredDAGValidator(["layer1", "layer2"])
        validator.register_node("A", "layer1")
        validator.register_node("B", "layer2")
        validator.add_dependency("A", "B")
        validator.add_dependency("B", "A")
        
        is_valid, violations = validator.validate(strict=False)
        assert is_valid is False
        assert len(violations) >= 1
        # 检查至少有一个循环依赖违规
        has_circular = any(v.violation_type == DependencyViolationType.CIRCULAR_DEPENDENCY for v in violations)
        assert has_circular

    def test_validate_reverse_dependency(self):
        """测试逆向依赖检测"""
        validator = LayeredDAGValidator(["layer1", "layer2", "layer3"])
        validator.register_node("A", "layer3")
        validator.register_node("B", "layer1")
        validator.add_dependency("A", "B")
        
        is_valid, violations = validator.validate(strict=False)
        assert is_valid is False
        assert len(violations) == 1
        assert violations[0].violation_type == DependencyViolationType.REVERSE_DEPENDENCY

    def test_validate_strict_mode(self):
        """测试严格模式"""
        validator = LayeredDAGValidator(["layer1", "layer2"])
        validator.register_node("A", "layer1")
        validator.register_node("B", "layer2")
        validator.add_dependency("A", "B")
        validator.add_dependency("B", "A")
        
        with pytest.raises(DAGError):
            validator.validate(strict=True)

    def test_get_topological_order(self):
        """测试获取拓扑排序"""
        validator = LayeredDAGValidator(["layer1", "layer2", "layer3"])
        validator.register_node("A", "layer1")
        validator.register_node("B", "layer2")
        validator.register_node("C", "layer3")
        validator.add_dependency("A", "B")
        validator.add_dependency("B", "C")
        
        order = validator.get_topological_order()
        assert order is not None
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")


class TestRuntimeDependencyMonitor:
    """测试运行时依赖监视器"""

    def test_record_valid_dependency(self):
        """测试记录有效的依赖"""
        validator = LayeredDAGValidator(["layer1", "layer2"])
        validator.register_node("A", "layer1")
        validator.register_node("B", "layer2")
        
        monitor = RuntimeDependencyMonitor(validator)
        monitor.record_dependency("A", "B")
        
        assert len(monitor.runtime_dependencies) == 1

    def test_record_invalid_dependency(self):
        """测试记录无效的依赖"""
        validator = LayeredDAGValidator(["layer1", "layer2"])
        validator.register_node("A", "layer2")
        validator.register_node("B", "layer1")
        
        monitor = RuntimeDependencyMonitor(validator)
        
        with pytest.raises(DAGError):
            monitor.record_dependency("A", "B")


class TestCreateModuleDependencyValidator:
    """测试创建模块依赖验证器"""

    def test_create_validator(self):
        """测试创建验证器"""
        validator = create_module_dependency_validator()
        assert validator is not None
        assert "input_layer" in validator.node_layers
        assert "scheduler" in validator.node_layers
        assert "agents" in validator.node_layers
        assert "executors" in validator.node_layers

    def test_module_dependency_valid(self):
        """测试模块间有效的依赖"""
        validator = create_module_dependency_validator()
        validator.add_dependency("input_layer", "scheduler")
        validator.add_dependency("scheduler", "agents")
        validator.add_dependency("agents", "executors")
        
        is_valid, violations = validator.validate(strict=False)
        assert is_valid is True


class TestDependencyViolation:
    """测试依赖违规记录"""

    def test_dependency_violation_str(self):
        """测试违规记录的字符串表示"""
        violation = DependencyViolation(
            violation_type=DependencyViolationType.CIRCULAR_DEPENDENCY,
            nodes=["A", "B", "A"],
            message="循环依赖检测"
        )
        str_repr = str(violation)
        assert "circular_dependency" in str_repr
        assert "循环依赖检测" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
