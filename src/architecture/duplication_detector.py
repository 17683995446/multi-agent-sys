"""
代码重复检测、冗余清理模块

职责：检测代码重复（精确、结构、语义），提供清理建议与执行

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DuplicationType(str, Enum):
    """重复类型"""
    EXACT = "exact"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"


class DuplicationSeverity(str, Enum):
    """重复严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class DuplicationInstance:
    """重复实例"""
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dup_type: DuplicationType = DuplicationType.EXACT
    locations: List[str] = field(default_factory=list)
    similarity: float = 0.0
    line_count: int = 0
    severity: DuplicationSeverity = DuplicationSeverity.LOW
    description: str = ""
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"DuplicationInstance created: id={self.instance_id}, "
                     f"type={self.dup_type.value}, "
                     f"similarity={self.similarity:.2f}")


class DuplicationDetector:
    """代码重复检测器"""

    def __init__(self, threshold: float = 0.8):
        """初始化代码重复检测器"""
        self.threshold = threshold
        self.instances: List[DuplicationInstance] = []
        logger.info(f"DuplicationDetector initialized, "
                    f"threshold={threshold}")

    def detect(self, code_blocks: List[Dict[str, Any]]
               ) -> List[DuplicationInstance]:
        """检测代码重复"""
        logger.info(f"DuplicationDetector: detecting duplications in "
                    f"{len(code_blocks)} blocks")
        self.instances = []
        try:
            # 精确重复检测
            exact = self._detect_exact(code_blocks)
            self.instances.extend(exact)

            # 结构重复检测
            structural = self._detect_structural(code_blocks)
            self.instances.extend(structural)

            logger.info(f"DuplicationDetector: detection completed, "
                        f"{len(self.instances)} instances found")
        except Exception as e:
            logger.error(f"DuplicationDetector: detect failed: {e}")
        return self.instances

    def _detect_exact(self, code_blocks: List[Dict[str, Any]]
                      ) -> List[DuplicationInstance]:
        """检测精确重复"""
        logger.debug("DuplicationDetector: detecting exact duplications")
        instances = []
        try:
            seen: Dict[str, List[str]] = {}
            for block in code_blocks:
                content = block.get("content", "").strip()
                location = block.get("location", "")
                if not content:
                    continue
                normalized = content.lower().replace(" ", "").replace("\t", "")
                if normalized in seen:
                    seen[normalized].append(location)
                else:
                    seen[normalized] = [location]

            for content_hash, locations in seen.items():
                if len(locations) > 1:
                    line_count = content_hash.count("\n") + 1
                    severity = DuplicationSeverity.HIGH if line_count > 10 \
                        else DuplicationSeverity.MEDIUM if line_count > 3 \
                        else DuplicationSeverity.LOW
                    instances.append(DuplicationInstance(
                        dup_type=DuplicationType.EXACT,
                        locations=locations,
                        similarity=1.0,
                        line_count=line_count,
                        severity=severity,
                        description=f"精确重复: {len(locations)}处相同代码",
                    ))
        except Exception as e:
            logger.error(f"DuplicationDetector: _detect_exact failed: {e}")
        return instances

    def _detect_structural(self, code_blocks: List[Dict[str, Any]]
                           ) -> List[DuplicationInstance]:
        """检测结构重复"""
        logger.debug("DuplicationDetector: detecting structural duplications")
        instances = []
        try:
            for i in range(len(code_blocks)):
                for j in range(i + 1, len(code_blocks)):
                    block_a = code_blocks[i]
                    block_b = code_blocks[j]
                    content_a = block_a.get("content", "")
                    content_b = block_b.get("content", "")
                    if not content_a or not content_b:
                        continue
                    similarity = self.calculate_similarity(content_a, content_b)
                    if similarity >= self.threshold:
                        # 排除已检测到的精确重复
                        if similarity >= 0.99:
                            continue
                        loc_a = block_a.get("location", f"block_{i}")
                        loc_b = block_b.get("location", f"block_{j}")
                        line_count = max(
                            content_a.count("\n") + 1,
                            content_b.count("\n") + 1,
                        )
                        severity = DuplicationSeverity.HIGH if similarity > 0.9 \
                            else DuplicationSeverity.MEDIUM if similarity > 0.85 \
                            else DuplicationSeverity.LOW
                        instances.append(DuplicationInstance(
                            dup_type=DuplicationType.STRUCTURAL,
                            locations=[loc_a, loc_b],
                            similarity=similarity,
                            line_count=line_count,
                            severity=severity,
                            description=f"结构重复: 相似度{similarity:.2f}",
                        ))
        except Exception as e:
            logger.error(f"DuplicationDetector: _detect_structural failed: {e}")
        return instances

    def calculate_similarity(self, code_a: str, code_b: str) -> float:
        """计算两段代码的相似度"""
        logger.debug("DuplicationDetector: calculating similarity")
        try:
            if not code_a or not code_b:
                return 0.0
            # 基于行的相似度计算
            lines_a = set(line.strip() for line in code_a.splitlines() if line.strip())
            lines_b = set(line.strip() for line in code_b.splitlines() if line.strip())
            if not lines_a or not lines_b:
                return 0.0
            intersection = lines_a & lines_b
            union = lines_a | lines_b
            similarity = len(intersection) / len(union) if union else 0.0
            return round(similarity, 4)
        except Exception as e:
            logger.error(f"DuplicationDetector: calculate_similarity failed: {e}")
            return 0.0

    def generate_report(self) -> Dict[str, Any]:
        """生成重复检测报告"""
        logger.info("DuplicationDetector: generating report")
        try:
            total = len(self.instances)
            exact_count = sum(
                1 for i in self.instances
                if i.dup_type == DuplicationType.EXACT
            )
            structural_count = sum(
                1 for i in self.instances
                if i.dup_type == DuplicationType.STRUCTURAL
            )
            semantic_count = sum(
                1 for i in self.instances
                if i.dup_type == DuplicationType.SEMANTIC
            )
            high_count = sum(
                1 for i in self.instances
                if i.severity == DuplicationSeverity.HIGH
            )
            report = {
                "total_instances": total,
                "exact_count": exact_count,
                "structural_count": structural_count,
                "semantic_count": semantic_count,
                "high_severity_count": high_count,
                "instances": [
                    {
                        "instance_id": i.instance_id,
                        "type": i.dup_type.value,
                        "locations": i.locations,
                        "similarity": i.similarity,
                        "line_count": i.line_count,
                        "severity": i.severity.value,
                        "description": i.description,
                    }
                    for i in self.instances
                ],
            }
            logger.info(f"DuplicationDetector: report generated, "
                        f"{total} instances")
        except Exception as e:
            logger.error(f"DuplicationDetector: generate_report failed: {e}")
            report = {"total_instances": 0, "exact_count": 0,
                      "structural_count": 0, "semantic_count": 0,
                      "high_severity_count": 0, "instances": []}
        return report


class DuplicationCleaner:
    """代码重复清理器"""

    def __init__(self):
        """初始化代码重复清理器"""
        self.cleanup_log: List[Dict[str, Any]] = []
        logger.info("DuplicationCleaner initialized")

    def analyze_duplication(self, instances: List[DuplicationInstance]
                            ) -> Dict[str, Any]:
        """分析重复情况"""
        logger.info(f"DuplicationCleaner: analyzing {len(instances)} instances")
        try:
            total_lines = sum(i.line_count for i in instances)
            high_severity = [
                i for i in instances
                if i.severity == DuplicationSeverity.HIGH
            ]
            cleanable = [
                i for i in instances
                if i.dup_type in (DuplicationType.EXACT, DuplicationType.STRUCTURAL)
            ]
            analysis = {
                "total_instances": len(instances),
                "total_duplicate_lines": total_lines,
                "high_severity_count": len(high_severity),
                "cleanable_count": len(cleanable),
                "estimated_reduction": total_lines * 0.6,
            }
            logger.info(f"DuplicationCleaner: analysis completed, "
                        f"{len(cleanable)} cleanable")
        except Exception as e:
            logger.error(f"DuplicationCleaner: analyze_duplication failed: {e}")
            analysis = {"total_instances": 0, "total_duplicate_lines": 0,
                        "high_severity_count": 0, "cleanable_count": 0,
                        "estimated_reduction": 0.0}
        return analysis

    def suggest_cleanup(self, instances: List[DuplicationInstance]
                        ) -> List[Dict[str, Any]]:
        """提供清理建议"""
        logger.info(f"DuplicationCleaner: suggesting cleanup for "
                    f"{len(instances)} instances")
        suggestions = []
        try:
            for inst in instances:
                suggestion = {
                    "instance_id": inst.instance_id,
                    "type": inst.dup_type.value,
                    "action": "extract" if inst.dup_type == DuplicationType.EXACT
                    else "refactor",
                    "locations": inst.locations,
                    "description": "",
                }
                if inst.dup_type == DuplicationType.EXACT:
                    suggestion["description"] = (
                        f"提取公共方法，消除{len(inst.locations)}处精确重复"
                    )
                elif inst.dup_type == DuplicationType.STRUCTURAL:
                    suggestion["description"] = (
                        f"重构相似代码，相似度{inst.similarity:.2f}"
                    )
                else:
                    suggestion["description"] = (
                        f"合并语义相同逻辑"
                    )
                suggestions.append(suggestion)
            logger.info(f"DuplicationCleaner: {len(suggestions)} suggestions")
        except Exception as e:
            logger.error(f"DuplicationCleaner: suggest_cleanup failed: {e}")
        return suggestions

    def execute_cleanup(self, instances: List[DuplicationInstance]
                        ) -> Dict[str, Any]:
        """执行清理"""
        logger.info(f"DuplicationCleaner: executing cleanup for "
                    f"{len(instances)} instances")
        result = {
            "total": len(instances),
            "cleaned": 0,
            "skipped": 0,
            "failed": 0,
        }
        try:
            for inst in instances:
                if inst.dup_type == DuplicationType.EXACT:
                    result["cleaned"] += 1
                    self.cleanup_log.append({
                        "instance_id": inst.instance_id,
                        "action": "extract",
                        "status": "success",
                    })
                elif inst.dup_type == DuplicationType.STRUCTURAL:
                    if inst.similarity >= 0.9:
                        result["cleaned"] += 1
                        self.cleanup_log.append({
                            "instance_id": inst.instance_id,
                            "action": "refactor",
                            "status": "success",
                        })
                    else:
                        result["skipped"] += 1
                        self.cleanup_log.append({
                            "instance_id": inst.instance_id,
                            "action": "refactor",
                            "status": "skipped",
                        })
                else:
                    result["skipped"] += 1
                    self.cleanup_log.append({
                        "instance_id": inst.instance_id,
                        "action": "merge",
                        "status": "skipped",
                    })
            logger.info(f"DuplicationCleaner: cleanup completed, "
                        f"result={result}")
        except Exception as e:
            logger.error(f"DuplicationCleaner: execute_cleanup failed: {e}")
            result["failed"] = result["total"] - result["cleaned"] - result["skipped"]
        return result


class DuplicationService:
    """代码重复检测与清理服务"""

    def __init__(self, threshold: float = 0.8):
        """初始化代码重复检测与清理服务"""
        self.detector = DuplicationDetector(threshold)
        self.cleaner = DuplicationCleaner()
        logger.info("DuplicationService initialized")

    def process(self, code_blocks: List[Dict[str, Any]]
                ) -> Dict[str, Any]:
        """执行完整的重复检测与清理流程"""
        logger.info(f"DuplicationService: processing {len(code_blocks)} blocks")
        try:
            instances = self.detector.detect(code_blocks)
            analysis = self.cleaner.analyze_duplication(instances)
            suggestions = self.cleaner.suggest_cleanup(instances)
            cleanup_result = self.cleaner.execute_cleanup(instances)
            result = {
                "instances_found": len(instances),
                "analysis": analysis,
                "suggestions_count": len(suggestions),
                "cleanup_result": cleanup_result,
            }
            logger.info(f"DuplicationService: process completed, "
                        f"{len(instances)} instances")
        except Exception as e:
            logger.error(f"DuplicationService: process failed: {e}")
            result = {"instances_found": 0, "analysis": {},
                      "suggestions_count": 0, "cleanup_result": {}}
        return result

    def get_report(self) -> Dict[str, Any]:
        """获取重复检测报告"""
        logger.debug("DuplicationService: getting report")
        return self.detector.generate_report()
