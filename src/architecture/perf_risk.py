"""
代码性能风险检测模块

职责：检测内存、CPU、IO、算法等性能风险，提供缓解建议

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, Enum):
    """风险类别"""
    MEMORY = "memory"
    CPU = "cpu"
    IO = "io"
    CONCURRENCY = "concurrency"
    ALGORITHM = "algorithm"


@dataclass
class PerformanceRisk:
    """性能风险记录"""
    risk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: RiskCategory = RiskCategory.MEMORY
    level: RiskLevel = RiskLevel.LOW
    location: str = ""
    description: str = ""
    impact: str = ""
    mitigation: str = ""
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"PerformanceRisk created: id={self.risk_id}, "
                     f"category={self.category.value}, "
                     f"level={self.level.value}")


class PerformanceAnalyzer:
    """性能风险分析器"""

    def __init__(self):
        """初始化性能风险分析器"""
        self.risks: List[PerformanceRisk] = []
        logger.info("PerformanceAnalyzer initialized")

    def analyze(self, code_data: Dict[str, Any]) -> List[PerformanceRisk]:
        """分析代码性能风险"""
        logger.info("PerformanceAnalyzer: analyzing performance risks")
        self.risks = []
        try:
            memory_risks = self._check_memory_risks(code_data)
            cpu_risks = self._check_cpu_risks(code_data)
            io_risks = self._check_io_risks(code_data)
            algo_risks = self._check_algorithm_risks(code_data)

            self.risks = memory_risks + cpu_risks + io_risks + algo_risks
            logger.info(f"PerformanceAnalyzer: analysis completed, "
                        f"{len(self.risks)} risks found")
        except Exception as e:
            logger.error(f"PerformanceAnalyzer: analyze failed: {e}")
        return self.risks

    def _check_memory_risks(self, code_data: Dict[str, Any]
                            ) -> List[PerformanceRisk]:
        """检查内存风险"""
        logger.debug("PerformanceAnalyzer: checking memory risks")
        risks = []
        try:
            # 大列表风险
            large_lists = code_data.get("large_lists", [])
            for item in large_lists:
                name = item.get("name", "") if isinstance(item, dict) else str(item)
                size = item.get("size", 0) if isinstance(item, dict) else 0
                if size > 100000:
                    level = RiskLevel.CRITICAL
                elif size > 10000:
                    level = RiskLevel.HIGH
                elif size > 1000:
                    level = RiskLevel.MEDIUM
                else:
                    level = RiskLevel.LOW
                risks.append(PerformanceRisk(
                    category=RiskCategory.MEMORY,
                    level=level,
                    location=code_data.get("file_path", ""),
                    description=f"大列表风险: {name}, 大小={size}",
                    impact="可能导致内存溢出",
                    mitigation="使用生成器或分批处理",
                ))

            # 全局缓存风险
            global_caches = code_data.get("global_caches", [])
            for cache in global_caches:
                name = cache.get("name", "") if isinstance(cache, dict) else str(cache)
                risks.append(PerformanceRisk(
                    category=RiskCategory.MEMORY,
                    level=RiskLevel.MEDIUM,
                    location=code_data.get("file_path", ""),
                    description=f"全局缓存无上限: {name}",
                    impact="缓存持续增长导致内存泄漏",
                    mitigation="设置缓存上限或使用LRU缓存",
                ))

            # 字符串拼接风险
            string_concatenations = code_data.get("string_concatenations", [])
            for sc in string_concatenations:
                name = sc.get("name", "") if isinstance(sc, dict) else str(sc)
                loops = sc.get("in_loop", False) if isinstance(sc, dict) else False
                level = RiskLevel.HIGH if loops else RiskLevel.LOW
                risks.append(PerformanceRisk(
                    category=RiskCategory.MEMORY,
                    level=level,
                    location=code_data.get("file_path", ""),
                    description=f"循环内字符串拼接: {name}",
                    impact="频繁创建临时字符串对象",
                    mitigation="使用列表join或StringIO",
                ))
        except Exception as e:
            logger.error(f"PerformanceAnalyzer: _check_memory_risks failed: {e}")
        return risks

    def _check_cpu_risks(self, code_data: Dict[str, Any]
                         ) -> List[PerformanceRisk]:
        """检查CPU风险"""
        logger.debug("PerformanceAnalyzer: checking CPU risks")
        risks = []
        try:
            # 高复杂度方法
            complex_methods = code_data.get("complex_methods", [])
            for method in complex_methods:
                name = method.get("name", "") if isinstance(method, dict) else str(method)
                complexity = method.get("complexity", 1) if isinstance(method, dict) else 1
                if complexity > 20:
                    level = RiskLevel.CRITICAL
                elif complexity > 10:
                    level = RiskLevel.HIGH
                elif complexity > 5:
                    level = RiskLevel.MEDIUM
                else:
                    level = RiskLevel.LOW
                risks.append(PerformanceRisk(
                    category=RiskCategory.CPU,
                    level=level,
                    location=code_data.get("file_path", ""),
                    description=f"高圈复杂度方法: {name}, 复杂度={complexity}",
                    impact="CPU执行路径过多，性能下降",
                    mitigation="拆分方法，降低圈复杂度",
                ))

            # 深层嵌套循环
            nested_loops = code_data.get("nested_loops", [])
            for nl in nested_loops:
                name = nl.get("name", "") if isinstance(nl, dict) else str(nl)
                depth = nl.get("depth", 1) if isinstance(nl, dict) else 1
                if depth >= 3:
                    level = RiskLevel.CRITICAL
                elif depth >= 2:
                    level = RiskLevel.HIGH
                else:
                    level = RiskLevel.MEDIUM
                risks.append(PerformanceRisk(
                    category=RiskCategory.CPU,
                    level=level,
                    location=code_data.get("file_path", ""),
                    description=f"深层嵌套循环: {name}, 深度={depth}",
                    impact="时间复杂度指数增长",
                    mitigation="减少嵌套层级，使用提前返回",
                ))
        except Exception as e:
            logger.error(f"PerformanceAnalyzer: _check_cpu_risks failed: {e}")
        return risks

    def _check_io_risks(self, code_data: Dict[str, Any]
                        ) -> List[PerformanceRisk]:
        """检查IO风险"""
        logger.debug("PerformanceAnalyzer: checking IO risks")
        risks = []
        try:
            # 同步IO操作
            sync_io = code_data.get("sync_io_operations", [])
            for op in sync_io:
                name = op.get("name", "") if isinstance(op, dict) else str(op)
                in_loop = op.get("in_loop", False) if isinstance(op, dict) else False
                level = RiskLevel.HIGH if in_loop else RiskLevel.MEDIUM
                risks.append(PerformanceRisk(
                    category=RiskCategory.IO,
                    level=level,
                    location=code_data.get("file_path", ""),
                    description=f"同步IO操作: {name}",
                    impact="阻塞线程，降低吞吐量",
                    mitigation="使用异步IO或批量处理",
                ))

            # 频繁文件操作
            frequent_file_ops = code_data.get("frequent_file_ops", [])
            for fop in frequent_file_ops:
                name = fop.get("name", "") if isinstance(fop, dict) else str(fop)
                count = fop.get("count", 1) if isinstance(fop, dict) else 1
                if count > 100:
                    level = RiskLevel.HIGH
                elif count > 10:
                    level = RiskLevel.MEDIUM
                else:
                    level = RiskLevel.LOW
                risks.append(PerformanceRisk(
                    category=RiskCategory.IO,
                    level=level,
                    location=code_data.get("file_path", ""),
                    description=f"频繁文件操作: {name}, 次数={count}",
                    impact="IO瓶颈",
                    mitigation="合并文件操作或使用缓存",
                ))
        except Exception as e:
            logger.error(f"PerformanceAnalyzer: _check_io_risks failed: {e}")
        return risks

    def _check_algorithm_risks(self, code_data: Dict[str, Any]
                               ) -> List[PerformanceRisk]:
        """检查算法风险"""
        logger.debug("PerformanceAnalyzer: checking algorithm risks")
        risks = []
        try:
            # 低效算法
            inefficient_algos = code_data.get("inefficient_algorithms", [])
            for algo in inefficient_algos:
                name = algo.get("name", "") if isinstance(algo, dict) else str(algo)
                complexity = algo.get("time_complexity", "O(n)") if isinstance(algo, dict) else "O(n)"
                if "n^2" in complexity or "n*n" in complexity:
                    level = RiskLevel.HIGH
                elif "nlog" in complexity:
                    level = RiskLevel.MEDIUM
                else:
                    level = RiskLevel.LOW
                risks.append(PerformanceRisk(
                    category=RiskCategory.ALGORITHM,
                    level=level,
                    location=code_data.get("file_path", ""),
                    description=f"低效算法: {name}, 时间复杂度={complexity}",
                    impact="大数据量下性能急剧下降",
                    mitigation="优化算法或使用更高效的数据结构",
                ))

            # 重复计算
            repeated_calculations = code_data.get("repeated_calculations", [])
            for rc in repeated_calculations:
                name = rc.get("name", "") if isinstance(rc, dict) else str(rc)
                risks.append(PerformanceRisk(
                    category=RiskCategory.ALGORITHM,
                    level=RiskLevel.MEDIUM,
                    location=code_data.get("file_path", ""),
                    description=f"重复计算: {name}",
                    impact="不必要的计算开销",
                    mitigation="缓存计算结果或使用记忆化",
                ))
        except Exception as e:
            logger.error(f"PerformanceAnalyzer: _check_algorithm_risks failed: {e}")
        return risks

    def generate_report(self) -> Dict[str, Any]:
        """生成性能风险报告"""
        logger.info("PerformanceAnalyzer: generating report")
        try:
            total = len(self.risks)
            by_category = {}
            for cat in RiskCategory:
                by_category[cat.value] = sum(
                    1 for r in self.risks if r.category == cat
                )
            by_level = {}
            for lev in RiskLevel:
                by_level[lev.value] = sum(
                    1 for r in self.risks if r.level == lev
                )
            critical_count = by_level.get(RiskLevel.CRITICAL.value, 0)
            high_count = by_level.get(RiskLevel.HIGH.value, 0)

            if critical_count > 0:
                overall_level = RiskLevel.CRITICAL
            elif high_count > 2:
                overall_level = RiskLevel.HIGH
            elif high_count > 0 or total > 5:
                overall_level = RiskLevel.MEDIUM
            else:
                overall_level = RiskLevel.LOW

            report = {
                "total_risks": total,
                "overall_level": overall_level.value,
                "by_category": by_category,
                "by_level": by_level,
                "risks": [
                    {
                        "risk_id": r.risk_id,
                        "category": r.category.value,
                        "level": r.level.value,
                        "location": r.location,
                        "description": r.description,
                        "impact": r.impact,
                        "mitigation": r.mitigation,
                    }
                    for r in self.risks
                ],
            }
            logger.info(f"PerformanceAnalyzer: report generated, "
                        f"overall_level={overall_level.value}")
        except Exception as e:
            logger.error(f"PerformanceAnalyzer: generate_report failed: {e}")
            report = {"total_risks": 0, "overall_level": "low",
                      "by_category": {}, "by_level": {}, "risks": []}
        return report


class PerfRiskService:
    """性能风险检测服务"""

    def __init__(self):
        """初始化性能风险检测服务"""
        self.analyzer = PerformanceAnalyzer()
        logger.info("PerfRiskService initialized")

    def analyze(self, code_data: Dict[str, Any]) -> List[PerformanceRisk]:
        """执行性能风险分析"""
        logger.info("PerfRiskService: analyzing")
        try:
            risks = self.analyzer.analyze(code_data)
            logger.info(f"PerfRiskService: analysis completed, "
                        f"{len(risks)} risks")
        except Exception as e:
            logger.error(f"PerfRiskService: analyze failed: {e}")
            risks = []
        return risks

    def get_risks(self, category: Optional[RiskCategory] = None,
                  level: Optional[RiskLevel] = None
                  ) -> List[PerformanceRisk]:
        """获取风险列表"""
        logger.debug("PerfRiskService: getting risks")
        risks = self.analyzer.risks
        if category is not None:
            risks = [r for r in risks if r.category == category]
        if level is not None:
            risks = [r for r in risks if r.level == level]
        return risks

    def get_report(self) -> Dict[str, Any]:
        """获取性能风险报告"""
        logger.debug("PerfRiskService: getting report")
        return self.analyzer.generate_report()
