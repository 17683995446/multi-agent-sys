"""
代码提交→评审校验链路
职责：代码提交管理、自动评审校验、评审流程控制

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReviewSeverity(str, Enum):
    """评审问题严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReviewStatus(str, Enum):
    """评审状态"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class CodeSubmission:
    """代码提交"""
    submission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: str = ""
    files: List[str] = field(default_factory=list)
    description: str = ""
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"CodeSubmission created: id={self.submission_id}, author={self.author}, "
                     f"files={len(self.files)}")


@dataclass
class ReviewFinding:
    """评审发现"""
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: ReviewSeverity = ReviewSeverity.INFO
    file_path: str = ""
    line_number: int = 0
    message: str = ""
    suggestion: str = ""

    def __post_init__(self):
        logger.debug(f"ReviewFinding created: id={self.finding_id}, "
                     f"severity={self.severity.value}, file={self.file_path}")


@dataclass
class ReviewResult:
    """评审结果"""
    submission_id: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    findings: List[ReviewFinding] = field(default_factory=list)
    score: float = 0.0
    reviewer_id: str = ""

    def __post_init__(self):
        logger.debug(f"ReviewResult created: submission_id={self.submission_id}, "
                     f"status={self.status.value}, score={self.score}")


class CodeReviewer:
    """代码评审器"""

    def __init__(self, reviewer_id: str = ""):
        """初始化代码评审器"""
        self.reviewer_id = reviewer_id or str(uuid.uuid4())
        self.style_rules: Dict[str, Any] = {
            "max_line_length": 120,
            "max_function_length": 50,
            "max_class_methods": 20,
        }
        self.security_patterns: List[str] = [
            "eval(", "exec(", "os.system(", "subprocess.call(",
            "pickle.loads(", "__import__(", "password", "secret",
        ]
        logger.info(f"CodeReviewer initialized: reviewer_id={self.reviewer_id}")

    def review(self, submission: CodeSubmission) -> ReviewResult:
        """执行代码评审"""
        logger.info(f"CodeReviewer: starting review for submission={submission.submission_id}")
        try:
            result = ReviewResult(
                submission_id=submission.submission_id,
                status=ReviewStatus.IN_REVIEW,
                reviewer_id=self.reviewer_id,
            )

            style_findings = self._check_style(submission)
            logic_findings = self._check_logic(submission)
            security_findings = self._check_security(submission)

            result.findings = style_findings + logic_findings + security_findings
            result.score = self._calculate_score(result.findings)

            # 评审器仅设置IN_REVIEW状态，最终决定由流水线做出
            result.status = ReviewStatus.IN_REVIEW

            logger.info(f"CodeReviewer: review completed for submission={submission.submission_id}, "
                        f"status={result.status.value}, score={result.score}, "
                        f"findings={len(result.findings)}")
        except Exception as e:
            logger.error(f"CodeReviewer: review failed: {e}")
            result = ReviewResult(
                submission_id=submission.submission_id,
                status=ReviewStatus.REJECTED,
                reviewer_id=self.reviewer_id,
                score=0.0,
            )

        return result

    def _check_style(self, submission: CodeSubmission) -> List[ReviewFinding]:
        """检查代码风格"""
        logger.debug(f"CodeReviewer: checking style for submission={submission.submission_id}")
        findings = []

        for file_path in submission.files:
            # 检查文件命名规范
            if " " in file_path:
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.WARNING,
                    file_path=file_path,
                    line_number=0,
                    message=f"文件名包含空格: {file_path}",
                    suggestion="使用下划线替代空格",
                ))

            # 检查文件扩展名
            if not any(file_path.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".go"]):
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.INFO,
                    file_path=file_path,
                    line_number=0,
                    message=f"非标准代码文件: {file_path}",
                    suggestion="确认文件类型是否正确",
                ))

        logger.debug(f"CodeReviewer: style check found {len(findings)} findings")
        return findings

    def _check_logic(self, submission: CodeSubmission) -> List[ReviewFinding]:
        """检查代码逻辑"""
        logger.debug(f"CodeReviewer: checking logic for submission={submission.submission_id}")
        findings = []

        # 检查提交描述
        if not submission.description:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.WARNING,
                file_path="",
                line_number=0,
                message="提交缺少描述信息",
                suggestion="添加有意义的提交描述",
            ))

        # 检查提交文件数量
        if len(submission.files) > 20:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.WARNING,
                file_path="",
                line_number=0,
                message=f"单次提交文件过多: {len(submission.files)}",
                suggestion="将大提交拆分为多个小提交",
            ))

        # 检查空提交
        if len(submission.files) == 0:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.ERROR,
                file_path="",
                line_number=0,
                message="提交不包含任何文件",
                suggestion="至少包含一个文件",
            ))

        logger.debug(f"CodeReviewer: logic check found {len(findings)} findings")
        return findings

    def _check_security(self, submission: CodeSubmission) -> List[ReviewFinding]:
        """检查代码安全"""
        logger.debug(f"CodeReviewer: checking security for submission={submission.submission_id}")
        findings = []

        for file_path in submission.files:
            for pattern in self.security_patterns:
                # 模拟安全检查：基于文件路径中的关键词
                if pattern.rstrip("(").lower() in file_path.lower():
                    findings.append(ReviewFinding(
                        severity=ReviewSeverity.CRITICAL,
                        file_path=file_path,
                        line_number=1,
                        message=f"检测到潜在安全风险: {pattern.rstrip('(')}",
                        suggestion=f"避免使用 {pattern.rstrip('(')}，寻找安全替代方案",
                    ))

        logger.debug(f"CodeReviewer: security check found {len(findings)} findings")
        return findings

    def _calculate_score(self, findings: List[ReviewFinding]) -> float:
        """计算评审得分"""
        logger.debug(f"CodeReviewer: calculating score from {len(findings)} findings")
        base_score = 100.0

        severity_weights = {
            ReviewSeverity.INFO: 1.0,
            ReviewSeverity.WARNING: 5.0,
            ReviewSeverity.ERROR: 15.0,
            ReviewSeverity.CRITICAL: 30.0,
        }

        for finding in findings:
            weight = severity_weights.get(finding.severity, 1.0)
            base_score -= weight

        score = max(0.0, base_score)
        logger.debug(f"CodeReviewer: calculated score={score}")
        return score


class ReviewPipeline:
    """评审流水线"""

    def __init__(self):
        """初始化评审流水线"""
        self.reviewer = CodeReviewer()
        self.submissions: Dict[str, CodeSubmission] = {}
        self.results: Dict[str, ReviewResult] = {}
        logger.info("ReviewPipeline initialized")

    def submit_code(self, author: str = "", files: List[str] = None,
                    description: str = "") -> CodeSubmission:
        """提交代码"""
        logger.info(f"ReviewPipeline: submitting code, author={author}, "
                    f"files={len(files) if files else 0}")
        try:
            submission = CodeSubmission(
                author=author,
                files=files or [],
                description=description,
            )
            self.submissions[submission.submission_id] = submission
            # 创建初始评审结果
            self.results[submission.submission_id] = ReviewResult(
                submission_id=submission.submission_id,
                status=ReviewStatus.PENDING,
            )
            logger.info(f"ReviewPipeline: code submitted, submission_id={submission.submission_id}")
        except Exception as e:
            logger.error(f"ReviewPipeline: submit_code failed: {e}")
            raise

        return submission

    def start_review(self, submission_id: str) -> Optional[ReviewResult]:
        """开始评审"""
        logger.info(f"ReviewPipeline: starting review for submission_id={submission_id}")
        if submission_id not in self.submissions:
            logger.warning(f"ReviewPipeline: submission_id={submission_id} not found")
            return None

        try:
            submission = self.submissions[submission_id]
            result = self.reviewer.review(submission)
            self.results[submission_id] = result
            logger.info(f"ReviewPipeline: review completed, status={result.status.value}, "
                        f"score={result.score}")
        except Exception as e:
            logger.error(f"ReviewPipeline: start_review failed: {e}")
            return None

        return result

    def get_review_result(self, submission_id: str) -> Optional[ReviewResult]:
        """获取评审结果"""
        logger.debug(f"ReviewPipeline: getting review result for submission_id={submission_id}")
        result = self.results.get(submission_id)
        if result is None:
            logger.warning(f"ReviewPipeline: no result for submission_id={submission_id}")
        return result

    def approve(self, submission_id: str, reviewer_id: str = "") -> bool:
        """批准评审"""
        logger.info(f"ReviewPipeline: approving submission_id={submission_id}, "
                    f"reviewer_id={reviewer_id}")
        if submission_id not in self.results:
            logger.warning(f"ReviewPipeline: submission_id={submission_id} not found in results")
            return False

        result = self.results[submission_id]
        if result.status not in (ReviewStatus.IN_REVIEW, ReviewStatus.NEEDS_REVISION):
            logger.warning(f"ReviewPipeline: cannot approve submission in status={result.status.value}")
            return False

        try:
            result.status = ReviewStatus.APPROVED
            if reviewer_id:
                result.reviewer_id = reviewer_id
            logger.info(f"ReviewPipeline: submission_id={submission_id} approved")
        except Exception as e:
            logger.error(f"ReviewPipeline: approve failed: {e}")
            return False

        return True

    def reject(self, submission_id: str, reviewer_id: str = "") -> bool:
        """拒绝评审"""
        logger.info(f"ReviewPipeline: rejecting submission_id={submission_id}, "
                    f"reviewer_id={reviewer_id}")
        if submission_id not in self.results:
            logger.warning(f"ReviewPipeline: submission_id={submission_id} not found in results")
            return False

        result = self.results[submission_id]
        if result.status not in (ReviewStatus.IN_REVIEW, ReviewStatus.NEEDS_REVISION):
            logger.warning(f"ReviewPipeline: cannot reject submission in status={result.status.value}")
            return False

        try:
            result.status = ReviewStatus.REJECTED
            if reviewer_id:
                result.reviewer_id = reviewer_id
            logger.info(f"ReviewPipeline: submission_id={submission_id} rejected")
        except Exception as e:
            logger.error(f"ReviewPipeline: reject failed: {e}")
            return False

        return True
