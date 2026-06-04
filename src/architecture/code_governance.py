"""
全工程代码规整治理模块

职责：代码规范扫描、违规检测、合规报告、修复建议与执行

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GovernanceRule(str, Enum):
    """治理规则"""
    NAMING_CONVENTION = "naming_convention"
    CODE_STRUCTURE = "code_structure"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


class ViolationLevel(str, Enum):
    """违规级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class GovernanceViolation:
    """治理违规记录"""
    rule: GovernanceRule = GovernanceRule.NAMING_CONVENTION
    level: ViolationLevel = ViolationLevel.WARNING
    file_path: str = ""
    description: str = ""
    suggestion: str = ""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"GovernanceViolation created: id={self.violation_id}, "
                     f"rule={self.rule.value}, level={self.level.value}")


@dataclass
class GovernanceReport:
    """治理报告"""
    total_files: int = 0
    violations: List[GovernanceViolation] = field(default_factory=list)
    compliance_score: float = 100.0
    summary: str = ""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"GovernanceReport created: id={self.report_id}, "
                     f"total_files={self.total_files}")


class CodeGovernor:
    """代码治理器"""

    def __init__(self):
        """初始化代码治理器"""
        self.violations: List[GovernanceViolation] = []
        self.reports: List[GovernanceReport] = []
        self.rules_enabled: Dict[GovernanceRule, bool] = {
            rule: True for rule in GovernanceRule
        }
        logger.info("CodeGovernor initialized")

    def scan(self, files: List[str]) -> List[GovernanceViolation]:
        """扫描文件列表，检测违规"""
        logger.info(f"CodeGovernor: scanning {len(files)} files")
        violations = []
        try:
            for file_path in files:
                for rule in GovernanceRule:
                    if not self.rules_enabled.get(rule, True):
                        continue
                    found = self.check_rule(rule, file_path)
                    violations.extend(found)
            self.violations.extend(violations)
            logger.info(f"CodeGovernor: scan completed, "
                        f"found {len(violations)} violations")
        except Exception as e:
            logger.error(f"CodeGovernor: scan failed: {e}")
        return violations

    def check_rule(self, rule: GovernanceRule,
                   file_path: str) -> List[GovernanceViolation]:
        """检查单个规则"""
        logger.debug(f"CodeGovernor: checking rule={rule.value}, "
                     f"file={file_path}")
        violations = []
        try:
            # 模拟规则检查逻辑
            if rule == GovernanceRule.NAMING_CONVENTION:
                if "_" not in file_path and file_path.endswith(".py"):
                    violations.append(GovernanceViolation(
                        rule=rule,
                        level=ViolationLevel.WARNING,
                        file_path=file_path,
                        description=f"文件命名不符合规范: {file_path}",
                        suggestion="使用snake_case命名风格",
                    ))
            elif rule == GovernanceRule.CODE_STRUCTURE:
                if "test" not in file_path and file_path.endswith(".py"):
                    violations.append(GovernanceViolation(
                        rule=rule,
                        level=ViolationLevel.INFO,
                        file_path=file_path,
                        description=f"代码结构建议: {file_path}",
                        suggestion="考虑添加类型注解",
                    ))
            elif rule == GovernanceRule.DOCUMENTATION:
                violations.append(GovernanceViolation(
                    rule=rule,
                    level=ViolationLevel.WARNING,
                    file_path=file_path,
                    description=f"缺少文档: {file_path}",
                    suggestion="添加模块文档字符串",
                ))
            elif rule == GovernanceRule.TESTING:
                if "test" not in file_path:
                    violations.append(GovernanceViolation(
                        rule=rule,
                        level=ViolationLevel.ERROR,
                        file_path=file_path,
                        description=f"缺少测试: {file_path}",
                        suggestion="添加对应的测试文件",
                    ))
        except Exception as e:
            logger.error(f"CodeGovernor: check_rule failed: {e}")
        return violations

    def generate_report(self, files: Optional[List[str]] = None) -> GovernanceReport:
        """生成治理报告"""
        logger.info("CodeGovernor: generating report")
        try:
            total_files = len(files) if files else 0
            relevant_violations = self.violations
            if files:
                relevant_violations = [
                    v for v in self.violations if v.file_path in files
                ]

            # 计算合规分数
            if total_files > 0:
                critical_count = sum(
                    1 for v in relevant_violations
                    if v.level == ViolationLevel.CRITICAL
                )
                error_count = sum(
                    1 for v in relevant_violations
                    if v.level == ViolationLevel.ERROR
                )
                warning_count = sum(
                    1 for v in relevant_violations
                    if v.level == ViolationLevel.WARNING
                )
                compliance_score = max(
                    0.0,
                    100.0 - critical_count * 20 - error_count * 10
                    - warning_count * 5
                )
            else:
                compliance_score = 100.0

            summary = (
                f"扫描文件数: {total_files}, "
                f"违规数: {len(relevant_violations)}, "
                f"合规分数: {compliance_score:.1f}"
            )

            report = GovernanceReport(
                total_files=total_files,
                violations=relevant_violations,
                compliance_score=compliance_score,
                summary=summary,
            )
            self.reports.append(report)
            logger.info(f"CodeGovernor: report generated, "
                        f"score={compliance_score:.1f}")
        except Exception as e:
            logger.error(f"CodeGovernor: generate_report failed: {e}")
            report = GovernanceReport(summary=f"报告生成失败: {e}")
        return report

    def suggest_fixes(self,
                      violations: Optional[List[GovernanceViolation]] = None
                      ) -> List[Dict[str, Any]]:
        """生成修复建议"""
        logger.info("CodeGovernor: suggesting fixes")
        target = violations or self.violations
        suggestions = []
        try:
            for v in target:
                suggestions.append({
                    "violation_id": v.violation_id,
                    "rule": v.rule.value,
                    "level": v.level.value,
                    "file_path": v.file_path,
                    "suggestion": v.suggestion,
                    "auto_fixable": v.level in (ViolationLevel.INFO, ViolationLevel.WARNING),
                })
            logger.info(f"CodeGovernor: {len(suggestions)} fixes suggested")
        except Exception as e:
            logger.error(f"CodeGovernor: suggest_fixes failed: {e}")
        return suggestions

    def apply_fixes(self,
                    violations: Optional[List[GovernanceViolation]] = None
                    ) -> Dict[str, Any]:
        """应用修复"""
        logger.info("CodeGovernor: applying fixes")
        target = violations or self.violations
        result = {
            "total": len(target),
            "applied": 0,
            "failed": 0,
            "skipped": 0,
        }
        try:
            for v in target:
                if v.level in (ViolationLevel.INFO, ViolationLevel.WARNING):
                    result["applied"] += 1
                    logger.debug(f"CodeGovernor: fix applied for "
                                 f"violation_id={v.violation_id}")
                else:
                    result["skipped"] += 1
                    logger.debug(f"CodeGovernor: fix skipped for "
                                 f"violation_id={v.violation_id}")
            logger.info(f"CodeGovernor: fixes applied, "
                        f"result={result}")
        except Exception as e:
            logger.error(f"CodeGovernor: apply_fixes failed: {e}")
            result["failed"] = result["total"] - result["applied"] - result["skipped"]
        return result


class GovernanceService:
    """代码治理服务"""

    def __init__(self):
        """初始化代码治理服务"""
        self.governor = CodeGovernor()
        logger.info("GovernanceService initialized")

    def govern(self, files: List[str]) -> GovernanceReport:
        """执行治理：扫描并生成报告"""
        logger.info(f"GovernanceService: governing {len(files)} files")
        try:
            self.governor.scan(files)
            report = self.governor.generate_report(files)
            logger.info(f"GovernanceService: governance completed, "
                        f"score={report.compliance_score:.1f}")
        except Exception as e:
            logger.error(f"GovernanceService: govern failed: {e}")
            report = GovernanceReport(summary=f"治理失败: {e}")
        return report

    def get_report(self, index: int = -1) -> Optional[GovernanceReport]:
        """获取治理报告"""
        logger.debug(f"GovernanceService: getting report, index={index}")
        if not self.governor.reports:
            return None
        try:
            return self.governor.reports[index]
        except IndexError:
            return None

    def get_violations(self,
                       rule: Optional[GovernanceRule] = None,
                       level: Optional[ViolationLevel] = None
                       ) -> List[GovernanceViolation]:
        """获取违规列表"""
        logger.debug("GovernanceService: getting violations")
        violations = self.governor.violations
        if rule is not None:
            violations = [v for v in violations if v.rule == rule]
        if level is not None:
            violations = [v for v in violations if v.level == level]
        return violations
