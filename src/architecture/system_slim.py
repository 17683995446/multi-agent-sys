"""
系统冗余清理、轻量化模块

职责：扫描冗余项、执行清理操作、生成清理报告

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RedundancyType(str, Enum):
    """冗余类型"""
    DEAD_CODE = "dead_code"
    UNUSED_IMPORT = "unused_import"
    DUPLICATE_LOGIC = "duplicate_logic"
    ORPHAN_RESOURCE = "orphan_resource"
    STALE_CONFIG = "stale_config"


class CleanupAction(str, Enum):
    """清理动作"""
    REMOVE = "remove"
    CONSOLIDATE = "consolidate"
    REPLACE = "replace"
    ARCHIVE = "archive"


@dataclass
class RedundancyItem:
    """冗余项"""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    redundancy_type: RedundancyType = RedundancyType.DEAD_CODE
    location: str = ""
    description: str = ""
    size_estimate: float = 0.0
    action: CleanupAction = CleanupAction.REMOVE

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"RedundancyItem created: item_id={self.item_id}, "
                     f"type={self.redundancy_type.value}, "
                     f"action={self.action.value}")


@dataclass
class SlimResult:
    """轻量化结果"""
    total_items: int = 0
    removed_items: int = 0
    space_saved: float = 0.0
    performance_gain: float = 0.0
    items: List[RedundancyItem] = field(default_factory=list)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"SlimResult created: total={self.total_items}, "
                     f"removed={self.removed_items}, "
                     f"space_saved={self.space_saved}")


class SystemSlimmer:
    """系统轻量化器"""

    def __init__(self):
        """初始化系统轻量化器"""
        self._results: Dict[str, SlimResult] = {}
        self._reports: Dict[str, Dict[str, Any]] = {}
        logger.info("SystemSlimmer initialized")

    def scan(self, code_data: Dict[str, Any]) -> List[RedundancyItem]:
        """扫描冗余项"""
        logger.info(f"SystemSlimmer: scanning, keys={list(code_data.keys())}")
        try:
            items: List[RedundancyItem] = []

            # 扫描各类冗余
            items.extend(self._find_dead_code(code_data))
            items.extend(self._find_unused_imports(code_data))
            items.extend(self._find_duplicates(code_data))
            items.extend(self._find_orphans(code_data))

            # 扫描过时配置
            stale_configs = code_data.get("stale_configs", [])
            for config in stale_configs:
                item = RedundancyItem(
                    redundancy_type=RedundancyType.STALE_CONFIG,
                    location=config.get("location", ""),
                    description=config.get("description", "过时配置项"),
                    size_estimate=config.get("size_estimate", 0.0),
                    action=CleanupAction.REPLACE,
                )
                items.append(item)

            logger.info(f"SystemSlimmer: scan completed, items={len(items)}")
        except Exception as e:
            logger.error(f"SystemSlimmer: scan failed: {e}")
            items = []
        return items

    def _find_dead_code(self, code_data: Dict[str, Any]) -> List[RedundancyItem]:
        """查找死代码"""
        logger.debug("SystemSlimmer: finding dead code")
        try:
            items: List[RedundancyItem] = []
            dead_code_entries = code_data.get("dead_code", [])
            for entry in dead_code_entries:
                item = RedundancyItem(
                    redundancy_type=RedundancyType.DEAD_CODE,
                    location=entry.get("location", ""),
                    description=entry.get("description", "未使用的代码"),
                    size_estimate=entry.get("size_estimate", 0.0),
                    action=CleanupAction.REMOVE,
                )
                items.append(item)
            logger.debug(f"SystemSlimmer: found {len(items)} dead code items")
        except Exception as e:
            logger.error(f"SystemSlimmer: _find_dead_code failed: {e}")
            items = []
        return items

    def _find_unused_imports(self, code_data: Dict[str, Any]) -> List[RedundancyItem]:
        """查找未使用的导入"""
        logger.debug("SystemSlimmer: finding unused imports")
        try:
            items: List[RedundancyItem] = []
            unused_imports = code_data.get("unused_imports", [])
            for entry in unused_imports:
                item = RedundancyItem(
                    redundancy_type=RedundancyType.UNUSED_IMPORT,
                    location=entry.get("location", ""),
                    description=entry.get("description", "未使用的导入"),
                    size_estimate=entry.get("size_estimate", 0.0),
                    action=CleanupAction.REMOVE,
                )
                items.append(item)
            logger.debug(f"SystemSlimmer: found {len(items)} unused import items")
        except Exception as e:
            logger.error(f"SystemSlimmer: _find_unused_imports failed: {e}")
            items = []
        return items

    def _find_duplicates(self, code_data: Dict[str, Any]) -> List[RedundancyItem]:
        """查找重复逻辑"""
        logger.debug("SystemSlimmer: finding duplicate logic")
        try:
            items: List[RedundancyItem] = []
            duplicates = code_data.get("duplicates", [])
            for entry in duplicates:
                item = RedundancyItem(
                    redundancy_type=RedundancyType.DUPLICATE_LOGIC,
                    location=entry.get("location", ""),
                    description=entry.get("description", "重复逻辑"),
                    size_estimate=entry.get("size_estimate", 0.0),
                    action=CleanupAction.CONSOLIDATE,
                )
                items.append(item)
            logger.debug(f"SystemSlimmer: found {len(items)} duplicate items")
        except Exception as e:
            logger.error(f"SystemSlimmer: _find_duplicates failed: {e}")
            items = []
        return items

    def _find_orphans(self, code_data: Dict[str, Any]) -> List[RedundancyItem]:
        """查找孤立资源"""
        logger.debug("SystemSlimmer: finding orphan resources")
        try:
            items: List[RedundancyItem] = []
            orphans = code_data.get("orphans", [])
            for entry in orphans:
                item = RedundancyItem(
                    redundancy_type=RedundancyType.ORPHAN_RESOURCE,
                    location=entry.get("location", ""),
                    description=entry.get("description", "孤立资源"),
                    size_estimate=entry.get("size_estimate", 0.0),
                    action=CleanupAction.ARCHIVE,
                )
                items.append(item)
            logger.debug(f"SystemSlimmer: found {len(items)} orphan items")
        except Exception as e:
            logger.error(f"SystemSlimmer: _find_orphans failed: {e}")
            items = []
        return items

    def cleanup(self, items: List[RedundancyItem]) -> SlimResult:
        """执行清理"""
        logger.info(f"SystemSlimmer: cleaning up {len(items)} items")
        try:
            removed_count = 0
            space_saved = 0.0

            for item in items:
                if item.action in (CleanupAction.REMOVE, CleanupAction.ARCHIVE):
                    removed_count += 1
                space_saved += item.size_estimate

            # 计算性能提升（简化模型）
            performance_gain = min(space_saved * 0.01, 50.0)

            result = SlimResult(
                total_items=len(items),
                removed_items=removed_count,
                space_saved=space_saved,
                performance_gain=performance_gain,
                items=items,
            )

            result_id = str(uuid.uuid4())
            self._results[result_id] = result

            logger.info(f"SystemSlimmer: cleanup completed, "
                        f"total={result.total_items}, "
                        f"removed={result.removed_items}, "
                        f"space_saved={result.space_saved}")
        except Exception as e:
            logger.error(f"SystemSlimmer: cleanup failed: {e}")
            result = SlimResult()
        return result

    def generate_report(self, result: SlimResult) -> Dict[str, Any]:
        """生成清理报告"""
        logger.info(f"SystemSlimmer: generating report, "
                    f"total={result.total_items}")
        try:
            # 按冗余类型分组统计
            type_summary: Dict[str, int] = {}
            for item in result.items:
                key = item.redundancy_type.value
                type_summary[key] = type_summary.get(key, 0) + 1

            # 按清理动作分组统计
            action_summary: Dict[str, int] = {}
            for item in result.items:
                key = item.action.value
                action_summary[key] = action_summary.get(key, 0) + 1

            report: Dict[str, Any] = {
                "total_items": result.total_items,
                "removed_items": result.removed_items,
                "space_saved": result.space_saved,
                "performance_gain": result.performance_gain,
                "type_summary": type_summary,
                "action_summary": action_summary,
                "details": [
                    {
                        "item_id": item.item_id,
                        "type": item.redundancy_type.value,
                        "location": item.location,
                        "description": item.description,
                        "size_estimate": item.size_estimate,
                        "action": item.action.value,
                    }
                    for item in result.items
                ],
                "timestamp": time.time(),
            }

            report_id = str(uuid.uuid4())
            self._reports[report_id] = report

            logger.info(f"SystemSlimmer: report generated, "
                        f"report_id={report_id}")
        except Exception as e:
            logger.error(f"SystemSlimmer: generate_report failed: {e}")
            report = {"error": str(e)}
        return report


class SystemSlimService:
    """系统轻量化服务"""

    def __init__(self, slimmer: Optional[SystemSlimmer] = None):
        """初始化系统轻量化服务"""
        self.slimmer = slimmer or SystemSlimmer()
        self._last_result: Optional[SlimResult] = None
        logger.info("SystemSlimService initialized")

    def slim(self, code_data: Dict[str, Any]) -> SlimResult:
        """执行系统轻量化"""
        logger.info("SystemSlimService: slimming system")
        items = self.slimmer.scan(code_data)
        result = self.slimmer.cleanup(items)
        self._last_result = result
        return result

    def get_result(self) -> Optional[SlimResult]:
        """获取轻量化结果"""
        logger.debug("SystemSlimService: getting result")
        return self._last_result

    def get_report(self) -> Dict[str, Any]:
        """获取清理报告"""
        logger.debug("SystemSlimService: getting report")
        if self._last_result is None:
            return {"message": "暂无清理结果"}
        return self.slimmer.generate_report(self._last_result)
