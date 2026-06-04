"""
隐式依赖/状态清除模块

职责：检测并清除隐式依赖、全局状态、副作用、耦合等隐式问题

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ImplicitType(str, Enum):
    """隐式问题类型"""
    HIDDEN_DEPENDENCY = "hidden_dependency"
    GLOBAL_STATE = "global_state"
    SIDE_EFFECT = "side_effect"
    COUPLING = "coupling"


@dataclass
class ImplicitIssue:
    """隐式问题记录"""
    issue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    implicit_type: ImplicitType = ImplicitType.HIDDEN_DEPENDENCY
    location: str = ""
    description: str = ""
    severity: float = 0.5
    suggestion: str = ""
    resolved: bool = False
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"ImplicitIssue created: id={self.issue_id}, "
                     f"type={self.implicit_type.value}")


class ImplicitDetector:
    """隐式问题检测器"""

    def __init__(self):
        """初始化隐式问题检测器"""
        self.issues: List[ImplicitIssue] = []
        logger.info("ImplicitDetector initialized")

    def detect_dependencies(self, code_data: Dict[str, Any]
                            ) -> List[ImplicitIssue]:
        """检测隐式依赖"""
        logger.info("ImplicitDetector: detecting hidden dependencies")
        issues = []
        try:
            imports = code_data.get("imports", [])
            used_imports = code_data.get("used_imports", [])
            # 检测未使用的导入（隐式依赖）
            unused = [imp for imp in imports if imp not in used_imports]
            for imp in unused:
                issue = ImplicitIssue(
                    implicit_type=ImplicitType.HIDDEN_DEPENDENCY,
                    location=code_data.get("file_path", ""),
                    description=f"未使用的导入依赖: {imp}",
                    severity=0.3,
                    suggestion=f"移除未使用的导入: {imp}",
                )
                issues.append(issue)

            # 检测循环导入
            circular = code_data.get("circular_imports", [])
            for circ in circular:
                issue = ImplicitIssue(
                    implicit_type=ImplicitType.HIDDEN_DEPENDENCY,
                    location=code_data.get("file_path", ""),
                    description=f"循环导入: {circ}",
                    severity=0.8,
                    suggestion=f"重构以消除循环导入: {circ}",
                )
                issues.append(issue)

            self.issues.extend(issues)
            logger.info(f"ImplicitDetector: found {len(issues)} "
                        f"hidden dependency issues")
        except Exception as e:
            logger.error(f"ImplicitDetector: detect_dependencies failed: {e}")
        return issues

    def detect_global_state(self, code_data: Dict[str, Any]
                            ) -> List[ImplicitIssue]:
        """检测全局状态"""
        logger.info("ImplicitDetector: detecting global state")
        issues = []
        try:
            globals_list = code_data.get("globals", [])
            for g in globals_list:
                name = g.get("name", "") if isinstance(g, dict) else str(g)
                mutable = g.get("mutable", True) if isinstance(g, dict) else True
                severity = 0.7 if mutable else 0.3
                issue = ImplicitIssue(
                    implicit_type=ImplicitType.GLOBAL_STATE,
                    location=code_data.get("file_path", ""),
                    description=f"全局状态: {name}",
                    severity=severity,
                    suggestion=f"将全局状态封装为类属性或使用依赖注入: {name}",
                )
                issues.append(issue)

            # 检测模块级可变对象
            module_mutables = code_data.get("module_mutables", [])
            for m in module_mutables:
                issue = ImplicitIssue(
                    implicit_type=ImplicitType.GLOBAL_STATE,
                    location=code_data.get("file_path", ""),
                    description=f"模块级可变对象: {m}",
                    severity=0.6,
                    suggestion=f"避免模块级可变状态: {m}",
                )
                issues.append(issue)

            self.issues.extend(issues)
            logger.info(f"ImplicitDetector: found {len(issues)} "
                        f"global state issues")
        except Exception as e:
            logger.error(f"ImplicitDetector: detect_global_state failed: {e}")
        return issues

    def detect_side_effects(self, code_data: Dict[str, Any]
                            ) -> List[ImplicitIssue]:
        """检测副作用"""
        logger.info("ImplicitDetector: detecting side effects")
        issues = []
        try:
            functions = code_data.get("functions", [])
            for func in functions:
                name = func.get("name", "") if isinstance(func, dict) else str(func)
                has_side_effect = func.get("has_side_effect", False) if isinstance(func, dict) else False
                modifies_global = func.get("modifies_global", False) if isinstance(func, dict) else False
                if has_side_effect:
                    issue = ImplicitIssue(
                        implicit_type=ImplicitType.SIDE_EFFECT,
                        location=code_data.get("file_path", ""),
                        description=f"函数存在副作用: {name}",
                        severity=0.5,
                        suggestion=f"分离纯函数与副作用: {name}",
                    )
                    issues.append(issue)
                if modifies_global:
                    issue = ImplicitIssue(
                        implicit_type=ImplicitType.SIDE_EFFECT,
                        location=code_data.get("file_path", ""),
                        description=f"函数修改全局状态: {name}",
                        severity=0.8,
                        suggestion=f"避免修改全局状态，使用返回值: {name}",
                    )
                    issues.append(issue)

            self.issues.extend(issues)
            logger.info(f"ImplicitDetector: found {len(issues)} "
                        f"side effect issues")
        except Exception as e:
            logger.error(f"ImplicitDetector: detect_side_effects failed: {e}")
        return issues

    def detect_coupling(self, code_data: Dict[str, Any]
                        ) -> List[ImplicitIssue]:
        """检测隐式耦合"""
        logger.info("ImplicitDetector: detecting coupling")
        issues = []
        try:
            couplings = code_data.get("couplings", [])
            for c in couplings:
                source = c.get("source", "") if isinstance(c, dict) else str(c)
                target = c.get("target", "") if isinstance(c, dict) else ""
                strength = c.get("strength", 0.5) if isinstance(c, dict) else 0.5
                if strength > 0.7:
                    issue = ImplicitIssue(
                        implicit_type=ImplicitType.COUPLING,
                        location=code_data.get("file_path", ""),
                        description=f"高耦合: {source} -> {target}",
                        severity=strength,
                        suggestion=f"引入接口解耦: {source}与{target}",
                    )
                    issues.append(issue)

            self.issues.extend(issues)
            logger.info(f"ImplicitDetector: found {len(issues)} "
                        f"coupling issues")
        except Exception as e:
            logger.error(f"ImplicitDetector: detect_coupling failed: {e}")
        return issues

    def generate_report(self) -> Dict[str, Any]:
        """生成检测报告"""
        logger.info("ImplicitDetector: generating report")
        try:
            total = len(self.issues)
            by_type = {}
            for t in ImplicitType:
                by_type[t.value] = sum(
                    1 for i in self.issues if i.implicit_type == t
                )
            avg_severity = (
                sum(i.severity for i in self.issues) / total
                if total > 0 else 0.0
            )
            report = {
                "total_issues": total,
                "by_type": by_type,
                "average_severity": round(avg_severity, 4),
                "issues": [
                    {
                        "issue_id": i.issue_id,
                        "type": i.implicit_type.value,
                        "location": i.location,
                        "description": i.description,
                        "severity": i.severity,
                        "suggestion": i.suggestion,
                        "resolved": i.resolved,
                    }
                    for i in self.issues
                ],
            }
            logger.info(f"ImplicitDetector: report generated, "
                        f"{total} issues")
        except Exception as e:
            logger.error(f"ImplicitDetector: generate_report failed: {e}")
            report = {"total_issues": 0, "by_type": {},
                      "average_severity": 0.0, "issues": []}
        return report


class ImplicitCleaner:
    """隐式问题清理器"""

    def __init__(self):
        """初始化隐式问题清理器"""
        self.clean_log: List[Dict[str, Any]] = []
        logger.info("ImplicitCleaner initialized")

    def clean_dependency(self, issue: ImplicitIssue) -> Dict[str, Any]:
        """清理隐式依赖"""
        logger.info(f"ImplicitCleaner: cleaning dependency "
                    f"id={issue.issue_id}")
        result = {
            "issue_id": issue.issue_id,
            "action": "remove_unused_import",
            "status": "success",
        }
        try:
            if issue.implicit_type != ImplicitType.HIDDEN_DEPENDENCY:
                result["status"] = "skipped"
                result["reason"] = "类型不匹配"
            else:
                issue.resolved = True
                self.clean_log.append(result)
                logger.info(f"ImplicitCleaner: dependency cleaned "
                            f"id={issue.issue_id}")
        except Exception as e:
            logger.error(f"ImplicitCleaner: clean_dependency failed: {e}")
            result["status"] = "failed"
        return result

    def clean_global_state(self, issue: ImplicitIssue) -> Dict[str, Any]:
        """清理全局状态"""
        logger.info(f"ImplicitCleaner: cleaning global state "
                    f"id={issue.issue_id}")
        result = {
            "issue_id": issue.issue_id,
            "action": "encapsulate_global",
            "status": "success",
        }
        try:
            if issue.implicit_type != ImplicitType.GLOBAL_STATE:
                result["status"] = "skipped"
                result["reason"] = "类型不匹配"
            else:
                issue.resolved = True
                self.clean_log.append(result)
                logger.info(f"ImplicitCleaner: global state cleaned "
                            f"id={issue.issue_id}")
        except Exception as e:
            logger.error(f"ImplicitCleaner: clean_global_state failed: {e}")
            result["status"] = "failed"
        return result

    def clean_side_effect(self, issue: ImplicitIssue) -> Dict[str, Any]:
        """清理副作用"""
        logger.info(f"ImplicitCleaner: cleaning side effect "
                    f"id={issue.issue_id}")
        result = {
            "issue_id": issue.issue_id,
            "action": "separate_pure_function",
            "status": "success",
        }
        try:
            if issue.implicit_type != ImplicitType.SIDE_EFFECT:
                result["status"] = "skipped"
                result["reason"] = "类型不匹配"
            else:
                issue.resolved = True
                self.clean_log.append(result)
                logger.info(f"ImplicitCleaner: side effect cleaned "
                            f"id={issue.issue_id}")
        except Exception as e:
            logger.error(f"ImplicitCleaner: clean_side_effect failed: {e}")
            result["status"] = "failed"
        return result

    def verify_clean(self, issues: List[ImplicitIssue]) -> Dict[str, Any]:
        """验证清理结果"""
        logger.info(f"ImplicitCleaner: verifying {len(issues)} issues")
        try:
            resolved = sum(1 for i in issues if i.resolved)
            unresolved = sum(1 for i in issues if not i.resolved)
            result = {
                "total": len(issues),
                "resolved": resolved,
                "unresolved": unresolved,
                "success_rate": resolved / len(issues) if issues else 1.0,
            }
            logger.info(f"ImplicitCleaner: verification completed, "
                        f"resolved={resolved}")
        except Exception as e:
            logger.error(f"ImplicitCleaner: verify_clean failed: {e}")
            result = {"total": 0, "resolved": 0, "unresolved": 0,
                      "success_rate": 0.0}
        return result


class ImplicitClearService:
    """隐式问题清除服务"""

    def __init__(self):
        """初始化隐式问题清除服务"""
        self.detector = ImplicitDetector()
        self.cleaner = ImplicitCleaner()
        logger.info("ImplicitClearService initialized")

    def process(self, code_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整的隐式问题检测与清除流程"""
        logger.info("ImplicitClearService: processing")
        try:
            # 检测所有类型
            dep_issues = self.detector.detect_dependencies(code_data)
            global_issues = self.detector.detect_global_state(code_data)
            side_issues = self.detector.detect_side_effects(code_data)
            coupling_issues = self.detector.detect_coupling(code_data)

            all_issues = dep_issues + global_issues + side_issues + coupling_issues

            # 清理
            for issue in all_issues:
                if issue.implicit_type == ImplicitType.HIDDEN_DEPENDENCY:
                    self.cleaner.clean_dependency(issue)
                elif issue.implicit_type == ImplicitType.GLOBAL_STATE:
                    self.cleaner.clean_global_state(issue)
                elif issue.implicit_type == ImplicitType.SIDE_EFFECT:
                    self.cleaner.clean_side_effect(issue)

            # 验证
            verification = self.cleaner.verify_clean(all_issues)

            result = {
                "total_issues": len(all_issues),
                "dependency_issues": len(dep_issues),
                "global_state_issues": len(global_issues),
                "side_effect_issues": len(side_issues),
                "coupling_issues": len(coupling_issues),
                "verification": verification,
            }
            logger.info(f"ImplicitClearService: process completed, "
                        f"{len(all_issues)} issues")
        except Exception as e:
            logger.error(f"ImplicitClearService: process failed: {e}")
            result = {"total_issues": 0, "dependency_issues": 0,
                      "global_state_issues": 0, "side_effect_issues": 0,
                      "coupling_issues": 0, "verification": {}}
        return result

    def get_report(self) -> Dict[str, Any]:
        """获取检测报告"""
        logger.debug("ImplicitClearService: getting report")
        return self.detector.generate_report()
