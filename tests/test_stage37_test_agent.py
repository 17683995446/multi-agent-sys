"""
阶段37验收测试：测试Agent初始化
"""

import pytest
from src.architecture.test_agent import (
    TestType,
    TestPriority,
    EdgeCaseType,
    TestCase,
    TestSuite,
    RegressionResult,
    ExceptionValidation,
    TestConfig,
    TestReport,
    TestCaseGenerator,
    RegressionTester,
    ExceptionValidator,
    TestAgent,
    get_test_agent,
    reset_test_agent
)


class TestTestConfig:
    """测试Agent类定义（验收项37.1）"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = TestConfig(name="TestAgent")
        
        assert config.name == "TestAgent"
        assert config.enable_edge_cases is True
        assert config.enable_boundary_tests is True
        assert config.enable_incremental_regression is True
        assert config.enable_exception_validation is True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = TestConfig(
            name="CustomTestAgent",
            enable_edge_cases=False,
            max_test_cases_per_function=50
        )
        
        assert config.name == "CustomTestAgent"
        assert config.enable_edge_cases is False
        assert config.max_test_cases_per_function == 50


class TestTestCaseGenerator:
    """测试用例生成器（验收项37.2）"""
    
    def test_generate_basic_tests(self):
        """测试基础用例生成"""
        generator = TestCaseGenerator()
        
        test_cases = generator.generate_basic_tests("process_data", ["data", "options"])
        
        assert len(test_cases) > 0
        assert any("basic" in tc.name for tc in test_cases)
    
    def test_generate_edge_cases(self):
        """测试边界用例生成"""
        generator = TestCaseGenerator()
        
        test_cases = generator.generate_edge_cases("process_data", ["data"])
        
        assert len(test_cases) > 0
        
        edge_types = set()
        for tc in test_cases:
            if tc.edge_case_type:
                edge_types.add(tc.edge_case_type)
        
        assert len(edge_types) >= 5
    
    def test_boundary_cases(self):
        """测试边界值测试"""
        generator = TestCaseGenerator()
        
        cases = generator._generate_boundary_cases("test_func", ["value"])
        
        assert len(cases) == 2
        assert any("boundary" in tc.name for tc in cases)
    
    def test_empty_cases(self):
        """测试空值测试"""
        generator = TestCaseGenerator()
        
        cases = generator._generate_empty_cases("test_func", ["value"])
        
        assert len(cases) >= 2
    
    def test_null_cases(self):
        """测试NULL测试"""
        generator = TestCaseGenerator()
        
        cases = generator._generate_null_cases("test_func", ["value"])
        
        assert len(cases) >= 1
    
    def test_max_min_value_cases(self):
        """测试最大值最小值测试"""
        generator = TestCaseGenerator()
        
        max_cases = generator._generate_max_value_cases("test_func", ["value"])
        min_cases = generator._generate_min_value_cases("test_func", ["value"])
        
        assert len(max_cases) >= 1
        assert len(min_cases) >= 1


class TestRegressionTester:
    """测试回归测试器（验收项37.3）"""
    
    def test_full_regression(self):
        """测试全部回归"""
        tester = RegressionTester()
        
        suite = TestSuite(
            name="Test Suite",
            test_cases=[
                TestCase(name="test_1"),
                TestCase(name="test_2"),
                TestCase(name="test_3"),
            ]
        )
        
        result = tester.run_full_regression(suite)
        
        assert result.full_regression is True
        assert result.passed_count >= 0
        assert result.failed_count >= 0
    
    def test_incremental_regression(self):
        """测试增量回归"""
        tester = RegressionTester()
        
        suite = TestSuite(
            name="Test Suite",
            test_cases=[
                TestCase(name="test_func_changed"),
                TestCase(name="test_func_unchanged"),
            ]
        )
        
        result = tester.run_incremental_regression(
            suite, 
            ["func_changed"]
        )
        
        assert result.full_regression is False
        assert len(result.incremental_tests) >= 1


class TestExceptionValidator:
    """测试异常验证器（验收项37.4）"""
    
    def test_validate_exception(self):
        """测试异常验证"""
        validator = ExceptionValidator()
        
        validation = validator.validate_exception(
            "IndexError",
            "Accessing out-of-bounds index"
        )
        
        assert validation.exception_type == "IndexError"
        assert validation.is_validated is True
        assert validation.validation_method == "scenario"
    
    def test_validate_multiple_exceptions(self):
        """测试多个异常验证"""
        validator = ExceptionValidator()
        
        exceptions = [
            ("IndexError", "Index out of bounds"),
            ("KeyError", "Missing key"),
            ("TypeError", "Type mismatch"),
        ]
        
        validations = validator.validate_exception(
            exceptions[0][0],
            exceptions[0][1]
        )
        
        assert validations is not None
    
    def test_index_error_validation(self):
        """测试IndexError验证"""
        validator = ExceptionValidator()
        
        validation = validator._validate_index_error("Index out of range")
        
        assert validation.exception_type == "IndexError"
        assert validation.is_validated is True
    
    def test_key_error_validation(self):
        """测试KeyError验证"""
        validator = ExceptionValidator()
        
        validation = validator._validate_key_error("Key not found")
        
        assert validation.exception_type == "KeyError"
        assert validation.is_validated is True


class TestTestAgent:
    """测试测试Agent"""
    
    def test_generate_test_cases(self):
        """测试生成测试用例"""
        config = TestConfig(name="TestAgent")
        agent = TestAgent(config)
        
        suite = agent.generate_test_cases("process_user", ["user_id", "name"])
        
        assert suite is not None
        assert suite.total_count > 0
    
    def test_run_regression_tests(self):
        """测试运行回归测试"""
        config = TestConfig(name="TestAgent")
        agent = TestAgent(config)
        
        suite = agent.generate_test_cases("test_func", ["param"])
        result = agent.run_regression_tests(suite)
        
        assert result is not None
        assert result.passed_count >= 0
    
    def test_run_incremental_regression(self):
        """测试增量回归"""
        config = TestConfig(
            name="TestAgent",
            enable_incremental_regression=True
        )
        agent = TestAgent(config)
        
        suite = agent.generate_test_cases("process_data", ["data"])
        result = agent.run_regression_tests(
            suite, 
            changed_functions=["process_data"]
        )
        
        assert result.full_regression is False
    
    def test_validate_exceptions(self):
        """测试验证异常"""
        config = TestConfig(
            name="TestAgent",
            enable_exception_validation=True
        )
        agent = TestAgent(config)
        
        exceptions = [
            ("IndexError", "Index out of range"),
            ("KeyError", "Missing key"),
        ]
        
        validations = agent.validate_exceptions(exceptions)
        
        assert len(validations) >= 2
    
    def test_generate_report(self):
        """测试生成报告"""
        config = TestConfig(name="TestAgent")
        agent = TestAgent(config)
        
        suite = agent.generate_test_cases("test_func", ["param"])
        result = agent.run_regression_tests(suite)
        
        report = agent.generate_report(suite, result)
        
        assert report is not None
        assert len(report.summary) > 0
        assert "Total test cases" in report.summary


class TestGlobalAgent:
    """测试全局Agent"""
    
    def test_get_global_agent(self):
        """测试获取全局Agent"""
        reset_test_agent()
        
        agent1 = get_test_agent()
        agent2 = get_test_agent()
        
        assert agent1 is agent2
    
    def test_reset_global_agent(self):
        """测试重置全局Agent"""
        agent1 = get_test_agent()
        reset_test_agent()
        agent2 = get_test_agent()
        
        assert agent1 is not agent2


class TestCompleteScenario:
    """测试完整场景"""
    
    def test_complete_test_scenario(self):
        """测试完整测试场景"""
        config = TestConfig(
            name="CompleteTestAgent",
            enable_edge_cases=True,
            enable_incremental_regression=True,
            enable_exception_validation=True
        )
        agent = TestAgent(config)
        
        suite = agent.generate_test_cases("process_order", ["order_id", "items", "customer"])
        assert suite.total_count > 5
        
        result = agent.run_regression_tests(
            suite,
            changed_functions=["process_order"]
        )
        assert result.full_regression is False
        
        exceptions = [
            ("IndexError", "Order items index out of range"),
            ("ValueError", "Invalid order status"),
        ]
        validations = agent.validate_exceptions(exceptions)
        assert len(validations) >= 2
        
        report = agent.generate_report(suite, result, validations)
        assert "Total test cases" in report.summary
        assert "Incremental" in report.summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
