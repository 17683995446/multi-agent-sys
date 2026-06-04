"""
接口文档自动同步更新模块

职责：文档变更检测、文档同步、冲突解决、同步状态管理

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """同步状态"""
    IN_SYNC = "in_sync"
    OUTDATED = "outdated"
    CONFLICT = "conflict"
    ERROR = "error"


@dataclass
class DocChange:
    """文档变更记录"""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_type: str = ""
    change_type: str = ""
    description: str = ""
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"DocChange created: id={self.change_id}, "
                     f"doc_type={self.doc_type}, change_type={self.change_type}")


@dataclass
class SyncResult:
    """同步结果"""
    total_docs: int = 0
    synced: int = 0
    outdated: int = 0
    conflicts: int = 0
    errors: int = 0
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"SyncResult created: id={self.result_id}, "
                     f"total={self.total_docs}, synced={self.synced}")


class DocSynchronizer:
    """文档同步器"""

    def __init__(self):
        """初始化文档同步器"""
        self.doc_status: Dict[str, SyncStatus] = {}
        self.changes: List[DocChange] = []
        self.conflict_resolutions: Dict[str, str] = {}
        logger.info("DocSynchronizer initialized")

    def detect_changes(self, doc_type: str = "") -> List[DocChange]:
        """检测文档变更"""
        logger.info(f"DocSynchronizer: detecting changes, doc_type={doc_type}")
        changes = []
        try:
            # 模拟变更检测
            for doc_id, status in self.doc_status.items():
                if status == SyncStatus.OUTDATED:
                    change = DocChange(
                        doc_type=doc_type or "api",
                        change_type="update",
                        description=f"文档已过时: {doc_id}",
                    )
                    changes.append(change)
                elif status == SyncStatus.CONFLICT:
                    change = DocChange(
                        doc_type=doc_type or "api",
                        change_type="conflict",
                        description=f"文档存在冲突: {doc_id}",
                    )
                    changes.append(change)
            self.changes.extend(changes)
            logger.info(f"DocSynchronizer: detected {len(changes)} changes")
        except Exception as e:
            logger.error(f"DocSynchronizer: detect_changes failed: {e}")
        return changes

    def sync_doc(self, doc_id: str) -> SyncStatus:
        """同步单个文档"""
        logger.info(f"DocSynchronizer: syncing doc_id={doc_id}")
        try:
            status = self.doc_status.get(doc_id, SyncStatus.IN_SYNC)
            if status == SyncStatus.IN_SYNC:
                logger.debug(f"DocSynchronizer: doc_id={doc_id} already in sync")
                return SyncStatus.IN_SYNC
            elif status == SyncStatus.OUTDATED:
                self.doc_status[doc_id] = SyncStatus.IN_SYNC
                logger.info(f"DocSynchronizer: doc_id={doc_id} synced")
                return SyncStatus.IN_SYNC
            elif status == SyncStatus.CONFLICT:
                if doc_id in self.conflict_resolutions:
                    self.doc_status[doc_id] = SyncStatus.IN_SYNC
                    logger.info(f"DocSynchronizer: doc_id={doc_id} conflict resolved and synced")
                    return SyncStatus.IN_SYNC
                else:
                    logger.warning(f"DocSynchronizer: doc_id={doc_id} has unresolved conflict")
                    return SyncStatus.CONFLICT
            elif status == SyncStatus.ERROR:
                logger.error(f"DocSynchronizer: doc_id={doc_id} has error, cannot sync")
                return SyncStatus.ERROR
        except Exception as e:
            logger.error(f"DocSynchronizer: sync_doc failed: {e}")
            self.doc_status[doc_id] = SyncStatus.ERROR
            return SyncStatus.ERROR
        return status

    def resolve_conflict(self, doc_id: str, resolution: str = "auto") -> bool:
        """解决文档冲突"""
        logger.info(f"DocSynchronizer: resolving conflict for doc_id={doc_id}, "
                    f"resolution={resolution}")
        status = self.doc_status.get(doc_id)
        if status != SyncStatus.CONFLICT:
            logger.warning(f"DocSynchronizer: doc_id={doc_id} is not in conflict, "
                           f"status={status.value if status else 'unknown'}")
            return False

        try:
            self.conflict_resolutions[doc_id] = resolution
            self.doc_status[doc_id] = SyncStatus.IN_SYNC
            logger.info(f"DocSynchronizer: conflict resolved for doc_id={doc_id}")
        except Exception as e:
            logger.error(f"DocSynchronizer: resolve_conflict failed: {e}")
            return False
        return True

    def get_sync_status(self, doc_id: str) -> SyncStatus:
        """获取文档同步状态"""
        logger.debug(f"DocSynchronizer: getting sync status for doc_id={doc_id}")
        return self.doc_status.get(doc_id, SyncStatus.IN_SYNC)


class DocSyncService:
    """文档同步服务"""

    def __init__(self):
        """初始化文档同步服务"""
        self.synchronizer = DocSynchronizer()
        self.sync_history: List[SyncResult] = []
        logger.info("DocSyncService initialized")

    def sync_all(self, doc_ids: List[str]) -> SyncResult:
        """同步所有文档"""
        logger.info(f"DocSyncService: syncing {len(doc_ids)} documents")
        result = SyncResult(total_docs=len(doc_ids))
        try:
            for doc_id in doc_ids:
                status = self.synchronizer.sync_doc(doc_id)
                if status == SyncStatus.IN_SYNC:
                    result.synced += 1
                elif status == SyncStatus.OUTDATED:
                    result.outdated += 1
                elif status == SyncStatus.CONFLICT:
                    result.conflicts += 1
                elif status == SyncStatus.ERROR:
                    result.errors += 1

            self.sync_history.append(result)
            logger.info(f"DocSyncService: sync completed, "
                        f"synced={result.synced}, conflicts={result.conflicts}")
        except Exception as e:
            logger.error(f"DocSyncService: sync_all failed: {e}")
            result.errors = len(doc_ids)
        return result

    def get_status(self, doc_id: str) -> SyncStatus:
        """获取文档同步状态"""
        logger.debug(f"DocSyncService: getting status for doc_id={doc_id}")
        return self.synchronizer.get_sync_status(doc_id)

    def get_changes(self, doc_type: str = "") -> List[DocChange]:
        """获取文档变更列表"""
        logger.debug(f"DocSyncService: getting changes, doc_type={doc_type}")
        changes = self.synchronizer.changes
        if doc_type:
            changes = [c for c in changes if c.doc_type == doc_type]
        return changes
