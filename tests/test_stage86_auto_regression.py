"""
阶段86验收测试 - 全自动回归测试套件
"""

import pytest
from src.architecture.auto_regression import (
    RegressionScope,
    RegressionStatus,
    RegressionSuite,
    RegressionRunner,
    AutoRegressionService,
)


class TestRegressionScope:
    """测试回归测试范围枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RegressionScope.FULL.value == "full"
        assert RegressionScope.PARTIAL.value == "partial"
        assert RegressionScope.INCREMENTAL.value == "incremental"
        assert RegressionScope.SMOKE.value == "smoke"

    def test_all_scopes(self):
        """测试所有范围"""
        scopes = list(RegressionScope)
        assert len(scopes) == 4


class TestRegressionStatus:
    """测试回归测试状态枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RegressionStatus.PENDING.value == "pending"
        assert RegressionStatus.RUNNING.value == "running"
        assert RegressionStatus.PASSED.value == "passed"
        assert RegressionStatus.FAILED.value == "failed"
        assert RegressionStatus.ERROR.value == "error"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(RegressionStatus)
        assert len(statuses) == 5


class TestRegressionSuite:
    """测试回归测试套件"""

    def test_default_creation(self):
        """测试默认创建"""
        suite = RegressionSuite()
        assert suite.suite_id != ""
        assert suite.scope == RegressionScope.FULL
        assert suite.test_cases == []
        assert suite.status == RegressionStatus.PENDING
        assert suite.pass_rate == 0.0
        assert suite.duration == 0.0
        assert suite.failures == []

    def test_custom_creation(self):
        """测试自定义创建"""
        suite = RegressionSuite(
            scope=RegressionScope.SMOKE,
            test_cases=["test_login", "test_logout"],
            status=RegressionStatus.RUNNING,
            pass_rate=50.0,
            duration=10.5,
            failures=["test_logout"],
        )
        assert suite.scope == RegressionScope.SMOKE
        assert len(suite.test_cases) == 2
        assert suite.status == RegressionStatus.RUNNING
        assert suite.pass_rate == 50.0
        assert suite.duration == 10.5
        assert len(suite.failures) == 1

    def test_suite_id_unique(self):
        """测试套件ID唯一性"""
        s1 = RegressionSuite()
        s2 = RegressionSuite()
        assert s1.suite_id != s2.suite_id


class TestRegressionRunner:
    """测试回归测试运行器"""

    def test_initialization(self):
        """测试初始化"""
        runner = RegressionRunner()
        assert len(runner._suites) == 0

    def test_run_full(self):
        """测试执行全量回归"""
        runner = RegressionRunner()
        suite = RegressionSuite(
            scope=RegressionScope.FULL,
            test_cases=["test_a", "test_b", "test_c"],
        )
        result = runner.run(suite)
        assert result.status == RegressionStatus.PASSED
        assert result.pass_rate == 100.0
        assert result.duration > 0

    def test_run_full_empty(self):
        """测试空测试用例全量回归"""
        runner = RegressionRunner()
        suite = RegressionSuite(scope=RegressionScope.FULL)
        result = runner.run(suite)
        assert result.status == RegressionStatus.PASSED
        assert result.pass_rate == 100.0

    def test_run_partial(self):
        """测试执行部分回归"""
        runner = RegressionRunner()
        suite = RegressionSuite(
            scope=RegressionScope.PARTIAL,
            test_cases=["test_a", "test_b", "test_c", "test_d", "test_e"],
        )
        result = runner.run(suite)
        assert result.status == RegressionStatus.PASSED
        assert result.pass_rate >= 80.0

    def test_run_partial_empty(self):
        """测试空测试用例部分回归"""
        runner = RegressionRunner()
        suite = RegressionSuite(scope=RegressionScope.PARTIAL)
        result = runner.run(suite)
        assert result.status == RegressionStatus.PASSED

    def test_run_incremental(self):
        """测试执行增量回归"""
        runner = RegressionRunner()
        suite = RegressionSuite(
            scope=RegressionScope.INCREMENTAL,
            test_cases=["test_new_1", "test_new_2"],
        )
        result = runner.run(suite)
        assert result.status == RegressionStatus.PASSED
        assert result.pass_rate == 100.0

    def test_run_incremental_empty(self):
        """测试空测试用例增量回归"""
        runner = RegressionRunner()
        suite = RegressionSuite(scope=RegressionScope.INCREMENTAL)
        result = runner.run(suite)
        assert result.status == RegressionStatus.PASSED

    def test_run_smoke(self):
        """测试执行冒烟测试"""
        runner = RegressionRunner()
        suite = RegressionSuite(
            scope=RegressionScope.SMOKE,
            test_cases=["test_core_1", "test_core_2", "test_core_3"],
        )
        result = runner.run(suite)
        assert result.status == RegressionStatus.PASSED

    def test_run_smoke_empty(self):
        """测试空测试用例冒烟测试"""
        runner = RegressionRunner()
        suite = RegressionSuite(scope=RegressionScope.SMOKE)
        result = runner.run(suite)
        assert result.status == RegressionStatus.PASSED

    def test_generate_report(self):
        """测试生成报告"""
        runner = RegressionRunner()
        suite = RegressionSuite(
            scope=RegressionScope.FULL,
            test_cases=["test_a", "test_b"],
        )
        runner.run(suite)
        report = runner.generate_report(suite.suite_id)
        assert "suite_id" in report
        assert "scope" in report
        assert "status" in report
        assert "pass_rate" in report
        assert "duration" in report
        assert "total_cases" in report
        assert "failures" in report

    def test_generate_report_not_found(self):
        """测试生成不存在的套件报告"""
        runner = RegressionRunner()
        report = runner.generate_report("nonexistent")
        assert "message" in report

    def test_run_saves_suite(self):
        """测试运行后保存套件"""
        runner = RegressionRunner()
        suite = RegressionSuite(
            scope=RegressionScope.FULL,
            test_cases=["test_1"],
        )
        runner.run(suite)
        assert suite.suite_id in runner._suites

    def test_run_full_duration(self):
        """测试全量回归执行时长"""
        runner = RegressionRunner()
        suite = RegressionSuite(
            scope=RegressionScope.FULL,
            test_cases=["test_1", "test_2", "test_3"],
        )
        result = runner.run(suite)
        assert result.duration >= 0


class TestAutoRegressionService:
    """测试全自动回归测试服务"""

    def test_initialization(self):
        """测试初始化"""
        service = AutoRegressionService()
        assert service.runner is not None

    def test_initialization_with_runner(self):
        """测试使用自定义运行器初始化"""
        runner = RegressionRunner()
        service = AutoRegressionService(runner=runner)
        assert service.runner is runner

    def test_run(self):
        """测试执行回归测试"""
        service = AutoRegressionService()
        suite = RegressionSuite(
            scope=RegressionScope.FULL,
            test_cases=["test_a", "test_b"],
        )
        result = service.run(suite)
        assert result.status == RegressionStatus.PASSED

    def test_get_result(self):
        """测试获取结果"""
        service = AutoRegressionService()
        suite = RegressionSuite(
            scope=RegressionScope.INCREMENTAL,
            test_cases=["test_1"],
        )
        service.run(suite)
        result = service.get_result(suite.suite_id)
        assert result is not None
        assert result.suite_id == suite.suite_id

    def test_get_result_not_found(self):
        """测试获取不存在的结果"""
        service = AutoRegressionService()
        result = service.get_result("nonexistent")
        assert result is None

    def test_get_report(self):
        """测试获取报告"""
        service = AutoRegressionService()
        suite = RegressionSuite(
            scope=RegressionScope.SMOKE,
            test_cases=["test_core"],
        )
        service.run(suite)
        report = service.get_report(suite.suite_id)
        assert "suite_id" in report
        assert "status" in report

    def test_get_report_not_found(self):
        """测试获取不存在的报告"""
        service = AutoRegressionService()
        report = service.get_report("nonexistent")
        assert "message" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
