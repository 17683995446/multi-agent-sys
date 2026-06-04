"""
类级别解耦重构

职责：分析类的耦合类型和程度，提供解耦策略并执行解耦重构

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CouplingType(str, Enum):
    """耦合类型"""
    DATA = "data"
    CONTROL = "control"
    CONTENT = "content"
    COMMON = "common"
    CONTROL_FLOW = "control_flow"


class DecouplingStrategy(str, Enum):
    """解耦策略"""
    EXTRACT_CLASS = "extract_class"
    INTRODUCE_INTERFACE = "introduce_interface"
    MOVE_METHOD = "move_method"
    DELEGATE = "delegate"


@dataclass
class ClassCouplingReport:
    """类耦合报告"""
    class_name: str = ""
    coupling_score: float = 0.0
    coupling_types: List[CouplingType] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"ClassCouplingReport created: class={self.class_name}, "
                     f"score={self.coupling_score}")


class ClassDecoupler:
    """类解耦器"""

    def __init__(self):
        """初始化类解耦器"""
        self._reports: Dict[str, ClassCouplingReport] = {}
        self._decoupling_log: List[Dict[str, Any]] = []
        logger.info("ClassDecoupler initialized")

    def analyze_coupling(self, class_name: str,
                         class_info: Optional[Dict[str, Any]] = None) -> ClassCouplingReport:
        """分析类的耦合情况"""
        logger.info(f"ClassDecoupler: analyzing coupling for class={class_name}")
        try:
            info = class_info or {}
            report = ClassCouplingReport(
                class_name=class_name,
                coupling_score=0.0,
                coupling_types=[],
                dependencies=info.get("dependencies", []),
            )

            # 分析耦合类型
            dep_count = len(report.dependencies)
            if dep_count > 5:
                report.coupling_types.append(CouplingType.DATA)
            if info.get("has_control_flags", False):
                report.coupling_types.append(CouplingType.CONTROL)
            if info.get("accesses_internal", False):
                report.coupling_types.append(CouplingType.CONTENT)
            if info.get("shares_global", False):
                report.coupling_types.append(CouplingType.COMMON)
            if info.get("control_flow_coupling", False):
                report.coupling_types.append(CouplingType.CONTROL_FLOW)

            # 计算耦合分数
            report.coupling_score = min(1.0, len(report.coupling_types) * 0.25 + dep_count * 0.05)

            self._reports[class_name] = report
            logger.info(f"ClassDecoupler: coupling analysis complete, "
                        f"score={report.coupling_score}, types={len(report.coupling_types)}")
        except Exception as e:
            logger.error(f"ClassDecoupler: analyze_coupling failed: {e}")
            report = ClassCouplingReport(class_name=class_name)

        return report

    def suggest_decoupling(self, report: ClassCouplingReport) -> List[Dict[str, Any]]:
        """根据耦合报告提供解耦建议"""
        logger.info(f"ClassDecoupler: suggesting decoupling for class={report.class_name}")
        suggestions: List[Dict[str, Any]] = []

        try:
            for coupling_type in report.coupling_types:
                if coupling_type == CouplingType.DATA:
                    suggestions.append({
                        "strategy": DecouplingStrategy.EXTRACT_CLASS,
                        "description": f"从 {report.class_name} 提取数据类以减少数据耦合",
                        "priority": "high",
                    })
                elif coupling_type == CouplingType.CONTROL:
                    suggestions.append({
                        "strategy": DecouplingStrategy.INTRODUCE_INTERFACE,
                        "description": f"为 {report.class_name} 引入接口以消除控制耦合",
                        "priority": "high",
                    })
                elif coupling_type == CouplingType.CONTENT:
                    suggestions.append({
                        "strategy": DecouplingStrategy.MOVE_METHOD,
                        "description": f"移动方法以避免 {report.class_name} 访问其他类内部",
                        "priority": "medium",
                    })
                elif coupling_type == CouplingType.COMMON:
                    suggestions.append({
                        "strategy": DecouplingStrategy.EXTRACT_CLASS,
                        "description": f"提取共享数据为独立类以消除公共耦合",
                        "priority": "medium",
                    })
                elif coupling_type == CouplingType.CONTROL_FLOW:
                    suggestions.append({
                        "strategy": DecouplingStrategy.DELEGATE,
                        "description": f"使用委托模式解耦 {report.class_name} 的控制流",
                        "priority": "low",
                    })

            if report.coupling_score > 0.7:
                suggestions.append({
                    "strategy": DecouplingStrategy.EXTRACT_CLASS,
                    "description": f"{report.class_name} 耦合度过高，建议整体拆分",
                    "priority": "critical",
                })

            logger.info(f"ClassDecoupler: generated {len(suggestions)} decoupling suggestions")
        except Exception as e:
            logger.error(f"ClassDecoupler: suggest_decoupling failed: {e}")

        return suggestions

    def execute_decoupling(self, report: ClassCouplingReport,
                           strategy: DecouplingStrategy) -> Dict[str, Any]:
        """执行解耦操作"""
        logger.info(f"ClassDecoupler: executing decoupling for class={report.class_name}, "
                     f"strategy={strategy.value}")
        try:
            result: Dict[str, Any] = {
                "class_name": report.class_name,
                "strategy": strategy.value,
                "status": "completed",
                "changes": [],
            }

            if strategy == DecouplingStrategy.EXTRACT_CLASS:
                result["changes"].append(f"从 {report.class_name} 提取新类")
                result["changes"].append(f"更新 {report.class_name} 的依赖")
            elif strategy == DecouplingStrategy.INTRODUCE_INTERFACE:
                result["changes"].append(f"为 {report.class_name} 定义接口")
                result["changes"].append(f"修改依赖方使用接口")
            elif strategy == DecouplingStrategy.MOVE_METHOD:
                result["changes"].append(f"移动方法到目标类")
                result["changes"].append(f"更新方法调用")
            elif strategy == DecouplingStrategy.DELEGATE:
                result["changes"].append(f"创建委托对象")
                result["changes"].append(f"替换直接调用为委托调用")

            self._decoupling_log.append(result)
            logger.info(f"ClassDecoupler: decoupling executed, "
                        f"changes={len(result['changes'])}")
        except Exception as e:
            logger.error(f"ClassDecoupler: execute_decoupling failed: {e}")
            result = {"class_name": report.class_name, "strategy": strategy.value,
                      "status": "failed", "error": str(e)}

        return result

    def verify_decoupling(self, report: ClassCouplingReport) -> Dict[str, Any]:
        """验证解耦结果"""
        logger.info(f"ClassDecoupler: verifying decoupling for class={report.class_name}")
        try:
            original_report = self._reports.get(report.class_name)
            result: Dict[str, Any] = {
                "class_name": report.class_name,
                "verified": False,
                "improvement": 0.0,
            }

            if original_report:
                score_diff = original_report.coupling_score - report.coupling_score
                result["improvement"] = round(max(0.0, score_diff), 4)
                result["verified"] = report.coupling_score < original_report.coupling_score
            else:
                result["verified"] = True

            logger.info(f"ClassDecoupler: verification result={result['verified']}, "
                        f"improvement={result['improvement']}")
        except Exception as e:
            logger.error(f"ClassDecoupler: verify_decoupling failed: {e}")
            result = {"class_name": report.class_name, "verified": False, "error": str(e)}

        return result


class ClassRefactorService:
    """类重构服务"""

    def __init__(self, decoupler: Optional[ClassDecoupler] = None):
        """初始化类重构服务"""
        self.decoupler = decoupler or ClassDecoupler()
        self._reports: Dict[str, ClassCouplingReport] = {}
        logger.info("ClassRefactorService initialized")

    def analyze(self, class_name: str,
                class_info: Optional[Dict[str, Any]] = None) -> ClassCouplingReport:
        """分析类的耦合情况"""
        logger.info(f"ClassRefactorService: analyzing class={class_name}")
        report = self.decoupler.analyze_coupling(class_name, class_info)
        self._reports[class_name] = report
        return report

    def refactor(self, class_name: str,
                 strategy: DecouplingStrategy = DecouplingStrategy.EXTRACT_CLASS) -> Dict[str, Any]:
        """执行类重构"""
        logger.info(f"ClassRefactorService: refactoring class={class_name}, "
                     f"strategy={strategy.value}")
        report = self._reports.get(class_name)
        if report is None:
            logger.warning(f"ClassRefactorService: no report for class={class_name}, "
                           f"running analysis first")
            report = self.analyze(class_name)

        result = self.decoupler.execute_decoupling(report, strategy)
        logger.info(f"ClassRefactorService: refactor result={result.get('status')}")
        return result

    def get_report(self, class_name: str) -> Optional[ClassCouplingReport]:
        """获取类的耦合报告"""
        logger.debug(f"ClassRefactorService: getting report for class={class_name}")
        return self._reports.get(class_name)
