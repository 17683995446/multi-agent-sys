"""
阶段55验收测试：评审通过→测试回归链路
"""

import pytest
from src.architecture.pipeline_testing import (
    TestType,
    TestStatus,
    TestCase,
    TestSuite,
    BaselineResult,
    RegressionReport,
    TestRunner,
    RegressionManager,
    TestingPipeline,
)


class TestTestType:
    """测试测试类型枚举"""

    def test_type_values(self):
        """测试测试类型枚举值"""
        assert TestType.UNIT.value == "unit"
        assert TestType.INTEGRATION.value == "integration"
        assert TestType.REGRESSION.value == "regression"
        assert TestType.PERFORMANCE.value == "performance"

    def test_all_types(self):
        """测试所有类型"""
        types = list(TestType)
        assert len(types) == 4


class TestTestStatus:
    """测试测试状态枚举"""

    def test_status_values(self):
        """测试测试状态枚举值"""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(TestStatus)
        assert len(statuses) == 5


class TestTestCase:
    """测试测试用例"""

    def test_default_creation(self):
        """测试默认创建"""
        tc = TestCase()
        assert tc.test_id != ""
        assert tc.test_type == TestType.UNIT
        assert tc.name == ""
        assert tc.description == ""
        assert tc.status == TestStatus.PENDING
        assert tc.duration == 0.0
        assert tc.error_message == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        tc = TestCase(
            test_type=TestType.INTEGRATION,
            name="test_login",
            description="测试登录功能",
            status=TestStatus.PASSED,
            duration=1.5,
        )
        assert tc.test_type == TestType.INTEGRATION
        assert tc.name == "test_login"
        assert tc.description == "测试登录功能"
        assert tc.status == TestStatus.PASSED
        assert tc.duration == 1.5

    def test_test_id_unique(self):
        """测试用例ID唯一性"""
        tc1 = TestCase()
        tc2 = TestCase()
        assert tc1.test_id != tc2.test_id


class TestTestSuite:
    """测试测试套件"""

    def test_default_creation(self):
        """测试默认创建"""
        suite = TestSuite()
        assert suite.suite_id != ""
        assert suite.name == ""
        assert suite.test_cases == []
        assert suite.total == 0
        assert suite.passed == 0
        assert suite.failed == 0
        assert suite.duration == 0.0

    def test_custom_creation(self):
        """测试自定义创建"""
        tc1 = TestCase(name="test1")
        tc2 = TestCase(name="test2")
        suite = TestSuite(
            name="登录测试套件",
            test_cases=[tc1, tc2],
            total=2,
            passed=2,
        )
        assert suite.name == "登录测试套件"
        assert len(suite.test_cases) == 2
        assert suite.total == 2
        assert suite.passed == 2

    def test_suite_id_unique(self):
        """测试套件ID唯一性"""
        s1 = TestSuite()
        s2 = TestSuite()
        assert s1.suite_id != s2.suite_id


class TestTestRunner:
    """测试测试运行器"""

    def test_initialization(self):
        """测试初始化"""
        runner = TestRunner()
        assert len(runner.results) == 0

    def test_run_unit_test_pass(self):
        """测试运行通过的单元测试"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.UNIT, name="test_addition")
        result = runner.run_test(tc)
        assert result.status == TestStatus.PASSED
        assert result.duration >= 0

    def test_run_unit_test_fail(self):
        """测试运行失败的单元测试"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.UNIT, name="test_fail_case")
        result = runner.run_test(tc)
        assert result.status == TestStatus.FAILED
        assert result.error_message != ""

    def test_run_integration_test_pass(self):
        """测试运行通过的集成测试"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.INTEGRATION, name="test_api_call")
        result = runner.run_test(tc)
        assert result.status == TestStatus.PASSED

    def test_run_integration_test_fail(self):
        """测试运行失败的集成测试"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.INTEGRATION, name="test_timeout_case")
        result = runner.run_test(tc)
        assert result.status == TestStatus.FAILED

    def test_run_regression_test_pass(self):
        """测试运行通过的回归测试"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.REGRESSION, name="test_stable_feature")
        result = runner.run_test(tc)
        assert result.status == TestStatus.PASSED

    def test_run_regression_test_fail(self):
        """测试运行失败的回归测试"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.REGRESSION, name="test_regress_case")
        result = runner.run_test(tc)
        assert result.status == TestStatus.FAILED

    def test_run_performance_test_pass(self):
        """测试运行通过的性能测试"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.PERFORMANCE, name="test_load")
        result = runner.run_test(tc)
        assert result.status == TestStatus.PASSED

    def test_run_performance_test_fail(self):
        """测试运行失败的性能测试"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.PERFORMANCE, name="test_slow_response")
        result = runner.run_test(tc)
        assert result.status == TestStatus.FAILED

    def test_run_suite(self):
        """测试运行测试套件"""
        runner = TestRunner()
        tc1 = TestCase(test_type=TestType.UNIT, name="test_a")
        tc2 = TestCase(test_type=TestType.UNIT, name="test_b")
        tc3 = TestCase(test_type=TestType.UNIT, name="test_fail_c")
        suite = TestSuite(name="测试套件", test_cases=[tc1, tc2, tc3])
        result = runner.run_suite(suite)
        assert result.total == 3
        assert result.passed == 2
        assert result.failed == 1
        assert result.duration >= 0

    def test_run_suite_all_pass(self):
        """测试运行全部通过的套件"""
        runner = TestRunner()
        tc1 = TestCase(test_type=TestType.UNIT, name="test_x")
        tc2 = TestCase(test_type=TestType.UNIT, name="test_y")
        suite = TestSuite(name="全部通过", test_cases=[tc1, tc2])
        result = runner.run_suite(suite)
        assert result.passed == 2
        assert result.failed == 0

    def test_run_suite_empty(self):
        """测试运行空套件"""
        runner = TestRunner()
        suite = TestSuite(name="空套件")
        result = runner.run_suite(suite)
        assert result.total == 0
        assert result.passed == 0
        assert result.failed == 0

    def test_results_stored(self):
        """测试结果存储"""
        runner = TestRunner()
        tc = TestCase(test_type=TestType.UNIT, name="test_stored")
        runner.run_test(tc)
        assert tc.test_id in runner.results


class TestRegressionManager:
    """测试回归管理器"""

    def test_initialization(self):
        """测试初始化"""
        manager = RegressionManager()
        assert len(manager.baselines) == 0

    def test_add_baseline(self):
        """测试添加基线"""
        manager = RegressionManager()
        baseline = manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True, "test_b": True, "test_c": False},
        )
        assert baseline.baseline_id in manager.baselines
        assert baseline.name == "v1.0基线"
        assert len(baseline.test_results) == 3

    def test_compare_with_baseline_no_regression(self):
        """测试与基线比对无回归"""
        manager = RegressionManager()
        baseline = manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True, "test_b": True},
        )
        current = {"test_a": True, "test_b": True}
        report = manager.compare_with_baseline(baseline.baseline_id, current)
        assert report is not None
        assert report.is_regressed is False
        assert len(report.regressions) == 0

    def test_compare_with_baseline_has_regression(self):
        """测试与基线比对有回归"""
        manager = RegressionManager()
        baseline = manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True, "test_b": True},
        )
        current = {"test_a": False, "test_b": True}
        report = manager.compare_with_baseline(baseline.baseline_id, current)
        assert report is not None
        assert report.is_regressed is True
        assert "test_a" in report.regressions

    def test_compare_with_baseline_improvement(self):
        """测试与基线比对有改进"""
        manager = RegressionManager()
        baseline = manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True, "test_b": False},
        )
        current = {"test_a": True, "test_b": True}
        report = manager.compare_with_baseline(baseline.baseline_id, current)
        assert report is not None
        assert "test_b" in report.improvements
        assert report.is_regressed is False

    def test_compare_with_baseline_nonexistent(self):
        """测试与不存在的基线比对"""
        manager = RegressionManager()
        current = {"test_a": True}
        report = manager.compare_with_baseline("nonexistent", current)
        assert report is None

    def test_detect_regressions(self):
        """测试检测回归"""
        manager = RegressionManager()
        baseline = manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True, "test_b": True, "test_c": True},
        )
        current = {"test_a": True, "test_b": False, "test_c": True}
        regressions = manager.detect_regressions(baseline.baseline_id, current)
        assert "test_b" in regressions
        assert len(regressions) == 1

    def test_detect_regressions_no_baseline(self):
        """测试检测回归时基线不存在"""
        manager = RegressionManager()
        regressions = manager.detect_regressions("nonexistent", {"test_a": True})
        assert regressions == []

    def test_compare_with_new_tests(self):
        """测试与基线比对新增测试"""
        manager = RegressionManager()
        baseline = manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True},
        )
        current = {"test_a": True, "test_new": True}
        report = manager.compare_with_baseline(baseline.baseline_id, current)
        assert report is not None
        assert report.total_tests == 2


class TestTestingPipeline:
    """测试测试流水线"""

    def test_initialization(self):
        """测试初始化"""
        pipeline = TestingPipeline()
        assert pipeline.runner is not None
        assert pipeline.regression_manager is not None
        assert len(pipeline.suites) == 0
        assert len(pipeline.reports) == 0

    def test_process_basic(self):
        """测试基本处理流程"""
        pipeline = TestingPipeline()
        tc1 = TestCase(test_type=TestType.UNIT, name="test_a")
        tc2 = TestCase(test_type=TestType.UNIT, name="test_b")
        suite = pipeline.process([tc1, tc2], suite_name="基本测试")
        assert suite.suite_id in pipeline.suites
        assert suite.total == 2
        assert suite.passed == 2
        assert suite.failed == 0

    def test_process_with_failures(self):
        """测试包含失败的处理流程"""
        pipeline = TestingPipeline()
        tc1 = TestCase(test_type=TestType.UNIT, name="test_a")
        tc2 = TestCase(test_type=TestType.UNIT, name="test_fail_b")
        suite = pipeline.process([tc1, tc2], suite_name="含失败测试")
        assert suite.total == 2
        assert suite.passed == 1
        assert suite.failed == 1

    def test_process_with_baseline(self):
        """测试带基线的处理流程"""
        pipeline = TestingPipeline()
        # 先添加基线
        baseline = pipeline.regression_manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True, "test_b": True},
        )
        # 运行测试并比对
        tc1 = TestCase(test_type=TestType.UNIT, name="test_a")
        tc2 = TestCase(test_type=TestType.UNIT, name="test_b")
        suite = pipeline.process(
            [tc1, tc2],
            suite_name="基线比对测试",
            baseline_id=baseline.baseline_id,
        )
        assert suite.suite_id in pipeline.reports
        report = pipeline.get_regression_report(suite.suite_id)
        assert report is not None
        assert report.is_regressed is False

    def test_process_with_regression(self):
        """测试带回归的处理流程"""
        pipeline = TestingPipeline()
        # 基线：全部通过
        baseline = pipeline.regression_manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True, "test_fail_b": True},
        )
        # 当前：有失败
        tc1 = TestCase(test_type=TestType.UNIT, name="test_a")
        tc2 = TestCase(test_type=TestType.UNIT, name="test_fail_b")
        suite = pipeline.process(
            [tc1, tc2],
            suite_name="回归检测",
            baseline_id=baseline.baseline_id,
        )
        report = pipeline.get_regression_report(suite.suite_id)
        assert report is not None
        assert report.is_regressed is True
        assert "test_fail_b" in report.regressions

    def test_process_without_baseline(self):
        """测试不带基线的处理流程"""
        pipeline = TestingPipeline()
        tc = TestCase(test_type=TestType.UNIT, name="test_a")
        suite = pipeline.process([tc], suite_name="无基线测试")
        assert suite.suite_id not in pipeline.reports

    def test_get_results(self):
        """测试获取结果"""
        pipeline = TestingPipeline()
        tc = TestCase(test_type=TestType.UNIT, name="test_a")
        suite = pipeline.process([tc], suite_name="获取结果测试")
        result = pipeline.get_results(suite.suite_id)
        assert result is not None
        assert result.suite_id == suite.suite_id

    def test_get_results_nonexistent(self):
        """测试获取不存在的结果"""
        pipeline = TestingPipeline()
        result = pipeline.get_results("nonexistent")
        assert result is None

    def test_get_regression_report(self):
        """测试获取回归报告"""
        pipeline = TestingPipeline()
        baseline = pipeline.regression_manager.add_baseline(
            name="v1.0基线",
            test_results={"test_a": True},
        )
        tc = TestCase(test_type=TestType.UNIT, name="test_a")
        suite = pipeline.process(
            [tc], suite_name="回归报告测试", baseline_id=baseline.baseline_id
        )
        report = pipeline.get_regression_report(suite.suite_id)
        assert report is not None

    def test_get_regression_report_nonexistent(self):
        """测试获取不存在的回归报告"""
        pipeline = TestingPipeline()
        report = pipeline.get_regression_report("nonexistent")
        assert report is None

    def test_full_pipeline_workflow(self):
        """测试完整流水线工作流"""
        pipeline = TestingPipeline()

        # 1. 建立基线
        baseline = pipeline.regression_manager.add_baseline(
            name="v1.0基线",
            test_results={
                "test_login": True,
                "test_logout": True,
                "test_register": True,
            },
        )

        # 2. 运行测试套件
        test_cases = [
            TestCase(test_type=TestType.UNIT, name="test_login"),
            TestCase(test_type=TestType.UNIT, name="test_logout"),
            TestCase(test_type=TestType.UNIT, name="test_register"),
        ]
        suite = pipeline.process(
            test_cases,
            suite_name="完整流程测试",
            baseline_id=baseline.baseline_id,
        )

        # 3. 验证结果
        assert suite.total == 3
        assert suite.passed == 3
        assert suite.failed == 0

        # 4. 验证回归报告
        report = pipeline.get_regression_report(suite.suite_id)
        assert report is not None
        assert report.is_regressed is False

    def test_mixed_test_types(self):
        """测试混合测试类型"""
        pipeline = TestingPipeline()
        test_cases = [
            TestCase(test_type=TestType.UNIT, name="test_unit_a"),
            TestCase(test_type=TestType.INTEGRATION, name="test_int_b"),
            TestCase(test_type=TestType.REGRESSION, name="test_reg_c"),
            TestCase(test_type=TestType.PERFORMANCE, name="test_perf_d"),
        ]
        suite = pipeline.process(test_cases, suite_name="混合类型测试")
        assert suite.total == 4
        assert suite.passed == 4

    def test_empty_test_cases(self):
        """测试空测试用例列表"""
        pipeline = TestingPipeline()
        suite = pipeline.process([], suite_name="空测试")
        assert suite.total == 0
        assert suite.passed == 0
        assert suite.failed == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
