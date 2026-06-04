"""
阶段67验收测试：需求迭代全自动开发
"""

import pytest
from src.architecture.auto_development import (
    IterationType,
    IterationStatus,
    IterationRequest,
    IterationResult,
    AutoDeveloper,
    AutoDevService,
)


class TestIterationType:
    """测试迭代类型枚举"""

    def test_type_values(self):
        """测试迭代类型枚举值"""
        assert IterationType.NEW_FEATURE.value == "new_feature"
        assert IterationType.ENHANCEMENT.value == "enhancement"
        assert IterationType.BUG_FIX.value == "bug_fix"
        assert IterationType.REFACTORING.value == "refactoring"

    def test_all_types(self):
        """测试所有类型"""
        types = list(IterationType)
        assert len(types) == 4


class TestIterationStatus:
    """测试迭代状态枚举"""

    def test_status_values(self):
        """测试迭代状态枚举值"""
        assert IterationStatus.PLANNED.value == "planned"
        assert IterationStatus.DEVELOPING.value == "developing"
        assert IterationStatus.TESTING.value == "testing"
        assert IterationStatus.COMPLETED.value == "completed"
        assert IterationStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(IterationStatus)
        assert len(statuses) == 5


class TestIterationRequest:
    """测试迭代请求"""

    def test_default_creation(self):
        """测试默认创建"""
        req = IterationRequest()
        assert req.request_id != ""
        assert req.iteration_type == IterationType.NEW_FEATURE
        assert req.description == ""
        assert req.requirements == []
        assert req.priority == 0
        assert req.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        req = IterationRequest(
            iteration_type=IterationType.BUG_FIX,
            description="修复登录Bug",
            requirements=["修复空指针", "添加验证"],
            priority=3,
        )
        assert req.iteration_type == IterationType.BUG_FIX
        assert req.description == "修复登录Bug"
        assert len(req.requirements) == 2
        assert req.priority == 3

    def test_request_id_unique(self):
        """测试请求ID唯一性"""
        r1 = IterationRequest()
        r2 = IterationRequest()
        assert r1.request_id != r2.request_id


class TestIterationResult:
    """测试迭代结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = IterationResult()
        assert result.request_id == ""
        assert result.status == IterationStatus.PLANNED
        assert result.changes == []
        assert result.test_results == {}
        assert result.documentation == ""
        assert result.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        result = IterationResult(
            request_id="req-001",
            status=IterationStatus.COMPLETED,
            changes=[{"requirement": "新增功能"}],
            test_results={"total": 10, "passed": 10},
            documentation="# 文档",
        )
        assert result.request_id == "req-001"
        assert result.status == IterationStatus.COMPLETED
        assert len(result.changes) == 1


class TestAutoDeveloper:
    """测试自动开发器"""

    def test_initialization(self):
        """测试初始化"""
        dev = AutoDeveloper()
        assert len(dev.requests) == 0
        assert len(dev.results) == 0
        assert len(dev.progress) == 0

    def test_plan_iteration(self):
        """测试规划迭代"""
        dev = AutoDeveloper()
        req = IterationRequest(
            iteration_type=IterationType.NEW_FEATURE,
            description="新功能开发",
            requirements=["需求1", "需求2"],
        )
        result = dev.plan_iteration(req)
        assert result.status == IterationStatus.PLANNED
        assert result.request_id == req.request_id
        assert req.request_id in dev.requests
        assert dev.progress[req.request_id] == 0.0

    def test_develop(self):
        """测试执行开发"""
        dev = AutoDeveloper()
        req = IterationRequest(
            iteration_type=IterationType.ENHANCEMENT,
            description="功能增强",
            requirements=["增强1", "增强2", "增强3"],
        )
        dev.plan_iteration(req)
        result = dev.develop(req.request_id)
        assert result.status == IterationStatus.DEVELOPING
        assert len(result.changes) == 3
        assert dev.progress[req.request_id] == 50.0

    def test_develop_not_found(self):
        """测试开发不存在的请求"""
        dev = AutoDeveloper()
        result = dev.develop("nonexistent")
        assert result.status == IterationStatus.FAILED

    def test_test(self):
        """测试执行测试"""
        dev = AutoDeveloper()
        req = IterationRequest(
            iteration_type=IterationType.NEW_FEATURE,
            description="测试功能",
            requirements=["需求1"],
        )
        dev.plan_iteration(req)
        dev.develop(req.request_id)
        result = dev.test(req.request_id)
        assert result.status == IterationStatus.TESTING
        assert result.test_results["total"] > 0
        assert result.test_results["failed"] == 0
        assert dev.progress[req.request_id] == 75.0

    def test_test_not_found(self):
        """测试测试不存在的请求"""
        dev = AutoDeveloper()
        result = dev.test("nonexistent")
        assert result.status == IterationStatus.FAILED

    def test_document(self):
        """测试生成文档"""
        dev = AutoDeveloper()
        req = IterationRequest(
            iteration_type=IterationType.REFACTORING,
            description="代码重构",
            requirements=["重构模块A"],
        )
        dev.plan_iteration(req)
        dev.develop(req.request_id)
        dev.test(req.request_id)
        result = dev.document(req.request_id)
        assert result.status == IterationStatus.COMPLETED
        assert result.documentation != ""
        assert "代码重构" in result.documentation
        assert dev.progress[req.request_id] == 100.0

    def test_document_not_found(self):
        """测试文档生成不存在的请求"""
        dev = AutoDeveloper()
        result = dev.document("nonexistent")
        assert result.status == IterationStatus.FAILED

    def test_get_progress(self):
        """测试获取进度"""
        dev = AutoDeveloper()
        req = IterationRequest(description="进度测试")
        dev.plan_iteration(req)
        assert dev.get_progress(req.request_id) == 0.0
        dev.develop(req.request_id)
        assert dev.get_progress(req.request_id) == 50.0

    def test_get_progress_not_found(self):
        """测试获取不存在请求的进度"""
        dev = AutoDeveloper()
        assert dev.get_progress("nonexistent") == 0.0

    def test_full_development_cycle(self):
        """测试完整开发周期"""
        dev = AutoDeveloper()
        req = IterationRequest(
            iteration_type=IterationType.NEW_FEATURE,
            description="完整周期测试",
            requirements=["功能1", "功能2"],
        )
        # 规划
        result = dev.plan_iteration(req)
        assert result.status == IterationStatus.PLANNED
        # 开发
        result = dev.develop(req.request_id)
        assert result.status == IterationStatus.DEVELOPING
        assert len(result.changes) == 2
        # 测试
        result = dev.test(req.request_id)
        assert result.status == IterationStatus.TESTING
        # 文档
        result = dev.document(req.request_id)
        assert result.status == IterationStatus.COMPLETED
        assert dev.get_progress(req.request_id) == 100.0


class TestAutoDevService:
    """测试自动开发服务"""

    def test_initialization(self):
        """测试初始化"""
        service = AutoDevService()
        assert service.developer is not None

    def test_process_request(self):
        """测试处理请求"""
        service = AutoDevService()
        req = IterationRequest(
            iteration_type=IterationType.NEW_FEATURE,
            description="服务层测试",
            requirements=["需求A"],
        )
        result = service.process_request(req)
        assert result.status == IterationStatus.COMPLETED
        assert len(result.changes) == 1
        assert result.documentation != ""

    def test_process_bug_fix_request(self):
        """测试处理Bug修复请求"""
        service = AutoDevService()
        req = IterationRequest(
            iteration_type=IterationType.BUG_FIX,
            description="修复严重Bug",
            requirements=["修复空指针"],
            priority=5,
        )
        result = service.process_request(req)
        assert result.status == IterationStatus.COMPLETED

    def test_get_result(self):
        """测试获取结果"""
        service = AutoDevService()
        req = IterationRequest(description="获取结果测试")
        service.process_request(req)
        result = service.get_result(req.request_id)
        assert result is not None
        assert result.request_id == req.request_id

    def test_get_result_not_found(self):
        """测试获取不存在的结果"""
        service = AutoDevService()
        result = service.get_result("nonexistent")
        assert result is None

    def test_get_status(self):
        """测试获取状态"""
        service = AutoDevService()
        req = IterationRequest(description="状态测试")
        service.process_request(req)
        status = service.get_status(req.request_id)
        assert status == IterationStatus.COMPLETED

    def test_get_status_not_found(self):
        """测试获取不存在的状态"""
        service = AutoDevService()
        status = service.get_status("nonexistent")
        assert status is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
