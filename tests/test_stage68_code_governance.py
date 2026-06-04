"""
阶段68验收测试：全工程代码规整治理
"""

import pytest
from src.architecture.code_governance import (
    GovernanceRule,
    ViolationLevel,
    GovernanceViolation,
    GovernanceReport,
    CodeGovernor,
    GovernanceService,
)


class TestGovernanceRule:
    """测试治理规则枚举"""

    def test_rule_values(self):
        """测试治理规则枚举值"""
        assert GovernanceRule.NAMING_CONVENTION.value == "naming_convention"
        assert GovernanceRule.CODE_STRUCTURE.value == "code_structure"
        assert GovernanceRule.DOCUMENTATION.value == "documentation"
        assert GovernanceRule.TESTING.value == "testing"

    def test_all_rules(self):
        """测试所有规则"""
        rules = list(GovernanceRule)
        assert len(rules) == 4


class TestViolationLevel:
    """测试违规级别枚举"""

    def test_level_values(self):
        """测试违规级别枚举值"""
        assert ViolationLevel.INFO.value == "info"
        assert ViolationLevel.WARNING.value == "warning"
        assert ViolationLevel.ERROR.value == "error"
        assert ViolationLevel.CRITICAL.value == "critical"

    def test_all_levels(self):
        """测试所有级别"""
        levels = list(ViolationLevel)
        assert len(levels) == 4


class TestGovernanceViolation:
    """测试治理违规记录"""

    def test_default_creation(self):
        """测试默认创建"""
        v = GovernanceViolation()
        assert v.violation_id != ""
        assert v.rule == GovernanceRule.NAMING_CONVENTION
        assert v.level == ViolationLevel.WARNING
        assert v.file_path == ""
        assert v.description == ""
        assert v.suggestion == ""
        assert v.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        v = GovernanceViolation(
            rule=GovernanceRule.TESTING,
            level=ViolationLevel.ERROR,
            file_path="src/main.py",
            description="缺少测试文件",
            suggestion="添加test_main.py",
        )
        assert v.rule == GovernanceRule.TESTING
        assert v.level == ViolationLevel.ERROR
        assert v.file_path == "src/main.py"
        assert v.description == "缺少测试文件"

    def test_violation_id_unique(self):
        """测试违规ID唯一性"""
        v1 = GovernanceViolation()
        v2 = GovernanceViolation()
        assert v1.violation_id != v2.violation_id


class TestGovernanceReport:
    """测试治理报告"""

    def test_default_creation(self):
        """测试默认创建"""
        report = GovernanceReport()
        assert report.total_files == 0
        assert report.violations == []
        assert report.compliance_score == 100.0
        assert report.summary == ""
        assert report.report_id != ""

    def test_custom_creation(self):
        """测试自定义创建"""
        v = GovernanceViolation(rule=GovernanceRule.DOCUMENTATION)
        report = GovernanceReport(
            total_files=10,
            violations=[v],
            compliance_score=85.5,
            summary="合规报告",
        )
        assert report.total_files == 10
        assert len(report.violations) == 1
        assert report.compliance_score == 85.5


class TestCodeGovernor:
    """测试代码治理器"""

    def test_initialization(self):
        """测试初始化"""
        governor = CodeGovernor()
        assert len(governor.violations) == 0
        assert len(governor.reports) == 0
        assert all(governor.rules_enabled.values())

    def test_scan(self):
        """测试扫描"""
        governor = CodeGovernor()
        violations = governor.scan(["main.py"])
        assert len(violations) > 0
        assert len(governor.violations) > 0

    def test_scan_multiple_files(self):
        """测试扫描多个文件"""
        governor = CodeGovernor()
        violations = governor.scan(["main.py", "utils.py", "test_main.py"])
        assert len(violations) > 0

    def test_scan_with_disabled_rule(self):
        """测试禁用规则后扫描"""
        governor = CodeGovernor()
        governor.rules_enabled[GovernanceRule.TESTING] = False
        violations = governor.scan(["main.py"])
        testing_violations = [v for v in violations if v.rule == GovernanceRule.TESTING]
        assert len(testing_violations) == 0

    def test_check_rule_naming(self):
        """测试命名规范检查"""
        governor = CodeGovernor()
        violations = governor.check_rule(GovernanceRule.NAMING_CONVENTION, "main.py")
        assert len(violations) > 0
        assert violations[0].rule == GovernanceRule.NAMING_CONVENTION

    def test_check_rule_documentation(self):
        """测试文档规范检查"""
        governor = CodeGovernor()
        violations = governor.check_rule(GovernanceRule.DOCUMENTATION, "main.py")
        assert len(violations) > 0
        assert violations[0].rule == GovernanceRule.DOCUMENTATION

    def test_check_rule_testing(self):
        """测试测试规范检查"""
        governor = CodeGovernor()
        violations = governor.check_rule(GovernanceRule.TESTING, "main.py")
        assert len(violations) > 0
        assert violations[0].level == ViolationLevel.ERROR

    def test_check_rule_testing_for_test_file(self):
        """测试测试文件不触发测试违规"""
        governor = CodeGovernor()
        violations = governor.check_rule(GovernanceRule.TESTING, "test_main.py")
        assert len(violations) == 0

    def test_generate_report(self):
        """测试生成报告"""
        governor = CodeGovernor()
        governor.scan(["main.py", "utils.py"])
        report = governor.generate_report(["main.py", "utils.py"])
        assert report.total_files == 2
        assert len(report.violations) > 0
        assert report.compliance_score < 100.0
        assert report.summary != ""

    def test_generate_report_no_files(self):
        """测试无文件时生成报告"""
        governor = CodeGovernor()
        report = governor.generate_report()
        assert report.compliance_score == 100.0

    def test_suggest_fixes(self):
        """测试生成修复建议"""
        governor = CodeGovernor()
        governor.scan(["main.py"])
        suggestions = governor.suggest_fixes()
        assert len(suggestions) > 0
        assert "suggestion" in suggestions[0]
        assert "auto_fixable" in suggestions[0]

    def test_suggest_fixes_specific_violations(self):
        """测试对特定违规生成修复建议"""
        governor = CodeGovernor()
        v = GovernanceViolation(
            rule=GovernanceRule.NAMING_CONVENTION,
            level=ViolationLevel.WARNING,
            suggestion="使用snake_case",
        )
        suggestions = governor.suggest_fixes([v])
        assert len(suggestions) == 1
        assert suggestions[0]["auto_fixable"] is True

    def test_apply_fixes(self):
        """测试应用修复"""
        governor = CodeGovernor()
        governor.scan(["main.py"])
        result = governor.apply_fixes()
        assert result["total"] > 0
        assert result["applied"] >= 0
        assert result["total"] == result["applied"] + result["skipped"] + result["failed"]

    def test_apply_fixes_warning_level(self):
        """测试修复WARNING级别违规"""
        governor = CodeGovernor()
        v = GovernanceViolation(level=ViolationLevel.WARNING)
        result = governor.apply_fixes([v])
        assert result["applied"] == 1

    def test_apply_fixes_error_level(self):
        """测试修复ERROR级别违规被跳过"""
        governor = CodeGovernor()
        v = GovernanceViolation(level=ViolationLevel.ERROR)
        result = governor.apply_fixes([v])
        assert result["skipped"] == 1


class TestGovernanceService:
    """测试代码治理服务"""

    def test_initialization(self):
        """测试初始化"""
        service = GovernanceService()
        assert service.governor is not None

    def test_govern(self):
        """测试执行治理"""
        service = GovernanceService()
        report = service.govern(["main.py", "utils.py"])
        assert report.total_files == 2
        assert report.compliance_score < 100.0

    def test_get_report(self):
        """测试获取报告"""
        service = GovernanceService()
        service.govern(["main.py"])
        report = service.get_report()
        assert report is not None
        assert report.total_files == 1

    def test_get_report_no_reports(self):
        """测试无报告时获取"""
        service = GovernanceService()
        report = service.get_report()
        assert report is None

    def test_get_violations(self):
        """测试获取违规列表"""
        service = GovernanceService()
        service.govern(["main.py"])
        violations = service.get_violations()
        assert len(violations) > 0

    def test_get_violations_by_rule(self):
        """测试按规则过滤违规"""
        service = GovernanceService()
        service.govern(["main.py"])
        violations = service.get_violations(rule=GovernanceRule.TESTING)
        assert all(v.rule == GovernanceRule.TESTING for v in violations)

    def test_get_violations_by_level(self):
        """测试按级别过滤违规"""
        service = GovernanceService()
        service.govern(["main.py"])
        violations = service.get_violations(level=ViolationLevel.ERROR)
        assert all(v.level == ViolationLevel.ERROR for v in violations)

    def test_full_governance_workflow(self):
        """测试完整治理工作流"""
        service = GovernanceService()
        # 1. 治理
        report = service.govern(["main.py", "utils.py", "test_main.py"])
        assert report.total_files == 3
        # 2. 获取违规
        violations = service.get_violations()
        assert len(violations) > 0
        # 3. 修复建议
        suggestions = service.governor.suggest_fixes()
        assert len(suggestions) > 0
        # 4. 应用修复
        result = service.governor.apply_fixes()
        assert result["total"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
