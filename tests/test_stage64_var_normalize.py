"""
阶段64验收测试 - 变量归一、去重、标准化
"""

import pytest
from src.architecture.var_normalize import (
    NormalizationType,
    VariableIssue,
    NormalizationResult,
    VariableNormalizer,
    NormalizationService,
)


class TestNormalizationType:
    """测试归一化类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert NormalizationType.NAMING.value == "naming"
        assert NormalizationType.TYPING.value == "typing"
        assert NormalizationType.SCOPING.value == "scoping"
        assert NormalizationType.DEDUPLICATION.value == "deduplication"

    def test_all_types(self):
        """测试所有类型"""
        types = list(NormalizationType)
        assert len(types) == 4


class TestVariableIssue:
    """测试变量问题"""

    def test_default_creation(self):
        """测试默认创建"""
        issue = VariableIssue()
        assert issue.var_name == ""
        assert issue.issue_type == NormalizationType.NAMING
        assert issue.description == ""
        assert issue.suggestion == ""
        assert issue.severity == "low"

    def test_custom_creation(self):
        """测试自定义创建"""
        issue = VariableIssue(
            var_name="BadName",
            issue_type=NormalizationType.NAMING,
            description="命名不符合规范",
            suggestion="bad_name",
            severity="medium",
        )
        assert issue.var_name == "BadName"
        assert issue.issue_type == NormalizationType.NAMING
        assert issue.severity == "medium"


class TestNormalizationResult:
    """测试归一化结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = NormalizationResult()
        assert result.total_vars == 0
        assert result.normalized == 0
        assert result.duplicates_removed == 0
        assert result.issues == []

    def test_custom_creation(self):
        """测试自定义创建"""
        result = NormalizationResult(
            total_vars=10,
            normalized=5,
            duplicates_removed=2,
            issues=[VariableIssue(var_name="x")],
        )
        assert result.total_vars == 10
        assert result.normalized == 5
        assert result.duplicates_removed == 2
        assert len(result.issues) == 1


class TestVariableNormalizer:
    """测试变量归一化器"""

    def test_initialization(self):
        """测试初始化"""
        normalizer = VariableNormalizer()
        assert normalizer._scanned_vars == {}
        assert normalizer._issues == []
        assert normalizer._result is None

    def test_scan_variables(self):
        """测试扫描变量"""
        normalizer = VariableNormalizer()
        variables = {
            "user_name": {"type": "str", "scope": "local"},
            "userAge": {"type": "int", "scope": "local"},
        }
        result = normalizer.scan_variables(variables)
        assert len(result) == 2
        assert "user_name" in result

    def test_detect_issues_naming(self):
        """测试检测命名问题"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "BadName": {"type": "str", "scope": "local"},
            "good_name": {"type": "str", "scope": "local"},
        })
        issues = normalizer.detect_issues()
        naming_issues = [i for i in issues if i.issue_type == NormalizationType.NAMING]
        assert len(naming_issues) >= 1

    def test_detect_issues_typing(self):
        """测试检测类型问题"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "count": {"type": "integer", "scope": "local"},
            "name": {"type": "string", "scope": "local"},
        })
        issues = normalizer.detect_issues()
        typing_issues = [i for i in issues if i.issue_type == NormalizationType.TYPING]
        assert len(typing_issues) >= 2

    def test_detect_issues_scoping(self):
        """测试检测作用域问题"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "global_var": {"type": "str", "scope": "global"},
        })
        issues = normalizer.detect_issues()
        scoping_issues = [i for i in issues if i.issue_type == NormalizationType.SCOPING]
        assert len(scoping_issues) >= 1

    def test_detect_issues_deduplication(self):
        """测试检测重复变量"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "user_name": {"type": "str", "scope": "local"},
            "userName": {"type": "str", "scope": "local"},
        })
        issues = normalizer.detect_issues()
        dup_issues = [i for i in issues if i.issue_type == NormalizationType.DEDUPLICATION]
        assert len(dup_issues) >= 1

    def test_normalize_naming_camel_case(self):
        """测试归一化驼峰命名"""
        normalizer = VariableNormalizer()
        assert normalizer.normalize_naming("userName") == "user_name"
        assert normalizer.normalize_naming("getUserById") == "get_user_by_id"

    def test_normalize_naming_already_snake(self):
        """测试归一化已经是snake_case的命名"""
        normalizer = VariableNormalizer()
        assert normalizer.normalize_naming("user_name") == "user_name"

    def test_normalize_naming_upper(self):
        """测试归一化全大写命名"""
        normalizer = VariableNormalizer()
        result = normalizer.normalize_naming("MAX_SIZE")
        assert result == "max_size"

    def test_remove_duplicates(self):
        """测试移除重复变量"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "user_name": {"type": "str", "scope": "local"},
            "userName": {"type": "str", "scope": "local"},
            "age": {"type": "int", "scope": "local"},
        })
        removed = normalizer.remove_duplicates()
        assert removed >= 1
        assert len(normalizer._scanned_vars) < 3

    def test_remove_duplicates_no_duplicates(self):
        """测试无重复变量时移除"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "user_name": {"type": "str", "scope": "local"},
            "user_age": {"type": "int", "scope": "local"},
        })
        removed = normalizer.remove_duplicates()
        assert removed == 0

    def test_standardize_types(self):
        """测试标准化类型"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "count": {"type": "integer", "scope": "local"},
            "name": {"type": "string", "scope": "local"},
            "flag": {"type": "boolean", "scope": "local"},
        })
        standardized = normalizer.standardize_types()
        assert standardized >= 3
        assert normalizer._scanned_vars["count"]["type"] == "int"
        assert normalizer._scanned_vars["name"]["type"] == "str"
        assert normalizer._scanned_vars["flag"]["type"] == "bool"

    def test_standardize_types_already_standard(self):
        """测试已标准化的类型"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "count": {"type": "int", "scope": "local"},
        })
        standardized = normalizer.standardize_types()
        assert standardized == 0

    def test_generate_report(self):
        """测试生成报告"""
        normalizer = VariableNormalizer()
        normalizer.scan_variables({
            "BadName": {"type": "integer", "scope": "local"},
            "good_name": {"type": "str", "scope": "local"},
        })
        normalizer.detect_issues()
        report = normalizer.generate_report()
        assert report.total_vars == 2
        assert len(report.issues) > 0


class TestNormalizationService:
    """测试归一化服务"""

    def test_initialization(self):
        """测试初始化"""
        service = NormalizationService()
        assert service.normalizer is not None

    def test_process(self):
        """测试完整处理流程"""
        service = NormalizationService()
        variables = {
            "BadName": {"type": "integer", "scope": "local"},
            "good_name": {"type": "str", "scope": "local"},
            "badName": {"type": "string", "scope": "global"},
        }
        result = service.process(variables)
        assert result.total_vars > 0
        assert len(result.issues) > 0

    def test_get_result(self):
        """测试获取结果"""
        service = NormalizationService()
        service.process({"var1": {"type": "str", "scope": "local"}})
        result = service.get_result()
        assert result is not None
        assert isinstance(result, NormalizationResult)

    def test_get_result_before_process(self):
        """测试处理前获取结果"""
        service = NormalizationService()
        result = service.get_result()
        assert result is None

    def test_get_issues_all(self):
        """测试获取所有问题"""
        service = NormalizationService()
        service.process({
            "BadName": {"type": "integer", "scope": "global"},
        })
        issues = service.get_issues()
        assert len(issues) > 0

    def test_get_issues_by_type(self):
        """测试按类型获取问题"""
        service = NormalizationService()
        service.process({
            "BadName": {"type": "integer", "scope": "global"},
        })
        naming_issues = service.get_issues(NormalizationType.NAMING)
        for issue in naming_issues:
            assert issue.issue_type == NormalizationType.NAMING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
