"""
工程质量风控体系模块

职责：评估工程质量多维度指标（可靠性、可维护性、效率、安全性、可用性），识别风险区域，生成质量评估报告

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class QualityDimension(str, Enum):
    """质量维度"""
    RELIABILITY = "reliability"
    MAINTAINABILITY = "maintainability"
    EFFICIENCY = "efficiency"
    SECURITY = "security"
    USABILITY = "usability"


class QualityLevel(str, Enum):
    """质量等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityMetric:
    """质量指标"""
    dimension: QualityDimension = QualityDimension.RELIABILITY
    level: QualityLevel = QualityLevel.GOOD
    score: float = 80.0
    description: str = ""
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"QualityMetric created: dimension={self.dimension.value}, "
                     f"level={self.level.value}, score={self.score}")


@dataclass
class QualityAssessment:
    """质量评估"""
    overall_score: float = 80.0
    metrics: List[QualityMetric] = field(default_factory=list)
    risk_areas: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"QualityAssessment created: overall_score={self.overall_score}, "
                     f"metrics={len(self.metrics)}, risk_areas={len(self.risk_areas)}")


class QualityController:
    """质量控制器"""

    def __init__(self):
        """初始化质量控制器"""
        self._assessments: List[QualityAssessment] = []
        logger.info("QualityController initialized")

    def assess(self, project_data: Dict[str, Any]) -> QualityAssessment:
        """评估项目质量"""
        logger.info(f"QualityController: assessing project, "
                     f"keys={list(project_data.keys())}")
        try:
            metrics: List[QualityMetric] = []
            metrics.append(self._assess_reliability(project_data))
            metrics.append(self._assess_maintainability(project_data))
            metrics.append(self._assess_efficiency(project_data))
            metrics.append(self._assess_security(project_data))

            overall_score = sum(m.score for m in metrics) / len(metrics) if metrics else 0.0
            risk_areas = self.get_risk_areas(metrics)

            assessment = QualityAssessment(
                overall_score=round(overall_score, 2),
                metrics=metrics,
                risk_areas=risk_areas,
            )
            self._assessments.append(assessment)
            logger.info(f"QualityController: assessment completed, "
                        f"overall_score={overall_score:.2f}")
        except Exception as e:
            logger.error(f"QualityController: assess failed: {e}")
            assessment = QualityAssessment(overall_score=0.0)
        return assessment

    def _assess_reliability(self, project_data: Dict[str, Any]) -> QualityMetric:
        """评估可靠性"""
        logger.debug("QualityController: assessing reliability")
        try:
            score = 80.0
            recommendations: List[str] = []
            bug_count = project_data.get("bug_count", 0)
            crash_rate = project_data.get("crash_rate", 0.0)
            test_pass_rate = project_data.get("test_pass_rate", 100.0)

            if bug_count > 20:
                score -= 20
                recommendations.append("Bug数量过多，建议加强代码审查")
            elif bug_count > 10:
                score -= 10
                recommendations.append("Bug数量偏多，建议增加测试覆盖")

            if crash_rate > 5.0:
                score -= 20
                recommendations.append("崩溃率过高，建议排查稳定性问题")
            elif crash_rate > 1.0:
                score -= 10
                recommendations.append("崩溃率偏高，建议关注异常处理")

            if test_pass_rate < 80.0:
                score -= 15
                recommendations.append("测试通过率过低，建议修复失败用例")

            score = max(0.0, min(100.0, score))
            level = self._score_to_level(score)

            return QualityMetric(
                dimension=QualityDimension.RELIABILITY,
                level=level,
                score=score,
                description=f"可靠性评分: {score:.1f}",
                recommendations=recommendations,
            )
        except Exception as e:
            logger.error(f"QualityController: _assess_reliability failed: {e}")
            return QualityMetric(
                dimension=QualityDimension.RELIABILITY,
                level=QualityLevel.POOR,
                score=0.0,
                description=f"评估失败: {e}",
            )

    def _assess_maintainability(self, project_data: Dict[str, Any]) -> QualityMetric:
        """评估可维护性"""
        logger.debug("QualityController: assessing maintainability")
        try:
            score = 80.0
            recommendations: List[str] = []
            code_complexity = project_data.get("code_complexity", 10)
            doc_coverage = project_data.get("doc_coverage", 50.0)
            duplication_rate = project_data.get("duplication_rate", 5.0)

            if code_complexity > 30:
                score -= 20
                recommendations.append("代码复杂度过高，建议进行重构")
            elif code_complexity > 20:
                score -= 10
                recommendations.append("代码复杂度偏高，建议简化逻辑")

            if doc_coverage < 30.0:
                score -= 15
                recommendations.append("文档覆盖率过低，建议补充文档")
            elif doc_coverage < 60.0:
                score -= 5
                recommendations.append("文档覆盖率偏低，建议增加文档")

            if duplication_rate > 15.0:
                score -= 15
                recommendations.append("代码重复率过高，建议提取公共方法")
            elif duplication_rate > 10.0:
                score -= 5
                recommendations.append("代码重复率偏高，建议关注代码复用")

            score = max(0.0, min(100.0, score))
            level = self._score_to_level(score)

            return QualityMetric(
                dimension=QualityDimension.MAINTAINABILITY,
                level=level,
                score=score,
                description=f"可维护性评分: {score:.1f}",
                recommendations=recommendations,
            )
        except Exception as e:
            logger.error(f"QualityController: _assess_maintainability failed: {e}")
            return QualityMetric(
                dimension=QualityDimension.MAINTAINABILITY,
                level=QualityLevel.POOR,
                score=0.0,
                description=f"评估失败: {e}",
            )

    def _assess_efficiency(self, project_data: Dict[str, Any]) -> QualityMetric:
        """评估效率"""
        logger.debug("QualityController: assessing efficiency")
        try:
            score = 80.0
            recommendations: List[str] = []
            avg_response_time = project_data.get("avg_response_time", 200)
            memory_usage = project_data.get("memory_usage", 50.0)
            cpu_usage = project_data.get("cpu_usage", 40.0)

            if avg_response_time > 2000:
                score -= 25
                recommendations.append("平均响应时间过长，建议优化关键路径")
            elif avg_response_time > 1000:
                score -= 15
                recommendations.append("平均响应时间偏长，建议关注性能瓶颈")

            if memory_usage > 80.0:
                score -= 15
                recommendations.append("内存使用率过高，建议排查内存泄漏")
            elif memory_usage > 60.0:
                score -= 5
                recommendations.append("内存使用率偏高，建议优化资源使用")

            if cpu_usage > 80.0:
                score -= 15
                recommendations.append("CPU使用率过高，建议优化计算逻辑")
            elif cpu_usage > 60.0:
                score -= 5
                recommendations.append("CPU使用率偏高，建议关注计算密集型任务")

            score = max(0.0, min(100.0, score))
            level = self._score_to_level(score)

            return QualityMetric(
                dimension=QualityDimension.EFFICIENCY,
                level=level,
                score=score,
                description=f"效率评分: {score:.1f}",
                recommendations=recommendations,
            )
        except Exception as e:
            logger.error(f"QualityController: _assess_efficiency failed: {e}")
            return QualityMetric(
                dimension=QualityDimension.EFFICIENCY,
                level=QualityLevel.POOR,
                score=0.0,
                description=f"评估失败: {e}",
            )

    def _assess_security(self, project_data: Dict[str, Any]) -> QualityMetric:
        """评估安全性"""
        logger.debug("QualityController: assessing security")
        try:
            score = 80.0
            recommendations: List[str] = []
            vuln_count = project_data.get("vulnerability_count", 0)
            auth_coverage = project_data.get("auth_coverage", 80.0)
            data_encryption = project_data.get("data_encryption", True)

            if vuln_count > 10:
                score -= 30
                recommendations.append("安全漏洞数量严重，建议立即修复")
            elif vuln_count > 5:
                score -= 20
                recommendations.append("安全漏洞数量偏多，建议优先修复高危漏洞")
            elif vuln_count > 0:
                score -= 10
                recommendations.append("存在安全漏洞，建议及时修复")

            if auth_coverage < 60.0:
                score -= 20
                recommendations.append("认证覆盖率过低，建议加强权限控制")
            elif auth_coverage < 80.0:
                score -= 10
                recommendations.append("认证覆盖率偏低，建议完善认证机制")

            if not data_encryption:
                score -= 15
                recommendations.append("敏感数据未加密，建议启用数据加密")

            score = max(0.0, min(100.0, score))
            level = self._score_to_level(score)

            return QualityMetric(
                dimension=QualityDimension.SECURITY,
                level=level,
                score=score,
                description=f"安全性评分: {score:.1f}",
                recommendations=recommendations,
            )
        except Exception as e:
            logger.error(f"QualityController: _assess_security failed: {e}")
            return QualityMetric(
                dimension=QualityDimension.SECURITY,
                level=QualityLevel.POOR,
                score=0.0,
                description=f"评估失败: {e}",
            )

    def _score_to_level(self, score: float) -> QualityLevel:
        """将分数转换为质量等级"""
        if score >= 90.0:
            return QualityLevel.EXCELLENT
        elif score >= 75.0:
            return QualityLevel.GOOD
        elif score >= 60.0:
            return QualityLevel.ACCEPTABLE
        elif score >= 40.0:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def generate_report(self) -> Dict[str, Any]:
        """生成质量评估报告"""
        logger.info("QualityController: generating report")
        try:
            if not self._assessments:
                return {"message": "暂无评估数据"}

            latest = self._assessments[-1]
            report: Dict[str, Any] = {
                "overall_score": latest.overall_score,
                "risk_areas": latest.risk_areas,
                "metrics": [
                    {
                        "dimension": m.dimension.value,
                        "level": m.level.value,
                        "score": m.score,
                        "description": m.description,
                        "recommendations": m.recommendations,
                    }
                    for m in latest.metrics
                ],
                "assessment_count": len(self._assessments),
            }
            logger.info(f"QualityController: report generated, "
                        f"overall_score={latest.overall_score}")
        except Exception as e:
            logger.error(f"QualityController: generate_report failed: {e}")
            report = {"error": str(e)}
        return report

    def get_risk_areas(self, metrics: Optional[List[QualityMetric]] = None) -> List[str]:
        """获取风险区域"""
        logger.debug("QualityController: getting risk areas")
        try:
            target = metrics or (self._assessments[-1].metrics if self._assessments else [])
            risk_areas: List[str] = []
            for m in target:
                if m.score < 60.0:
                    risk_areas.append(f"{m.dimension.value}: {m.description}")
            return risk_areas
        except Exception as e:
            logger.error(f"QualityController: get_risk_areas failed: {e}")
            return []


class QualityControlService:
    """质量风控服务"""

    def __init__(self, controller: Optional[QualityController] = None):
        """初始化质量风控服务"""
        self.controller = controller or QualityController()
        logger.info("QualityControlService initialized")

    def assess(self, project_data: Dict[str, Any]) -> QualityAssessment:
        """执行质量评估"""
        logger.info("QualityControlService: assessing project")
        return self.controller.assess(project_data)

    def get_assessment(self, index: int = -1) -> Optional[QualityAssessment]:
        """获取质量评估"""
        logger.debug(f"QualityControlService: getting assessment, index={index}")
        if not self.controller._assessments:
            return None
        try:
            return self.controller._assessments[index]
        except IndexError:
            return None

    def get_report(self) -> Dict[str, Any]:
        """获取质量评估报告"""
        logger.debug("QualityControlService: getting report")
        return self.controller.generate_report()

    def get_risk_areas(self) -> List[str]:
        """获取风险区域"""
        logger.debug("QualityControlService: getting risk areas")
        return self.controller.get_risk_areas()
