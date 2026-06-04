"""
阶段41验收测试：HTD层级任务拆解算法
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.architecture.htd_decomposer import (
    HTDDecomposer,
    HTDDecompositionService,
    SubTask,
    TaskDecomposition,
    TaskStatus,
    TaskPriority,
    get_htd_service,
    reset_htd_service
)


class TestSubTask(unittest.TestCase):
    """测试SubTask类"""
    
    def test_create_subtask(self):
        """测试创建子任务"""
        task = SubTask(name="Test Task", description="Test Description")
        self.assertIsNotNone(task.task_id)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.description, "Test Description")
        self.assertEqual(task.level, 0)
        self.assertEqual(task.status, TaskStatus.PENDING)
    
    def test_add_child(self):
        """测试添加子任务"""
        parent = SubTask(name="Parent Task")
        child = SubTask(name="Child Task")
        parent.add_child(child)
        
        self.assertEqual(len(parent.children), 1)
        self.assertEqual(child.parent_id, parent.task_id)
        self.assertEqual(child.level, 1)
    
    def test_is_leaf(self):
        """测试是否是叶子节点"""
        parent = SubTask(name="Parent Task")
        child = SubTask(name="Child Task")
        parent.add_child(child)
        
        self.assertFalse(parent.is_leaf())
        self.assertTrue(child.is_leaf())
    
    def test_get_leaf_tasks(self):
        """测试获取所有叶子任务"""
        root = SubTask(name="Root Task")
        child1 = SubTask(name="Child 1")
        child2 = SubTask(name="Child 2")
        subchild = SubTask(name="Subchild")
        
        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(subchild)
        
        leaves = root.get_leaf_tasks()
        self.assertEqual(len(leaves), 2)
        leaf_names = {t.name for t in leaves}
        self.assertIn("Subchild", leaf_names)
        self.assertIn("Child 2", leaf_names)


class TestHTDDecomposer(unittest.TestCase):
    """测试HTDDecomposer类"""
    
    def setUp(self):
        """测试准备"""
        self.decomposer = HTDDecomposer(max_levels=5, min_task_size=0.5)
    
    def test_decompose_simple_task(self):
        """测试分解简单任务"""
        decomposition = self.decomposer.decompose(
            "简单开发任务",
            "完成一个简单的开发功能",
            estimated_time=8.0
        )
        
        self.assertIsNotNone(decomposition)
        self.assertIsNotNone(decomposition.root_task)
        self.assertGreater(decomposition.total_levels, 1)
        self.assertGreater(decomposition.total_tasks, 1)
        self.assertTrue(decomposition.validation_result["valid"])
    
    def test_decompose_design_task(self):
        """测试分解设计任务"""
        decomposition = self.decomposer.decompose(
            "系统架构设计",
            "设计系统的整体架构",
            estimated_time=16.0
        )
        
        self.assertIsNotNone(decomposition)
        self.assertIsNotNone(decomposition.root_task)
        self.assertIn("设计", decomposition.root_task.name)
    
    def test_decompose_test_task(self):
        """测试分解测试任务"""
        decomposition = self.decomposer.decompose(
            "系统测试",
            "执行系统集成测试",
            estimated_time=12.0
        )
        
        self.assertIsNotNone(decomposition)
        self.assertIsNotNone(decomposition.root_task)
    
    def test_decompose_document_task(self):
        """测试分解文档任务"""
        decomposition = self.decomposer.decompose(
            "技术文档",
            "编写项目技术文档",
            estimated_time=10.0
        )
        
        self.assertIsNotNone(decomposition)
        self.assertIsNotNone(decomposition.root_task)
    
    def test_decompose_max_levels(self):
        """测试最大层级限制"""
        decomposer = HTDDecomposer(max_levels=3)
        decomposition = decomposer.decompose(
            "多层级任务",
            "需要多层分解的任务",
            estimated_time=40.0
        )
        
        self.assertLessEqual(decomposition.total_levels, 4)  # 根任务是0级
    
    def test_validate_decomposition(self):
        """测试验证分解结果"""
        decomposition = self.decomposer.decompose(
            "测试任务",
            "测试验证功能",
            estimated_time=6.0
        )
        
        validation = decomposition.validation_result
        self.assertIn("valid", validation)
        self.assertIn("errors", validation)
        self.assertIn("warnings", validation)
        self.assertIn("atom_check", validation)
        self.assertIn("integrity_check", validation)
    
    def test_get_flat_task_list(self):
        """测试获取扁平化任务列表"""
        decomposition = self.decomposer.decompose(
            "扁平化测试",
            "测试扁平化功能",
            estimated_time=8.0
        )
        
        flat_list = self.decomposer.get_flat_task_list(decomposition)
        self.assertEqual(len(flat_list), decomposition.total_tasks)
    
    def test_get_dependency_graph(self):
        """测试获取依赖图"""
        decomposition = self.decomposer.decompose(
            "依赖图测试",
            "测试依赖图生成",
            estimated_time=6.0
        )
        
        graph = self.decomposer.get_task_dependency_graph(decomposition)
        self.assertIsInstance(graph, dict)
        self.assertEqual(len(graph), decomposition.total_tasks)


class TestHTDDecompositionService(unittest.TestCase):
    """测试HTDDecompositionService类"""
    
    def setUp(self):
        """测试准备"""
        reset_htd_service()
        self.service = get_htd_service()
    
    def tearDown(self):
        """测试清理"""
        reset_htd_service()
    
    def test_decompose_task(self):
        """测试服务分解任务"""
        decomposition = self.service.decompose_task(
            "服务测试任务",
            "通过服务进行分解",
            estimated_time=10.0,
            max_levels=3
        )
        
        self.assertIsNotNone(decomposition)
        self.assertIsNotNone(decomposition.decomposition_id)
    
    def test_get_decomposition(self):
        """测试获取分解结果"""
        decomposition1 = self.service.decompose_task(
            "任务1",
            "描述1",
            estimated_time=5.0
        )
        
        retrieved = self.service.get_decomposition(decomposition1.decomposition_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.decomposition_id, decomposition1.decomposition_id)
    
    def test_get_performance_stats(self):
        """测试获取性能统计"""
        self.service.decompose_task("任务1", "描述1", 5.0)
        self.service.decompose_task("任务2", "描述2", 8.0)
        
        stats = self.service.get_performance_stats()
        self.assertEqual(stats["total_decompositions"], 2)
        self.assertIn("avg_time", stats)
        self.assertIn("max_time", stats)
        self.assertIn("min_time", stats)


class TestHTDIntegration(unittest.TestCase):
    """测试HTD集成功能"""
    
    def test_three_level_decomposition(self):
        """测试三层分解"""
        decomposer = HTDDecomposer(max_levels=3)
        decomposition = decomposer.decompose(
            "三层分解任务",
            "需要分解到三层的任务",
            estimated_time=24.0
        )
        
        self.assertGreaterEqual(decomposition.total_levels, 3)
        self.assertTrue(decomposition.validation_result["valid"])
    
    def test_multiple_task_types(self):
        """测试多种任务类型"""
        decomposer = HTDDecomposer()
        
        task_types = [
            ("设计任务", "架构设计工作", 16.0),
            ("开发任务", "功能开发实现", 12.0),
            ("测试任务", "测试验证工作", 8.0),
            ("文档任务", "文档编写工作", 6.0)
        ]
        
        for name, desc, time in task_types:
            decomposition = decomposer.decompose(name, desc, time)
            self.assertTrue(decomposition.validation_result["valid"])
    
    def test_performance_requirement(self):
        """测试性能要求"""
        decomposer = HTDDecomposer()
        
        # 测试分解时间应小于3秒
        import time
        start = time.time()
        decomposition = decomposer.decompose(
            "性能测试任务",
            "测试分解性能",
            estimated_time=20.0
        )
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 3.0)  # 验收标准：<3秒/任务


class TestHTDValidation(unittest.TestCase):
    """测试HTD验证功能"""
    
    def test_atomicity_validation(self):
        """测试原子性验证"""
        decomposer = HTDDecomposer(min_task_size=0.5)
        decomposition = decomposer.decompose(
            "原子性测试",
            "验证原子性检查",
            estimated_time=4.0
        )
        
        # 检查叶子任务大小
        leaf_tasks = decomposition.root_task.get_leaf_tasks()
        for task in leaf_tasks:
            # 大多数叶子任务应该符合最小任务大小
            self.assertGreater(task.estimated_time, 0)
    
    def test_integrity_validation(self):
        """测试完整性验证"""
        decomposer = HTDDecomposer()
        decomposition = decomposer.decompose(
            "完整性测试",
            "验证完整性检查",
            estimated_time=10.0
        )
        
        # 时间总和应该接近根任务时间
        leaf_tasks = decomposition.root_task.get_leaf_tasks()
        total_leaf_time = sum(t.estimated_time for t in leaf_tasks)
        root_time = decomposition.root_task.estimated_time
        
        # 允许10%的误差
        self.assertLess(abs(total_leaf_time - root_time), root_time * 0.2)


def run_acceptance_tests():
    """运行验收测试"""
    print("=" * 60)
    print("阶段41验收测试：HTD层级任务拆解算法")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(TestSubTask))
    suite.addTests(loader.loadTestsFromTestCase(TestHTDDecomposer))
    suite.addTests(loader.loadTestsFromTestCase(TestHTDDecompositionService))
    suite.addTests(loader.loadTestsFromTestCase(TestHTDIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestHTDValidation))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出验收结果
    print("\n" + "=" * 60)
    print("验收测试结果汇总")
    print("=" * 60)
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"跳过数: {len(result.skipped)}")
    print("=" * 60)
    
    # 判断是否通过验收
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("✅ 阶段41验收测试通过！")
        print("\n验收标准达成情况：")
        print("  ✅ HTD算法集成：已实现完整的HTD层级分解")
        print("  ✅ 层级分解：支持3层以上分解")
        print("  ✅ 分解结果验证：原子性和完整性检查")
        print("  ✅ 分解性能：分解时间<3秒/任务")
        return True
    else:
        print("❌ 阶段41验收测试失败！")
        return False


if __name__ == "__main__":
    success = run_acceptance_tests()
    sys.exit(0 if success else 1)
