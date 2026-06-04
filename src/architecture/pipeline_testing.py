"""
评审通过→测试回归链路
职责：测试执行、回归检测、基线比对

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TestType(str, Enum):
    """测试类型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    PERFORMANCE = "performance"


class TestStatus(str, Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestCase:
    """测试用例"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_type: TestType = TestType.UNIT
    name: str = ""
    description: str = ""
    status: TestStatus = TestStatus.PENDING
    duration: float = 0.0
    error_message: str = ""

    def __post_init__(self):
        logger.debug(f"TestCase created: id={self.test_id}, name={self.name}, "
                     f"type={self.test_type.value}")


@dataclass
class TestSuite:
    """测试套件"""
    suite_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    test_cases: List[TestCase] = field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0
    duration: float = 0.0

    def __post_init__(self):
        logger.debug(f"TestSuite created: id={self.suite_id}, name={self.name}")


@dataclass
class BaselineResult:
    """基线结果"""
    baseline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    test_results: Dict[str, bool] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"BaselineResult created: id={self.baseline_id}, name={self.name}")


@dataclass
class RegressionReport:
    """回归报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    regressions: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    is_regressed: bool = False

    def __post_init__(self):
        logger.debug(f"RegressionReport created: id={self.report_id}, "
                     f"regressed={self.is_regressed}")


class TestRunner:
    """测试运行器"""

    def __init__(self):
        """初始化测试运行器"""
        self.results: Dict[str, TestCase] = {}
        logger.info("TestRunner initialized")

    def run_test(self, test_case: TestCase) -> TestCase:
        """运行单个测试用例"""
        logger.info(f"TestRunner: running test id={test_case.test_id}, "
                    f"name={test_case.name}, type={test_case.test_type.value}")
        try:
            test_case.status = TestStatus.RUNNING
            start_time = time.time()

            if test_case.test_type == TestType.UNIT:
                result = self._run_unit_test(test_case)
            elif test_case.test_type == TestType.INTEGRATION:
                result = self._run_integration_test(test_case)
            elif test_case.test_type == TestType.REGRESSION:
                result = self._run_regression_test(test_case)
            elif test_case.test_type == TestType.PERFORMANCE:
                result = self._run_performance_test(test_case)
            else:
                result = self._run_unit_test(test_case)

            test_case.duration = round(time.time() - start_time, 4)
            test_case.status = result.status
            test_case.error_message = result.error_message

            self.results[test_case.test_id] = test_case
            logger.info(f"TestRunner: test id={test_case.test_id} completed, "
                        f"status={test_case.status.value}, duration={test_case.duration}")
        except Exception as e:
            logger.error(f"TestRunner: test id={test_case.test_id} failed: {e}")
            test_case.status = TestStatus.FAILED
            test_case.error_message = str(e)
            test_case.duration = round(time.time() - start_time, 4)
            self.results[test_case.test_id] = test_case

        return test_case

    def run_suite(self, suite: TestSuite) -> TestSuite:
        """运行测试套件"""
        logger.info(f"TestRunner: running suite id={suite.suite_id}, "
                    f"name={suite.name}, cases={len(suite.test_cases)}")
        try:
            start_time = time.time()

            for test_case in suite.test_cases:
                self.run_test(test_case)

            suite.duration = round(time.time() - start_time, 4)
            suite.total = len(suite.test_cases)
            suite.passed = sum(1 for tc in suite.test_cases if tc.status == TestStatus.PASSED)
            suite.failed = sum(1 for tc in suite.test_cases if tc.status == TestStatus.FAILED)

            logger.info(f"TestRunner: suite id={suite.suite_id} completed, "
                        f"total={suite.total}, passed={suite.passed}, "
                        f"failed={suite.failed}, duration={suite.duration}")
        except Exception as e:
            logger.error(f"TestRunner: suite id={suite.suite_id} failed: {e}")

        return suite

    def _run_unit_test(self, test_case: TestCase) -> TestCase:
        """运行单元测试"""
        logger.debug(f"TestRunner: running unit test id={test_case.test_id}")
        # 模拟单元测试执行
        result = TestCase(
            test_id=test_case.test_id,
            test_type=test_case.test_type,
            name=test_case.name,
            description=test_case.description,
        )

        # 基于测试名称模拟结果：包含"fail"的测试会失败
        if "fail" in test_case.name.lower() or "error" in test_case.name.lower():
            result.status = TestStatus.FAILED
            result.error_message = f"单元测试失败: {test_case.name}"
        else:
            result.status = TestStatus.PASSED

        return result

    def _run_integration_test(self, test_case: TestCase) -> TestCase:
        """运行集成测试"""
        logger.debug(f"TestRunner: running integration test id={test_case.test_id}")
        result = TestCase(
            test_id=test_case.test_id,
            test_type=test_case.test_type,
            name=test_case.name,
            description=test_case.description,
        )

        if "fail" in test_case.name.lower() or "timeout" in test_case.name.lower():
            result.status = TestStatus.FAILED
            result.error_message = f"集成测试失败: {test_case.name}"
        else:
            result.status = TestStatus.PASSED

        return result

    def _run_regression_test(self, test_case: TestCase) -> TestCase:
        """运行回归测试"""
        logger.debug(f"TestRunner: running regression test id={test_case.test_id}")
        result = TestCase(
            test_id=test_case.test_id,
            test_type=test_case.test_type,
            name=test_case.name,
            description=test_case.description,
        )

        if "regress" in test_case.name.lower() or "fail" in test_case.name.lower():
            result.status = TestStatus.FAILED
            result.error_message = f"回归测试失败: {test_case.name}"
        else:
            result.status = TestStatus.PASSED

        return result

    def _run_performance_test(self, test_case: TestCase) -> TestCase:
        """运行性能测试"""
        logger.debug(f"TestRunner: running performance test id={test_case.test_id}")
        result = TestCase(
            test_id=test_case.test_id,
            test_type=test_case.test_type,
            name=test_case.name,
            description=test_case.description,
        )

        if "slow" in test_case.name.lower() or "fail" in test_case.name.lower():
            result.status = TestStatus.FAILED
            result.error_message = f"性能测试失败: {test_case.name}"
        else:
            result.status = TestStatus.PASSED

        return result


class RegressionManager:
    """回归管理器"""

    def __init__(self):
        """初始化回归管理器"""
        self.baselines: Dict[str, BaselineResult] = {}
        logger.info("RegressionManager initialized")

    def add_baseline(self, name: str, test_results: Dict[str, bool]) -> BaselineResult:
        """添加基线结果"""
        logger.info(f"RegressionManager: adding baseline name={name}, "
                    f"tests={len(test_results)}")
        try:
            baseline = BaselineResult(
                name=name,
                test_results=test_results,
            )
            self.baselines[baseline.baseline_id] = baseline
            logger.info(f"RegressionManager: baseline added id={baseline.baseline_id}")
        except Exception as e:
            logger.error(f"RegressionManager: add_baseline failed: {e}")
            raise

        return baseline

    def compare_with_baseline(self, baseline_id: str,
                              current_results: Dict[str, bool]) -> Optional[RegressionReport]:
        """与基线进行比对"""
        logger.info(f"RegressionManager: comparing with baseline_id={baseline_id}, "
                    f"current_tests={len(current_results)}")
        if baseline_id not in self.baselines:
            logger.warning(f"RegressionManager: baseline_id={baseline_id} not found")
            return None

        try:
            baseline = self.baselines[baseline_id]
            report = RegressionReport()

            all_test_names = set(baseline.test_results.keys()) | set(current_results.keys())

            for test_name in all_test_names:
                baseline_passed = baseline.test_results.get(test_name, None)
                current_passed = current_results.get(test_name, None)

                if baseline_passed is True and current_passed is False:
                    report.regressions.append(test_name)
                elif baseline_passed is False and current_passed is True:
                    report.improvements.append(test_name)

            report.total_tests = len(all_test_names)
            report.passed_tests = sum(1 for v in current_results.values() if v is True)
            report.failed_tests = sum(1 for v in current_results.values() if v is False)
            report.is_regressed = len(report.regressions) > 0

            logger.info(f"RegressionManager: comparison done, "
                        f"regressions={len(report.regressions)}, "
                        f"improvements={len(report.improvements)}, "
                        f"is_regressed={report.is_regressed}")
        except Exception as e:
            logger.error(f"RegressionManager: compare_with_baseline failed: {e}")
            return None

        return report

    def detect_regressions(self, baseline_id: str,
                           current_results: Dict[str, bool]) -> List[str]:
        """检测回归"""
        logger.info(f"RegressionManager: detecting regressions for baseline_id={baseline_id}")
        report = self.compare_with_baseline(baseline_id, current_results)
        if report is None:
            logger.warning(f"RegressionManager: no report for baseline_id={baseline_id}")
            return []

        logger.info(f"RegressionManager: detected {len(report.regressions)} regressions")
        return report.regressions


class TestingPipeline:
    """测试流水线"""

    def __init__(self):
        """初始化测试流水线"""
        self.runner = TestRunner()
        self.regression_manager = RegressionManager()
        self.suites: Dict[str, TestSuite] = {}
        self.reports: Dict[str, RegressionReport] = {}
        logger.info("TestingPipeline initialized")

    def process(self, test_cases: List[TestCase], suite_name: str = "",
                baseline_id: Optional[str] = None) -> TestSuite:
        """处理测试流程：运行测试套件并可选地进行回归比对"""
        logger.info(f"TestingPipeline: processing {len(test_cases)} test cases, "
                    f"suite_name={suite_name}")
        try:
            suite = TestSuite(
                name=suite_name,
                test_cases=test_cases,
            )

            # 运行测试
            suite = self.runner.run_suite(suite)
            self.suites[suite.suite_id] = suite

            # 如果指定了基线，进行回归比对
            if baseline_id is not None:
                current_results = {
                    tc.name: tc.status == TestStatus.PASSED
                    for tc in suite.test_cases
                }
                report = self.regression_manager.compare_with_baseline(
                    baseline_id, current_results
                )
                if report is not None:
                    self.reports[suite.suite_id] = report

            logger.info(f"TestingPipeline: processing completed, "
                        f"suite_id={suite.suite_id}, "
                        f"passed={suite.passed}, failed={suite.failed}")
        except Exception as e:
            logger.error(f"TestingPipeline: process failed: {e}")
            raise

        return suite

    def get_results(self, suite_id: str) -> Optional[TestSuite]:
        """获取测试结果"""
        logger.debug(f"TestingPipeline: getting results for suite_id={suite_id}")
        result = self.suites.get(suite_id)
        if result is None:
            logger.warning(f"TestingPipeline: no results for suite_id={suite_id}")
        return result

    def get_regression_report(self, suite_id: str) -> Optional[RegressionReport]:
        """获取回归报告"""
        logger.debug(f"TestingPipeline: getting regression report for suite_id={suite_id}")
        report = self.reports.get(suite_id)
        if report is None:
            logger.warning(f"TestingPipeline: no regression report for suite_id={suite_id}")
        return report
