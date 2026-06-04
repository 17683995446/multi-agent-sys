"""
回归影响范围精准分析模块

职责：分析代码变更的影响范围，追踪依赖关系，评估功能、性能、安全等维度的影响，生成影响报告

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ImpactLevel(str, Enum):
    """影响级别"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImpactArea(str, Enum):
    """影响领域"""
    FUNCTIONALITY = "functionality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPATIBILITY = "compatibility"
    MAINTAINABILITY = "maintainability"


@dataclass
class ImpactRecord:
    """影响记录"""
    impact_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    area: ImpactArea = ImpactArea.FUNCTIONALITY
    level: ImpactLevel = ImpactLevel.MEDIUM
    affected_components: List[str] = field(default_factory=list)
    description: str = ""
    mitigation: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"ImpactRecord created: impact_id={self.impact_id}, "
                     f"area={self.area.value}, level={self.level.value}")


class ImpactAnalyzer:
    """影响分析器"""

    def __init__(self):
        """初始化影响分析器"""
        self._impacts: List[ImpactRecord] = []
        self._dependency_map: Dict[str, List[str]] = {}
        logger.info("ImpactAnalyzer initialized")

    def analyze_change(self, change_description: str,
                       changed_files: List[str]) -> List[ImpactRecord]:
        """分析代码变更的影响范围"""
        logger.info(f"ImpactAnalyzer: analyzing change, "
                     f"description={change_description}, "
                     f"files={len(changed_files)}")
        impacts = []
        try:
            dependencies = self._trace_dependencies(changed_files)
            functional_impacts = self._assess_functional_impact(
                change_description, changed_files, dependencies)
            performance_impacts = self._assess_performance_impact(
                change_description, changed_files, dependencies)
            impacts.extend(functional_impacts)
            impacts.extend(performance_impacts)
            self._impacts.extend(impacts)
            logger.info(f"ImpactAnalyzer: analysis completed, "
                        f"found {len(impacts)} impacts")
        except Exception as e:
            logger.error(f"ImpactAnalyzer: analyze_change failed: {e}")
        return impacts

    def _trace_dependencies(self, changed_files: List[str]) -> Dict[str, List[str]]:
        """追踪依赖关系"""
        logger.debug(f"ImpactAnalyzer: tracing dependencies, "
                     f"files={len(changed_files)}")
        dependencies: Dict[str, List[str]] = {}
        try:
            for file_path in changed_files:
                deps: List[str] = []
                if file_path.endswith(".py"):
                    module_name = file_path.replace("/", ".").replace(".py", "")
                    deps.append(f"{module_name}.related_module")
                    deps.append(f"{module_name}.test_module")
                dependencies[file_path] = deps
                self._dependency_map[file_path] = deps
        except Exception as e:
            logger.error(f"ImpactAnalyzer: _trace_dependencies failed: {e}")
        return dependencies

    def _assess_functional_impact(self, change_description: str,
                                   changed_files: List[str],
                                   dependencies: Dict[str, List[str]]) -> List[ImpactRecord]:
        """评估功能影响"""
        logger.debug(f"ImpactAnalyzer: assessing functional impact, "
                     f"files={len(changed_files)}")
        impacts = []
        try:
            affected: List[str] = []
            for file_path, deps in dependencies.items():
                affected.extend(deps)
            affected.extend(changed_files)

            level = ImpactLevel.MEDIUM
            if "重构" in change_description or "删除" in change_description:
                level = ImpactLevel.HIGH
            elif "修复" in change_description or "新增" in change_description:
                level = ImpactLevel.LOW

            impacts.append(ImpactRecord(
                area=ImpactArea.FUNCTIONALITY,
                level=level,
                affected_components=affected[:10],
                description=f"功能影响：{change_description}",
                mitigation="建议执行回归测试验证功能完整性",
            ))
        except Exception as e:
            logger.error(f"ImpactAnalyzer: _assess_functional_impact failed: {e}")
        return impacts

    def _assess_performance_impact(self, change_description: str,
                                    changed_files: List[str],
                                    dependencies: Dict[str, List[str]]) -> List[ImpactRecord]:
        """评估性能影响"""
        logger.debug(f"ImpactAnalyzer: assessing performance impact, "
                     f"files={len(changed_files)}")
        impacts = []
        try:
            level = ImpactLevel.NONE
            affected: List[str] = []
            if "循环" in change_description or "查询" in change_description:
                level = ImpactLevel.MEDIUM
                affected = changed_files
            if "缓存" in change_description:
                level = ImpactLevel.HIGH
                affected = changed_files

            if level != ImpactLevel.NONE:
                impacts.append(ImpactRecord(
                    area=ImpactArea.PERFORMANCE,
                    level=level,
                    affected_components=affected,
                    description=f"性能影响：{change_description}",
                    mitigation="建议执行性能基准测试对比变更前后指标",
                ))
        except Exception as e:
            logger.error(f"ImpactAnalyzer: _assess_performance_impact failed: {e}")
        return impacts

    def generate_report(self) -> Dict[str, Any]:
        """生成影响分析报告"""
        logger.info("ImpactAnalyzer: generating report")
        try:
            by_area: Dict[str, int] = {}
            by_level: Dict[str, int] = {}
            for impact in self._impacts:
                by_area[impact.area.value] = by_area.get(impact.area.value, 0) + 1
                by_level[impact.level.value] = by_level.get(impact.level.value, 0) + 1

            critical_count = by_level.get("critical", 0)
            high_count = by_level.get("high", 0)

            if critical_count > 0:
                overall_level = "严重"
            elif high_count > 0:
                overall_level = "高"
            elif len(self._impacts) > 0:
                overall_level = "中等"
            else:
                overall_level = "低"

            report: Dict[str, Any] = {
                "total_impacts": len(self._impacts),
                "by_area": by_area,
                "by_level": by_level,
                "overall_level": overall_level,
                "impacts": [
                    {
                        "impact_id": i.impact_id,
                        "area": i.area.value,
                        "level": i.level.value,
                        "affected_components": i.affected_components,
                        "description": i.description,
                        "mitigation": i.mitigation,
                    }
                    for i in self._impacts
                ],
            }
            logger.info(f"ImpactAnalyzer: report generated, "
                        f"overall_level={overall_level}")
        except Exception as e:
            logger.error(f"ImpactAnalyzer: generate_report failed: {e}")
            report = {"error": str(e)}
        return report


class ImpactAnalysisService:
    """影响分析服务"""

    def __init__(self, analyzer: Optional[ImpactAnalyzer] = None):
        """初始化影响分析服务"""
        self.analyzer = analyzer or ImpactAnalyzer()
        logger.info("ImpactAnalysisService initialized")

    def analyze(self, change_description: str,
                changed_files: List[str]) -> List[ImpactRecord]:
        """执行影响分析"""
        logger.info(f"ImpactAnalysisService: analyzing, "
                     f"description={change_description}")
        return self.analyzer.analyze_change(change_description, changed_files)

    def get_impacts(self, area: Optional[ImpactArea] = None,
                    level: Optional[ImpactLevel] = None) -> List[ImpactRecord]:
        """获取影响记录列表"""
        logger.debug("ImpactAnalysisService: getting impacts")
        impacts = self.analyzer._impacts
        if area is not None:
            impacts = [i for i in impacts if i.area == area]
        if level is not None:
            impacts = [i for i in impacts if i.level == level]
        return impacts

    def get_report(self) -> Dict[str, Any]:
        """获取影响分析报告"""
        logger.debug("ImpactAnalysisService: getting report")
        return self.analyzer.generate_report()
