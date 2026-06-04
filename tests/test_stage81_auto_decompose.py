"""
阶段81验收测试 - 全自动拆解为原子任务清单
"""

import pytest
from src.architecture.auto_decompose import (
    DecompositionStrategy,
    AtomTaskType,
    AtomTask,
    AutoDecomposer,
    AutoDecomposeService,
)


class TestDecompositionStrategy:
    """测试拆解策略枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert DecompositionStrategy.BY_FEATURE.value == "by_feature"
        assert DecompositionStrategy.BY_MODULE.value == "by_module"
        assert DecompositionStrategy.BY_LAYER.value == "by_layer"
        assert DecompositionStrategy.BY_RESPONSIBILITY.value == "by_responsibility"

    def test_all_strategies(self):
        """测试所有策略"""
        strategies = list(DecompositionStrategy)
        assert len(strategies) == 4


class TestAtomTaskType:
    """测试原子任务类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert AtomTaskType.DESIGN.value == "design"
        assert AtomTaskType.CODE.value == "code"
        assert AtomTaskType.TEST.value == "test"
        assert AtomTaskType.REVIEW.value == "review"
        assert AtomTaskType.DOC.value == "doc"

    def test_all_types(self):
        """测试所有任务类型"""
        types = list(AtomTaskType)
        assert len(types) == 5


class TestAtomTask:
    """测试原子任务"""

    def test_default_creation(self):
        """测试默认创建"""
        task = AtomTask()
        assert task.task_id != ""
        assert task.task_type == AtomTaskType.CODE
        assert task.name == ""
        assert task.description == ""
        assert task.dependencies == []
        assert task.estimated_complexity == 1.0
        assert task.priority == 0

    def test_custom_creation(self):
        """测试自定义创建"""
        task = AtomTask(
            task_type=AtomTaskType.DESIGN,
            name="设计用户模块",
            description="设计用户模块的架构",
            dependencies=["dep1", "dep2"],
            estimated_complexity=3.5,
            priority=5,
        )
        assert task.task_type == AtomTaskType.DESIGN
        assert task.name == "设计用户模块"
        assert task.description == "设计用户模块的架构"
        assert len(task.dependencies) == 2
        assert task.estimated_complexity == 3.5
        assert task.priority == 5

    def test_unique_ids(self):
        """测试唯一ID"""
        task1 = AtomTask()
        task2 = AtomTask()
        assert task1.task_id != task2.task_id


class TestAutoDecomposer:
    """测试自动拆解器"""

    def test_initialization(self):
        """测试初始化"""
        decomposer = AutoDecomposer()
        assert decomposer._tasks == []
        assert decomposer._strategy is None

    def test_decompose_by_feature(self):
        """测试按功能拆解"""
        decomposer = AutoDecomposer()
        requirements = {
            "features": ["用户管理", "订单系统", "支付模块"],
        }
        tasks = decomposer.decompose(requirements, DecompositionStrategy.BY_FEATURE)
        assert len(tasks) == 9  # 3 features * 3 tasks (design, code, test)
        assert all(isinstance(t, AtomTask) for t in tasks)

    def test_decompose_by_module(self):
        """测试按模块拆解"""
        decomposer = AutoDecomposer()
        requirements = {
            "modules": ["auth", "api", "core"],
        }
        tasks = decomposer.decompose(requirements, DecompositionStrategy.BY_MODULE)
        assert len(tasks) == 9  # 3 modules * 3 tasks (code, test, review)

    def test_decompose_by_layer(self):
        """测试按层次拆解"""
        decomposer = AutoDecomposer()
        requirements = {
            "layers": ["presentation", "business", "data"],
        }
        tasks = decomposer.decompose(requirements, DecompositionStrategy.BY_LAYER)
        assert len(tasks) == 6  # 3 layers * 2 tasks (design, code)

    def test_decompose_by_responsibility(self):
        """测试按职责拆解"""
        decomposer = AutoDecomposer()
        requirements = {
            "responsibilities": ["core_logic", "data_handling"],
        }
        tasks = decomposer.decompose(requirements, DecompositionStrategy.BY_RESPONSIBILITY)
        assert len(tasks) == 8  # 2 responsibilities * 4 tasks (design, code, test, doc)

    def test_decompose_empty_requirements(self):
        """测试空需求拆解"""
        decomposer = AutoDecomposer()
        tasks = decomposer.decompose({}, DecompositionStrategy.BY_FEATURE)
        assert len(tasks) > 0  # 应生成默认任务

    def test_analyze_requirements(self):
        """测试分析需求"""
        decomposer = AutoDecomposer()
        requirements = {
            "features": ["f1", "f2"],
            "modules": ["m1"],
            "complexity": "high",
            "has_api": True,
            "has_ui": True,
            "has_db": True,
        }
        analysis = decomposer._analyze_requirements(requirements)
        assert analysis["feature_count"] == 2
        assert analysis["module_count"] == 1
        assert analysis["complexity"] == "high"
        assert analysis["has_api"] is True

    def test_estimate_complexity(self):
        """测试估算复杂度"""
        decomposer = AutoDecomposer()
        task = AtomTask(task_type=AtomTaskType.CODE)
        analysis = {"complexity": "high", "has_api": True}
        complexity = decomposer._estimate_complexity(task, analysis)
        assert complexity > 5.0  # 高复杂度应增加基础值

    def test_estimate_complexity_low(self):
        """测试低复杂度估算"""
        decomposer = AutoDecomposer()
        task = AtomTask(task_type=AtomTaskType.DOC)
        analysis = {"complexity": "low"}
        complexity = decomposer._estimate_complexity(task, analysis)
        assert complexity < 2.0

    def test_generate_task_list(self):
        """测试生成任务清单"""
        decomposer = AutoDecomposer()
        requirements = {"features": ["用户管理"]}
        decomposer.decompose(requirements, DecompositionStrategy.BY_FEATURE)
        task_list = decomposer.generate_task_list()
        assert "total_tasks" in task_list
        assert "by_type" in task_list
        assert "total_complexity" in task_list
        assert "avg_complexity" in task_list
        assert "strategy" in task_list
        assert task_list["total_tasks"] == 3

    def test_feature_dependencies(self):
        """测试功能拆解的依赖关系"""
        decomposer = AutoDecomposer()
        requirements = {"features": ["用户管理"]}
        tasks = decomposer.decompose(requirements, DecompositionStrategy.BY_FEATURE)
        design_task = tasks[0]
        code_task = tasks[1]
        test_task = tasks[2]
        assert design_task.task_type == AtomTaskType.DESIGN
        assert code_task.dependencies == [design_task.task_id]
        assert test_task.dependencies == [code_task.task_id]

    def test_layer_sequential_dependencies(self):
        """测试层次拆解的顺序依赖"""
        decomposer = AutoDecomposer()
        requirements = {"layers": ["前端", "后端", "数据层"]}
        tasks = decomposer.decompose(requirements, DecompositionStrategy.BY_LAYER)
        # 第二层的design应依赖第一层的code
        assert len(tasks) == 6
        assert tasks[0].task_type == AtomTaskType.DESIGN
        assert tasks[1].task_type == AtomTaskType.CODE
        assert tasks[2].task_type == AtomTaskType.DESIGN
        assert tasks[2].dependencies == [tasks[1].task_id]


class TestAutoDecomposeService:
    """测试自动拆解服务"""

    def test_initialization(self):
        """测试初始化"""
        service = AutoDecomposeService()
        assert service.decomposer is not None

    def test_initialization_with_decomposer(self):
        """测试使用自定义拆解器初始化"""
        decomposer = AutoDecomposer()
        service = AutoDecomposeService(decomposer=decomposer)
        assert service.decomposer is decomposer

    def test_decompose(self):
        """测试执行拆解"""
        service = AutoDecomposeService()
        requirements = {"features": ["用户管理", "订单系统"]}
        tasks = service.decompose(requirements, DecompositionStrategy.BY_FEATURE)
        assert len(tasks) == 6

    def test_get_task_list(self):
        """测试获取任务清单"""
        service = AutoDecomposeService()
        requirements = {"features": ["用户管理"]}
        service.decompose(requirements)
        task_list = service.get_task_list()
        assert "total_tasks" in task_list
        assert task_list["total_tasks"] == 3

    def test_get_statistics(self):
        """测试获取统计信息"""
        service = AutoDecomposeService()
        requirements = {"features": ["用户管理", "订单系统"]}
        service.decompose(requirements)
        stats = service.get_statistics()
        assert "total_tasks" in stats
        assert "by_type" in stats
        assert "total_complexity" in stats
        assert "avg_complexity" in stats
        assert stats["total_tasks"] == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
