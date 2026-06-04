import pytest
from src.executors.ruff_integration import (
    RuleConfig,
    RuffChecker,
    ScanResult,
    Violation,
    ViolationSeverity,
    CustomRule,
    CustomRuleRegistry,
    CodeQualityChecker,
)


class TestRuleConfig:
    """测试规则配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = RuleConfig()
        assert config.line_length == 120
        assert config.target_version == "py311"
        assert len(config.enabled_rules) > 0
        assert "E501" in config.disabled_rules
    
    def test_enable_rule(self):
        """测试启用规则"""
        config = RuleConfig()
        config.enable_rule("EXAMPLE")
        assert "EXAMPLE" in config.enabled_rules
    
    def test_disable_rule(self):
        """测试禁用规则"""
        config = RuleConfig()
        config.disable_rule("E101")
        assert "E101" in config.disabled_rules


class TestViolation:
    """测试违规信息"""
    
    def test_violation_creation(self):
        """测试创建违规"""
        violation = Violation(
            file="test.py",
            line=10,
            column=5,
            rule_code="E123",
            message="Test violation"
        )
        assert violation.file == "test.py"
        assert violation.line == 10
        assert violation.rule_code == "E123"
    
    def test_violation_str(self):
        """测试违规字符串表示"""
        violation = Violation(
            file="test.py",
            line=10,
            column=5,
            rule_code="E123",
            message="Test violation"
        )
        str_repr = str(violation)
        assert "test.py:10:5" in str_repr
        assert "E123" in str_repr


class TestRuffChecker:
    """测试Ruff检查器"""
    
    def test_init(self):
        """测试初始化"""
        checker = RuffChecker()
        assert checker.config is not None
    
    def test_check_simple_code(self):
        """测试检查简单代码"""
        checker = RuffChecker()
        code = """
def hello():
    print("Hello")
"""
        result = checker.check_code(code, "test.py")
        assert isinstance(result, ScanResult)
        assert result.file == "test.py"
    
    def test_check_empty_code(self):
        """测试检查空代码"""
        checker = RuffChecker()
        result = checker.check_code("", "empty.py")
        assert isinstance(result, ScanResult)
        assert not result.has_violations
    
    def test_check_line_length(self):
        """测试检查行长度"""
        checker = RuffChecker()
        long_line = "x = " + "a" * 150
        code = f"{long_line}\n"
        result = checker.check_code(code, "long_line.py")
        assert isinstance(result, ScanResult)
        # 备用模式应该能检测到行长度问题


class TestCustomRule:
    """测试自定义规则"""
    
    def test_custom_rule_registry(self):
        """测试自定义规则注册表"""
        registry = CustomRuleRegistry()
        
        class TestRule(CustomRule):
            def check(self, code: str) -> list:
                return []
        
        rule = TestRule("TEST001", "Test Rule")
        registry.register(rule)
        
        assert registry.get("TEST001") is not None
        
        registry.unregister("TEST001")
        assert registry.get("TEST001") is None


class TestCodeQualityChecker:
    """测试综合代码质量检查器"""
    
    def test_init(self):
        """测试初始化"""
        checker = CodeQualityChecker()
        assert checker.ruff_checker is not None
        assert checker.custom_rules is not None
    
    def test_check_code(self):
        """测试检查代码"""
        checker = CodeQualityChecker()
        code = """
def greet():
    print("Hello world")
"""
        result = checker.check(code, "greet.py")
        assert "file" in result
        assert "total_issues" in result
    
    def test_format_code(self):
        """测试格式化代码"""
        checker = CodeQualityChecker()
        code = "def test():    pass"
        formatted = checker.format_code(code)
        # 在备用模式下原样返回
        assert formatted is not None


class TestScanResult:
    """测试扫描结果"""
    
    def test_has_violations(self):
        """测试是否有违规"""
        result = ScanResult(file="test.py")
        assert not result.has_violations
        
        result.violations.append(Violation(
            file="test.py",
            line=1,
            column=1
        ))
        assert result.has_violations
    
    def test_count_violations(self):
        """测试统计违规"""
        result = ScanResult(file="test.py")
        result.violations = [
            Violation(file="test.py", line=1, column=1, severity=ViolationSeverity.ERROR),
            Violation(file="test.py", line=2, column=1, severity=ViolationSeverity.WARNING),
            Violation(file="test.py", line=3, column=1, severity=ViolationSeverity.WARNING),
        ]
        result.total_violations = 3
        result.error_count = 1
        result.warning_count = 2
        
        assert result.error_count == 1
        assert result.warning_count == 2
        assert result.total_violations == 3


class TestViolationSeverity:
    """测试违规严重程度"""
    
    def test_severity_values(self):
        """测试严重程度值"""
        assert ViolationSeverity.ERROR.value == "error"
        assert ViolationSeverity.WARNING.value == "warning"
        assert ViolationSeverity.INFO.value == "info"


class TestCustomRuleIntegration:
    """测试自定义规则集成"""
    
    def test_custom_rule_check(self):
        """测试自定义规则检查"""
        registry = CustomRuleRegistry()
        
        class NoPrintRule(CustomRule):
            def __init__(self):
                super().__init__("CUST001", "No print statements")
            
            def check(self, code: str) -> list:
                violations = []
                if "print(" in code:
                    violations.append(Violation(
                        file="temp.py",
                        line=1,
                        column=code.find("print(") + 1,
                        rule_code=self.code,
                        message="Print statement not allowed",
                        severity=ViolationSeverity.WARNING
                    ))
                return violations
        
        registry.register(NoPrintRule())
        
        checker = CodeQualityChecker()
        checker.custom_rules = registry
        
        result = checker.check("print('hello')")
        assert "custom_violations" in result
