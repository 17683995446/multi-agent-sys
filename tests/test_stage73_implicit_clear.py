"""
阶段73验收测试：隐式依赖/状态清除
"""

import pytest
from src.architecture.implicit_clear import (
    ImplicitType,
    ImplicitIssue,
    ImplicitDetector,
    ImplicitCleaner,
    ImplicitClearService,
)


class TestImplicitType:
    """测试隐式问题类型枚举"""

    def test_type_values(self):
        """测试隐式问题类型枚举值"""
        assert ImplicitType.HIDDEN_DEPENDENCY.value == "hidden_dependency"
        assert ImplicitType.GLOBAL_STATE.value == "global_state"
        assert ImplicitType.SIDE_EFFECT.value == "side_effect"
        assert ImplicitType.COUPLING.value == "coupling"

    def test_all_types(self):
        """测试所有类型"""
        types = list(ImplicitType)
        assert len(types) == 4


class TestImplicitIssue:
    """测试隐式问题记录"""

    def test_default_creation(self):
        """测试默认创建"""
        issue = ImplicitIssue()
        assert issue.issue_id != ""
        assert issue.implicit_type == ImplicitType.HIDDEN_DEPENDENCY
        assert issue.location == ""
        assert issue.description == ""
        assert issue.severity == 0.5
        assert issue.suggestion == ""
        assert issue.resolved is False
        assert issue.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        issue = ImplicitIssue(
            implicit_type=ImplicitType.GLOBAL_STATE,
            location="main.py:10",
            description="全局变量",
            severity=0.8,
            suggestion="封装为类属性",
        )
        assert issue.implicit_type == ImplicitType.GLOBAL_STATE
        assert issue.location == "main.py:10"
        assert issue.severity == 0.8

    def test_issue_id_unique(self):
        """测试问题ID唯一性"""
        issue1 = ImplicitIssue()
        issue2 = ImplicitIssue()
        assert issue1.issue_id != issue2.issue_id


class TestImplicitDetector:
    """测试隐式问题检测器"""

    def test_initialization(self):
        """测试初始化"""
        detector = ImplicitDetector()
        assert len(detector.issues) == 0

    def test_detect_dependencies_unused_imports(self):
        """检测未使用的导入"""
        detector = ImplicitDetector()
        code_data = {
            "file_path": "main.py",
            "imports": ["os", "sys", "json"],
            "used_imports": ["os"],
        }
        issues = detector.detect_dependencies(code_data)
        assert len(issues) > 0
        assert all(i.implicit_type == ImplicitType.HIDDEN_DEPENDENCY for i in issues)

    def test_detect_dependencies_circular(self):
        """检测循环导入"""
        detector = ImplicitDetector()
        code_data = {
            "file_path": "main.py",
            "imports": [],
            "used_imports": [],
            "circular_imports": ["a -> b -> a"],
        }
        issues = detector.detect_dependencies(code_data)
        circular_issues = [i for i in issues if "循环" in i.description]
        assert len(circular_issues) > 0

    def test_detect_global_state(self):
        """检测全局状态"""
        detector = ImplicitDetector()
        code_data = {
            "file_path": "main.py",
            "globals": [
                {"name": "counter", "mutable": True},
                {"name": "PI", "mutable": False},
            ],
        }
        issues = detector.detect_global_state(code_data)
        assert len(issues) == 2
        mutable_issues = [i for i in issues if i.severity > 0.5]
        assert len(mutable_issues) > 0

    def test_detect_global_state_module_mutables(self):
        """检测模块级可变对象"""
        detector = ImplicitDetector()
        code_data = {
            "file_path": "main.py",
            "globals": [],
            "module_mutables": ["cache_dict"],
        }
        issues = detector.detect_global_state(code_data)
        assert len(issues) > 0

    def test_detect_side_effects(self):
        """检测副作用"""
        detector = ImplicitDetector()
        code_data = {
            "file_path": "main.py",
            "functions": [
                {"name": "process", "has_side_effect": True, "modifies_global": False},
                {"name": "pure_func", "has_side_effect": False, "modifies_global": False},
            ],
        }
        issues = detector.detect_side_effects(code_data)
        assert len(issues) > 0

    def test_detect_side_effects_modifies_global(self):
        """检测修改全局状态的副作用"""
        detector = ImplicitDetector()
        code_data = {
            "file_path": "main.py",
            "functions": [
                {"name": "update_counter", "has_side_effect": False, "modifies_global": True},
            ],
        }
        issues = detector.detect_side_effects(code_data)
        global_issues = [i for i in issues if "全局状态" in i.description]
        assert len(global_issues) > 0

    def test_detect_coupling(self):
        """检测隐式耦合"""
        detector = ImplicitDetector()
        code_data = {
            "file_path": "main.py",
            "couplings": [
                {"source": "ServiceA", "target": "ServiceB", "strength": 0.8},
                {"source": "ServiceC", "target": "ServiceD", "strength": 0.3},
            ],
        }
        issues = detector.detect_coupling(code_data)
        # 只有strength > 0.7才会被检测
        assert len(issues) == 1

    def test_generate_report(self):
        """测试生成报告"""
        detector = ImplicitDetector()
        code_data = {
            "file_path": "main.py",
            "imports": ["os", "sys"],
            "used_imports": ["os"],
        }
        detector.detect_dependencies(code_data)
        report = detector.generate_report()
        assert "total_issues" in report
        assert "by_type" in report
        assert "average_severity" in report


class TestImplicitCleaner:
    """测试隐式问题清理器"""

    def test_initialization(self):
        """测试初始化"""
        cleaner = ImplicitCleaner()
        assert len(cleaner.clean_log) == 0

    def test_clean_dependency(self):
        """测试清理隐式依赖"""
        cleaner = ImplicitCleaner()
        issue = ImplicitIssue(
            implicit_type=ImplicitType.HIDDEN_DEPENDENCY,
            description="未使用的导入: sys",
        )
        result = cleaner.clean_dependency(issue)
        assert result["status"] == "success"
        assert issue.resolved is True

    def test_clean_dependency_wrong_type(self):
        """测试清理类型不匹配"""
        cleaner = ImplicitCleaner()
        issue = ImplicitIssue(
            implicit_type=ImplicitType.GLOBAL_STATE,
            description="全局变量",
        )
        result = cleaner.clean_dependency(issue)
        assert result["status"] == "skipped"

    def test_clean_global_state(self):
        """测试清理全局状态"""
        cleaner = ImplicitCleaner()
        issue = ImplicitIssue(
            implicit_type=ImplicitType.GLOBAL_STATE,
            description="全局变量: counter",
        )
        result = cleaner.clean_global_state(issue)
        assert result["status"] == "success"
        assert issue.resolved is True

    def test_clean_side_effect(self):
        """测试清理副作用"""
        cleaner = ImplicitCleaner()
        issue = ImplicitIssue(
            implicit_type=ImplicitType.SIDE_EFFECT,
            description="函数存在副作用: process",
        )
        result = cleaner.clean_side_effect(issue)
        assert result["status"] == "success"
        assert issue.resolved is True

    def test_verify_clean(self):
        """测试验证清理结果"""
        cleaner = ImplicitCleaner()
        issues = [
            ImplicitIssue(implicit_type=ImplicitType.HIDDEN_DEPENDENCY, resolved=True),
            ImplicitIssue(implicit_type=ImplicitType.GLOBAL_STATE, resolved=False),
        ]
        # 先清理第一个
        cleaner.clean_dependency(issues[0])
        result = cleaner.verify_clean(issues)
        assert result["total"] == 2
        assert result["resolved"] >= 1

    def test_verify_clean_empty(self):
        """测试验证空列表"""
        cleaner = ImplicitCleaner()
        result = cleaner.verify_clean([])
        assert result["success_rate"] == 1.0


class TestImplicitClearService:
    """测试隐式问题清除服务"""

    def test_initialization(self):
        """测试初始化"""
        service = ImplicitClearService()
        assert service.detector is not None
        assert service.cleaner is not None

    def test_process(self):
        """测试完整流程"""
        service = ImplicitClearService()
        code_data = {
            "file_path": "main.py",
            "imports": ["os", "sys"],
            "used_imports": ["os"],
            "globals": [{"name": "counter", "mutable": True}],
            "functions": [{"name": "process", "has_side_effect": True, "modifies_global": False}],
            "couplings": [],
        }
        result = service.process(code_data)
        assert result["total_issues"] > 0
        assert result["dependency_issues"] > 0
        assert "verification" in result

    def test_get_report(self):
        """测试获取报告"""
        service = ImplicitClearService()
        code_data = {
            "file_path": "main.py",
            "imports": ["os", "sys"],
            "used_imports": ["os"],
            "globals": [],
            "functions": [],
            "couplings": [],
        }
        service.process(code_data)
        report = service.get_report()
        assert "total_issues" in report

    def test_process_no_issues(self):
        """测试无隐式问题"""
        service = ImplicitClearService()
        code_data = {
            "file_path": "main.py",
            "imports": ["os"],
            "used_imports": ["os"],
            "globals": [],
            "functions": [],
            "couplings": [],
        }
        result = service.process(code_data)
        assert result["total_issues"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
