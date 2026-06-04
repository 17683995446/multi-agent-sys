"""
阶段57验收测试：评审失败回退重改分支
"""

import pytest
from src.architecture.pipeline_rollback import (
    RollbackReason,
    RollbackStatus,
    RollbackPoint,
    RollbackAction,
    RollbackManager,
    RevisionHandler,
    RollbackPipeline,
)


class TestRollbackReason:
    """测试回退原因枚举"""

    def test_reason_values(self):
        """测试回退原因枚举值"""
        assert RollbackReason.REVIEW_FAILED.value == "review_failed"
        assert RollbackReason.TEST_FAILED.value == "test_failed"
        assert RollbackReason.BUILD_FAILED.value == "build_failed"
        assert RollbackReason.MANUAL.value == "manual"

    def test_all_reasons(self):
        """测试所有原因"""
        reasons = list(RollbackReason)
        assert len(reasons) == 4


class TestRollbackStatus:
    """测试回退状态枚举"""

    def test_status_values(self):
        """测试回退状态枚举值"""
        assert RollbackStatus.PENDING.value == "pending"
        assert RollbackStatus.ROLLING_BACK.value == "rolling_back"
        assert RollbackStatus.COMPLETED.value == "completed"
        assert RollbackStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(RollbackStatus)
        assert len(statuses) == 4


class TestRollbackPoint:
    """测试回退检查点"""

    def test_default_creation(self):
        """测试默认创建"""
        point = RollbackPoint()
        assert point.point_id != ""
        assert point.description == ""
        assert point.snapshot == {}
        assert point.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        point = RollbackPoint(
            description="初始版本",
            snapshot={"version": "1.0", "files": ["a.py", "b.py"]},
        )
        assert point.description == "初始版本"
        assert point.snapshot["version"] == "1.0"
        assert len(point.snapshot["files"]) == 2

    def test_point_id_unique(self):
        """测试检查点ID唯一性"""
        p1 = RollbackPoint()
        p2 = RollbackPoint()
        assert p1.point_id != p2.point_id


class TestRollbackAction:
    """测试回退操作记录"""

    def test_default_creation(self):
        """测试默认创建"""
        action = RollbackAction()
        assert action.action_id != ""
        assert action.reason == RollbackReason.MANUAL
        assert action.from_point == ""
        assert action.to_point == ""
        assert action.status == RollbackStatus.PENDING
        assert action.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        action = RollbackAction(
            reason=RollbackReason.REVIEW_FAILED,
            from_point="point-1",
            to_point="point-0",
            status=RollbackStatus.COMPLETED,
        )
        assert action.reason == RollbackReason.REVIEW_FAILED
        assert action.from_point == "point-1"
        assert action.to_point == "point-0"
        assert action.status == RollbackStatus.COMPLETED


class TestRollbackManager:
    """测试回退管理器"""

    def test_initialization(self):
        """测试初始化"""
        manager = RollbackManager()
        assert len(manager.checkpoints) == 0
        assert len(manager.actions) == 0
        assert manager.current_point_id is None

    def test_create_checkpoint(self):
        """测试创建检查点"""
        manager = RollbackManager()
        point = manager.create_checkpoint(description="初始检查点",
                                          snapshot={"version": "1.0"})
        assert point.point_id in manager.checkpoints
        assert manager.current_point_id == point.point_id
        assert point.description == "初始检查点"

    def test_create_multiple_checkpoints(self):
        """测试创建多个检查点"""
        manager = RollbackManager()
        p1 = manager.create_checkpoint(description="检查点1")
        p2 = manager.create_checkpoint(description="检查点2")
        assert len(manager.checkpoints) == 2
        assert manager.current_point_id == p2.point_id

    def test_rollback_success(self):
        """测试成功回退"""
        manager = RollbackManager()
        p1 = manager.create_checkpoint(description="初始版本")
        p2 = manager.create_checkpoint(description="修改后版本")
        action = manager.rollback(p1.point_id, reason=RollbackReason.REVIEW_FAILED)
        assert action is not None
        assert action.status == RollbackStatus.COMPLETED
        assert action.from_point == p2.point_id
        assert action.to_point == p1.point_id
        assert manager.current_point_id == p1.point_id

    def test_rollback_nonexistent_point(self):
        """测试回退到不存在的检查点"""
        manager = RollbackManager()
        manager.create_checkpoint(description="初始")
        action = manager.rollback("nonexistent", reason=RollbackReason.MANUAL)
        assert action is None

    def test_rollback_no_current_point(self):
        """测试无当前点时回退"""
        manager = RollbackManager()
        # 手动清除current_point_id
        manager.current_point_id = None
        point = RollbackPoint(description="测试点")
        manager.checkpoints[point.point_id] = point
        action = manager.rollback(point.point_id)
        assert action is None

    def test_get_checkpoint(self):
        """测试获取检查点"""
        manager = RollbackManager()
        point = manager.create_checkpoint(description="获取测试")
        retrieved = manager.get_checkpoint(point.point_id)
        assert retrieved is not None
        assert retrieved.point_id == point.point_id

    def test_get_checkpoint_nonexistent(self):
        """测试获取不存在的检查点"""
        manager = RollbackManager()
        result = manager.get_checkpoint("nonexistent")
        assert result is None

    def test_list_checkpoints(self):
        """测试列出检查点"""
        manager = RollbackManager()
        manager.create_checkpoint(description="检查点1")
        manager.create_checkpoint(description="检查点2")
        points = manager.list_checkpoints()
        assert len(points) == 2


class TestRevisionHandler:
    """测试修订处理器"""

    def test_initialization(self):
        """测试初始化"""
        handler = RevisionHandler()
        assert len(handler.revision_plans) == 0
        assert len(handler.revision_tracks) == 0

    def test_handle_review_failure(self):
        """测试处理评审失败"""
        handler = RevisionHandler()
        review_result = {
            "findings": [
                {"area": "代码风格", "severity": "warning"},
                {"area": "安全问题", "severity": "critical"},
            ],
        }
        plan = handler.handle_review_failure(review_result)
        assert "plan_id" in plan
        assert plan["reason"] == "review_failed"
        assert plan["priority"] == "high"
        assert "代码风格" in plan["focus_areas"]
        assert "安全问题" in plan["focus_areas"]

    def test_handle_test_failure(self):
        """测试处理测试失败"""
        handler = RevisionHandler()
        test_result = {
            "failed_tests": [
                {"module": "auth", "test": "test_login"},
                {"module": "api", "test": "test_endpoint"},
            ],
        }
        plan = handler.handle_test_failure(test_result)
        assert "plan_id" in plan
        assert plan["reason"] == "test_failed"
        assert plan["priority"] == "critical"
        assert "auth" in plan["affected_modules"]
        assert "api" in plan["affected_modules"]

    def test_create_revision_plan(self):
        """测试创建修订计划"""
        handler = RevisionHandler()
        plan = handler.create_revision_plan(
            reason=RollbackReason.BUILD_FAILED,
            details={"error": "编译错误"},
        )
        assert plan["plan_id"] in handler.revision_plans
        assert plan["reason"] == "build_failed"
        assert plan["status"] == "pending"

    def test_track_revision(self):
        """测试跟踪修订"""
        handler = RevisionHandler()
        plan = handler.create_revision_plan(reason=RollbackReason.MANUAL)
        result = handler.track_revision(plan["plan_id"], {"status": "in_progress", "progress": 50})
        assert result is True
        assert len(handler.revision_tracks[plan["plan_id"]]) == 1
        assert handler.revision_plans[plan["plan_id"]]["status"] == "in_progress"

    def test_track_revision_nonexistent_plan(self):
        """测试跟踪不存在的计划"""
        handler = RevisionHandler()
        result = handler.track_revision("nonexistent", {"status": "done"})
        assert result is False

    def test_track_multiple_revisions(self):
        """测试多次跟踪修订"""
        handler = RevisionHandler()
        plan = handler.create_revision_plan(reason=RollbackReason.MANUAL)
        handler.track_revision(plan["plan_id"], {"status": "in_progress"})
        handler.track_revision(plan["plan_id"], {"status": "completed"})
        tracks = handler.revision_tracks[plan["plan_id"]]
        assert len(tracks) == 2
        assert handler.revision_plans[plan["plan_id"]]["status"] == "completed"


class TestRollbackPipeline:
    """测试回退流水线"""

    def test_initialization(self):
        """测试初始化"""
        pipeline = RollbackPipeline()
        assert pipeline.manager is not None
        assert pipeline.handler is not None
        assert len(pipeline.failure_records) == 0

    def test_process_review_failure(self):
        """测试处理评审失败"""
        pipeline = RollbackPipeline()
        pipeline.manager.create_checkpoint(description="初始版本")
        result = pipeline.process_failure(
            RollbackReason.REVIEW_FAILED,
            {"findings": [{"area": "代码风格"}]},
        )
        assert "failure_id" in result
        assert result["reason"] == "review_failed"
        assert result["revision_plan"] is not None
        assert result["failure_id"] in pipeline.failure_records

    def test_process_test_failure(self):
        """测试处理测试失败"""
        pipeline = RollbackPipeline()
        pipeline.manager.create_checkpoint(description="初始版本")
        result = pipeline.process_failure(
            RollbackReason.TEST_FAILED,
            {"failed_tests": [{"module": "core"}]},
        )
        assert result["reason"] == "test_failed"
        assert result["revision_plan"]["priority"] == "critical"

    def test_process_manual_failure(self):
        """测试处理手动回退"""
        pipeline = RollbackPipeline()
        pipeline.manager.create_checkpoint(description="初始版本")
        result = pipeline.process_failure(RollbackReason.MANUAL)
        assert result["reason"] == "manual"

    def test_process_failure_with_rollback(self):
        """测试处理失败并回退"""
        pipeline = RollbackPipeline()
        p1 = pipeline.manager.create_checkpoint(description="版本1")
        p2 = pipeline.manager.create_checkpoint(description="版本2")
        result = pipeline.process_failure(
            RollbackReason.REVIEW_FAILED,
            {"findings": []},
        )
        assert result["rollback_action"] is not None
        assert result["rollback_action"].status == RollbackStatus.COMPLETED

    def test_process_failure_without_enough_checkpoints(self):
        """测试检查点不足时处理失败"""
        pipeline = RollbackPipeline()
        pipeline.manager.create_checkpoint(description="唯一检查点")
        result = pipeline.process_failure(RollbackReason.MANUAL)
        assert result["rollback_action"] is None

    def test_get_rollback_status(self):
        """测试获取回退状态"""
        pipeline = RollbackPipeline()
        pipeline.manager.create_checkpoint(description="初始")
        result = pipeline.process_failure(RollbackReason.MANUAL)
        status = pipeline.get_rollback_status(result["failure_id"])
        assert status is not None
        assert status["failure_id"] == result["failure_id"]

    def test_get_rollback_status_nonexistent(self):
        """测试获取不存在的回退状态"""
        pipeline = RollbackPipeline()
        status = pipeline.get_rollback_status("nonexistent")
        assert status is None

    def test_full_pipeline_workflow(self):
        """测试完整流水线工作流"""
        pipeline = RollbackPipeline()

        # 1. 创建检查点
        p1 = pipeline.manager.create_checkpoint(
            description="v1.0", snapshot={"version": "1.0"}
        )
        p2 = pipeline.manager.create_checkpoint(
            description="v2.0", snapshot={"version": "2.0"}
        )

        # 2. 处理评审失败
        result = pipeline.process_failure(
            RollbackReason.REVIEW_FAILED,
            {"findings": [{"area": "安全性", "severity": "critical"}]},
        )

        # 3. 验证回退
        assert result["rollback_action"] is not None
        assert result["rollback_action"].status == RollbackStatus.COMPLETED

        # 4. 验证修订计划
        plan = result["revision_plan"]
        assert plan["priority"] == "high"

        # 5. 跟踪修订
        pipeline.handler.track_revision(plan["plan_id"], {"status": "in_progress"})
        pipeline.handler.track_revision(plan["plan_id"], {"status": "completed"})

        # 6. 验证状态
        status = pipeline.get_rollback_status(result["failure_id"])
        assert status is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
