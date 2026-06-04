"""
Stage 2: 项目目录架构测试

验收标准：
- 四层架构目录创建
- 模块导入无循环依赖
- __init__.py文件规范
- 配置文件存在
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestArchitectureStructure:
    """测试架构结构"""

    def test_four_layer_directories(self):
        """验证四层架构目录存在"""
        project_root = Path(__file__).parent.parent
        layers = ['input_layer', 'scheduler', 'agents', 'executors']

        for layer in layers:
            layer_path = project_root / 'src' / layer
            assert layer_path.exists(), f"层级目录 {layer} 不存在"
            assert layer_path.is_dir(), f"{layer} 不是目录"

    def test_layer_init_files(self):
        """验证层级__init__.py文件"""
        project_root = Path(__file__).parent.parent
        layers = ['input_layer', 'scheduler', 'agents', 'executors']

        for layer in layers:
            init_file = project_root / 'src' / layer / '__init__.py'
            assert init_file.exists(), f"{layer} 的 __init__.py 不存在"

    def test_architecture_module(self):
        """验证架构模块"""
        import architecture
        from architecture import DependencyGraph, DependencyRule

        assert DependencyGraph is not None
        assert DependencyRule is not None


class TestDependencyManagement:
    """测试依赖管理"""

    def test_dependency_rule_creation(self):
        """验证依赖规则创建"""
        from architecture import DependencyRule, LayerType

        rule = DependencyRule()
        assert rule is not None

    def test_layer_dependency_allowed(self):
        """验证层级依赖规则"""
        from architecture import DependencyRule, LayerType

        assert DependencyRule.can_depend(LayerType.INPUT, LayerType.SCHEDULER)
        assert DependencyRule.can_depend(LayerType.SCHEDULER, LayerType.AGENTS)
        assert DependencyRule.can_depend(LayerType.AGENTS, LayerType.EXECUTORS)

    def test_layer_dependency_forbidden(self):
        """验证禁止的依赖"""
        from architecture import DependencyRule, LayerType

        assert not DependencyRule.can_depend(LayerType.INPUT, LayerType.AGENTS)
        assert not DependencyRule.can_depend(LayerType.EXECUTORS, LayerType.INPUT)
        assert not DependencyRule.can_depend(LayerType.AGENTS, LayerType.SCHEDULER)


class TestDependencyGraph:
    """测试依赖图"""

    def test_graph_creation(self):
        """验证依赖图创建"""
        from architecture import DependencyGraph, LayerType

        graph = DependencyGraph()
        assert graph is not None
        assert len(graph.modules) == 0

    def test_add_module(self):
        """验证添加模块"""
        from architecture import DependencyGraph, LayerType

        graph = DependencyGraph()
        graph.add_module('test.module', LayerType.CORE)
        assert 'test.module' in graph.modules

    def test_add_dependency(self):
        """验证添加依赖"""
        from architecture import DependencyGraph, LayerType

        graph = DependencyGraph()
        graph.add_module('layer1', LayerType.INPUT)
        graph.add_module('layer2', LayerType.SCHEDULER)

        result = graph.add_dependency('layer1', 'layer2')
        assert result is True
        assert 'layer2' in graph.modules['layer1'].dependencies

    def test_cycle_detection(self):
        """验证循环检测"""
        from architecture import DependencyGraph, LayerType

        graph = DependencyGraph()
        graph.add_module('a', LayerType.INPUT)
        graph.add_module('b', LayerType.SCHEDULER)

        graph.add_dependency('a', 'b')
        cycles = graph.detect_cycles()
        assert len(cycles) == 0

    def test_topological_sort(self):
        """验证拓扑排序"""
        from architecture import DependencyGraph, LayerType

        graph = DependencyGraph()
        graph.add_module('input', LayerType.INPUT)
        graph.add_module('scheduler', LayerType.SCHEDULER)
        graph.add_module('agents', LayerType.AGENTS)
        graph.add_module('executors', LayerType.EXECUTORS)

        graph.add_dependency('input', 'scheduler')
        graph.add_dependency('scheduler', 'agents')
        graph.add_dependency('agents', 'executors')

        sorted_modules = graph.topological_sort()
        assert len(sorted_modules) == 4


class TestConfiguration:
    """测试配置"""

    def test_config_files_exist(self):
        """验证配置文件存在"""
        project_root = Path(__file__).parent.parent
        config_files = ['base.yaml', 'development.yaml', 'production.yaml']

        for config_file in config_files:
            config_path = project_root / 'config' / config_file
            assert config_path.exists(), f"配置文件 {config_file} 不存在"

    def test_config_loading(self):
        """验证配置加载"""
        import yaml
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config' / 'base.yaml'

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert 'system' in config
        assert 'python' in config


class TestModuleImports:
    """测试模块导入"""

    def test_input_layer_import(self):
        """验证输入层导入"""
        from input_layer import TaskInput, TaskClassifier

        assert TaskInput is not None
        assert TaskClassifier is not None

    def test_scheduler_import(self):
        """验证调度层导入"""
        from scheduler import TaskScheduler, TaskStatus

        assert TaskScheduler is not None
        assert TaskStatus is not None

    def test_agents_import(self):
        """验证Agent层导入"""
        from agents import BaseAgent, AgentRegistry, AdminAgent

        assert BaseAgent is not None
        assert AgentRegistry is not None
        assert AdminAgent is not None

    def test_executors_import(self):
        """验证执行层导入"""
        from executors import ASTParser, CodeScanner

        assert ASTParser is not None
        assert CodeScanner is not None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
