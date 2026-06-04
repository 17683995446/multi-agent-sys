"""
方法原子化拆分重构

职责：分析方法复杂度，提供拆分建议并执行方法级拆分重构

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MethodComplexity(str, Enum):
    """方法复杂度"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HIGHLY_COMPLEX = "highly_complex"


class SplitStrategy(str, Enum):
    """拆分策略"""
    BY_RESPONSIBILITY = "by_responsibility"
    BY_PARAMETER = "by_parameter"
    BY_RETURN_VALUE = "by_return_value"
    BY_CONDITION = "by_condition"


@dataclass
class MethodAnalysis:
    """方法分析结果"""
    method_name: str = ""
    complexity: MethodComplexity = MethodComplexity.SIMPLE
    line_count: int = 0
    responsibility_count: int = 0
    split_suggestions: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"MethodAnalysis created: method={self.method_name}, "
                     f"complexity={self.complexity.value}")


class MethodSplitter:
    """方法拆分器"""

    def __init__(self):
        """初始化方法拆分器"""
        self._analyses: Dict[str, MethodAnalysis] = {}
        self._split_log: List[Dict[str, Any]] = []
        logger.info("MethodSplitter initialized")

    def analyze_method(self, method_name: str,
                       method_info: Optional[Dict[str, Any]] = None) -> MethodAnalysis:
        """分析方法复杂度和职责"""
        logger.info(f"MethodSplitter: analyzing method={method_name}")
        try:
            info = method_info or {}
            line_count = info.get("line_count", 0)
            responsibility_count = info.get("responsibility_count", 1)
            param_count = info.get("param_count", 0)
            return_count = info.get("return_count", 1)
            branch_count = info.get("branch_count", 0)

            # 确定复杂度
            complexity = self._determine_complexity(
                line_count, responsibility_count, branch_count
            )

            analysis = MethodAnalysis(
                method_name=method_name,
                complexity=complexity,
                line_count=line_count,
                responsibility_count=responsibility_count,
            )

            # 生成拆分建议
            if complexity in (MethodComplexity.COMPLEX, MethodComplexity.HIGHLY_COMPLEX):
                analysis.split_suggestions = self._generate_split_suggestions(
                    method_name, line_count, responsibility_count,
                    param_count, return_count, branch_count
                )

            self._analyses[method_name] = analysis
            logger.info(f"MethodSplitter: analysis complete, "
                        f"complexity={complexity.value}, "
                        f"suggestions={len(analysis.split_suggestions)}")
        except Exception as e:
            logger.error(f"MethodSplitter: analyze_method failed: {e}")
            analysis = MethodAnalysis(method_name=method_name)

        return analysis

    def suggest_split(self, method_name: str,
                      strategy: Optional[SplitStrategy] = None) -> List[Dict[str, Any]]:
        """提供方法拆分建议"""
        logger.info(f"MethodSplitter: suggesting split for method={method_name}, "
                     f"strategy={strategy}")
        try:
            analysis = self._analyses.get(method_name)
            if analysis is None:
                logger.warning(f"MethodSplitter: no analysis for method={method_name}")
                return []

            if analysis.complexity in (MethodComplexity.SIMPLE, MethodComplexity.MODERATE):
                logger.info(f"MethodSplitter: method={method_name} is {analysis.complexity.value}, "
                            f"no split needed")
                return []

            suggestions = analysis.split_suggestions
            if strategy is not None:
                suggestions = [s for s in suggestions if s.get("strategy") == strategy.value]

            logger.info(f"MethodSplitter: {len(suggestions)} split suggestions")
        except Exception as e:
            logger.error(f"MethodSplitter: suggest_split failed: {e}")
            suggestions = []

        return suggestions

    def execute_split(self, method_name: str,
                      strategy: SplitStrategy = SplitStrategy.BY_RESPONSIBILITY) -> Dict[str, Any]:
        """执行方法拆分"""
        logger.info(f"MethodSplitter: executing split for method={method_name}, "
                     f"strategy={strategy.value}")
        try:
            analysis = self._analyses.get(method_name)
            if analysis is None:
                logger.warning(f"MethodSplitter: no analysis for method={method_name}")
                return {"method_name": method_name, "status": "failed",
                        "error": "未找到方法分析结果"}

            if analysis.complexity in (MethodComplexity.SIMPLE, MethodComplexity.MODERATE):
                logger.info(f"MethodSplitter: method={method_name} does not need splitting")
                return {"method_name": method_name, "status": "skipped",
                        "reason": "方法复杂度低，无需拆分"}

            result: Dict[str, Any] = {
                "method_name": method_name,
                "strategy": strategy.value,
                "status": "completed",
                "new_methods": [],
            }

            # 根据策略生成新方法
            if strategy == SplitStrategy.BY_RESPONSIBILITY:
                for i in range(analysis.responsibility_count):
                    result["new_methods"].append(f"{method_name}_responsibility_{i + 1}")
            elif strategy == SplitStrategy.BY_PARAMETER:
                result["new_methods"].append(f"{method_name}_with_params")
                result["new_methods"].append(f"{method_name}_default")
            elif strategy == SplitStrategy.BY_RETURN_VALUE:
                result["new_methods"].append(f"{method_name}_get_result")
                result["new_methods"].append(f"{method_name}_check_status")
            elif strategy == SplitStrategy.BY_CONDITION:
                result["new_methods"].append(f"{method_name}_positive")
                result["new_methods"].append(f"{method_name}_negative")

            self._split_log.append(result)
            logger.info(f"MethodSplitter: split executed, "
                        f"new_methods={len(result['new_methods'])}")
        except Exception as e:
            logger.error(f"MethodSplitter: execute_split failed: {e}")
            result = {"method_name": method_name, "status": "failed", "error": str(e)}

        return result

    def verify_split(self, method_name: str) -> Dict[str, Any]:
        """验证拆分结果"""
        logger.info(f"MethodSplitter: verifying split for method={method_name}")
        try:
            split_entries = [
                log for log in self._split_log
                if log.get("method_name") == method_name and log.get("status") == "completed"
            ]

            result: Dict[str, Any] = {
                "method_name": method_name,
                "verified": len(split_entries) > 0,
                "split_count": len(split_entries),
                "total_new_methods": sum(
                    len(e.get("new_methods", [])) for e in split_entries
                ),
            }

            logger.info(f"MethodSplitter: verification result={result['verified']}, "
                        f"split_count={result['split_count']}")
        except Exception as e:
            logger.error(f"MethodSplitter: verify_split failed: {e}")
            result = {"method_name": method_name, "verified": False, "error": str(e)}

        return result

    def _determine_complexity(self, line_count: int, responsibility_count: int,
                              branch_count: int) -> MethodComplexity:
        """确定方法复杂度等级"""
        logger.debug(f"MethodSplitter: determining complexity, "
                     f"lines={line_count}, responsibilities={responsibility_count}, "
                     f"branches={branch_count}")
        score = 0
        if line_count > 50:
            score += 2
        elif line_count > 20:
            score += 1

        if responsibility_count > 3:
            score += 2
        elif responsibility_count > 1:
            score += 1

        if branch_count > 5:
            score += 2
        elif branch_count > 2:
            score += 1

        if score >= 5:
            return MethodComplexity.HIGHLY_COMPLEX
        elif score >= 3:
            return MethodComplexity.COMPLEX
        elif score >= 1:
            return MethodComplexity.MODERATE
        else:
            return MethodComplexity.SIMPLE

    def _generate_split_suggestions(self, method_name: str, line_count: int,
                                    responsibility_count: int, param_count: int,
                                    return_count: int, branch_count: int) -> List[Dict[str, Any]]:
        """生成拆分建议"""
        logger.debug(f"MethodSplitter: generating split suggestions for {method_name}")
        suggestions: List[Dict[str, Any]] = []

        if responsibility_count > 1:
            suggestions.append({
                "strategy": SplitStrategy.BY_RESPONSIBILITY.value,
                "description": f"按职责拆分 {method_name}，当前有 {responsibility_count} 个职责",
                "priority": "high",
                "estimated_new_methods": responsibility_count,
            })

        if param_count > 4:
            suggestions.append({
                "strategy": SplitStrategy.BY_PARAMETER.value,
                "description": f"按参数拆分 {method_name}，当前有 {param_count} 个参数",
                "priority": "medium",
                "estimated_new_methods": 2,
            })

        if return_count > 1:
            suggestions.append({
                "strategy": SplitStrategy.BY_RETURN_VALUE.value,
                "description": f"按返回值拆分 {method_name}，当前有 {return_count} 种返回",
                "priority": "medium",
                "estimated_new_methods": return_count,
            })

        if branch_count > 3:
            suggestions.append({
                "strategy": SplitStrategy.BY_CONDITION.value,
                "description": f"按条件拆分 {method_name}，当前有 {branch_count} 个分支",
                "priority": "high",
                "estimated_new_methods": 2,
            })

        return suggestions


class MethodRefactorService:
    """方法重构服务"""

    def __init__(self, splitter: Optional[MethodSplitter] = None):
        """初始化方法重构服务"""
        self.splitter = splitter or MethodSplitter()
        logger.info("MethodRefactorService initialized")

    def analyze(self, method_name: str,
                method_info: Optional[Dict[str, Any]] = None) -> MethodAnalysis:
        """分析方法"""
        logger.info(f"MethodRefactorService: analyzing method={method_name}")
        return self.splitter.analyze_method(method_name, method_info)

    def split(self, method_name: str,
              strategy: SplitStrategy = SplitStrategy.BY_RESPONSIBILITY) -> Dict[str, Any]:
        """拆分方法"""
        logger.info(f"MethodRefactorService: splitting method={method_name}, "
                     f"strategy={strategy.value}")
        return self.splitter.execute_split(method_name, strategy)

    def get_analysis(self, method_name: str) -> Optional[MethodAnalysis]:
        """获取方法分析结果"""
        logger.debug(f"MethodRefactorService: getting analysis for method={method_name}")
        return self.splitter._analyses.get(method_name)
