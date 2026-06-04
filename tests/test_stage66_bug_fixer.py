"""
阶段66验收测试：批量Bug自动修复
"""

import pytest
from src.architecture.bug_fixer import (
    FixStrategy,
    FixStatus,
    BugFix,
    BugFixer,
    BugFixService,
)


class TestFixStrategy:
    """测试修复策略枚举"""

    def test_strategy_values(self):
        """测试修复策略枚举值"""
        assert FixStrategy.PATCH.value == "patch"
        assert FixStrategy.REPLACE.value == "replace"
        assert FixStrategy.REFACTOR.value == "refactor"
        assert FixStrategy.WORKAROUND.value == "workaround"

    def test_all_strategies(self):
        """测试所有策略"""
        strategies = list(FixStrategy)
        assert len(strategies) == 4


class TestFixStatus:
    """测试修复状态枚举"""

    def test_status_values(self):
        """测试修复状态枚举值"""
        assert FixStatus.PENDING.value == "pending"
        assert FixStatus.APPLYING.value == "applying"
        assert FixStatus.APPLIED.value == "applied"
        assert FixStatus.VERIFIED.value == "verified"
        assert FixStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(FixStatus)
        assert len(statuses) == 5


class TestBugFix:
    """测试Bug修复记录"""

    def test_default_creation(self):
        """测试默认创建"""
        fix = BugFix()
        assert fix.fix_id != ""
        assert fix.bug_id == ""
        assert fix.strategy == FixStrategy.PATCH
        assert fix.description == ""
        assert fix.code_changes == []
        assert fix.status == FixStatus.PENDING
        assert fix.verified is False
        assert fix.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        fix = BugFix(
            bug_id="BUG-001",
            strategy=FixStrategy.REPLACE,
            description="修复空指针异常",
            code_changes=[{"type": "replace", "applied": True}],
            status=FixStatus.APPLIED,
            verified=True,
        )
        assert fix.bug_id == "BUG-001"
        assert fix.strategy == FixStrategy.REPLACE
        assert fix.description == "修复空指针异常"
        assert len(fix.code_changes) == 1
        assert fix.status == FixStatus.APPLIED
        assert fix.verified is True

    def test_fix_id_unique(self):
        """测试修复ID唯一性"""
        f1 = BugFix()
        f2 = BugFix()
        assert f1.fix_id != f2.fix_id


class TestBugFixer:
    """测试Bug修复器"""

    def test_initialization(self):
        """测试初始化"""
        fixer = BugFixer()
        assert len(fixer.fixes) == 0
        assert len(fixer.rollback_stack) == 0

    def test_fix_bug_patch(self):
        """测试补丁修复"""
        fixer = BugFixer()
        fix = fixer.fix_bug("BUG-001", FixStrategy.PATCH, "补丁修复描述")
        assert fix.bug_id == "BUG-001"
        assert fix.strategy == FixStrategy.PATCH
        assert fix.status == FixStatus.APPLIED
        assert len(fix.code_changes) == 1
        assert fix.code_changes[0]["type"] == "patch"
        assert fix.fix_id in fixer.fixes

    def test_fix_bug_replace(self):
        """测试替换修复"""
        fixer = BugFixer()
        fix = fixer.fix_bug("BUG-002", FixStrategy.REPLACE, "替换修复描述")
        assert fix.strategy == FixStrategy.REPLACE
        assert fix.status == FixStatus.APPLIED
        assert fix.code_changes[0]["type"] == "replace"

    def test_fix_bug_refactor(self):
        """测试重构修复"""
        fixer = BugFixer()
        fix = fixer.fix_bug("BUG-003", FixStrategy.REFACTOR, "重构修复描述")
        assert fix.strategy == FixStrategy.REFACTOR
        assert fix.status == FixStatus.APPLIED
        assert fix.code_changes[0]["type"] == "refactor"

    def test_fix_bug_workaround(self):
        """测试规避修复"""
        fixer = BugFixer()
        fix = fixer.fix_bug("BUG-004", FixStrategy.WORKAROUND, "规避修复描述")
        assert fix.strategy == FixStrategy.WORKAROUND
        assert fix.status == FixStatus.APPLIED
        assert fix.code_changes[0]["type"] == "workaround"

    def test_fix_bug_with_code_changes(self):
        """测试带代码变更的修复"""
        fixer = BugFixer()
        changes = [{"type": "edit", "file": "main.py", "applied": True}]
        fix = fixer.fix_bug("BUG-005", FixStrategy.PATCH, "带变更修复",
                            code_changes=changes)
        assert len(fix.code_changes) == 2  # 原始变更 + 策略变更

    def test_fix_bug_added_to_rollback_stack(self):
        """测试修复添加到回滚栈"""
        fixer = BugFixer()
        fix = fixer.fix_bug("BUG-006", FixStrategy.PATCH)
        assert fix.fix_id in fixer.rollback_stack

    def test_verify_fix_success(self):
        """测试验证修复成功"""
        fixer = BugFixer()
        fix = fixer.fix_bug("BUG-007", FixStrategy.PATCH)
        result = fixer.verify_fix(fix.fix_id)
        assert result is True
        assert fix.status == FixStatus.VERIFIED
        assert fix.verified is True

    def test_verify_fix_not_found(self):
        """测试验证不存在的修复"""
        fixer = BugFixer()
        result = fixer.verify_fix("nonexistent")
        assert result is False

    def test_verify_fix_not_applied(self):
        """测试验证未应用的修复"""
        fixer = BugFixer()
        fix = BugFix(bug_id="BUG-008", status=FixStatus.PENDING)
        fixer.fixes[fix.fix_id] = fix
        result = fixer.verify_fix(fix.fix_id)
        assert result is False

    def test_rollback_fix_success(self):
        """测试回滚修复成功"""
        fixer = BugFixer()
        fix = fixer.fix_bug("BUG-009", FixStrategy.PATCH)
        result = fixer.rollback_fix(fix.fix_id)
        assert result is True
        assert fix.status == FixStatus.FAILED
        assert fix.verified is False
        assert all(not c["applied"] for c in fix.code_changes)

    def test_rollback_fix_not_found(self):
        """测试回滚不存在的修复"""
        fixer = BugFixer()
        result = fixer.rollback_fix("nonexistent")
        assert result is False

    def test_rollback_fix_pending_status(self):
        """测试回滚待处理状态的修复"""
        fixer = BugFixer()
        fix = BugFix(bug_id="BUG-010", status=FixStatus.PENDING)
        fixer.fixes[fix.fix_id] = fix
        result = fixer.rollback_fix(fix.fix_id)
        assert result is False


class TestBugFixService:
    """测试Bug修复服务"""

    def test_initialization(self):
        """测试初始化"""
        service = BugFixService()
        assert service.fixer is not None
        assert service.statistics["total_fixes"] == 0

    def test_fix(self):
        """测试执行修复"""
        service = BugFixService()
        fix = service.fix("BUG-100", FixStrategy.REPLACE, "服务层修复")
        assert fix.bug_id == "BUG-100"
        assert service.statistics["total_fixes"] == 1

    def test_verify(self):
        """测试验证修复"""
        service = BugFixService()
        fix = service.fix("BUG-101", FixStrategy.PATCH)
        result = service.verify(fix.fix_id)
        assert result is True
        assert service.statistics["verified_fixes"] == 1

    def test_get_fix(self):
        """测试获取修复记录"""
        service = BugFixService()
        fix = service.fix("BUG-102", FixStrategy.REFACTOR)
        retrieved = service.get_fix(fix.fix_id)
        assert retrieved is not None
        assert retrieved.fix_id == fix.fix_id

    def test_get_fix_not_found(self):
        """测试获取不存在的修复记录"""
        service = BugFixService()
        result = service.get_fix("nonexistent")
        assert result is None

    def test_get_statistics(self):
        """测试获取统计信息"""
        service = BugFixService()
        service.fix("BUG-200", FixStrategy.PATCH)
        service.fix("BUG-201", FixStrategy.REPLACE)
        stats = service.get_statistics()
        assert stats["total_fixes"] == 2

    def test_full_workflow(self):
        """测试完整工作流"""
        service = BugFixService()
        # 1. 修复Bug
        fix = service.fix("BUG-300", FixStrategy.REFACTOR, "完整流程测试")
        assert fix.status == FixStatus.APPLIED
        # 2. 验证修复
        result = service.verify(fix.fix_id)
        assert result is True
        assert fix.status == FixStatus.VERIFIED
        # 3. 查看统计
        stats = service.get_statistics()
        assert stats["total_fixes"] == 1
        assert stats["verified_fixes"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
