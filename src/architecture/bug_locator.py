"""
批量Bug自动定位

职责：分析Bug报告，追踪堆栈信息，追踪数据流，定位根因并生成报告

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BugSeverity(str, Enum):
    """Bug严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BugCategory(str, Enum):
    """Bug类别"""
    LOGIC = "logic"
    SYNTAX = "syntax"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPATIBILITY = "compatibility"


@dataclass
class BugReport:
    """Bug报告"""
    bug_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: BugSeverity = BugSeverity.MEDIUM
    category: BugCategory = BugCategory.LOGIC
    location: str = ""
    description: str = ""
    stack_trace: str = ""
    root_cause: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"BugReport created: bug_id={self.bug_id}, "
                     f"severity={self.severity.value}")


class BugLocator:
    """Bug定位器"""

    def __init__(self):
        """初始化Bug定位器"""
        self._bugs: Dict[str, BugReport] = {}
        self._statistics: Dict[str, Any] = {
            "total": 0,
            "by_severity": {},
            "by_category": {},
        }
        logger.info("BugLocator initialized")

    def locate_bug(self, description: str, stack_trace: str = "",
                   severity: BugSeverity = BugSeverity.MEDIUM,
                   category: BugCategory = BugCategory.LOGIC) -> BugReport:
        """定位Bug"""
        logger.info(f"BugLocator: locating bug, severity={severity.value}, "
                     f"category={category.value}")
        try:
            report = BugReport(
                severity=severity,
                category=category,
                description=description,
                stack_trace=stack_trace,
            )

            # 分析堆栈信息确定位置
            if stack_trace:
                report.location = self.analyze_stack_trace(stack_trace)
            else:
                report.location = "unknown"

            # 追踪数据流
            data_flow = self.trace_data_flow(report.location, description)

            # 识别根因
            report.root_cause = self.identify_root_cause(report, data_flow)

            # 存储报告
            self._bugs[report.bug_id] = report
            self._update_statistics(report)

            logger.info(f"BugLocator: bug located, bug_id={report.bug_id}, "
                        f"location={report.location}, root_cause={report.root_cause}")
        except Exception as e:
            logger.error(f"BugLocator: locate_bug failed: {e}")
            report = BugReport(description=description, severity=severity, category=category)

        return report

    def analyze_stack_trace(self, stack_trace: str) -> str:
        """分析堆栈信息"""
        logger.info(f"BugLocator: analyzing stack trace, length={len(stack_trace)}")
        try:
            if not stack_trace:
                return "unknown"

            # 解析堆栈信息，提取最顶层位置
            lines = stack_trace.strip().split('\n')
            for line in reversed(lines):
                line = line.strip()
                if 'File' in line and 'line' in line:
                    # 提取文件和行号
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        if part.startswith('File'):
                            return part
                    break

            # 如果无法解析，返回第一行
            location = lines[-1] if lines else "unknown"
            logger.info(f"BugLocator: stack trace analyzed, location={location}")
        except Exception as e:
            logger.error(f"BugLocator: analyze_stack_trace failed: {e}")
            location = "parse_error"

        return location

    def trace_data_flow(self, location: str, description: str) -> Dict[str, Any]:
        """追踪数据流"""
        logger.info(f"BugLocator: tracing data flow from location={location}")
        try:
            data_flow: Dict[str, Any] = {
                "source": location,
                "flow_steps": [],
                "affected_variables": [],
                "related_operations": [],
            }

            # 模拟数据流追踪
            if location and location != "unknown":
                data_flow["flow_steps"].append(f"起始点: {location}")
                data_flow["flow_steps"].append(f"数据传播: {location} -> 相关模块")
                data_flow["affected_variables"] = self._extract_variables(description)
                data_flow["related_operations"] = self._extract_operations(description)

            logger.info(f"BugLocator: data flow traced, "
                        f"steps={len(data_flow['flow_steps'])}, "
                        f"variables={len(data_flow['affected_variables'])}")
        except Exception as e:
            logger.error(f"BugLocator: trace_data_flow failed: {e}")
            data_flow = {"source": location, "flow_steps": [], "error": str(e)}

        return data_flow

    def identify_root_cause(self, report: BugReport,
                            data_flow: Dict[str, Any]) -> str:
        """识别根因"""
        logger.info(f"BugLocator: identifying root cause for bug_id={report.bug_id}")
        try:
            root_causes: Dict[BugCategory, str] = {
                BugCategory.LOGIC: "逻辑错误：条件判断或算法实现有误",
                BugCategory.SYNTAX: "语法错误：代码语法不符合规范",
                BugCategory.PERFORMANCE: "性能问题：存在低效算法或资源泄漏",
                BugCategory.SECURITY: "安全问题：存在输入验证或权限控制缺陷",
                BugCategory.COMPATIBILITY: "兼容性问题：接口或数据格式不兼容",
            }

            root_cause = root_causes.get(report.category, "未知根因")

            # 根据数据流细化根因
            affected_vars = data_flow.get("affected_variables", [])
            if affected_vars:
                root_cause += f"，涉及变量: {', '.join(affected_vars[:3])}"

            related_ops = data_flow.get("related_operations", [])
            if related_ops:
                root_cause += f"，相关操作: {', '.join(related_ops[:3])}"

            logger.info(f"BugLocator: root cause identified: {root_cause}")
        except Exception as e:
            logger.error(f"BugLocator: identify_root_cause failed: {e}")
            root_cause = "根因分析失败"

        return root_cause

    def generate_report(self, bug_id: Optional[str] = None) -> Dict[str, Any]:
        """生成Bug分析报告"""
        logger.info(f"BugLocator: generating report, bug_id={bug_id}")
        try:
            if bug_id and bug_id in self._bugs:
                report = self._bugs[bug_id]
                result: Dict[str, Any] = {
                    "bug_id": report.bug_id,
                    "severity": report.severity.value,
                    "category": report.category.value,
                    "location": report.location,
                    "description": report.description,
                    "root_cause": report.root_cause,
                    "recommendation": self._generate_recommendation(report),
                }
            else:
                # 生成统计报告
                result = {
                    "statistics": dict(self._statistics),
                    "bugs": [
                        {
                            "bug_id": r.bug_id,
                            "severity": r.severity.value,
                            "category": r.category.value,
                            "location": r.location,
                            "root_cause": r.root_cause,
                        }
                        for r in self._bugs.values()
                    ],
                }

            logger.info(f"BugLocator: report generated")
        except Exception as e:
            logger.error(f"BugLocator: generate_report failed: {e}")
            result = {"error": str(e)}

        return result

    def _update_statistics(self, report: BugReport) -> None:
        """更新统计信息"""
        logger.debug(f"BugLocator: updating statistics for bug_id={report.bug_id}")
        self._statistics["total"] += 1

        sev = report.severity.value
        self._statistics["by_severity"][sev] = (
            self._statistics["by_severity"].get(sev, 0) + 1
        )

        cat = report.category.value
        self._statistics["by_category"][cat] = (
            self._statistics["by_category"].get(cat, 0) + 1
        )

    def _extract_variables(self, description: str) -> List[str]:
        """从描述中提取变量名"""
        import re
        # 简单匹配变量名模式
        variables = re.findall(r'\b([a-z_][a-z0-9_]*)\b', description)
        return list(set(variables))[:5]

    def _extract_operations(self, description: str) -> List[str]:
        """从描述中提取操作"""
        operations = []
        operation_keywords = ["读取", "写入", "修改", "删除", "创建", "查询",
                              "read", "write", "update", "delete", "create"]
        for keyword in operation_keywords:
            if keyword in description.lower():
                operations.append(keyword)
        return operations[:5]

    def _generate_recommendation(self, report: BugReport) -> str:
        """生成修复建议"""
        recommendations: Dict[BugCategory, str] = {
            BugCategory.LOGIC: "建议检查条件判断逻辑和算法实现",
            BugCategory.SYNTAX: "建议使用语法检查工具修复语法错误",
            BugCategory.PERFORMANCE: "建议优化算法复杂度并检查资源使用",
            BugCategory.SECURITY: "建议加强输入验证和权限控制",
            BugCategory.COMPATIBILITY: "建议检查接口版本和数据格式兼容性",
        }
        return recommendations.get(report.category, "建议进一步分析")


class BugLocationService:
    """Bug定位服务"""

    def __init__(self, locator: Optional[BugLocator] = None):
        """初始化Bug定位服务"""
        self.locator = locator or BugLocator()
        logger.info("BugLocationService initialized")

    def locate(self, description: str, stack_trace: str = "",
               severity: BugSeverity = BugSeverity.MEDIUM,
               category: BugCategory = BugCategory.LOGIC) -> BugReport:
        """定位Bug"""
        logger.info(f"BugLocationService: locating bug, severity={severity.value}")
        return self.locator.locate_bug(description, stack_trace, severity, category)

    def get_bug(self, bug_id: str) -> Optional[BugReport]:
        """获取Bug报告"""
        logger.debug(f"BugLocationService: getting bug_id={bug_id}")
        return self.locator._bugs.get(bug_id)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        logger.debug("BugLocationService: getting statistics")
        return dict(self.locator._statistics)
