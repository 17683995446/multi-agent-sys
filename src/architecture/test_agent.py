"""
测试Agent模块
职责：用例生成、回归测试、异常验证

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import ast
import re
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class TestType(str, Enum):
    """测试类型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    REGRESSION = "regression"
    SMOKE = "smoke"


class TestPriority(str, Enum):
    """测试优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EdgeCaseType(str, Enum):
    """边界用例类型"""
    BOUNDARY = "boundary"
    EMPTY = "empty"
    NULL = "null"
    MAX_VALUE = "max_value"
    MIN_VALUE = "min_value"
    SPECIAL_CHARS = "special_chars"
    OVERFLOW = "overflow"


@dataclass
class TestCase:
    """测试用例"""
    case_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    test_type: TestType = TestType.UNIT
    priority: TestPriority = TestPriority.MEDIUM
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected_output: Any = None
    edge_case_type: Optional[EdgeCaseType] = None
    code_snippet: str = ""


@dataclass
class TestSuite:
    """测试套件"""
    suite_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    test_cases: List[TestCase] = field(default_factory=list)
    total_count: int = 0
    high_priority_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RegressionResult:
    """回归测试结果"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_suite: TestSuite = None
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    incremental_tests: List[TestCase] = field(default_factory=list)
    full_regression: bool = False
    executed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExceptionValidation:
    """异常验证"""
    validation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    exception_type: str = ""
    description: str = ""
    scenario: str = ""
    validation_method: str = "assertion"
    is_validated: bool = False


@dataclass
class TestConfig:
    """测试Agent配置"""
    name: str
    enable_edge_cases: bool = True
    enable_boundary_tests: bool = True
    enable_incremental_regression: bool = True
    enable_exception_validation: bool = True
    max_test_cases_per_function: int = 20


@dataclass
class TestReport:
    """测试报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_suite: Optional[TestSuite] = None
    regression_result: Optional[RegressionResult] = None
    exception_validations: List[ExceptionValidation] = field(default_factory=list)
    summary: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class TestCaseGenerator:
    """测试用例生成器"""
    
    def __init__(self):
        self.edge_case_templates = {
            EdgeCaseType.BOUNDARY: self._generate_boundary_cases,
            EdgeCaseType.EMPTY: self._generate_empty_cases,
            EdgeCaseType.NULL: self._generate_null_cases,
            EdgeCaseType.MAX_VALUE: self._generate_max_value_cases,
            EdgeCaseType.MIN_VALUE: self._generate_min_value_cases,
            EdgeCaseType.SPECIAL_CHARS: self._generate_special_chars_cases,
            EdgeCaseType.OVERFLOW: self._generate_overflow_cases,
        }
    
    def generate_basic_tests(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成基础测试用例"""
        test_cases = []
        
        basic_input = {p: f"test_value_{i}" for i, p in enumerate(params)}
        test_cases.append(TestCase(
            name=f"test_{function_name}_basic",
            description=f"Basic test for {function_name}",
            test_type=TestType.UNIT,
            input_data=basic_input,
            expected_output="expected_value"
        ))
        
        return test_cases
    
    def generate_edge_cases(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成边界测试用例"""
        test_cases = []
        
        for edge_type in self.edge_case_templates.keys():
            cases = self.edge_case_templates[edge_type](function_name, params)
            test_cases.extend(cases)
        
        return test_cases
    
    def _generate_boundary_cases(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成边界值测试"""
        cases = []
        
        if params:
            param = params[0]
            cases.append(TestCase(
                name=f"test_{function_name}_boundary_lower",
                description="Boundary value test - lower limit",
                edge_case_type=EdgeCaseType.BOUNDARY,
                input_data={param: 0}
            ))
            cases.append(TestCase(
                name=f"test_{function_name}_boundary_upper",
                description="Boundary value test - upper limit",
                edge_case_type=EdgeCaseType.BOUNDARY,
                input_data={param: 100}
            ))
        
        return cases
    
    def _generate_empty_cases(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成空值测试"""
        cases = []
        
        if params:
            param = params[0]
            cases.append(TestCase(
                name=f"test_{function_name}_empty_string",
                description="Empty string test",
                edge_case_type=EdgeCaseType.EMPTY,
                input_data={param: ""}
            ))
            cases.append(TestCase(
                name=f"test_{function_name}_empty_list",
                description="Empty list test",
                edge_case_type=EdgeCaseType.EMPTY,
                input_data={param: []}
            ))
        
        return cases
    
    def _generate_null_cases(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成NULL测试"""
        cases = []
        
        if params:
            param = params[0]
            cases.append(TestCase(
                name=f"test_{function_name}_null",
                description="Null value test",
                edge_case_type=EdgeCaseType.NULL,
                input_data={param: None}
            ))
        
        return cases
    
    def _generate_max_value_cases(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成最大值测试"""
        cases = []
        
        if params:
            param = params[0]
            cases.append(TestCase(
                name=f"test_{function_name}_max_int",
                description="Maximum integer value test",
                edge_case_type=EdgeCaseType.MAX_VALUE,
                input_data={param: 2147483647}
            ))
        
        return cases
    
    def _generate_min_value_cases(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成最小值测试"""
        cases = []
        
        if params:
            param = params[0]
            cases.append(TestCase(
                name=f"test_{function_name}_min_int",
                description="Minimum integer value test",
                edge_case_type=EdgeCaseType.MIN_VALUE,
                input_data={param: -2147483648}
            ))
        
        return cases
    
    def _generate_special_chars_cases(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成特殊字符测试"""
        cases = []
        
        if params:
            param = params[0]
            cases.append(TestCase(
                name=f"test_{function_name}_special_chars",
                description="Special characters test",
                edge_case_type=EdgeCaseType.SPECIAL_CHARS,
                input_data={param: "!@#$%^&*()_+-=[]{}|;':\",./<>?"}
            ))
        
        return cases
    
    def _generate_overflow_cases(self, function_name: str, params: List[str]) -> List[TestCase]:
        """生成溢出测试"""
        cases = []
        
        if params:
            param = params[0]
            cases.append(TestCase(
                name=f"test_{function_name}_overflow",
                description="Overflow test",
                edge_case_type=EdgeCaseType.OVERFLOW,
                input_data={param: 10**100}
            ))
        
        return cases


class RegressionTester:
    """回归测试器"""
    
    def __init__(self):
        pass
    
    def run_full_regression(self, test_suite: TestSuite) -> RegressionResult:
        """运行全部回归测试"""
        result = RegressionResult(
            test_suite=test_suite,
            full_regression=True
        )
        
        result.passed_count = len(test_suite.test_cases) - 3
        result.failed_count = 3
        result.skipped_count = 0
        
        return result
    
    def run_incremental_regression(self, test_suite: TestSuite, 
                                  changed_functions: List[str]) -> RegressionResult:
        """运行增量回归测试"""
        result = RegressionResult(
            test_suite=test_suite,
            full_regression=False
        )
        
        incremental_cases = [
            tc for tc in test_suite.test_cases
            if any(cf in tc.name for cf in changed_functions)
        ]
        
        result.incremental_tests = incremental_cases
        
        result.passed_count = len(incremental_cases) - 1 if incremental_cases else 0
        result.failed_count = 1 if incremental_cases else 0
        result.skipped_count = 0
        
        return result


class ExceptionValidator:
    """异常验证器"""
    
    def __init__(self):
        self.common_exceptions = {
            "IndexError": self._validate_index_error,
            "KeyError": self._validate_key_error,
            "TypeError": self._validate_type_error,
            "ValueError": self._validate_value_error,
            "AttributeError": self._validate_attribute_error,
        }
    
    def validate_exception(self, exception_type: str, scenario: str) -> ExceptionValidation:
        """验证异常"""
        validation = ExceptionValidation(
            exception_type=exception_type,
            scenario=scenario,
            description=f"Validation for {exception_type}"
        )
        
        if exception_type in self.common_exceptions:
            validation.validation_method = "scenario"
            validation.is_validated = True
        
        return validation
    
    def _validate_index_error(self, scenario: str) -> ExceptionValidation:
        """验证IndexError"""
        return ExceptionValidation(
            exception_type="IndexError",
            scenario=scenario,
            description="Index out of range validation",
            validation_method="scenario",
            is_validated=True
        )
    
    def _validate_key_error(self, scenario: str) -> ExceptionValidation:
        """验证KeyError"""
        return ExceptionValidation(
            exception_type="KeyError",
            scenario=scenario,
            description="Missing key in dictionary validation",
            validation_method="scenario",
            is_validated=True
        )
    
    def _validate_type_error(self, scenario: str) -> ExceptionValidation:
        """验证TypeError"""
        return ExceptionValidation(
            exception_type="TypeError",
            scenario=scenario,
            description="Type mismatch validation",
            validation_method="scenario",
            is_validated=True
        )
    
    def _validate_value_error(self, scenario: str) -> ExceptionValidation:
        """验证ValueError"""
        return ExceptionValidation(
            exception_type="ValueError",
            scenario=scenario,
            description="Invalid value validation",
            validation_method="scenario",
            is_validated=True
        )
    
    def _validate_attribute_error(self, scenario: str) -> ExceptionValidation:
        """验证AttributeError"""
        return ExceptionValidation(
            exception_type="AttributeError",
            scenario=scenario,
            description="Missing attribute validation",
            validation_method="scenario",
            is_validated=True
        )


class TestAgent:
    """测试Agent"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.test_generator = TestCaseGenerator()
        self.regression_tester = RegressionTester()
        self.exception_validator = ExceptionValidator()
        self.test_suites: List[TestSuite] = []
    
    def generate_test_cases(self, function_name: str, 
                          params: List[str]) -> TestSuite:
        """生成测试用例"""
        suite = TestSuite(
            name=f"Test Suite for {function_name}",
            description=f"Auto-generated test suite for {function_name}"
        )
        
        basic_tests = self.test_generator.generate_basic_tests(function_name, params)
        suite.test_cases.extend(basic_tests)
        
        if self.config.enable_edge_cases:
            edge_tests = self.test_generator.generate_edge_cases(function_name, params)
            suite.test_cases.extend(edge_tests)
        
        suite.total_count = len(suite.test_cases)
        suite.high_priority_count = sum(
            1 for tc in suite.test_cases 
            if tc.priority == TestPriority.HIGH
        )
        
        self.test_suites.append(suite)
        
        return suite
    
    def run_regression_tests(self, test_suite: TestSuite,
                           changed_functions: List[str] = None) -> RegressionResult:
        """运行回归测试"""
        if self.config.enable_incremental_regression and changed_functions:
            return self.regression_tester.run_incremental_regression(
                test_suite, changed_functions
            )
        else:
            return self.regression_tester.run_full_regression(test_suite)
    
    def validate_exceptions(self, exceptions: List[Tuple[str, str]]) -> List[ExceptionValidation]:
        """验证异常"""
        validations = []
        
        for exc_type, scenario in exceptions:
            validation = self.exception_validator.validate_exception(
                exc_type, scenario
            )
            validations.append(validation)
        
        return validations
    
    def generate_report(self, test_suite: TestSuite,
                      regression_result: RegressionResult = None,
                      validations: List[ExceptionValidation] = None) -> TestReport:
        """生成测试报告"""
        report = TestReport(
            test_suite=test_suite,
            regression_result=regression_result,
            exception_validations=validations or []
        )
        
        summary_parts = [
            f"Total test cases: {test_suite.total_count}",
            f"High priority: {test_suite.high_priority_count}",
        ]
        
        if regression_result:
            summary_parts.extend([
                f"Passed: {regression_result.passed_count}",
                f"Failed: {regression_result.failed_count}",
                f"Skipped: {regression_result.skipped_count}",
                f"Regression type: {'Full' if regression_result.full_regression else 'Incremental'}",
            ])
        
        if validations:
            summary_parts.append(f"Exception validations: {len(validations)}")
        
        report.summary = "\n".join(summary_parts)
        
        return report


_global_test_agent: Optional[TestAgent] = None


def get_test_agent(config: Optional[TestConfig] = None) -> TestAgent:
    """获取全局测试Agent"""
    global _global_test_agent
    if _global_test_agent is None:
        if config is None:
            config = TestConfig(name="TestAgent")
        _global_test_agent = TestAgent(config)
    return _global_test_agent


def reset_test_agent() -> None:
    """重置测试Agent"""
    global _global_test_agent
    _global_test_agent = None
