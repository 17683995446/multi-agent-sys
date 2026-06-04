"""
阶段65验收测试 - 批量Bug自动定位
"""

import pytest
from src.architecture.bug_locator import (
    BugSeverity,
    BugCategory,
    BugReport,
    BugLocator,
    BugLocationService,
)


class TestBugSeverity:
    """测试Bug严重程度枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert BugSeverity.CRITICAL.value == "critical"
        assert BugSeverity.HIGH.value == "high"
        assert BugSeverity.MEDIUM.value == "medium"
        assert BugSeverity.LOW.value == "low"

    def test_all_severities(self):
        """测试所有严重程度"""
        severities = list(BugSeverity)
        assert len(severities) == 4


class TestBugCategory:
    """测试Bug类别枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert BugCategory.LOGIC.value == "logic"
        assert BugCategory.SYNTAX.value == "syntax"
        assert BugCategory.PERFORMANCE.value == "performance"
        assert BugCategory.SECURITY.value == "security"
        assert BugCategory.COMPATIBILITY.value == "compatibility"

    def test_all_categories(self):
        """测试所有类别"""
        categories = list(BugCategory)
        assert len(categories) == 5


class TestBugReport:
    """测试Bug报告"""

    def test_default_creation(self):
        """测试默认创建"""
        report = BugReport()
        assert report.bug_id != ""
        assert report.severity == BugSeverity.MEDIUM
        assert report.category == BugCategory.LOGIC
        assert report.location == ""
        assert report.description == ""
        assert report.stack_trace == ""
        assert report.root_cause == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        report = BugReport(
            severity=BugSeverity.CRITICAL,
            category=BugCategory.SECURITY,
            location="auth.py:42",
            description="SQL注入漏洞",
            stack_trace="File auth.py, line 42",
            root_cause="未对输入进行参数化处理",
        )
        assert report.severity == BugSeverity.CRITICAL
        assert report.category == BugCategory.SECURITY
        assert report.location == "auth.py:42"

    def test_bug_id_unique(self):
        """测试Bug ID唯一性"""
        r1 = BugReport()
        r2 = BugReport()
        assert r1.bug_id != r2.bug_id


class TestBugLocator:
    """测试Bug定位器"""

    def test_initialization(self):
        """测试初始化"""
        locator = BugLocator()
        assert locator._bugs == {}
        assert locator._statistics["total"] == 0

    def test_locate_bug(self):
        """测试定位Bug"""
        locator = BugLocator()
        report = locator.locate_bug(
            "空指针异常",
            stack_trace="File main.py, line 10\nFile utils.py, line 5",
            severity=BugSeverity.HIGH,
            category=BugCategory.LOGIC,
        )
        assert report.bug_id != ""
        assert report.severity == BugSeverity.HIGH
        assert report.category == BugCategory.LOGIC
        assert report.location != "unknown"
        assert report.root_cause != ""

    def test_locate_bug_no_stack_trace(self):
        """测试无堆栈信息时定位Bug"""
        locator = BugLocator()
        report = locator.locate_bug("功能异常")
        assert report.location == "unknown"
        assert report.root_cause != ""

    def test_locate_bug_critical(self):
        """测试定位严重Bug"""
        locator = BugLocator()
        report = locator.locate_bug(
            "系统崩溃",
            severity=BugSeverity.CRITICAL,
            category=BugCategory.LOGIC,
        )
        assert report.severity == BugSeverity.CRITICAL

    def test_locate_bug_security(self):
        """测试定位安全Bug"""
        locator = BugLocator()
        report = locator.locate_bug(
            "权限绕过",
            severity=BugSeverity.CRITICAL,
            category=BugCategory.SECURITY,
        )
        assert report.category == BugCategory.SECURITY
        assert "安全" in report.root_cause

    def test_locate_bug_performance(self):
        """测试定位性能Bug"""
        locator = BugLocator()
        report = locator.locate_bug(
            "响应时间过长",
            severity=BugSeverity.MEDIUM,
            category=BugCategory.PERFORMANCE,
        )
        assert report.category == BugCategory.PERFORMANCE
        assert "性能" in report.root_cause

    def test_analyze_stack_trace(self):
        """测试分析堆栈信息"""
        locator = BugLocator()
        stack = "File app.py, line 42, in process\nFile core.py, line 10, in handle"
        location = locator.analyze_stack_trace(stack)
        assert location != "unknown"
        assert "File" in location

    def test_analyze_stack_trace_empty(self):
        """测试分析空堆栈"""
        locator = BugLocator()
        location = locator.analyze_stack_trace("")
        assert location == "unknown"

    def test_analyze_stack_trace_no_file(self):
        """测试分析无文件信息的堆栈"""
        locator = BugLocator()
        location = locator.analyze_stack_trace("Some error occurred")
        assert location != ""

    def test_trace_data_flow(self):
        """测试追踪数据流"""
        locator = BugLocator()
        flow = locator.trace_data_flow("main.py:10", "变量读取错误")
        assert flow["source"] == "main.py:10"
        assert len(flow["flow_steps"]) > 0

    def test_trace_data_flow_unknown_location(self):
        """测试未知位置的数据流追踪"""
        locator = BugLocator()
        flow = locator.trace_data_flow("unknown", "错误")
        assert flow["source"] == "unknown"

    def test_identify_root_cause_logic(self):
        """测试识别逻辑错误根因"""
        locator = BugLocator()
        report = BugReport(category=BugCategory.LOGIC)
        root_cause = locator.identify_root_cause(report, {"affected_variables": ["count"]})
        assert "逻辑" in root_cause

    def test_identify_root_cause_syntax(self):
        """测试识别语法错误根因"""
        locator = BugLocator()
        report = BugReport(category=BugCategory.SYNTAX)
        root_cause = locator.identify_root_cause(report, {})
        assert "语法" in root_cause

    def test_identify_root_cause_security(self):
        """测试识别安全错误根因"""
        locator = BugLocator()
        report = BugReport(category=BugCategory.SECURITY)
        root_cause = locator.identify_root_cause(report, {
            "affected_variables": ["input"],
            "related_operations": ["读取"],
        })
        assert "安全" in root_cause

    def test_generate_report_single(self):
        """测试生成单个Bug报告"""
        locator = BugLocator()
        report = locator.locate_bug(
            "测试Bug",
            severity=BugSeverity.HIGH,
            category=BugCategory.LOGIC,
        )
        result = locator.generate_report(report.bug_id)
        assert result["bug_id"] == report.bug_id
        assert "recommendation" in result

    def test_generate_report_statistics(self):
        """测试生成统计报告"""
        locator = BugLocator()
        locator.locate_bug("Bug1", severity=BugSeverity.HIGH, category=BugCategory.LOGIC)
        locator.locate_bug("Bug2", severity=BugSeverity.LOW, category=BugCategory.SYNTAX)
        result = locator.generate_report()
        assert "statistics" in result
        assert result["statistics"]["total"] == 2
        assert len(result["bugs"]) == 2

    def test_statistics_updated(self):
        """测试统计信息更新"""
        locator = BugLocator()
        locator.locate_bug("Bug1", severity=BugSeverity.CRITICAL, category=BugCategory.SECURITY)
        locator.locate_bug("Bug2", severity=BugSeverity.MEDIUM, category=BugCategory.LOGIC)
        stats = locator._statistics
        assert stats["total"] == 2
        assert stats["by_severity"]["critical"] == 1
        assert stats["by_severity"]["medium"] == 1
        assert stats["by_category"]["security"] == 1
        assert stats["by_category"]["logic"] == 1


class TestBugLocationService:
    """测试Bug定位服务"""

    def test_initialization(self):
        """测试初始化"""
        service = BugLocationService()
        assert service.locator is not None

    def test_locate(self):
        """测试定位"""
        service = BugLocationService()
        report = service.locate(
            "空指针异常",
            stack_trace="File main.py, line 10",
            severity=BugSeverity.HIGH,
        )
        assert report.bug_id != ""
        assert report.severity == BugSeverity.HIGH

    def test_get_bug(self):
        """测试获取Bug报告"""
        service = BugLocationService()
        report = service.locate("测试Bug")
        retrieved = service.get_bug(report.bug_id)
        assert retrieved is report

    def test_get_bug_not_found(self):
        """测试获取不存在的Bug"""
        service = BugLocationService()
        result = service.get_bug("nonexistent")
        assert result is None

    def test_get_statistics(self):
        """测试获取统计信息"""
        service = BugLocationService()
        service.locate("Bug1", severity=BugSeverity.HIGH, category=BugCategory.LOGIC)
        service.locate("Bug2", severity=BugSeverity.LOW, category=BugCategory.SYNTAX)
        stats = service.get_statistics()
        assert stats["total"] == 2

    def test_get_statistics_empty(self):
        """测试空统计信息"""
        service = BugLocationService()
        stats = service.get_statistics()
        assert stats["total"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
