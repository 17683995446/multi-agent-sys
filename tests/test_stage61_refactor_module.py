"""
阶段61验收测试 - 大型项目模块级重构
"""

import pytest
from src.architecture.refactor_module import (
    RefactorType,
    RefactorStatus,
    ModuleRefactorPlan,
    ModuleRefactorer,
    ModuleRefactorService,
)


class TestRefactorType:
    """测试重构类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RefactorType.EXTRACT_MODULE.value == "extract_module"
        assert RefactorType.MERGE_MODULE.value == "merge_module"
        assert RefactorType.RENAME_MODULE.value == "rename_module"
        assert RefactorType.RESTRUCTURE.value == "restructure"

    def test_all_types(self):
        """测试所有类型"""
        types = list(RefactorType)
        assert len(types) == 4


class TestRefactorStatus:
    """测试重构状态枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RefactorStatus.PLANNED.value == "planned"
        assert RefactorStatus.IN_PROGRESS.value == "in_progress"
        assert RefactorStatus.COMPLETED.value == "completed"
        assert RefactorStatus.ROLLED_BACK.value == "rolled_back"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(RefactorStatus)
        assert len(statuses) == 4


class TestModuleRefactorPlan:
    """测试模块重构计划"""

    def test_default_creation(self):
        """测试默认创建"""
        plan = ModuleRefactorPlan()
        assert plan.plan_id != ""
        assert plan.refactor_type == RefactorType.EXTRACT_MODULE
        assert plan.source_module == ""
        assert plan.target_module == ""
        assert plan.changes == []
        assert plan.risk_level == "low"
        assert plan.status == RefactorStatus.PLANNED

    def test_custom_creation(self):
        """测试自定义创建"""
        plan = ModuleRefactorPlan(
            refactor_type=RefactorType.MERGE_MODULE,
            source_module="module_a",
            target_module="module_b",
            changes=["合并模块"],
            risk_level="high",
            status=RefactorStatus.IN_PROGRESS,
        )
        assert plan.refactor_type == RefactorType.MERGE_MODULE
        assert plan.source_module == "module_a"
        assert plan.target_module == "module_b"
        assert plan.changes == ["合并模块"]
        assert plan.risk_level == "high"
        assert plan.status == RefactorStatus.IN_PROGRESS

    def test_plan_id_unique(self):
        """测试计划ID唯一性"""
        plan1 = ModuleRefactorPlan()
        plan2 = ModuleRefactorPlan()
        assert plan1.plan_id != plan2.plan_id


class TestModuleRefactorer:
    """测试模块重构器"""

    def test_initialization(self):
        """测试初始化"""
        refactorer = ModuleRefactorer()
        assert refactorer._analysis_cache == {}
        assert refactorer._execution_log == []

    def test_analyze_module(self):
        """测试分析模块"""
        refactorer = ModuleRefactorer()
        result = refactorer.analyze_module("user_service", {
            "size": 500,
            "dependencies": ["db", "cache"],
            "exports": ["UserService"],
        })
        assert result["module_name"] == "user_service"
        assert result["size"] == 500
        assert len(result["dependencies"]) == 2

    def test_analyze_module_large(self):
        """测试分析大模块"""
        refactorer = ModuleRefactorer()
        result = refactorer.analyze_module("big_module", {
            "size": 2000,
            "dependencies": [f"dep_{i}" for i in range(12)],
        })
        assert len(result["refactor_suggestions"]) >= 2

    def test_analyze_module_default(self):
        """测试分析模块默认信息"""
        refactorer = ModuleRefactorer()
        result = refactorer.analyze_module("simple_module")
        assert result["module_name"] == "simple_module"
        assert result["size"] == 0

    def test_plan_refactor_extract(self):
        """测试规划提取模块重构"""
        refactorer = ModuleRefactorer()
        plan = refactorer.plan_refactor(
            RefactorType.EXTRACT_MODULE, "source_mod", "target_mod"
        )
        assert plan.refactor_type == RefactorType.EXTRACT_MODULE
        assert plan.source_module == "source_mod"
        assert plan.target_module == "target_mod"
        assert plan.risk_level == "medium"
        assert len(plan.changes) > 0

    def test_plan_refactor_merge(self):
        """测试规划合并模块重构"""
        refactorer = ModuleRefactorer()
        plan = refactorer.plan_refactor(
            RefactorType.MERGE_MODULE, "mod_a", "mod_b"
        )
        assert plan.risk_level == "high"
        assert len(plan.changes) > 0

    def test_plan_refactor_rename(self):
        """测试规划重命名模块重构"""
        refactorer = ModuleRefactorer()
        plan = refactorer.plan_refactor(
            RefactorType.RENAME_MODULE, "old_name", "new_name"
        )
        assert plan.risk_level == "low"

    def test_plan_refactor_restructure(self):
        """测试规划重组模块重构"""
        refactorer = ModuleRefactorer()
        plan = refactorer.plan_refactor(
            RefactorType.RESTRUCTURE, "complex_mod"
        )
        assert plan.risk_level == "high"

    def test_execute_refactor(self):
        """测试执行重构"""
        refactorer = ModuleRefactorer()
        plan = refactorer.plan_refactor(
            RefactorType.EXTRACT_MODULE, "source", "target"
        )
        result = refactorer.execute_refactor(plan)
        assert result is True
        assert plan.status == RefactorStatus.COMPLETED

    def test_execute_refactor_already_completed(self):
        """测试执行已完成的重构"""
        refactorer = ModuleRefactorer()
        plan = ModuleRefactorPlan(status=RefactorStatus.COMPLETED)
        result = refactorer.execute_refactor(plan)
        assert result is False

    def test_verify_refactor_completed(self):
        """测试验证已完成的重构"""
        refactorer = ModuleRefactorer()
        plan = refactorer.plan_refactor(
            RefactorType.EXTRACT_MODULE, "source", "target"
        )
        refactorer.execute_refactor(plan)
        result = refactorer.verify_refactor(plan)
        assert result["verified"] is True

    def test_verify_refactor_not_completed(self):
        """测试验证未完成的重构"""
        refactorer = ModuleRefactorer()
        plan = refactorer.plan_refactor(
            RefactorType.EXTRACT_MODULE, "source", "target"
        )
        result = refactorer.verify_refactor(plan)
        assert result["verified"] is False

    def test_rollback(self):
        """测试回滚重构"""
        refactorer = ModuleRefactorer()
        plan = refactorer.plan_refactor(
            RefactorType.EXTRACT_MODULE, "source", "target"
        )
        refactorer.execute_refactor(plan)
        result = refactorer.rollback(plan)
        assert result is True
        assert plan.status == RefactorStatus.ROLLED_BACK

    def test_rollback_not_executed(self):
        """测试回滚未执行的重构"""
        refactorer = ModuleRefactorer()
        plan = ModuleRefactorPlan()
        result = refactorer.rollback(plan)
        assert result is False


class TestModuleRefactorService:
    """测试模块重构服务"""

    def test_initialization(self):
        """测试初始化"""
        service = ModuleRefactorService()
        assert service.refactorer is not None
        assert len(service._plans) == 0

    def test_create_plan(self):
        """测试创建计划"""
        service = ModuleRefactorService()
        plan = service.create_plan(
            RefactorType.EXTRACT_MODULE, "source_mod", "target_mod"
        )
        assert plan is not None
        assert plan.source_module == "source_mod"

    def test_execute_plan(self):
        """测试执行计划"""
        service = ModuleRefactorService()
        plan = service.create_plan(
            RefactorType.RENAME_MODULE, "old_mod", "new_mod"
        )
        result = service.execute_plan(plan.plan_id)
        assert result is True

    def test_execute_plan_not_found(self):
        """测试执行不存在的计划"""
        service = ModuleRefactorService()
        result = service.execute_plan("nonexistent")
        assert result is False

    def test_get_plan(self):
        """测试获取计划"""
        service = ModuleRefactorService()
        plan = service.create_plan(
            RefactorType.EXTRACT_MODULE, "source_mod"
        )
        retrieved = service.get_plan(plan.plan_id)
        assert retrieved is plan

    def test_get_plan_not_found(self):
        """测试获取不存在的计划"""
        service = ModuleRefactorService()
        retrieved = service.get_plan("nonexistent")
        assert retrieved is None

    def test_list_plans(self):
        """测试列出所有计划"""
        service = ModuleRefactorService()
        service.create_plan(RefactorType.EXTRACT_MODULE, "mod1")
        service.create_plan(RefactorType.MERGE_MODULE, "mod2")
        plans = service.list_plans()
        assert len(plans) == 2

    def test_list_plans_by_status(self):
        """测试按状态列出计划"""
        service = ModuleRefactorService()
        plan = service.create_plan(RefactorType.EXTRACT_MODULE, "mod1")
        service.execute_plan(plan.plan_id)
        completed = service.list_plans(RefactorStatus.COMPLETED)
        planned = service.list_plans(RefactorStatus.PLANNED)
        assert len(completed) == 1
        assert len(planned) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
