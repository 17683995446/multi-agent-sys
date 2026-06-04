"""
阶段58验收测试：测试失败缺陷回流分支
"""

import pytest
from src.architecture.pipeline_defect import (
    DefectSeverity,
    DefectStatus,
    DefectRecord,
    DefectDetector,
    DefectRouter,
    DefectPipeline,
)


class TestDefectSeverity:
    """测试缺陷严重程度枚举"""

    def test_severity_values(self):
        """测试缺陷严重程度枚举值"""
        assert DefectSeverity.BLOCKER.value == "blocker"
        assert DefectSeverity.CRITICAL.value == "critical"
        assert DefectSeverity.MAJOR.value == "major"
        assert DefectSeverity.MINOR.value == "minor"
        assert DefectSeverity.TRIVIAL.value == "trivial"

    def test_all_severities(self):
        """测试所有严重程度"""
        severities = list(DefectSeverity)
        assert len(severities) == 5


class TestDefectStatus:
    """测试缺陷状态枚举"""

    def test_status_values(self):
        """测试缺陷状态枚举值"""
        assert DefectStatus.DETECTED.value == "detected"
        assert DefectStatus.ANALYZING.value == "analyzing"
        assert DefectStatus.ASSIGNED.value == "assigned"
        assert DefectStatus.FIXING.value == "fixing"
        assert DefectStatus.FIXED.value == "fixed"
        assert DefectStatus.VERIFIED.value == "verified"
        assert DefectStatus.CLOSED.value == "closed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(DefectStatus)
        assert len(statuses) == 7


class TestDefectRecord:
    """测试缺陷记录"""

    def test_default_creation(self):
        """测试默认创建"""
        record = DefectRecord()
        assert record.defect_id != ""
        assert record.test_case_id == ""
        assert record.severity == DefectSeverity.MAJOR
        assert record.description == ""
        assert record.status == DefectStatus.DETECTED
        assert record.assignee == ""
        assert record.root_cause == ""
        assert record.fix_description == ""
        assert record.created_at > 0
        assert record.updated_at > 0
        assert record.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        record = DefectRecord(
            test_case_id="tc-001",
            severity=DefectSeverity.CRITICAL,
            description="登录功能异常",
            status=DefectStatus.ASSIGNED,
            assignee="dev_agent_1",
            root_cause="空指针引用",
        )
        assert record.test_case_id == "tc-001"
        assert record.severity == DefectSeverity.CRITICAL
        assert record.description == "登录功能异常"
        assert record.status == DefectStatus.ASSIGNED
        assert record.assignee == "dev_agent_1"
        assert record.root_cause == "空指针引用"

    def test_defect_id_unique(self):
        """测试缺陷ID唯一性"""
        r1 = DefectRecord()
        r2 = DefectRecord()
        assert r1.defect_id != r2.defect_id


class TestDefectDetector:
    """测试缺陷检测器"""

    def test_initialization(self):
        """测试初始化"""
        detector = DefectDetector()
        assert len(detector.detected_defects) == 0

    def test_detect_from_failed_test(self):
        """测试从失败测试检测缺陷"""
        detector = DefectDetector()
        defect = detector.detect_from_test(
            test_case_id="tc-001",
            test_result={"failed": True, "error_message": "断言失败"},
        )
        assert defect is not None
        assert defect.test_case_id == "tc-001"
        assert defect.status == DefectStatus.DETECTED
        assert defect.defect_id in detector.detected_defects

    def test_detect_from_passed_test(self):
        """测试从通过测试不检测缺陷"""
        detector = DefectDetector()
        defect = detector.detect_from_test(
            test_case_id="tc-002",
            test_result={"failed": False},
        )
        assert defect is None

    def test_detect_with_no_result(self):
        """测试无测试结果时不检测缺陷"""
        detector = DefectDetector()
        defect = detector.detect_from_test(test_case_id="tc-003")
        assert defect is None

    def test_analyze_root_cause_assertion(self):
        """测试分析断言错误根因"""
        detector = DefectDetector()
        defect = detector.detect_from_test(
            test_case_id="tc-004",
            test_result={"failed": True, "error_type": "assertion"},
        )
        result = detector.analyze_root_cause(defect.defect_id)
        assert result is not None
        assert "断言失败" in result.root_cause
        assert result.status == DefectStatus.ANALYZING

    def test_analyze_root_cause_timeout(self):
        """测试分析超时错误根因"""
        detector = DefectDetector()
        defect = detector.detect_from_test(
            test_case_id="tc-005",
            test_result={"failed": True, "error_type": "timeout"},
        )
        result = detector.analyze_root_cause(defect.defect_id)
        assert result is not None
        assert "超时" in result.root_cause

    def test_analyze_root_cause_exception(self):
        """测试分析异常错误根因"""
        detector = DefectDetector()
        defect = detector.detect_from_test(
            test_case_id="tc-006",
            test_result={"failed": True, "error_type": "exception"},
        )
        result = detector.analyze_root_cause(defect.defect_id)
        assert result is not None
        assert "异常" in result.root_cause

    def test_analyze_root_cause_unknown(self):
        """测试分析未知错误根因"""
        detector = DefectDetector()
        defect = detector.detect_from_test(
            test_case_id="tc-007",
            test_result={"failed": True, "error_type": "other"},
        )
        result = detector.analyze_root_cause(defect.defect_id)
        assert result is not None
        assert "未知" in result.root_cause

    def test_analyze_root_cause_nonexistent(self):
        """测试分析不存在的缺陷"""
        detector = DefectDetector()
        result = detector.analyze_root_cause("nonexistent")
        assert result is None

    def test_classify_severity_blocker(self):
        """测试分类为阻断级"""
        detector = DefectDetector()
        severity = detector.classify_severity({"impact": "system_down"})
        assert severity == DefectSeverity.BLOCKER

    def test_classify_severity_critical(self):
        """测试分类为严重级"""
        detector = DefectDetector()
        severity = detector.classify_severity({"impact": "data_loss"})
        assert severity == DefectSeverity.CRITICAL

    def test_classify_severity_major(self):
        """测试分类为主要级"""
        detector = DefectDetector()
        severity = detector.classify_severity({"impact": "feature_broken"})
        assert severity == DefectSeverity.MAJOR

    def test_classify_severity_minor(self):
        """测试分类为次要级"""
        detector = DefectDetector()
        severity = detector.classify_severity({"impact": "cosmetic"})
        assert severity == DefectSeverity.MINOR

    def test_classify_severity_trivial(self):
        """测试分类为轻微级"""
        detector = DefectDetector()
        severity = detector.classify_severity({})
        assert severity == DefectSeverity.TRIVIAL


class TestDefectRouter:
    """测试缺陷路由器"""

    def test_initialization(self):
        """测试初始化"""
        router = DefectRouter()
        assert len(router.assignments) == 0
        assert len(router.fix_records) == 0

    def test_route_to_agent_auto_blocker(self):
        """测试自动路由阻断级缺陷"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.BLOCKER)
        result = router.route_to_agent(defect)
        assert result is True
        assert defect.assignee == "senior_dev_agent"
        assert defect.status == DefectStatus.ASSIGNED

    def test_route_to_agent_auto_critical(self):
        """测试自动路由严重级缺陷"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.CRITICAL)
        router.route_to_agent(defect)
        assert defect.assignee == "senior_dev_agent"

    def test_route_to_agent_auto_major(self):
        """测试自动路由主要级缺陷"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.MAJOR)
        router.route_to_agent(defect)
        assert defect.assignee == "dev_agent"

    def test_route_to_agent_auto_minor(self):
        """测试自动路由次要级缺陷"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.MINOR)
        router.route_to_agent(defect)
        assert defect.assignee == "junior_dev_agent"

    def test_route_to_agent_explicit(self):
        """测试显式指定Agent路由"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.MAJOR)
        router.route_to_agent(defect, agent_id="custom_agent")
        assert defect.assignee == "custom_agent"

    def test_track_fix(self):
        """测试跟踪修复"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.MAJOR)
        router.route_to_agent(defect, agent_id="dev_agent")
        result = router.track_fix(defect.defect_id, fix_description="修复了空指针问题")
        assert result is True
        assert defect.defect_id in router.fix_records
        assert router.fix_records[defect.defect_id]["fix_description"] == "修复了空指针问题"

    def test_track_fix_unassigned(self):
        """测试跟踪未分配缺陷的修复"""
        router = DefectRouter()
        result = router.track_fix("nonexistent", fix_description="修复")
        assert result is False

    def test_verify_fix_success(self):
        """测试验证修复成功"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.MAJOR)
        router.route_to_agent(defect)
        router.track_fix(defect.defect_id, fix_description="已修复")
        result = router.verify_fix(defect, verification_result=True)
        assert result is True
        assert defect.status == DefectStatus.VERIFIED

    def test_verify_fix_failure(self):
        """测试验证修复失败"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.MAJOR)
        router.route_to_agent(defect)
        result = router.verify_fix(defect, verification_result=False)
        assert result is True
        assert defect.status == DefectStatus.FIXING

    def test_escalate_up(self):
        """测试升级缺陷严重程度"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.MINOR)
        result = router.escalate(defect, target_severity=DefectSeverity.CRITICAL)
        assert result is True
        assert defect.severity == DefectSeverity.CRITICAL

    def test_escalate_same_level(self):
        """测试升级到相同严重程度"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.MAJOR)
        result = router.escalate(defect, target_severity=DefectSeverity.MAJOR)
        assert result is True
        assert defect.severity == DefectSeverity.MAJOR

    def test_escalate_down_ignored(self):
        """测试降级严重程度被忽略"""
        router = DefectRouter()
        defect = DefectRecord(severity=DefectSeverity.CRITICAL)
        result = router.escalate(defect, target_severity=DefectSeverity.MINOR)
        assert result is True
        assert defect.severity == DefectSeverity.CRITICAL  # 不变


class TestDefectPipeline:
    """测试缺陷回流流水线"""

    def test_initialization(self):
        """测试初始化"""
        pipeline = DefectPipeline()
        assert pipeline.detector is not None
        assert pipeline.router is not None
        assert len(pipeline.defects) == 0

    def test_process_defect_from_failed_test(self):
        """测试从失败测试处理缺陷"""
        pipeline = DefectPipeline()
        defect = pipeline.process_defect(
            test_case_id="tc-001",
            test_result={"failed": True, "error_message": "断言失败", "error_type": "assertion"},
        )
        assert defect is not None
        assert defect.status == DefectStatus.ASSIGNED
        assert defect.assignee != ""
        assert defect.root_cause != ""
        assert defect.defect_id in pipeline.defects

    def test_process_defect_from_passed_test(self):
        """测试从通过测试不产生缺陷"""
        pipeline = DefectPipeline()
        defect = pipeline.process_defect(
            test_case_id="tc-002",
            test_result={"failed": False},
        )
        assert defect is None

    def test_process_defect_with_explicit_agent(self):
        """测试指定Agent处理缺陷"""
        pipeline = DefectPipeline()
        defect = pipeline.process_defect(
            test_case_id="tc-003",
            test_result={"failed": True, "error_message": "超时", "error_type": "timeout"},
            agent_id="senior_agent",
        )
        assert defect is not None
        assert defect.assignee == "senior_agent"

    def test_process_defect_blocker(self):
        """测试处理阻断级缺陷"""
        pipeline = DefectPipeline()
        defect = pipeline.process_defect(
            test_case_id="tc-004",
            test_result={
                "failed": True,
                "error_message": "系统崩溃",
                "error_type": "crash",
                "impact": "system_down",
            },
        )
        assert defect is not None
        assert defect.severity == DefectSeverity.BLOCKER
        assert defect.assignee == "senior_dev_agent"

    def test_get_defect_status(self):
        """测试获取缺陷状态"""
        pipeline = DefectPipeline()
        defect = pipeline.process_defect(
            test_case_id="tc-005",
            test_result={"failed": True, "error_message": "错误", "error_type": "assertion"},
        )
        status = pipeline.get_defect_status(defect.defect_id)
        assert status is not None
        assert status["defect_id"] == defect.defect_id
        assert status["status"] == DefectStatus.ASSIGNED.value
        assert "root_cause" in status

    def test_get_defect_status_nonexistent(self):
        """测试获取不存在缺陷的状态"""
        pipeline = DefectPipeline()
        status = pipeline.get_defect_status("nonexistent")
        assert status is None

    def test_get_defect_metrics_empty(self):
        """测试空缺陷指标"""
        pipeline = DefectPipeline()
        metrics = pipeline.get_defect_metrics()
        assert metrics["total"] == 0
        assert metrics["fix_rate"] == 0.0

    def test_get_defect_metrics_with_defects(self):
        """测试有缺陷时的指标"""
        pipeline = DefectPipeline()
        # 创建一个缺陷
        defect = pipeline.process_defect(
            test_case_id="tc-006",
            test_result={"failed": True, "error_message": "错误A", "error_type": "assertion"},
        )
        metrics = pipeline.get_defect_metrics()
        assert metrics["total"] == 1
        assert "by_severity" in metrics
        assert "by_status" in metrics

    def test_get_defect_metrics_fix_rate(self):
        """测试缺陷修复率指标"""
        pipeline = DefectPipeline()
        # 创建缺陷并标记为已修复
        defect = pipeline.process_defect(
            test_case_id="tc-007",
            test_result={"failed": True, "error_message": "错误B", "error_type": "assertion"},
        )
        # 手动设置已验证状态
        defect.status = DefectStatus.VERIFIED
        metrics = pipeline.get_defect_metrics()
        assert metrics["fix_rate"] == 1.0

    def test_full_pipeline_workflow(self):
        """测试完整缺陷回流工作流"""
        pipeline = DefectPipeline()

        # 1. 从测试结果检测缺陷
        defect = pipeline.process_defect(
            test_case_id="tc-full-001",
            test_result={
                "failed": True,
                "error_message": "登录接口返回500",
                "error_type": "exception",
                "impact": "feature_broken",
            },
        )
        assert defect is not None
        assert defect.severity == DefectSeverity.MAJOR
        assert defect.status == DefectStatus.ASSIGNED

        # 2. 跟踪修复
        pipeline.router.track_fix(defect.defect_id, fix_description="修复了空指针异常")

        # 3. 验证修复
        pipeline.router.verify_fix(defect, verification_result=True)
        assert defect.status == DefectStatus.VERIFIED

        # 4. 获取状态
        status = pipeline.get_defect_status(defect.defect_id)
        assert status["status"] == "verified"

        # 5. 获取指标
        metrics = pipeline.get_defect_metrics()
        assert metrics["total"] == 1
        assert metrics["fix_rate"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
