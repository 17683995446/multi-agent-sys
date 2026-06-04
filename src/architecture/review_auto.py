"""
自动生成评审报告/整改建议模块

职责：自动评审代码和架构，生成评审发现和整改建议，支持多维度评审

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReviewCategory(str, Enum):
    """评审类别"""
    ARCHITECTURE = "architecture"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"


class RecommendationPriority(str, Enum):
    """建议优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReviewFinding:
    """评审发现"""
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: ReviewCategory = ReviewCategory.CODE_QUALITY
    severity: RecommendationPriority = RecommendationPriority.MEDIUM
    description: str = ""
    location: str = ""
    recommendation: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"ReviewFinding created: finding_id={self.finding_id}, "
                     f"category={self.category.value}, severity={self.severity.value}")


class AutoReviewer:
    """自动评审器"""

    def __init__(self):
        """初始化自动评审器"""
        self._findings: List[ReviewFinding] = []
        logger.info("AutoReviewer initialized")

    def review(self, project_data: Dict[str, Any]) -> List[ReviewFinding]:
        """执行全面评审"""
        logger.info(f"AutoReviewer: reviewing project, "
                    f"keys={list(project_data.keys())}")
        try:
            self._findings = []
            self._findings.extend(self._review_architecture(project_data))
            self._findings.extend(self._review_code_quality(project_data))
            self._findings.extend(self._review_security(project_data))
            self._findings.extend(self._review_performance(project_data))
            self._findings.extend(self._review_maintainability(project_data))

            logger.info(f"AutoReviewer: review completed, "
                        f"findings={len(self._findings)}")
        except Exception as e:
            logger.error(f"AutoReviewer: review failed: {e}")
        return self._findings

    def _review_architecture(self, project_data: Dict[str, Any]) -> List[ReviewFinding]:
        """评审架构"""
        logger.debug("AutoReviewer: reviewing architecture")
        findings: List[ReviewFinding] = []
        try:
            coupling = project_data.get("coupling_score", 0)
            if coupling > 15:
                findings.append(ReviewFinding(
                    category=ReviewCategory.ARCHITECTURE,
                    severity=RecommendationPriority.CRITICAL,
                    description=f"系统耦合度过高: {coupling}",
                    location="全局",
                    recommendation="引入接口抽象层，降低模块间直接依赖",
                ))
            elif coupling > 8:
                findings.append(ReviewFinding(
                    category=ReviewCategory.ARCHITECTURE,
                    severity=RecommendationPriority.HIGH,
                    description=f"系统耦合度偏高: {coupling}",
                    location="全局",
                    recommendation="考虑使用依赖注入或事件驱动架构",
                ))

            layer_count = project_data.get("layer_count", 0)
            if layer_count > 6:
                findings.append(ReviewFinding(
                    category=ReviewCategory.ARCHITECTURE,
                    severity=RecommendationPriority.MEDIUM,
                    description=f"架构层次过多: {layer_count}层",
                    location="全局",
                    recommendation="简化架构层次，合并职责相近的层",
                ))

            circular_deps = project_data.get("circular_dependencies", 0)
            if circular_deps > 0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.ARCHITECTURE,
                    severity=RecommendationPriority.HIGH,
                    description=f"存在循环依赖: {circular_deps}处",
                    location="全局",
                    recommendation="引入中介者模式或事件总线消除循环依赖",
                ))
        except Exception as e:
            logger.error(f"AutoReviewer: _review_architecture failed: {e}")
        return findings

    def _review_code_quality(self, project_data: Dict[str, Any]) -> List[ReviewFinding]:
        """评审代码质量"""
        logger.debug("AutoReviewer: reviewing code quality")
        findings: List[ReviewFinding] = []
        try:
            complexity = project_data.get("avg_complexity", 0)
            if complexity > 25:
                findings.append(ReviewFinding(
                    category=ReviewCategory.CODE_QUALITY,
                    severity=RecommendationPriority.CRITICAL,
                    description=f"平均圈复杂度过高: {complexity}",
                    location="全局",
                    recommendation="重构高复杂度函数，拆分为更小的函数",
                ))
            elif complexity > 15:
                findings.append(ReviewFinding(
                    category=ReviewCategory.CODE_QUALITY,
                    severity=RecommendationPriority.HIGH,
                    description=f"平均圈复杂度偏高: {complexity}",
                    location="全局",
                    recommendation="简化条件逻辑，提取方法降低复杂度",
                ))

            duplication = project_data.get("duplication_rate", 0.0)
            if duplication > 20.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.CODE_QUALITY,
                    severity=RecommendationPriority.HIGH,
                    description=f"代码重复率过高: {duplication:.1f}%",
                    location="全局",
                    recommendation="提取公共方法或基类，消除重复代码",
                ))
            elif duplication > 10.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.CODE_QUALITY,
                    severity=RecommendationPriority.MEDIUM,
                    description=f"代码重复率偏高: {duplication:.1f}%",
                    location="全局",
                    recommendation="关注重复代码，考虑提取公共逻辑",
                ))

            naming_score = project_data.get("naming_score", 80.0)
            if naming_score < 50.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.CODE_QUALITY,
                    severity=RecommendationPriority.MEDIUM,
                    description=f"命名规范评分低: {naming_score:.1f}",
                    location="全局",
                    recommendation="遵循命名规范，使用有意义的变量和方法名",
                ))
        except Exception as e:
            logger.error(f"AutoReviewer: _review_code_quality failed: {e}")
        return findings

    def _review_security(self, project_data: Dict[str, Any]) -> List[ReviewFinding]:
        """评审安全性"""
        logger.debug("AutoReviewer: reviewing security")
        findings: List[ReviewFinding] = []
        try:
            vuln_count = project_data.get("vulnerability_count", 0)
            if vuln_count > 10:
                findings.append(ReviewFinding(
                    category=ReviewCategory.SECURITY,
                    severity=RecommendationPriority.CRITICAL,
                    description=f"安全漏洞数量严重: {vuln_count}个",
                    location="全局",
                    recommendation="立即修复所有高危漏洞，建立安全扫描流程",
                ))
            elif vuln_count > 5:
                findings.append(ReviewFinding(
                    category=ReviewCategory.SECURITY,
                    severity=RecommendationPriority.HIGH,
                    description=f"安全漏洞数量偏多: {vuln_count}个",
                    location="全局",
                    recommendation="优先修复高危漏洞，加强安全编码培训",
                ))
            elif vuln_count > 0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.SECURITY,
                    severity=RecommendationPriority.MEDIUM,
                    description=f"存在安全漏洞: {vuln_count}个",
                    location="全局",
                    recommendation="及时修复已知漏洞，定期进行安全扫描",
                ))

            auth_coverage = project_data.get("auth_coverage", 100.0)
            if auth_coverage < 60.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.SECURITY,
                    severity=RecommendationPriority.CRITICAL,
                    description=f"认证覆盖率极低: {auth_coverage:.1f}%",
                    location="全局",
                    recommendation="加强接口认证，确保所有敏感操作都有权限控制",
                ))
            elif auth_coverage < 80.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.SECURITY,
                    severity=RecommendationPriority.HIGH,
                    description=f"认证覆盖率不足: {auth_coverage:.1f}%",
                    location="全局",
                    recommendation="完善认证机制，覆盖所有对外接口",
                ))

            has_sql_injection = project_data.get("sql_injection_risk", False)
            if has_sql_injection:
                findings.append(ReviewFinding(
                    category=ReviewCategory.SECURITY,
                    severity=RecommendationPriority.CRITICAL,
                    description="存在SQL注入风险",
                    location="数据库访问层",
                    recommendation="使用参数化查询，禁止拼接SQL语句",
                ))
        except Exception as e:
            logger.error(f"AutoReviewer: _review_security failed: {e}")
        return findings

    def _review_performance(self, project_data: Dict[str, Any]) -> List[ReviewFinding]:
        """评审性能"""
        logger.debug("AutoReviewer: reviewing performance")
        findings: List[ReviewFinding] = []
        try:
            avg_response = project_data.get("avg_response_time", 200)
            if avg_response > 2000:
                findings.append(ReviewFinding(
                    category=ReviewCategory.PERFORMANCE,
                    severity=RecommendationPriority.CRITICAL,
                    description=f"平均响应时间过长: {avg_response}ms",
                    location="全局",
                    recommendation="优化关键路径，引入缓存和异步处理",
                ))
            elif avg_response > 1000:
                findings.append(ReviewFinding(
                    category=ReviewCategory.PERFORMANCE,
                    severity=RecommendationPriority.HIGH,
                    description=f"平均响应时间偏长: {avg_response}ms",
                    location="全局",
                    recommendation="分析性能瓶颈，优化数据库查询和算法",
                ))

            memory_usage = project_data.get("memory_usage", 50.0)
            if memory_usage > 85.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.PERFORMANCE,
                    severity=RecommendationPriority.HIGH,
                    description=f"内存使用率过高: {memory_usage:.1f}%",
                    location="全局",
                    recommendation="排查内存泄漏，优化数据结构和缓存策略",
                ))
            elif memory_usage > 70.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.PERFORMANCE,
                    severity=RecommendationPriority.MEDIUM,
                    description=f"内存使用率偏高: {memory_usage:.1f}%",
                    location="全局",
                    recommendation="关注内存使用趋势，优化资源管理",
                ))

            n_plus_one = project_data.get("n_plus_one_queries", 0)
            if n_plus_one > 0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.PERFORMANCE,
                    severity=RecommendationPriority.HIGH,
                    description=f"存在N+1查询问题: {n_plus_one}处",
                    location="数据访问层",
                    recommendation="使用预加载或批量查询替代循环查询",
                ))
        except Exception as e:
            logger.error(f"AutoReviewer: _review_performance failed: {e}")
        return findings

    def _review_maintainability(self, project_data: Dict[str, Any]) -> List[ReviewFinding]:
        """评审可维护性"""
        logger.debug("AutoReviewer: reviewing maintainability")
        findings: List[ReviewFinding] = []
        try:
            doc_coverage = project_data.get("doc_coverage", 50.0)
            if doc_coverage < 20.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.MAINTAINABILITY,
                    severity=RecommendationPriority.HIGH,
                    description=f"文档覆盖率极低: {doc_coverage:.1f}%",
                    location="全局",
                    recommendation="为核心模块补充文档，建立文档规范",
                ))
            elif doc_coverage < 50.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.MAINTAINABILITY,
                    severity=RecommendationPriority.MEDIUM,
                    description=f"文档覆盖率偏低: {doc_coverage:.1f}%",
                    location="全局",
                    recommendation="增加文档覆盖，特别是公共接口和复杂逻辑",
                ))

            test_coverage = project_data.get("test_coverage", 0.0)
            if test_coverage < 30.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.MAINTAINABILITY,
                    severity=RecommendationPriority.CRITICAL,
                    description=f"测试覆盖率极低: {test_coverage:.1f}%",
                    location="全局",
                    recommendation="为核心逻辑编写单元测试，建立测试规范",
                ))
            elif test_coverage < 60.0:
                findings.append(ReviewFinding(
                    category=ReviewCategory.MAINTAINABILITY,
                    severity=RecommendationPriority.HIGH,
                    description=f"测试覆盖率不足: {test_coverage:.1f}%",
                    location="全局",
                    recommendation="提升测试覆盖率，重点关注边界条件",
                ))

            todo_count = project_data.get("todo_count", 0)
            if todo_count > 20:
                findings.append(ReviewFinding(
                    category=ReviewCategory.MAINTAINABILITY,
                    severity=RecommendationPriority.MEDIUM,
                    description=f"TODO/FIXME数量过多: {todo_count}个",
                    location="全局",
                    recommendation="清理技术债务，处理遗留的TODO和FIXME",
                ))
        except Exception as e:
            logger.error(f"AutoReviewer: _review_maintainability failed: {e}")
        return findings

    def generate_report(self) -> Dict[str, Any]:
        """生成评审报告"""
        logger.info("AutoReviewer: generating report")
        try:
            by_category: Dict[str, int] = {}
            by_severity: Dict[str, int] = {}
            for finding in self._findings:
                by_category[finding.category.value] = by_category.get(finding.category.value, 0) + 1
                by_severity[finding.severity.value] = by_severity.get(finding.severity.value, 0) + 1

            critical_count = by_severity.get(RecommendationPriority.CRITICAL.value, 0)
            overall_severity = RecommendationPriority.LOW
            if critical_count > 0:
                overall_severity = RecommendationPriority.CRITICAL
            elif by_severity.get(RecommendationPriority.HIGH.value, 0) > 2:
                overall_severity = RecommendationPriority.HIGH
            elif by_severity.get(RecommendationPriority.HIGH.value, 0) > 0 or sum(by_severity.values()) > 5:
                overall_severity = RecommendationPriority.MEDIUM

            report: Dict[str, Any] = {
                "overall_severity": overall_severity.value,
                "total_findings": len(self._findings),
                "by_category": by_category,
                "by_severity": by_severity,
                "findings": [
                    {
                        "finding_id": f.finding_id,
                        "category": f.category.value,
                        "severity": f.severity.value,
                        "description": f.description,
                        "location": f.location,
                        "recommendation": f.recommendation,
                    }
                    for f in self._findings
                ],
            }
            logger.info(f"AutoReviewer: report generated, "
                        f"total_findings={len(self._findings)}")
        except Exception as e:
            logger.error(f"AutoReviewer: generate_report failed: {e}")
            report = {"error": str(e)}
        return report

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """生成整改建议"""
        logger.info("AutoReviewer: generating recommendations")
        try:
            sorted_findings = sorted(
                self._findings,
                key=lambda f: {
                    RecommendationPriority.CRITICAL.value: 0,
                    RecommendationPriority.HIGH.value: 1,
                    RecommendationPriority.MEDIUM.value: 2,
                    RecommendationPriority.LOW.value: 3,
                }.get(f.severity.value, 4),
            )
            recommendations = [
                {
                    "finding_id": f.finding_id,
                    "category": f.category.value,
                    "severity": f.severity.value,
                    "recommendation": f.recommendation,
                    "description": f.description,
                }
                for f in sorted_findings
            ]
            logger.info(f"AutoReviewer: generated {len(recommendations)} recommendations")
        except Exception as e:
            logger.error(f"AutoReviewer: generate_recommendations failed: {e}")
            recommendations = []
        return recommendations


class AutoReviewService:
    """自动评审服务"""

    def __init__(self, reviewer: Optional[AutoReviewer] = None):
        """初始化自动评审服务"""
        self.reviewer = reviewer or AutoReviewer()
        logger.info("AutoReviewService initialized")

    def review(self, project_data: Dict[str, Any]) -> List[ReviewFinding]:
        """执行评审"""
        logger.info("AutoReviewService: reviewing project")
        return self.reviewer.review(project_data)

    def get_report(self) -> Dict[str, Any]:
        """获取评审报告"""
        logger.debug("AutoReviewService: getting report")
        return self.reviewer.generate_report()

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取整改建议"""
        logger.debug("AutoReviewService: getting recommendations")
        return self.reviewer.generate_recommendations()
