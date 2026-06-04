"""
变量归一、去重、标准化

职责：扫描变量，检测命名、类型、作用域问题，执行归一化和去重操作

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NormalizationType(str, Enum):
    """归一化类型"""
    NAMING = "naming"
    TYPING = "typing"
    SCOPING = "scoping"
    DEDUPLICATION = "deduplication"


@dataclass
class VariableIssue:
    """变量问题"""
    var_name: str = ""
    issue_type: NormalizationType = NormalizationType.NAMING
    description: str = ""
    suggestion: str = ""
    severity: str = "low"

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"VariableIssue created: var={self.var_name}, "
                     f"type={self.issue_type.value}")


@dataclass
class NormalizationResult:
    """归一化结果"""
    total_vars: int = 0
    normalized: int = 0
    duplicates_removed: int = 0
    issues: List[VariableIssue] = field(default_factory=list)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"NormalizationResult created: total={self.total_vars}, "
                     f"normalized={self.normalized}")


class VariableNormalizer:
    """变量归一化器"""

    def __init__(self):
        """初始化变量归一化器"""
        self._scanned_vars: Dict[str, Dict[str, Any]] = {}
        self._issues: List[VariableIssue] = []
        self._result: Optional[NormalizationResult] = None
        logger.info("VariableNormalizer initialized")

    def scan_variables(self, variables: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
        """扫描变量集合"""
        logger.info("VariableNormalizer: scanning variables")
        try:
            if variables is not None:
                self._scanned_vars = dict(variables)
            logger.info(f"VariableNormalizer: scanned {len(self._scanned_vars)} variables")
        except Exception as e:
            logger.error(f"VariableNormalizer: scan_variables failed: {e}")

        return self._scanned_vars

    def detect_issues(self) -> List[VariableIssue]:
        """检测变量问题"""
        logger.info("VariableNormalizer: detecting issues")
        self._issues = []

        try:
            seen_names: Dict[str, List[str]] = {}

            for var_name, var_info in self._scanned_vars.items():
                # 检测命名问题
                if self._has_naming_issue(var_name):
                    self._issues.append(VariableIssue(
                        var_name=var_name,
                        issue_type=NormalizationType.NAMING,
                        description=f"变量 '{var_name}' 命名不符合规范",
                        suggestion=self._suggest_naming(var_name),
                        severity="medium",
                    ))

                # 检测类型问题
                var_type = var_info.get("type", "")
                if self._has_typing_issue(var_name, var_type):
                    self._issues.append(VariableIssue(
                        var_name=var_name,
                        issue_type=NormalizationType.TYPING,
                        description=f"变量 '{var_name}' 类型 '{var_type}' 需要标准化",
                        suggestion=self._suggest_typing(var_type),
                        severity="low",
                    ))

                # 检测作用域问题
                scope = var_info.get("scope", "")
                if self._has_scoping_issue(scope):
                    self._issues.append(VariableIssue(
                        var_name=var_name,
                        issue_type=NormalizationType.SCOPING,
                        description=f"变量 '{var_name}' 作用域 '{scope}' 不当",
                        suggestion="缩小变量作用域",
                        severity="high",
                    ))

                # 检测重复
                lower_name = var_name.lower().replace("_", "")
                if lower_name not in seen_names:
                    seen_names[lower_name] = []
                seen_names[lower_name].append(var_name)

            # 检查重复变量
            for normalized_name, originals in seen_names.items():
                if len(originals) > 1:
                    for orig in originals:
                        self._issues.append(VariableIssue(
                            var_name=orig,
                            issue_type=NormalizationType.DEDUPLICATION,
                            description=f"变量 '{orig}' 与 {originals} 可能重复",
                            suggestion=f"统一为 '{normalized_name}'",
                            severity="high",
                        ))

            logger.info(f"VariableNormalizer: detected {len(self._issues)} issues")
        except Exception as e:
            logger.error(f"VariableNormalizer: detect_issues failed: {e}")

        return self._issues

    def normalize_naming(self, var_name: str) -> str:
        """归一化变量命名"""
        logger.info(f"VariableNormalizer: normalizing naming for var={var_name}")
        try:
            # 全大写常量保持原样（仅转小写）
            import re
            if var_name.isupper() or (var_name.count('_') > 0 and
                                       all(part.isupper() or part == '' for part in var_name.split('_'))):
                normalized = var_name.lower()
            else:
                # 处理驼峰命名
                normalized = var_name
                normalized = re.sub(r'([A-Z])', r'_\1', normalized).lower()
                # 移除前导下划线
                normalized = normalized.lstrip('_')
                # 合并连续下划线
                normalized = re.sub(r'_+', '_', normalized)
                # 移除尾部下划线
                normalized = normalized.rstrip('_')

            logger.info(f"VariableNormalizer: normalized '{var_name}' -> '{normalized}'")
        except Exception as e:
            logger.error(f"VariableNormalizer: normalize_naming failed: {e}")
            normalized = var_name

        return normalized

    def remove_duplicates(self) -> int:
        """移除重复变量"""
        logger.info("VariableNormalizer: removing duplicates")
        try:
            seen_normalized: Dict[str, str] = {}
            duplicates = []
            original_count = len(self._scanned_vars)

            for var_name in list(self._scanned_vars.keys()):
                normalized = self.normalize_naming(var_name)
                if normalized in seen_normalized:
                    duplicates.append(var_name)
                else:
                    seen_normalized[normalized] = var_name

            for dup in duplicates:
                del self._scanned_vars[dup]

            removed = len(duplicates)
            logger.info(f"VariableNormalizer: removed {removed} duplicates")
        except Exception as e:
            logger.error(f"VariableNormalizer: remove_duplicates failed: {e}")
            removed = 0

        return removed

    def standardize_types(self) -> int:
        """标准化变量类型"""
        logger.info("VariableNormalizer: standardizing types")
        try:
            standardized = 0
            type_mapping = {
                "int": "int",
                "integer": "int",
                "float": "float",
                "double": "float",
                "str": "str",
                "string": "str",
                "bool": "bool",
                "boolean": "bool",
                "list": "List",
                "array": "List",
                "dict": "Dict",
                "map": "Dict",
                "dictionary": "Dict",
            }

            for var_name, var_info in self._scanned_vars.items():
                current_type = var_info.get("type", "")
                if current_type.lower() in type_mapping:
                    new_type = type_mapping[current_type.lower()]
                    if new_type != current_type:
                        var_info["type"] = new_type
                        standardized += 1

            logger.info(f"VariableNormalizer: standardized {standardized} types")
        except Exception as e:
            logger.error(f"VariableNormalizer: standardize_types failed: {e}")
            standardized = 0

        return standardized

    def generate_report(self) -> NormalizationResult:
        """生成归一化报告"""
        logger.info("VariableNormalizer: generating report")
        try:
            total = len(self._scanned_vars)
            issues = list(self._issues)
            normalized_count = sum(
                1 for issue in issues
                if issue.issue_type in (NormalizationType.NAMING, NormalizationType.TYPING)
            )

            self._result = NormalizationResult(
                total_vars=total,
                normalized=normalized_count,
                duplicates_removed=sum(
                    1 for issue in issues
                    if issue.issue_type == NormalizationType.DEDUPLICATION
                ),
                issues=issues,
            )

            logger.info(f"VariableNormalizer: report generated, "
                        f"total={total}, normalized={normalized_count}")
        except Exception as e:
            logger.error(f"VariableNormalizer: generate_report failed: {e}")
            self._result = NormalizationResult()

        return self._result

    def _has_naming_issue(self, var_name: str) -> bool:
        """检查命名问题"""
        if not var_name:
            return True
        if var_name.startswith('__') and var_name.endswith('__'):
            return False
        if var_name.isupper():
            return False
        if '-' in var_name:
            return True
        if var_name[0].isupper() and not var_name.isupper():
            return True
        return False

    def _suggest_naming(self, var_name: str) -> str:
        """建议命名"""
        return self.normalize_naming(var_name)

    def _has_typing_issue(self, var_name: str, var_type: str) -> bool:
        """检查类型问题"""
        non_standard_types = {"integer", "double", "string", "boolean", "array", "map", "dictionary"}
        return var_type.lower() in non_standard_types

    def _suggest_typing(self, var_type: str) -> str:
        """建议类型"""
        type_mapping = {
            "integer": "int", "double": "float", "string": "str",
            "boolean": "bool", "array": "List", "map": "Dict", "dictionary": "Dict",
        }
        return type_mapping.get(var_type.lower(), var_type)

    def _has_scoping_issue(self, scope: str) -> bool:
        """检查作用域问题"""
        return scope in ("global", "module_level_unused")


class NormalizationService:
    """归一化服务"""

    def __init__(self, normalizer: Optional[VariableNormalizer] = None):
        """初始化归一化服务"""
        self.normalizer = normalizer or VariableNormalizer()
        logger.info("NormalizationService initialized")

    def process(self, variables: Dict[str, Dict[str, Any]]) -> NormalizationResult:
        """执行完整的归一化流程"""
        logger.info("NormalizationService: processing variables")
        try:
            self.normalizer.scan_variables(variables)
            self.normalizer.detect_issues()
            self.normalizer.remove_duplicates()
            self.normalizer.standardize_types()
            result = self.normalizer.generate_report()
            logger.info(f"NormalizationService: processing complete, "
                        f"total={result.total_vars}, normalized={result.normalized}")
        except Exception as e:
            logger.error(f"NormalizationService: process failed: {e}")
            result = NormalizationResult()

        return result

    def get_result(self) -> Optional[NormalizationResult]:
        """获取归一化结果"""
        logger.debug("NormalizationService: getting result")
        return self.normalizer._result

    def get_issues(self, issue_type: Optional[NormalizationType] = None) -> List[VariableIssue]:
        """获取问题列表"""
        logger.debug(f"NormalizationService: getting issues, type={issue_type}")
        issues = self.normalizer._issues
        if issue_type is not None:
            issues = [i for i in issues if i.issue_type == issue_type]
        return issues
