"""
阶段54验收测试：代码提交→评审校验链路
"""

import pytest
from src.architecture.pipeline_review import (
    ReviewSeverity,
    ReviewStatus,
    CodeSubmission,
    ReviewFinding,
    ReviewResult,
    CodeReviewer,
    ReviewPipeline,
)


class TestReviewSeverity:
    """测试评审严重程度枚举"""

    def test_severity_values(self):
        """测试评审严重程度枚举值"""
        assert ReviewSeverity.INFO.value == "info"
        assert ReviewSeverity.WARNING.value == "warning"
        assert ReviewSeverity.ERROR.value == "error"
        assert ReviewSeverity.CRITICAL.value == "critical"

    def test_all_severities(self):
        """测试所有严重程度"""
        severities = list(ReviewSeverity)
        assert len(severities) == 4


class TestReviewStatus:
    """测试评审状态枚举"""

    def test_status_values(self):
        """测试评审状态枚举值"""
        assert ReviewStatus.PENDING.value == "pending"
        assert ReviewStatus.IN_REVIEW.value == "in_review"
        assert ReviewStatus.APPROVED.value == "approved"
        assert ReviewStatus.REJECTED.value == "rejected"
        assert ReviewStatus.NEEDS_REVISION.value == "needs_revision"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(ReviewStatus)
        assert len(statuses) == 5


class TestCodeSubmission:
    """测试代码提交"""

    def test_default_creation(self):
        """测试默认创建"""
        submission = CodeSubmission()
        assert submission.submission_id != ""
        assert submission.author == ""
        assert submission.files == []
        assert submission.description == ""
        assert submission.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        submission = CodeSubmission(
            author="developer1",
            files=["main.py", "utils.py"],
            description="添加新功能",
        )
        assert submission.author == "developer1"
        assert len(submission.files) == 2
        assert submission.description == "添加新功能"

    def test_submission_id_unique(self):
        """测试提交ID唯一性"""
        s1 = CodeSubmission()
        s2 = CodeSubmission()
        assert s1.submission_id != s2.submission_id


class TestReviewFinding:
    """测试评审发现"""

    def test_default_creation(self):
        """测试默认创建"""
        finding = ReviewFinding()
        assert finding.finding_id != ""
        assert finding.severity == ReviewSeverity.INFO
        assert finding.file_path == ""
        assert finding.line_number == 0
        assert finding.message == ""
        assert finding.suggestion == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        finding = ReviewFinding(
            severity=ReviewSeverity.ERROR,
            file_path="main.py",
            line_number=42,
            message="未处理的异常",
            suggestion="添加异常处理",
        )
        assert finding.severity == ReviewSeverity.ERROR
        assert finding.file_path == "main.py"
        assert finding.line_number == 42
        assert finding.message == "未处理的异常"

    def test_finding_id_unique(self):
        """测试发现ID唯一性"""
        f1 = ReviewFinding()
        f2 = ReviewFinding()
        assert f1.finding_id != f2.finding_id


class TestReviewResult:
    """测试评审结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = ReviewResult()
        assert result.submission_id == ""
        assert result.status == ReviewStatus.PENDING
        assert result.findings == []
        assert result.score == 0.0
        assert result.reviewer_id == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        finding = ReviewFinding(severity=ReviewSeverity.WARNING, message="测试发现")
        result = ReviewResult(
            submission_id="sub-001",
            status=ReviewStatus.APPROVED,
            findings=[finding],
            score=85.0,
            reviewer_id="reviewer-001",
        )
        assert result.submission_id == "sub-001"
        assert result.status == ReviewStatus.APPROVED
        assert len(result.findings) == 1
        assert result.score == 85.0
        assert result.reviewer_id == "reviewer-001"


class TestCodeReviewer:
    """测试代码评审器"""

    def test_initialization(self):
        """测试初始化"""
        reviewer = CodeReviewer()
        assert reviewer.reviewer_id != ""
        assert reviewer.style_rules is not None
        assert reviewer.security_patterns is not None

    def test_initialization_with_id(self):
        """测试使用指定ID初始化"""
        reviewer = CodeReviewer(reviewer_id="reviewer-001")
        assert reviewer.reviewer_id == "reviewer-001"

    def test_review_clean_submission(self):
        """测试评审干净的提交"""
        reviewer = CodeReviewer()
        submission = CodeSubmission(
            author="dev1",
            files=["main.py", "utils.py"],
            description="添加新功能",
        )
        result = reviewer.review(submission)
        assert result.submission_id == submission.submission_id
        assert result.score > 0
        assert result.reviewer_id == reviewer.reviewer_id

    def test_review_empty_files(self):
        """测试评审空文件提交"""
        reviewer = CodeReviewer()
        submission = CodeSubmission(
            author="dev1",
            files=[],
            description="空提交",
        )
        result = reviewer.review(submission)
        # 空文件应该有ERROR级别的发现
        has_error = any(f.severity == ReviewSeverity.ERROR for f in result.findings)
        assert has_error is True

    def test_review_no_description(self):
        """测试评审无描述提交"""
        reviewer = CodeReviewer()
        submission = CodeSubmission(
            author="dev1",
            files=["main.py"],
            description="",
        )
        result = reviewer.review(submission)
        has_warning = any("描述" in f.message for f in result.findings)
        assert has_warning is True

    def test_review_security_issue(self):
        """测试评审安全问题"""
        reviewer = CodeReviewer()
        submission = CodeSubmission(
            author="dev1",
            files=["eval_handler.py"],
            description="添加评估功能",
        )
        result = reviewer.review(submission)
        has_critical = any(f.severity == ReviewSeverity.CRITICAL for f in result.findings)
        assert has_critical is True

    def test_review_file_with_spaces(self):
        """测试评审文件名含空格"""
        reviewer = CodeReviewer()
        submission = CodeSubmission(
            author="dev1",
            files=["my file.py"],
            description="添加文件",
        )
        result = reviewer.review(submission)
        has_space_warning = any("空格" in f.message for f in result.findings)
        assert has_space_warning is True

    def test_review_too_many_files(self):
        """测试评审文件过多"""
        reviewer = CodeReviewer()
        files = [f"file_{i}.py" for i in range(25)]
        submission = CodeSubmission(
            author="dev1",
            files=files,
            description="大批量提交",
        )
        result = reviewer.review(submission)
        has_too_many = any("过多" in f.message for f in result.findings)
        assert has_too_many is True

    def test_calculate_score_no_findings(self):
        """测试无发现时的得分"""
        reviewer = CodeReviewer()
        score = reviewer._calculate_score([])
        assert score == 100.0

    def test_calculate_score_with_findings(self):
        """测试有发现时的得分"""
        reviewer = CodeReviewer()
        findings = [
            ReviewFinding(severity=ReviewSeverity.INFO),
            ReviewFinding(severity=ReviewSeverity.WARNING),
            ReviewFinding(severity=ReviewSeverity.ERROR),
        ]
        score = reviewer._calculate_score(findings)
        assert score < 100.0
        assert score >= 0.0

    def test_calculate_score_critical(self):
        """测试严重问题时的得分"""
        reviewer = CodeReviewer()
        findings = [
            ReviewFinding(severity=ReviewSeverity.CRITICAL),
            ReviewFinding(severity=ReviewSeverity.CRITICAL),
            ReviewFinding(severity=ReviewSeverity.CRITICAL),
            ReviewFinding(severity=ReviewSeverity.CRITICAL),
        ]
        score = reviewer._calculate_score(findings)
        assert score == 0.0  # 4个CRITICAL = 120分扣减，下限为0

    def test_review_sets_in_review(self):
        """测试评审后状态为IN_REVIEW"""
        reviewer = CodeReviewer()
        submission = CodeSubmission(
            author="dev1",
            files=["main.py"],
            description="小修改",
        )
        result = reviewer.review(submission)
        assert result.status == ReviewStatus.IN_REVIEW

    def test_review_score_reflects_quality(self):
        """测试评审得分反映代码质量"""
        reviewer = CodeReviewer()
        # 高质量提交
        good = CodeSubmission(author="dev1", files=["main.py"], description="好提交")
        good_result = reviewer.review(good)
        # 低质量提交
        bad_files = ["eval_" + f"file_{i}.py" for i in range(25)]
        bad = CodeSubmission(author="dev1", files=bad_files, description="")
        bad_result = reviewer.review(bad)
        assert good_result.score > bad_result.score


class TestReviewPipeline:
    """测试评审流水线"""

    def test_initialization(self):
        """测试初始化"""
        pipeline = ReviewPipeline()
        assert pipeline.reviewer is not None
        assert len(pipeline.submissions) == 0
        assert len(pipeline.results) == 0

    def test_submit_code(self):
        """测试提交代码"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="初始提交",
        )
        assert submission.submission_id in pipeline.submissions
        assert submission.author == "dev1"
        assert submission.submission_id in pipeline.results
        assert pipeline.results[submission.submission_id].status == ReviewStatus.PENDING

    def test_submit_code_empty(self):
        """测试提交空代码"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code()
        assert submission.author == ""
        assert submission.files == []
        assert submission.description == ""

    def test_start_review(self):
        """测试开始评审"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试提交",
        )
        result = pipeline.start_review(submission.submission_id)
        assert result is not None
        assert result.submission_id == submission.submission_id
        assert result.status == ReviewStatus.IN_REVIEW

    def test_start_review_nonexistent(self):
        """测试评审不存在的提交"""
        pipeline = ReviewPipeline()
        result = pipeline.start_review("nonexistent-id")
        assert result is None

    def test_get_review_result(self):
        """测试获取评审结果"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试",
        )
        # 评审前获取
        result = pipeline.get_review_result(submission.submission_id)
        assert result is not None
        assert result.status == ReviewStatus.PENDING

    def test_get_review_result_after_review(self):
        """测试评审后获取结果"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试",
        )
        pipeline.start_review(submission.submission_id)
        result = pipeline.get_review_result(submission.submission_id)
        assert result is not None
        assert result.status != ReviewStatus.PENDING

    def test_get_review_result_nonexistent(self):
        """测试获取不存在的结果"""
        pipeline = ReviewPipeline()
        result = pipeline.get_review_result("nonexistent-id")
        assert result is None

    def test_approve(self):
        """测试批准评审"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试",
        )
        pipeline.start_review(submission.submission_id)
        success = pipeline.approve(submission.submission_id, reviewer_id="reviewer-001")
        assert success is True
        result = pipeline.get_review_result(submission.submission_id)
        assert result.status == ReviewStatus.APPROVED
        assert result.reviewer_id == "reviewer-001"

    def test_approve_nonexistent(self):
        """测试批准不存在的提交"""
        pipeline = ReviewPipeline()
        success = pipeline.approve("nonexistent-id")
        assert success is False

    def test_approve_already_approved(self):
        """测试批准已批准的提交"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试",
        )
        pipeline.start_review(submission.submission_id)
        pipeline.approve(submission.submission_id)
        # 再次批准应失败
        success = pipeline.approve(submission.submission_id)
        assert success is False

    def test_reject(self):
        """测试拒绝评审"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试",
        )
        pipeline.start_review(submission.submission_id)
        success = pipeline.reject(submission.submission_id, reviewer_id="reviewer-002")
        assert success is True
        result = pipeline.get_review_result(submission.submission_id)
        assert result.status == ReviewStatus.REJECTED
        assert result.reviewer_id == "reviewer-002"

    def test_reject_nonexistent(self):
        """测试拒绝不存在的提交"""
        pipeline = ReviewPipeline()
        success = pipeline.reject("nonexistent-id")
        assert success is False

    def test_reject_already_rejected(self):
        """测试拒绝已拒绝的提交"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试",
        )
        pipeline.start_review(submission.submission_id)
        pipeline.reject(submission.submission_id)
        # 再次拒绝应失败
        success = pipeline.reject(submission.submission_id)
        assert success is False

    def test_full_pipeline_workflow(self):
        """测试完整流水线工作流"""
        pipeline = ReviewPipeline()

        # 1. 提交代码
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py", "utils.py", "config.py"],
            description="添加用户管理功能",
        )
        assert submission.submission_id in pipeline.submissions

        # 2. 开始评审
        result = pipeline.start_review(submission.submission_id)
        assert result is not None
        assert result.status == ReviewStatus.IN_REVIEW

        # 3. 根据得分决定批准或拒绝
        if result.score >= 50:
            success = pipeline.approve(submission.submission_id)
            assert success is True
            final = pipeline.get_review_result(submission.submission_id)
            assert final.status == ReviewStatus.APPROVED
        else:
            success = pipeline.reject(submission.submission_id)
            assert success is True
            final = pipeline.get_review_result(submission.submission_id)
            assert final.status == ReviewStatus.REJECTED

    def test_multiple_submissions(self):
        """测试多次提交"""
        pipeline = ReviewPipeline()
        s1 = pipeline.submit_code(author="dev1", files=["a.py"], description="提交1")
        s2 = pipeline.submit_code(author="dev2", files=["b.py"], description="提交2")
        s3 = pipeline.submit_code(author="dev3", files=["c.py"], description="提交3")

        assert len(pipeline.submissions) == 3
        assert s1.submission_id != s2.submission_id
        assert s2.submission_id != s3.submission_id

        pipeline.start_review(s1.submission_id)
        pipeline.start_review(s2.submission_id)
        pipeline.start_review(s3.submission_id)

        r1 = pipeline.get_review_result(s1.submission_id)
        r2 = pipeline.get_review_result(s2.submission_id)
        r3 = pipeline.get_review_result(s3.submission_id)
        assert r1 is not None
        assert r2 is not None
        assert r3 is not None

    def test_approve_pending_submission(self):
        """测试批准待评审的提交"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试",
        )
        # 未开始评审直接批准应失败
        success = pipeline.approve(submission.submission_id)
        assert success is False

    def test_needs_revision_then_approve(self):
        """测试需要修改后批准"""
        pipeline = ReviewPipeline()
        submission = pipeline.submit_code(
            author="dev1",
            files=["main.py"],
            description="测试",
        )
        pipeline.start_review(submission.submission_id)
        result = pipeline.get_review_result(submission.submission_id)

        # 如果状态是NEEDS_REVISION，可以批准
        if result.status == ReviewStatus.NEEDS_REVISION:
            success = pipeline.approve(submission.submission_id)
            assert success is True
            final = pipeline.get_review_result(submission.submission_id)
            assert final.status == ReviewStatus.APPROVED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
