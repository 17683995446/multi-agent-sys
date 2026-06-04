"""
阶段71验收测试：原子化代码规范校验
"""

import pytest
from src.architecture.code_check import (
    CheckLevel,
    CheckResult,
    CheckItem,
    CodeChecker,
    CodeCheckService,
)


class TestCheckLevel:
    """测试校验级别枚举"""

    def test_level_values(self):
        """测试校验级别枚举值"""
        assert CheckLevel.VARIABLE.value == "variable"
        assert CheckLevel.METHOD.value == "method"
        assert CheckLevel.CLASS.value == "class"
        assert CheckLevel.MODULE.value == "module"

    def test_all_levels(self):
        """测试所有级别"""
        levels = list(CheckLevel)
        assert len(levels) == 4


class TestCheckResult:
    """测试校验结果枚举"""

    def test_result_values(self):
        """测试校验结果枚举值"""
        assert CheckResult.PASS.value == "pass"
        assert CheckResult.WARNING.value == "warning"
        assert CheckResult.FAIL.value == "fail"

    def test_all_results(self):
        """测试所有结果"""
        results = list(CheckResult)
        assert len(results) == 3


class TestCheckItem:
    """测试校验项"""

    def test_default_creation(self):
        """测试默认创建"""
        item = CheckItem()
        assert item.item_id != ""
        assert item.level == CheckLevel.VARIABLE
        assert item.rule == ""
        assert item.result == CheckResult.PASS
        assert item.message == ""
        assert item.location == ""
        assert item.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        item = CheckItem(
            level=CheckLevel.METHOD,
            rule="参数数量",
            result=CheckResult.FAIL,
            message="方法参数过多",
            location="main.py:10",
        )
        assert item.level == CheckLevel.METHOD
        assert item.rule == "参数数量"
        assert item.result == CheckResult.FAIL
        assert item.message == "方法参数过多"
        assert item.location == "main.py:10"

    def test_item_id_unique(self):
        """测试校验项ID唯一性"""
        item1 = CheckItem()
        item2 = CheckItem()
        assert item1.item_id != item2.item_id


class TestCodeChecker:
    """测试代码规范校验器"""

    def test_initialization(self):
        """测试初始化"""
        checker = CodeChecker()
        assert len(checker.items) == 0
        assert len(checker.rules) == 4

    def test_check_variable_snake_case(self):
        """测试snake_case变量命名合规"""
        checker = CodeChecker()
        items = checker.check_variable("my_var", "main.py:5")
        assert len(items) > 0
        naming_items = [i for i in items if i.rule == "命名规范"]
        assert any(i.result == CheckResult.PASS for i in naming_items)

    def test_check_variable_pascal_case_warning(self):
        """测试PascalCase变量命名警告"""
        checker = CodeChecker()
        items = checker.check_variable("MyVar", "main.py:5")
        naming_items = [i for i in items if i.rule == "命名规范"]
        assert any(i.result == CheckResult.WARNING for i in naming_items)

    def test_check_variable_type_annotation(self):
        """测试变量类型注解检查"""
        checker = CodeChecker()
        items = checker.check_variable("my_var", "main.py:5")
        type_items = [i for i in items if i.rule == "类型注解"]
        assert len(type_items) > 0

    def test_check_method_few_params(self):
        """测试方法参数数量合规"""
        checker = CodeChecker()
        items = checker.check_method("my_method", params=3, location="main.py:10")
        param_items = [i for i in items if i.rule == "参数数量"]
        assert any(i.result == CheckResult.PASS for i in param_items)

    def test_check_method_many_params(self):
        """测试方法参数过多"""
        checker = CodeChecker()
        items = checker.check_method("my_method", params=10, location="main.py:10")
        param_items = [i for i in items if i.rule == "参数数量"]
        assert any(i.result == CheckResult.FAIL for i in param_items)

    def test_check_method_medium_params(self):
        """测试方法参数较多"""
        checker = CodeChecker()
        items = checker.check_method("my_method", params=6, location="main.py:10")
        param_items = [i for i in items if i.rule == "参数数量"]
        assert any(i.result == CheckResult.WARNING for i in param_items)

    def test_check_class_pascal_case(self):
        """测试类命名PascalCase合规"""
        checker = CodeChecker()
        items = checker.check_class("MyClass", method_count=5,
                                    base_count=1, location="main.py:20")
        naming_items = [i for i in items if i.rule == "命名规范"]
        assert any(i.result == CheckResult.PASS for i in naming_items)

    def test_check_class_wrong_naming(self):
        """测试类命名不规范"""
        checker = CodeChecker()
        items = checker.check_class("my_class", method_count=5,
                                    base_count=1, location="main.py:20")
        naming_items = [i for i in items if i.rule == "命名规范"]
        assert any(i.result == CheckResult.FAIL for i in naming_items)

    def test_check_class_too_many_methods(self):
        """测试类方法过多"""
        checker = CodeChecker()
        items = checker.check_class("MyClass", method_count=25,
                                    base_count=1, location="main.py:20")
        method_items = [i for i in items if i.rule == "方法数量"]
        assert any(i.result == CheckResult.FAIL for i in method_items)

    def test_check_class_deep_inheritance(self):
        """测试继承层次过深"""
        checker = CodeChecker()
        items = checker.check_class("MyClass", method_count=5,
                                    base_count=5, location="main.py:20")
        inherit_items = [i for i in items if i.rule == "继承深度"]
        assert any(i.result == CheckResult.FAIL for i in inherit_items)

    def test_check_module_too_many_imports(self):
        """测试模块导入过多"""
        checker = CodeChecker()
        items = checker.check_module("my_module", import_count=25,
                                     location="main.py")
        import_items = [i for i in items if i.rule == "导入规范"]
        assert any(i.result == CheckResult.FAIL for i in import_items)

    def test_check_module_too_many_lines(self):
        """测试模块行数过多"""
        checker = CodeChecker()
        items = checker.check_module("my_module", line_count=600,
                                     location="main.py")
        line_items = [i for i in items if i.rule == "行数限制"]
        assert any(i.result == CheckResult.FAIL for i in line_items)

    def test_run_all_checks(self):
        """测试运行所有校验"""
        checker = CodeChecker()
        code_data = {
            "variables": [{"name": "my_var", "location": "main.py:5"}],
            "methods": [{"name": "my_method", "params": 3, "location": "main.py:10"}],
            "classes": [{"name": "MyClass", "method_count": 5, "base_count": 1, "location": "main.py:20"}],
            "modules": [{"name": "my_module", "line_count": 100, "import_count": 5, "location": "main.py"}],
        }
        items = checker.run_all_checks(code_data)
        assert len(items) > 0

    def test_generate_report(self):
        """测试生成报告"""
        checker = CodeChecker()
        checker.check_variable("MyVar", "main.py:5")
        report = checker.generate_report()
        assert "total_items" in report
        assert "pass_count" in report
        assert "warning_count" in report
        assert "fail_count" in report
        assert "score" in report


class TestCodeCheckService:
    """测试代码规范校验服务"""

    def test_initialization(self):
        """测试初始化"""
        service = CodeCheckService()
        assert service.checker is not None

    def test_check(self):
        """测试执行校验"""
        service = CodeCheckService()
        code_data = {
            "variables": [{"name": "my_var", "location": "main.py:5"}],
            "methods": [{"name": "my_method", "params": 3, "location": "main.py:10"}],
            "classes": [{"name": "MyClass", "method_count": 5, "base_count": 1, "location": "main.py:20"}],
            "modules": [{"name": "my_module", "line_count": 100, "import_count": 5, "location": "main.py"}],
        }
        items = service.check(code_data)
        assert len(items) > 0

    def test_get_report(self):
        """测试获取报告"""
        service = CodeCheckService()
        code_data = {
            "variables": [{"name": "MyVar", "location": "main.py:5"}],
        }
        service.check(code_data)
        report = service.get_report()
        assert report["total_items"] > 0

    def test_get_violations(self):
        """测试获取违规项"""
        service = CodeCheckService()
        code_data = {
            "variables": [{"name": "MyVar", "location": "main.py:5"}],
        }
        service.check(code_data)
        violations = service.get_violations()
        assert len(violations) > 0
        assert all(v.result != CheckResult.PASS for v in violations)

    def test_get_violations_by_level(self):
        """测试按级别过滤违规项"""
        service = CodeCheckService()
        code_data = {
            "variables": [{"name": "MyVar", "location": "main.py:5"}],
        }
        service.check(code_data)
        violations = service.get_violations(level=CheckLevel.VARIABLE)
        assert all(v.level == CheckLevel.VARIABLE for v in violations)

    def test_get_violations_by_result(self):
        """测试按结果过滤违规项"""
        service = CodeCheckService()
        code_data = {
            "variables": [{"name": "MyVar", "location": "main.py:5"}],
        }
        service.check(code_data)
        violations = service.get_violations(result=CheckResult.WARNING)
        assert all(v.result == CheckResult.WARNING for v in violations)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
