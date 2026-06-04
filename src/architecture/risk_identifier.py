"""
自动识别高风险/烂代码模块

职责：识别项目中的高风险模块和烂代码区域，支持多维度风险检测，生成风险报告

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RiskCategory(str, Enum):
    """风险类别"""
    HIGH_COMPLEXITY = "high_complexity"
    LOW_COVERAGE = "low_coverage"
    FREQUENT_CHANGES = "frequent_changes"
    MANY_BUGS = "many_bugs"
    TIGHT_COUPLING = "tight_coupling"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskIndicator:
    """风险指标"""
    indicator_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: RiskCategory = RiskCategory.HIGH_COMPLEXITY
    level: RiskLevel = RiskLevel.MEDIUM
    module_path: str = ""
    description: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"RiskIndicator created: indicator_id={self.indicator_id}, "
                     f"category={self.category.value}, level={self.level.value}")


class RiskIdentifier:
    """风险识别器"""

    def __init__(self):
        """初始化风险识别器"""
        self._indicators: List[RiskIndicator] = []
        logger.info("RiskIdentifier initialized")

    def identify(self, project_data: Dict[str, Any]) -> List[RiskIndicator]:
        """识别项目中的风险"""
        logger.info(f"RiskIdentifier: identifying risks, "
                    f"keys={list(project_data.keys())}")
        try:
            self._indicators = []
            self._indicators.extend(self._check_complexity(project_data))
            self._indicators.extend(self._check_coverage(project_data))
            self._indicators.extend(self._check_change_frequency(project_data))
            self._indicators.extend(self._check_coupling(project_data))
            self._indicators.extend(self._check_bugs(project_data))

            logger.info(f"RiskIdentifier: identified {len(self._indicators)} risk indicators")
        except Exception as e:
            logger.error(f"RiskIdentifier: identify failed: {e}")
        return self._indicators

    def _check_complexity(self, project_data: Dict[str, Any]) -> List[RiskIndicator]:
        """检查代码复杂度"""
        logger.debug("RiskIdentifier: checking complexity")
        indicators: List[RiskIndicator] = []
        try:
            modules = project_data.get("modules", {})
            for module_path, module_info in modules.items():
                if isinstance(module_info, dict):
                    complexity = module_info.get("cyclomatic_complexity", 0)
                    if complexity > 30:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.HIGH_COMPLEXITY,
                            level=RiskLevel.CRITICAL,
                            module_path=module_path,
                            description=f"模块圈复杂度过高: {complexity}",
                            metrics={"cyclomatic_complexity": complexity},
                        ))
                    elif complexity > 20:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.HIGH_COMPLEXITY,
                            level=RiskLevel.HIGH,
                            module_path=module_path,
                            description=f"模块圈复杂度偏高: {complexity}",
                            metrics={"cyclomatic_complexity": complexity},
                        ))
                    elif complexity > 10:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.HIGH_COMPLEXITY,
                            level=RiskLevel.MEDIUM,
                            module_path=module_path,
                            description=f"模块圈复杂度略高: {complexity}",
                            metrics={"cyclomatic_complexity": complexity},
                        ))
        except Exception as e:
            logger.error(f"RiskIdentifier: _check_complexity failed: {e}")
        return indicators

    def _check_coverage(self, project_data: Dict[str, Any]) -> List[RiskIndicator]:
        """检查测试覆盖率"""
        logger.debug("RiskIdentifier: checking coverage")
        indicators: List[RiskIndicator] = []
        try:
            modules = project_data.get("modules", {})
            for module_path, module_info in modules.items():
                if isinstance(module_info, dict):
                    coverage = module_info.get("test_coverage", 100.0)
                    if coverage < 30.0:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.LOW_COVERAGE,
                            level=RiskLevel.CRITICAL,
                            module_path=module_path,
                            description=f"测试覆盖率极低: {coverage:.1f}%",
                            metrics={"test_coverage": coverage},
                        ))
                    elif coverage < 50.0:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.LOW_COVERAGE,
                            level=RiskLevel.HIGH,
                            module_path=module_path,
                            description=f"测试覆盖率偏低: {coverage:.1f}%",
                            metrics={"test_coverage": coverage},
                        ))
                    elif coverage < 70.0:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.LOW_COVERAGE,
                            level=RiskLevel.MEDIUM,
                            module_path=module_path,
                            description=f"测试覆盖率不足: {coverage:.1f}%",
                            metrics={"test_coverage": coverage},
                        ))
        except Exception as e:
            logger.error(f"RiskIdentifier: _check_coverage failed: {e}")
        return indicators

    def _check_change_frequency(self, project_data: Dict[str, Any]) -> List[RiskIndicator]:
        """检查变更频率"""
        logger.debug("RiskIdentifier: checking change frequency")
        indicators: List[RiskIndicator] = []
        try:
            modules = project_data.get("modules", {})
            for module_path, module_info in modules.items():
                if isinstance(module_info, dict):
                    changes = module_info.get("change_count", 0)
                    if changes > 50:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.FREQUENT_CHANGES,
                            level=RiskLevel.CRITICAL,
                            module_path=module_path,
                            description=f"变更频率极高: {changes}次",
                            metrics={"change_count": changes},
                        ))
                    elif changes > 30:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.FREQUENT_CHANGES,
                            level=RiskLevel.HIGH,
                            module_path=module_path,
                            description=f"变更频率偏高: {changes}次",
                            metrics={"change_count": changes},
                        ))
                    elif changes > 15:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.FREQUENT_CHANGES,
                            level=RiskLevel.MEDIUM,
                            module_path=module_path,
                            description=f"变更频率略高: {changes}次",
                            metrics={"change_count": changes},
                        ))
        except Exception as e:
            logger.error(f"RiskIdentifier: _check_change_frequency failed: {e}")
        return indicators

    def _check_coupling(self, project_data: Dict[str, Any]) -> List[RiskIndicator]:
        """检查耦合度"""
        logger.debug("RiskIdentifier: checking coupling")
        indicators: List[RiskIndicator] = []
        try:
            modules = project_data.get("modules", {})
            for module_path, module_info in modules.items():
                if isinstance(module_info, dict):
                    coupling = module_info.get("coupling_score", 0)
                    if coupling > 20:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.TIGHT_COUPLING,
                            level=RiskLevel.CRITICAL,
                            module_path=module_path,
                            description=f"耦合度极高: {coupling}",
                            metrics={"coupling_score": coupling},
                        ))
                    elif coupling > 12:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.TIGHT_COUPLING,
                            level=RiskLevel.HIGH,
                            module_path=module_path,
                            description=f"耦合度偏高: {coupling}",
                            metrics={"coupling_score": coupling},
                        ))
                    elif coupling > 6:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.TIGHT_COUPLING,
                            level=RiskLevel.MEDIUM,
                            module_path=module_path,
                            description=f"耦合度略高: {coupling}",
                            metrics={"coupling_score": coupling},
                        ))
        except Exception as e:
            logger.error(f"RiskIdentifier: _check_coupling failed: {e}")
        return indicators

    def _check_bugs(self, project_data: Dict[str, Any]) -> List[RiskIndicator]:
        """检查Bug数量"""
        logger.debug("RiskIdentifier: checking bugs")
        indicators: List[RiskIndicator] = []
        try:
            modules = project_data.get("modules", {})
            for module_path, module_info in modules.items():
                if isinstance(module_info, dict):
                    bug_count = module_info.get("bug_count", 0)
                    if bug_count > 15:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.MANY_BUGS,
                            level=RiskLevel.CRITICAL,
                            module_path=module_path,
                            description=f"Bug数量极多: {bug_count}个",
                            metrics={"bug_count": bug_count},
                        ))
                    elif bug_count > 8:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.MANY_BUGS,
                            level=RiskLevel.HIGH,
                            module_path=module_path,
                            description=f"Bug数量偏多: {bug_count}个",
                            metrics={"bug_count": bug_count},
                        ))
                    elif bug_count > 3:
                        indicators.append(RiskIndicator(
                            category=RiskCategory.MANY_BUGS,
                            level=RiskLevel.MEDIUM,
                            module_path=module_path,
                            description=f"Bug数量略多: {bug_count}个",
                            metrics={"bug_count": bug_count},
                        ))
        except Exception as e:
            logger.error(f"RiskIdentifier: _check_bugs failed: {e}")
        return indicators

    def generate_risk_report(self) -> Dict[str, Any]:
        """生成风险报告"""
        logger.info("RiskIdentifier: generating risk report")
        try:
            by_category: Dict[str, int] = {}
            by_level: Dict[str, int] = {}
            for indicator in self._indicators:
                by_category[indicator.category.value] = by_category.get(indicator.category.value, 0) + 1
                by_level[indicator.level.value] = by_level.get(indicator.level.value, 0) + 1

            critical_count = by_level.get(RiskLevel.CRITICAL.value, 0)
            high_count = by_level.get(RiskLevel.HIGH.value, 0)

            overall_level = RiskLevel.LOW
            if critical_count > 0:
                overall_level = RiskLevel.CRITICAL
            elif high_count > 2:
                overall_level = RiskLevel.HIGH
            elif high_count > 0 or sum(by_level.values()) > 5:
                overall_level = RiskLevel.MEDIUM

            report: Dict[str, Any] = {
                "overall_level": overall_level.value,
                "total_indicators": len(self._indicators),
                "by_category": by_category,
                "by_level": by_level,
                "indicators": [
                    {
                        "indicator_id": ind.indicator_id,
                        "category": ind.category.value,
                        "level": ind.level.value,
                        "module_path": ind.module_path,
                        "description": ind.description,
                        "metrics": ind.metrics,
                    }
                    for ind in self._indicators
                ],
            }
            logger.info(f"RiskIdentifier: risk report generated, "
                        f"overall_level={overall_level.value}, "
                        f"total={len(self._indicators)}")
        except Exception as e:
            logger.error(f"RiskIdentifier: generate_risk_report failed: {e}")
            report = {"error": str(e)}
        return report


class RiskIdentifyService:
    """风险识别服务"""

    def __init__(self, identifier: Optional[RiskIdentifier] = None):
        """初始化风险识别服务"""
        self.identifier = identifier or RiskIdentifier()
        logger.info("RiskIdentifyService initialized")

    def identify(self, project_data: Dict[str, Any]) -> List[RiskIndicator]:
        """执行风险识别"""
        logger.info("RiskIdentifyService: identifying risks")
        return self.identifier.identify(project_data)

    def get_risks(self, level: Optional[RiskLevel] = None) -> List[RiskIndicator]:
        """获取风险列表"""
        logger.debug(f"RiskIdentifyService: getting risks, level={level}")
        if level is None:
            return self.identifier._indicators
        return [ind for ind in self.identifier._indicators if ind.level == level]

    def get_report(self) -> Dict[str, Any]:
        """获取风险报告"""
        logger.debug("RiskIdentifyService: getting report")
        return self.identifier.generate_risk_report()
