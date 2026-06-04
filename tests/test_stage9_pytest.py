import pytest
from src.executors.pytest_integration import (
    TestStatus,
    TestResult,
    TestSuiteResult,
    FixtureDef,
    PytestRunner,
    TestCollector,
    FixtureRegistry,
    CoverageConfig,
    PytestIntegration,
)


class TestCoreDataStructures:
    """测试核心数据结构"""
    
    def test_test_status_enum(self):
        """测试测试状态枚举"""
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"
    
    def test_test_result_creation(self):
        """测试测试结果创建"""
        result = TestResult(
            name="test_example",
            status=TestStatus.PASSED,
            duration=0.5,
        )
        assert result.name == "test_example"
        assert result.status == TestStatus.PASSED
        assert result.duration == 0.5
    
    def test_test_suite_result_calculation(self):
        """测试测试套件结果计算"""
        suite = TestSuiteResult()
        suite.passed = 8
        suite.failed = 1
        suite.skipped = 1
        suite.total_tests = 10
        
        assert suite.success_rate == 0.8
        assert suite.total_tests == 10
    
    def test_fixture_def(self):
        """测试fixture定义"""
        fixture = FixtureDef(
            name="sample_fixture",
            scope="function",
        )
        assert fixture.name == "sample_fixture"
        assert fixture.scope == "function"


class TestPytestRunner:
    """测试Pytest运行器"""
    
    def test_runner_initialization(self):
        """测试运行器初始化"""
        runner = PytestRunner()
        assert runner is not None
        assert runner.verbosity == 1
    
    def test_discover_tests(self):
        """测试测试发现功能"""
        runner = PytestRunner()
        tests = runner.discover_tests()
        assert isinstance(tests, list)
    
    def test_add_option(self):
        """测试添加选项"""
        runner = PytestRunner()
        runner.add_option("--tb=short")
        assert "--tb=short" in runner.addopts
    
    def test_set_verbosity(self):
        """测试设置详细程度"""
        runner = PytestRunner()
        runner.set_verbosity(2)
        assert runner.verbosity == 2


class TestCollector:
    """测试收集器"""
    
    def test_collector_initialization(self):
        """测试收集器初始化"""
        collector = TestCollector()
        assert collector is not None


class TestFixtureRegistry:
    """测试fixture注册表"""
    
    def test_registry_initialization(self):
        """测试注册表初始化"""
        registry = FixtureRegistry()
        assert len(registry.list_all()) == 0
    
    def test_register_fixture(self):
        """测试注册fixture"""
        registry = FixtureRegistry()
        fixture = FixtureDef(name="test_fixture")
        
        registry.register(fixture)
        assert registry.get("test_fixture") is not None
        assert len(registry.list_all()) == 1
    
    def test_unregister_fixture(self):
        """测试注销fixture"""
        registry = FixtureRegistry()
        fixture = FixtureDef(name="test_fixture")
        
        registry.register(fixture)
        registry.unregister("test_fixture")
        
        assert registry.get("test_fixture") is None
        assert len(registry.list_all()) == 0


class TestCoverageConfig:
    """测试覆盖率配置"""
    
    def test_coverage_config_defaults(self):
        """测试覆盖率配置默认值"""
        config = CoverageConfig()
        assert "src" in config.source
        assert len(config.omit) > 0
        assert config.minimum_percent == 80.0
    
    def test_to_pytest_args(self):
        """测试转换为pytest参数"""
        config = CoverageConfig()
        args = config.to_pytest_args()
        assert len(args) > 0


class TestPytestIntegration:
    """测试Pytest集成入口"""
    
    def test_integration_initialization(self):
        """测试集成初始化"""
        integration = PytestIntegration()
        assert integration.runner is not None
        assert integration.collector is not None
        assert integration.fixture_registry is not None
        assert integration.coverage_config is not None


class TestRealWorldScenarios:
    """测试实际场景"""
    
    def test_simple_test_discovery(self):
        """测试简单的测试发现"""
        runner = PytestRunner()
        test_files = runner.discover_tests()
        # 应该能找到我们自己的测试文件
        assert len(test_files) >= 1
    
    def test_multiple_fixtures(self):
        """测试多个fixture"""
        registry = FixtureRegistry()
        registry.register(FixtureDef(name="fixture1"))
        registry.register(FixtureDef(name="fixture2"))
        registry.register(FixtureDef(name="fixture3"))
        
        assert len(registry.list_all()) == 3
    
    def test_coverage_config_customization(self):
        """测试覆盖率配置自定义"""
        config = CoverageConfig()
        config.source.append("custom_source")
        config.minimum_percent = 90.0
        
        assert "custom_source" in config.source
        assert config.minimum_percent == 90.0


# 提供一些简单的fixture给测试使用
@pytest.fixture
def sample_list():
    """简单的列表fixture"""
    return [1, 2, 3, 4, 5]


@pytest.fixture
def sample_dict():
    """简单的字典fixture"""
    return {"key": "value", "test": "pytest"}


class TestWithFixtures:
    """测试使用fixture的测试"""
    
    def test_with_sample_list(self, sample_list):
        """测试使用列表fixture"""
        assert len(sample_list) == 5
        assert 3 in sample_list
    
    def test_with_sample_dict(self, sample_dict):
        """测试使用字典fixture"""
        assert "key" in sample_dict
        assert sample_dict["test"] == "pytest"
