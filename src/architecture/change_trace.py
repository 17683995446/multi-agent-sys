"""
变更记录自动溯源模块

职责：变更记录管理、变更溯源、影响分析、变更历史追踪

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """变更类型"""
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    REFACTOR = "refactor"
    MERGE = "merge"


@dataclass
class ChangeRecord:
    """变更记录"""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_type: ChangeType = ChangeType.MODIFY
    file_path: str = ""
    author: str = ""
    description: str = ""
    timestamp: float = field(default_factory=time.time)
    related_changes: List[str] = field(default_factory=list)

    def __post_init__(self):
        logger.debug(f"ChangeRecord created: id={self.change_id}, "
                     f"type={self.change_type.value}, file={self.file_path}")


class ChangeGraph:
    """变更图"""

    def __init__(self):
        """初始化变更图"""
        self.changes: Dict[str, ChangeRecord] = {}
        self.edges: Dict[str, List[str]] = {}
        logger.info("ChangeGraph initialized")

    def add_change(self, record: ChangeRecord) -> str:
        """添加变更记录到图中"""
        logger.info(f"ChangeGraph: adding change, id={record.change_id}")
        try:
            self.changes[record.change_id] = record
            if record.change_id not in self.edges:
                self.edges[record.change_id] = []

            # 建立关联边
            for related_id in record.related_changes:
                if related_id in self.changes:
                    if related_id not in self.edges:
                        self.edges[related_id] = []
                    self.edges[record.change_id].append(related_id)
                    self.edges[related_id].append(record.change_id)

            logger.info(f"ChangeGraph: change added, id={record.change_id}, "
                        f"edges={len(self.edges.get(record.change_id, []))}")
        except Exception as e:
            logger.error(f"ChangeGraph: add_change failed: {e}")
        return record.change_id

    def get_change(self, change_id: str) -> Optional[ChangeRecord]:
        """获取变更记录"""
        logger.debug(f"ChangeGraph: getting change, id={change_id}")
        record = self.changes.get(change_id)
        if record is None:
            logger.warning(f"ChangeGraph: change_id={change_id} not found")
        return record

    def trace_origin(self, change_id: str) -> List[ChangeRecord]:
        """溯源变更来源"""
        logger.info(f"ChangeGraph: tracing origin for change_id={change_id}")
        visited = set()
        origins = []

        def _trace(cid: str):
            if cid in visited:
                return
            visited.add(cid)
            record = self.changes.get(cid)
            if record is None:
                return
            # 沿着关联边追溯
            for related_id in record.related_changes:
                if related_id not in visited:
                    _trace(related_id)
                    related = self.changes.get(related_id)
                    if related:
                        origins.append(related)

        _trace(change_id)
        logger.info(f"ChangeGraph: traced {len(origins)} origin records")
        return origins

    def trace_impact(self, change_id: str) -> List[ChangeRecord]:
        """追踪变更影响"""
        logger.info(f"ChangeGraph: tracing impact for change_id={change_id}")
        impacted = []
        visited = set()

        def _trace(cid: str):
            if cid in visited:
                return
            visited.add(cid)
            # 查找所有关联到此变更的记录
            for other_id, edges in self.edges.items():
                if cid in edges and other_id not in visited:
                    record = self.changes.get(other_id)
                    if record:
                        impacted.append(record)
                        _trace(other_id)

        _trace(change_id)
        logger.info(f"ChangeGraph: traced {len(impacted)} impacted records")
        return impacted

    def get_history(self, file_path: str = "") -> List[ChangeRecord]:
        """获取变更历史"""
        logger.info(f"ChangeGraph: getting history, file_path={file_path}")
        records = list(self.changes.values())
        if file_path:
            records = [r for r in records if r.file_path == file_path]
        # 按时间排序
        records.sort(key=lambda r: r.timestamp)
        logger.info(f"ChangeGraph: found {len(records)} history records")
        return records


class ChangeTraceService:
    """变更溯源服务"""

    def __init__(self):
        """初始化变更溯源服务"""
        self.graph = ChangeGraph()
        logger.info("ChangeTraceService initialized")

    def record_change(self, change_type: ChangeType, file_path: str,
                      author: str = "", description: str = "",
                      related_changes: Optional[List[str]] = None) -> ChangeRecord:
        """记录变更"""
        logger.info(f"ChangeTraceService: recording change, "
                    f"type={change_type.value}, file={file_path}")
        try:
            record = ChangeRecord(
                change_type=change_type,
                file_path=file_path,
                author=author,
                description=description,
                related_changes=related_changes or [],
            )
            self.graph.add_change(record)
            logger.info(f"ChangeTraceService: change recorded, "
                        f"id={record.change_id}")
        except Exception as e:
            logger.error(f"ChangeTraceService: record_change failed: {e}")
            record = ChangeRecord(
                change_type=change_type,
                file_path=file_path,
                description=f"记录失败: {e}",
            )
        return record

    def trace(self, change_id: str) -> Dict[str, Any]:
        """溯源变更"""
        logger.info(f"ChangeTraceService: tracing change_id={change_id}")
        record = self.graph.get_change(change_id)
        if record is None:
            logger.warning(f"ChangeTraceService: change_id={change_id} not found")
            return {"change": None, "origins": [], "impact": []}

        origins = self.graph.trace_origin(change_id)
        impact = self.graph.trace_impact(change_id)

        result = {
            "change": record,
            "origins": origins,
            "impact": impact,
        }
        logger.info(f"ChangeTraceService: trace completed, "
                    f"origins={len(origins)}, impact={len(impact)}")
        return result

    def get_history(self, file_path: str = "") -> List[ChangeRecord]:
        """获取变更历史"""
        logger.info(f"ChangeTraceService: getting history, "
                    f"file_path={file_path}")
        return self.graph.get_history(file_path)

    def get_impact(self, change_id: str) -> List[ChangeRecord]:
        """获取变更影响"""
        logger.info(f"ChangeTraceService: getting impact for "
                    f"change_id={change_id}")
        return self.graph.trace_impact(change_id)
