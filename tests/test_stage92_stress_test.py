"""
阶段92验收测试 - 多Agent协作压力测试
"""

import pytest
from src.architecture.stress_test import (
    StressTestType,
    StressTestConfig,
    StressTestResult,
    StressTester,
    StressTestService,
)


class TestStressTestType:
    """测试压力测试类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert StressTestType.CONCURRENT_AGENTS.value == "concurrent_agents"
        assert StressTestType.HIGH_VOLUME_TASKS.value == "high_volume_tasks"
        assert StressTestType.LONG_DURATION.value == "long_duration"
        assert StressTestType.MIXED_WORKLOAD.value == "mixed_workload"

    def test_all_types(self):
        """测试所有类型"""
        types = list(StressTestType)
        assert len(types) == 4


class TestStressTestConfig:
    """测试压力测试配置"""

    def test_default_creation(self):
        """测试默认创建"""
        config = StressTestConfig()
        assert config.test_type == StressTestType.CONCURRENT_AGENTS
        assert config.agent_count == 10
        assert config.task_count == 100
        assert config.duration_seconds == 60.0
        assert config.ramp_up_seconds == 10.0

    def test_custom_creation(self):
        """测试自定义创建"""
        config = StressTestConfig(
            test_type=StressTestType.HIGH_VOLUME_TASKS,
            agent_count=50,
            task_count=500,
            duration_seconds=120.0,
            ramp_up_seconds=20.0,
        )
        assert config.test_type == StressTestType.HIGH_VOLUME_TASKS
        assert config.agent_count == 50
        assert config.task_count == 500
        assert config.duration_seconds == 120.0
        assert config.ramp_up_seconds == 20.0


class TestStressTestResult:
    """测试压力测试结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = StressTestResult()
        assert result.test_id != ""
        assert result.total_operations == 0
        assert result.successful_ops == 0
        assert result.failed_ops == 0
        assert result.avg_latency == 0.0
        assert result.max_latency == 0.0
        assert result.throughput == 0.0
        assert result.errors == []

    def test_result_id_unique(self):
        """测试结果ID唯一性"""
        r1 = StressTestResult()
        r2 = StressTestResult()
        assert r1.test_id != r2.test_id


class TestStressTester:
    """测试多Agent协作压力测试器"""

    def test_initialization(self):
        """测试初始化"""
        tester = StressTester()
        assert len(tester._results) == 0
        assert len(tester._metrics) == 0

    def test_run_concurrent(self):
        """测试运行并发Agent测试"""
        tester = StressTester()
        config = StressTestConfig(
            test_type=StressTestType.CONCURRENT_AGENTS,
            agent_count=20,
        )
        result = tester.run(config)
        assert result.total_operations > 0
        assert result.test_id in tester._results

    def test_run_high_volume(self):
        """测试运行高任务量测试"""
        tester = StressTester()
        config = StressTestConfig(
            test_type=StressTestType.HIGH_VOLUME_TASKS,
            task_count=50,
        )
        result = tester.run(config)
        assert result.total_operations > 0
        assert result.throughput > 0

    def test_run_long_duration(self):
        """测试运行长持续时间测试"""
        tester = StressTester()
        config = StressTestConfig(
            test_type=StressTestType.LONG_DURATION,
            duration_seconds=1.0,
        )
        result = tester.run(config)
        assert result.total_operations > 0
        assert result.successful_ops > 0

    def test_run_mixed_workload(self):
        """测试运行混合负载测试"""
        tester = StressTester()
        config = StressTestConfig(
            test_type=StressTestType.MIXED_WORKLOAD,
            agent_count=5,
            task_count=10,
        )
        result = tester.run(config)
        assert result.total_operations > 0

    def test_run_saves_result(self):
        """测试运行后保存结果"""
        tester = StressTester()
        config = StressTestConfig()
        result = tester.run(config)
        assert result.test_id in tester._results

    def test_collect_metrics(self):
        """测试收集指标"""
        tester = StressTester()
        config = StressTestConfig(agent_count=5)
        tester.run(config)
        assert len(tester._metrics) > 0
        metrics = tester._metrics[0]
        assert "test_id" in metrics
        assert "total_operations" in metrics
        assert "throughput" in metrics

    def test_generate_report(self):
        """测试生成报告"""
        tester = StressTester()
        config = StressTestConfig(agent_count=5)
        result = tester.run(config)
        report = tester.generate_report(result.test_id)
        assert "test_id" in report
        assert "test_type" in report
        assert "total_operations" in report
        assert "successful_ops" in report
        assert "failed_ops" in report
        assert "success_rate" in report
        assert "avg_latency" in report
        assert "max_latency" in report
        assert "throughput" in report

    def test_generate_report_not_found(self):
        """测试生成报告未找到"""
        tester = StressTester()
        report = tester.generate_report("non-existent-id")
        assert "message" in report

    def test_run_concurrent_agents_latency(self):
        """测试并发Agent延迟计算"""
        tester = StressTester()
        config = StressTestConfig(
            test_type=StressTestType.CONCURRENT_AGENTS,
            agent_count=3,
        )
        result = tester.run(config)
        assert result.avg_latency > 0
        assert result.max_latency >= result.avg_latency

    def test_run_high_volume_task_count(self):
        """测试高任务量任务计数"""
        tester = StressTester()
        config = StressTestConfig(
            test_type=StressTestType.HIGH_VOLUME_TASKS,
            task_count=20,
        )
        result = tester.run(config)
        assert result.total_operations >= 20


class TestStressTestService:
    """测试多Agent协作压力测试服务"""

    def test_initialization(self):
        """测试初始化"""
        service = StressTestService()
        assert service.tester is not None

    def test_initialization_with_tester(self):
        """测试使用自定义测试器初始化"""
        tester = StressTester()
        service = StressTestService(tester=tester)
        assert service.tester is tester

    def test_run(self):
        """测试执行压力测试"""
        service = StressTestService()
        config = StressTestConfig(agent_count=5)
        result = service.run(config)
        assert result.total_operations > 0

    def test_get_result(self):
        """测试获取测试结果"""
        service = StressTestService()
        config = StressTestConfig(agent_count=5)
        result = service.run(config)
        fetched = service.get_result(result.test_id)
        assert fetched is not None
        assert fetched.test_id == result.test_id

    def test_get_result_not_found(self):
        """测试获取不存在的测试结果"""
        service = StressTestService()
        result = service.get_result("non-existent-id")
        assert result is None

    def test_get_report(self):
        """测试获取测试报告"""
        service = StressTestService()
        config = StressTestConfig(agent_count=5)
        result = service.run(config)
        report = service.get_report(result.test_id)
        assert "test_id" in report
        assert "total_operations" in report

    def test_get_report_not_found(self):
        """测试获取不存在的测试报告"""
        service = StressTestService()
        report = service.get_report("non-existent-id")
        assert "message" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
