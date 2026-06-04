import pytest
import tempfile
import os
from src.architecture import (
    EntropyType,
    EntropyMetric,
    EntropyReport,
    EntropyCalculator,
    EntropyReducer,
    EntropyRule,
    EntropyMonitor,
    EntropyManager,
    create_entropy_manager
)


class TestEntropyType:
    """测试熵值类型"""

    def test_entropy_types(self):
        """测试熵值类型枚举"""
        assert EntropyType.STRUCTURAL.value == "structural"
        assert EntropyType.NAMING.value == "naming"
        assert EntropyType.COMPLEXITY.value == "complexity"
        assert EntropyType.DUPLICATION.value == "duplication"
        assert EntropyType.COUPLING.value == "coupling"
        assert EntropyType.COHESION.value == "cohesion"


class TestEntropyMetric:
    """测试熵值指标"""

    def test_create_metric(self):
        """测试创建熵值指标"""
        metric = EntropyMetric(
            metric_type=EntropyType.COMPLEXITY,
            name="复杂度熵",
            value=0.7,
            weight=1.5,
            threshold=0.5
        )
        assert metric.value == 0.7
        assert metric.is_violation() is True

    def test_metric_is_violation(self):
        """测试违规检测"""
        metric = EntropyMetric(
            metric_type=EntropyType.COMPLEXITY,
            name="test",
            value=0.3,
            threshold=0.5
        )
        assert metric.is_violation() is False


class TestEntropyCalculator:
    """测试熵值计算器"""

    def test_calculate_structural_entropy(self):
        """测试结构熵计算"""
        code = """
def func():
    if True:
        print(1)
    else:
        print(2)
"""
        entropy = EntropyCalculator.calculate_structural_entropy(code)
        assert 0.0 <= entropy <= 1.0

    def test_calculate_naming_entropy(self):
        """测试命名熵计算"""
        code = """
def func():
    x = 1
    y = 2
    return x + y
"""
        entropy = EntropyCalculator.calculate_naming_entropy(code)
        assert 0.0 <= entropy <= 1.0

    def test_calculate_complexity_entropy(self):
        """测试复杂度熵计算"""
        code = """
def func():
    if True:
        while True:
            for i in range(10):
                pass
"""
        entropy = EntropyCalculator.calculate_complexity_entropy(code)
        assert 0.0 <= entropy <= 1.0

    def test_calculate_duplication_entropy(self):
        """测试重复熵计算"""
        code = """
x = 1
y = 2
x = 1
z = 3
"""
        entropy = EntropyCalculator.calculate_duplication_entropy(code)
        assert 0.0 <= entropy <= 1.0

    def test_calculate_coupling_entropy(self):
        """测试耦合熵计算"""
        imports = ["os", "sys", "json", "time"]
        entropy = EntropyCalculator.calculate_coupling_entropy(imports)
        assert 0.0 <= entropy <= 1.0


class TestEntropyReducer:
    """测试熵减工具"""

    def test_reduce_complexity(self):
        """测试降低复杂度"""
        code = """
def func():
    if True:
        if True:
            if True:
                pass
"""
        reduced, suggestions = EntropyReducer.reduce_complexity(code)
        assert isinstance(suggestions, list)

    def test_reduce_duplication(self):
        """测试减少重复"""
        code = """
x = 1
y = 2
z = 3
x = 1
y = 2
w = 4
x = 1
"""
        reduced, suggestions = EntropyReducer.reduce_duplication(code)
        assert isinstance(suggestions, list)

    def test_improve_naming(self):
        """测试改进命名"""
        code = """
def f(a, b, c):
    x = a + b + c
    return x
"""
        reduced, suggestions = EntropyReducer.improve_naming(code)
        assert len(suggestions) > 0

    def test_auto_reduce(self):
        """测试自动熵减"""
        code = """
def f(a):
    if True:
        if True:
            print("test")
            print("test")
    return a
"""
        reduced, suggestions = EntropyReducer.auto_reduce(code)
        assert isinstance(suggestions, list)


class TestEntropyRule:
    """测试熵值规范"""

    def test_create_rule(self):
        """测试创建规范"""
        rule = EntropyRule()
        assert rule.get_rule("max_complexity") == 10
        assert rule.get_rule("max_function_length") == 50

    def test_set_rule(self):
        """测试设置规则"""
        rule = EntropyRule()
        rule.set_rule("max_complexity", 15)
        assert rule.get_rule("max_complexity") == 15

    def test_validate(self):
        """测试验证"""
        rule = EntropyRule()
        code = "def f(): pass"
        is_valid, violations = rule.validate(code)
        assert is_valid is True


class TestEntropyMonitor:
    """测试熵值监控器"""

    def test_add_report(self):
        """测试添加报告"""
        monitor = EntropyMonitor()
        report = EntropyReport(
            report_id="test-001",
            file_path="test.py",
            overall_entropy=0.5,
            metrics=[],
            violations=[],
            suggestions=[]
        )
        monitor.add_report(report)
        assert len(monitor.history) == 1

    def test_get_trend(self):
        """测试获取趋势"""
        monitor = EntropyMonitor()
        for i in range(3):
            report = EntropyReport(
                report_id=f"test-{i}",
                file_path="test.py",
                overall_entropy=0.3 + i * 0.1,
                metrics=[],
                violations=[],
                suggestions=[]
            )
            monitor.add_report(report)

        trend = monitor.get_trend("test.py")
        assert len(trend) == 3

    def test_get_alerts(self):
        """测试获取告警"""
        monitor = EntropyMonitor()
        report = EntropyReport(
            report_id="test-001",
            file_path="test.py",
            overall_entropy=0.8,
            metrics=[],
            violations=[],
            suggestions=[]
        )
        monitor.add_report(report)
        alerts = monitor.get_alerts()
        assert len(alerts) > 0

    def test_get_summary(self):
        """测试获取摘要"""
        monitor = EntropyMonitor()
        summary = monitor.get_summary()
        assert "total_files" in summary
        assert "average_entropy" in summary


class TestEntropyManager:
    """测试熵值管理器"""

    def test_create_manager(self):
        """测试创建管理器"""
        manager = create_entropy_manager()
        assert manager is not None
        assert isinstance(manager, EntropyManager)

    def test_analyze_file(self):
        """测试分析文件"""
        manager = create_entropy_manager()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test_func():
    x = 1
    y = 2
    if x > y:
        print("x > y")
    return x + y
""")
            temp_file = f.name

        try:
            report = manager.analyze_file(temp_file)
            assert report.file_path == temp_file
            assert 0.0 <= report.overall_entropy <= 1.0
            assert len(report.metrics) > 0
        finally:
            os.unlink(temp_file)

    def test_reduce_entropy(self):
        """测试降低熵值"""
        manager = create_entropy_manager()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def test():
    if True:
        if True:
            print("test")
""")
            temp_file = f.name

        try:
            code, suggestions = manager.reduce_entropy(temp_file)
            assert isinstance(code, str)
            assert isinstance(suggestions, list)
        finally:
            os.unlink(temp_file)

    def test_get_monitor_summary(self):
        """测试获取监控摘要"""
        manager = create_entropy_manager()
        summary = manager.get_monitor_summary()
        assert "total_files" in summary

    def test_get_alerts(self):
        """测试获取告警"""
        manager = create_entropy_manager()
        alerts = manager.get_alerts()
        assert isinstance(alerts, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
