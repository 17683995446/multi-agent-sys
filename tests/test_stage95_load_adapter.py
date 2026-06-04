"""
阶段95验收测试 - 批量工程任务压测适配
"""

import pytest
from src.architecture.load_adapter import (
    LoadProfile,
    LoadConfig,
    LoadMetrics,
    LoadGenerator,
    LoadAdapterService,
)


class TestLoadProfile:
    """测试负载配置枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert LoadProfile.LIGHT.value == "light"
        assert LoadProfile.MODERATE.value == "moderate"
        assert LoadProfile.HEAVY.value == "heavy"
        assert LoadProfile.EXTREME.value == "extreme"

    def test_all_profiles(self):
        """测试所有负载配置"""
        profiles = list(LoadProfile)
        assert len(profiles) == 4


class TestLoadConfig:
    """测试负载配置"""

    def test_default_creation(self):
        """测试默认创建"""
        config = LoadConfig()
        assert config.profile == LoadProfile.MODERATE
        assert config.concurrent_tasks == 10
        assert config.total_tasks == 100
        assert config.task_complexity == 1.0
        assert config.think_time_ms == 100

    def test_custom_creation(self):
        """测试自定义创建"""
        config = LoadConfig(
            profile=LoadProfile.HEAVY,
            concurrent_tasks=50,
            total_tasks=500,
            task_complexity=2.0,
            think_time_ms=50,
        )
        assert config.profile == LoadProfile.HEAVY
        assert config.concurrent_tasks == 50
        assert config.total_tasks == 500
        assert config.task_complexity == 2.0
        assert config.think_time_ms == 50


class TestLoadMetrics:
    """测试负载指标"""

    def test_default_creation(self):
        """测试默认创建"""
        metrics = LoadMetrics()
        assert metrics.total_tasks == 0
        assert metrics.completed == 0
        assert metrics.failed == 0
        assert metrics.avg_response_time == 0.0
        assert metrics.p95_response_time == 0.0
        assert metrics.p99_response_time == 0.0
        assert metrics.throughput == 0.0
        assert metrics.error_rate == 0.0

    def test_custom_creation(self):
        """测试自定义创建"""
        metrics = LoadMetrics(
            total_tasks=100,
            completed=95,
            failed=5,
            avg_response_time=0.15,
            p95_response_time=0.3,
            p99_response_time=0.5,
            throughput=500.0,
            error_rate=5.0,
        )
        assert metrics.total_tasks == 100
        assert metrics.completed == 95
        assert metrics.failed == 5
        assert metrics.throughput == 500.0


class TestLoadGenerator:
    """测试负载生成器"""

    def test_initialization(self):
        """测试初始化"""
        generator = LoadGenerator()
        assert len(generator._metrics_history) == 0
        assert len(generator._response_times) == 0

    def test_generate_load_light(self):
        """测试生成轻量负载"""
        generator = LoadGenerator()
        config = LoadConfig(
            profile=LoadProfile.LIGHT,
            total_tasks=10,
        )
        metrics = generator.generate_load(config)
        assert metrics.total_tasks == 10
        assert metrics.completed + metrics.failed == 10
        assert metrics.avg_response_time > 0

    def test_generate_load_moderate(self):
        """测试生成中等负载"""
        generator = LoadGenerator()
        config = LoadConfig(
            profile=LoadProfile.MODERATE,
            total_tasks=20,
        )
        metrics = generator.generate_load(config)
        assert metrics.total_tasks == 20
        assert metrics.completed + metrics.failed == 20

    def test_generate_load_heavy(self):
        """测试生成重度负载"""
        generator = LoadGenerator()
        config = LoadConfig(
            profile=LoadProfile.HEAVY,
            total_tasks=15,
        )
        metrics = generator.generate_load(config)
        assert metrics.total_tasks == 15

    def test_generate_load_extreme(self):
        """测试生成极限负载"""
        generator = LoadGenerator()
        config = LoadConfig(
            profile=LoadProfile.EXTREME,
            total_tasks=10,
        )
        metrics = generator.generate_load(config)
        assert metrics.total_tasks == 10

    def test_generate_load_saves_history(self):
        """测试生成负载后保存历史"""
        generator = LoadGenerator()
        config = LoadConfig(total_tasks=5)
        generator.generate_load(config)
        assert len(generator._metrics_history) == 1

    def test_create_task(self):
        """测试创建任务"""
        generator = LoadGenerator()
        config = LoadConfig(task_complexity=2.0)
        task = generator._create_task(0, config)
        assert task["task_id"] == "task_0"
        assert task["complexity"] == 2.0

    def test_execute_task(self):
        """测试执行任务"""
        generator = LoadGenerator()
        config = LoadConfig(profile=LoadProfile.LIGHT)
        task = {"task_id": "task_0", "index": 0, "complexity": 1.0}
        success, response_time = generator._execute_task(task, config)
        assert response_time > 0

    def test_measure_response_light(self):
        """测试轻量负载响应时间"""
        generator = LoadGenerator()
        config = LoadConfig(profile=LoadProfile.LIGHT)
        task = {"task_id": "task_0", "index": 0, "complexity": 1.0}
        response_time = generator._measure_response(task, config)
        assert response_time > 0
        assert response_time < 1.0

    def test_measure_response_extreme(self):
        """测试极限负载响应时间"""
        generator = LoadGenerator()
        config = LoadConfig(profile=LoadProfile.EXTREME)
        task = {"task_id": "task_0", "index": 0, "complexity": 1.0}
        response_time = generator._measure_response(task, config)
        assert response_time > 0

    def test_collect_metrics(self):
        """测试收集指标"""
        generator = LoadGenerator()
        response_times = [0.01, 0.02, 0.03, 0.04, 0.05,
                          0.06, 0.07, 0.08, 0.09, 0.10]
        metrics = generator.collect_metrics(10, 8, 2, response_times, 1.0)
        assert metrics.total_tasks == 10
        assert metrics.completed == 8
        assert metrics.failed == 2
        assert metrics.avg_response_time > 0
        assert metrics.p95_response_time >= metrics.avg_response_time
        assert metrics.p99_response_time >= metrics.p95_response_time
        assert metrics.throughput == 10.0
        assert metrics.error_rate == 20.0

    def test_collect_metrics_empty(self):
        """测试收集空指标"""
        generator = LoadGenerator()
        metrics = generator.collect_metrics(0, 0, 0, [], 1.0)
        assert metrics.total_tasks == 0
        assert metrics.avg_response_time == 0.0


class TestLoadAdapterService:
    """测试批量工程任务压测适配服务"""

    def test_initialization(self):
        """测试初始化"""
        service = LoadAdapterService()
        assert service.generator is not None

    def test_initialization_with_generator(self):
        """测试使用自定义生成器初始化"""
        generator = LoadGenerator()
        service = LoadAdapterService(generator=generator)
        assert service.generator is generator

    def test_run_load_test(self):
        """测试运行负载测试"""
        service = LoadAdapterService()
        config = LoadConfig(profile=LoadProfile.LIGHT, total_tasks=10)
        metrics = service.run_load_test(config)
        assert metrics.total_tasks == 10

    def test_get_metrics(self):
        """测试获取指标历史"""
        service = LoadAdapterService()
        config = LoadConfig(total_tasks=5)
        service.run_load_test(config)
        history = service.get_metrics()
        assert len(history) == 1

    def test_get_metrics_empty(self):
        """测试获取空指标历史"""
        service = LoadAdapterService()
        history = service.get_metrics()
        assert history == []

    def test_get_report(self):
        """测试获取测试报告"""
        service = LoadAdapterService()
        config = LoadConfig(total_tasks=10)
        service.run_load_test(config)
        report = service.get_report()
        assert "total_tasks" in report
        assert "completed" in report
        assert "failed" in report
        assert "throughput" in report
        assert "error_rate" in report
        assert "history_count" in report

    def test_get_report_empty(self):
        """测试获取空报告"""
        service = LoadAdapterService()
        report = service.get_report()
        assert "message" in report

    def test_suggest_scaling_high_error(self):
        """测试高错误率扩缩容推荐"""
        service = LoadAdapterService()
        metrics = LoadMetrics(
            total_tasks=100,
            completed=85,
            failed=15,
            avg_response_time=0.5,
            error_rate=15.0,
        )
        suggestion = service.suggest_scaling(metrics)
        assert suggestion["action"] == "scale_up"
        assert suggestion["recommended_instances"] == 3

    def test_suggest_scaling_moderate_error(self):
        """测试中等错误率扩缩容推荐"""
        service = LoadAdapterService()
        metrics = LoadMetrics(
            total_tasks=100,
            completed=93,
            failed=7,
            avg_response_time=0.3,
            error_rate=7.0,
        )
        suggestion = service.suggest_scaling(metrics)
        assert suggestion["action"] == "scale_up"

    def test_suggest_scaling_slow_response(self):
        """测试慢响应扩缩容推荐"""
        service = LoadAdapterService()
        metrics = LoadMetrics(
            total_tasks=100,
            completed=99,
            failed=1,
            avg_response_time=1.5,
            error_rate=1.0,
        )
        suggestion = service.suggest_scaling(metrics)
        assert suggestion["action"] == "scale_up"

    def test_suggest_scaling_low_load(self):
        """测试低负载扩缩容推荐"""
        service = LoadAdapterService()
        metrics = LoadMetrics(
            total_tasks=100,
            completed=100,
            failed=0,
            avg_response_time=0.05,
            error_rate=0.0,
        )
        suggestion = service.suggest_scaling(metrics)
        assert suggestion["action"] == "scale_down"

    def test_suggest_scaling_normal(self):
        """测试正常负载扩缩容推荐"""
        service = LoadAdapterService()
        metrics = LoadMetrics(
            total_tasks=100,
            completed=98,
            failed=2,
            avg_response_time=0.3,
            error_rate=2.0,
        )
        suggestion = service.suggest_scaling(metrics)
        assert suggestion["action"] == "maintain"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
