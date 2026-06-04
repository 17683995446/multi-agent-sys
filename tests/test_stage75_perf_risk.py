"""
阶段75验收测试：代码性能风险检测
"""

import pytest
from src.architecture.perf_risk import (
    RiskLevel,
    RiskCategory,
    PerformanceRisk,
    PerformanceAnalyzer,
    PerfRiskService,
)


class TestRiskLevel:
    """测试风险级别枚举"""

    def test_level_values(self):
        """测试风险级别枚举值"""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_all_levels(self):
        """测试所有级别"""
        levels = list(RiskLevel)
        assert len(levels) == 4


class TestRiskCategory:
    """测试风险类别枚举"""

    def test_category_values(self):
        """测试风险类别枚举值"""
        assert RiskCategory.MEMORY.value == "memory"
        assert RiskCategory.CPU.value == "cpu"
        assert RiskCategory.IO.value == "io"
        assert RiskCategory.CONCURRENCY.value == "concurrency"
        assert RiskCategory.ALGORITHM.value == "algorithm"

    def test_all_categories(self):
        """测试所有类别"""
        categories = list(RiskCategory)
        assert len(categories) == 5


class TestPerformanceRisk:
    """测试性能风险记录"""

    def test_default_creation(self):
        """测试默认创建"""
        risk = PerformanceRisk()
        assert risk.risk_id != ""
        assert risk.category == RiskCategory.MEMORY
        assert risk.level == RiskLevel.LOW
        assert risk.location == ""
        assert risk.description == ""
        assert risk.impact == ""
        assert risk.mitigation == ""
        assert risk.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        risk = PerformanceRisk(
            category=RiskCategory.CPU,
            level=RiskLevel.HIGH,
            location="main.py:50",
            description="高圈复杂度方法",
            impact="CPU执行路径过多",
            mitigation="拆分方法",
        )
        assert risk.category == RiskCategory.CPU
        assert risk.level == RiskLevel.HIGH
        assert risk.location == "main.py:50"
        assert risk.description == "高圈复杂度方法"

    def test_risk_id_unique(self):
        """测试风险ID唯一性"""
        r1 = PerformanceRisk()
        r2 = PerformanceRisk()
        assert r1.risk_id != r2.risk_id


class TestPerformanceAnalyzer:
    """测试性能风险分析器"""

    def test_initialization(self):
        """测试初始化"""
        analyzer = PerformanceAnalyzer()
        assert len(analyzer.risks) == 0

    def test_check_memory_risks_large_list(self):
        """测试大列表内存风险"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 150000}],
        }
        risks = analyzer._check_memory_risks(code_data)
        assert len(risks) > 0
        assert risks[0].category == RiskCategory.MEMORY
        assert risks[0].level == RiskLevel.CRITICAL

    def test_check_memory_risks_small_list(self):
        """测试小列表低风险"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 500}],
        }
        risks = analyzer._check_memory_risks(code_data)
        assert len(risks) > 0
        assert risks[0].level == RiskLevel.LOW

    def test_check_memory_risks_global_cache(self):
        """测试全局缓存风险"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "global_caches": [{"name": "cache"}],
        }
        risks = analyzer._check_memory_risks(code_data)
        assert len(risks) > 0
        assert any("缓存" in r.description for r in risks)

    def test_check_cpu_risks_complex_method(self):
        """测试高圈复杂度CPU风险"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "complex_methods": [{"name": "process", "complexity": 25}],
        }
        risks = analyzer._check_cpu_risks(code_data)
        assert len(risks) > 0
        assert risks[0].level == RiskLevel.CRITICAL

    def test_check_cpu_risks_nested_loops(self):
        """测试深层嵌套循环CPU风险"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "nested_loops": [{"name": "search", "depth": 3}],
        }
        risks = analyzer._check_cpu_risks(code_data)
        assert len(risks) > 0
        assert risks[0].level == RiskLevel.CRITICAL

    def test_check_io_risks_sync_io(self):
        """测试同步IO风险"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "sync_io_operations": [{"name": "read_file", "in_loop": True}],
        }
        risks = analyzer._check_io_risks(code_data)
        assert len(risks) > 0
        assert risks[0].level == RiskLevel.HIGH

    def test_check_io_risks_frequent_file_ops(self):
        """测试频繁文件操作风险"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "frequent_file_ops": [{"name": "write_log", "count": 200}],
        }
        risks = analyzer._check_io_risks(code_data)
        assert len(risks) > 0
        assert risks[0].level == RiskLevel.HIGH

    def test_check_algorithm_risks_inefficient(self):
        """测试低效算法风险"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "inefficient_algorithms": [{"name": "bubble_sort", "time_complexity": "O(n^2)"}],
        }
        risks = analyzer._check_algorithm_risks(code_data)
        assert len(risks) > 0
        assert risks[0].level == RiskLevel.HIGH

    def test_analyze(self):
        """测试完整分析"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 50000}],
            "complex_methods": [{"name": "process", "complexity": 15}],
            "sync_io_operations": [{"name": "read_file", "in_loop": False}],
            "inefficient_algorithms": [{"name": "sort", "time_complexity": "O(nlogn)"}],
        }
        risks = analyzer.analyze(code_data)
        assert len(risks) > 0

    def test_generate_report(self):
        """测试生成报告"""
        analyzer = PerformanceAnalyzer()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 50000}],
        }
        analyzer.analyze(code_data)
        report = analyzer.generate_report()
        assert "total_risks" in report
        assert "overall_level" in report
        assert "by_category" in report
        assert "by_level" in report


class TestPerfRiskService:
    """测试性能风险检测服务"""

    def test_initialization(self):
        """测试初始化"""
        service = PerfRiskService()
        assert service.analyzer is not None

    def test_analyze(self):
        """测试执行分析"""
        service = PerfRiskService()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 50000}],
            "complex_methods": [{"name": "process", "complexity": 15}],
        }
        risks = service.analyze(code_data)
        assert len(risks) > 0

    def test_get_risks(self):
        """测试获取风险列表"""
        service = PerfRiskService()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 50000}],
            "complex_methods": [{"name": "process", "complexity": 15}],
        }
        service.analyze(code_data)
        risks = service.get_risks()
        assert len(risks) > 0

    def test_get_risks_by_category(self):
        """测试按类别过滤风险"""
        service = PerfRiskService()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 50000}],
            "complex_methods": [{"name": "process", "complexity": 15}],
        }
        service.analyze(code_data)
        memory_risks = service.get_risks(category=RiskCategory.MEMORY)
        assert all(r.category == RiskCategory.MEMORY for r in memory_risks)

    def test_get_risks_by_level(self):
        """测试按级别过滤风险"""
        service = PerfRiskService()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 50000}],
        }
        service.analyze(code_data)
        critical_risks = service.get_risks(level=RiskLevel.CRITICAL)
        assert all(r.level == RiskLevel.CRITICAL for r in critical_risks)

    def test_get_report(self):
        """测试获取报告"""
        service = PerfRiskService()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 50000}],
        }
        service.analyze(code_data)
        report = service.get_report()
        assert report["total_risks"] > 0
        assert report["overall_level"] in ["low", "medium", "high", "critical"]

    def test_full_workflow(self):
        """测试完整工作流"""
        service = PerfRiskService()
        code_data = {
            "file_path": "main.py",
            "large_lists": [{"name": "data", "size": 50000}],
            "complex_methods": [{"name": "process", "complexity": 25}],
            "sync_io_operations": [{"name": "read_file", "in_loop": True}],
            "inefficient_algorithms": [{"name": "sort", "time_complexity": "O(n^2)"}],
        }
        risks = service.analyze(code_data)
        assert len(risks) >= 4
        report = service.get_report()
        assert report["overall_level"] == "critical"
        memory_risks = service.get_risks(category=RiskCategory.MEMORY)
        assert len(memory_risks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
