"""
阶段69验收测试：接口文档自动同步更新
"""

import pytest
from src.architecture.doc_sync import (
    SyncStatus,
    DocChange,
    SyncResult,
    DocSynchronizer,
    DocSyncService,
)


class TestSyncStatus:
    """测试同步状态枚举"""

    def test_status_values(self):
        """测试同步状态枚举值"""
        assert SyncStatus.IN_SYNC.value == "in_sync"
        assert SyncStatus.OUTDATED.value == "outdated"
        assert SyncStatus.CONFLICT.value == "conflict"
        assert SyncStatus.ERROR.value == "error"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(SyncStatus)
        assert len(statuses) == 4


class TestDocChange:
    """测试文档变更记录"""

    def test_default_creation(self):
        """测试默认创建"""
        change = DocChange()
        assert change.change_id != ""
        assert change.doc_type == ""
        assert change.change_type == ""
        assert change.description == ""
        assert change.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        change = DocChange(
            doc_type="api",
            change_type="update",
            description="API接口变更",
        )
        assert change.doc_type == "api"
        assert change.change_type == "update"
        assert change.description == "API接口变更"

    def test_change_id_unique(self):
        """测试变更ID唯一性"""
        c1 = DocChange()
        c2 = DocChange()
        assert c1.change_id != c2.change_id


class TestSyncResult:
    """测试同步结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = SyncResult()
        assert result.total_docs == 0
        assert result.synced == 0
        assert result.outdated == 0
        assert result.conflicts == 0
        assert result.errors == 0
        assert result.result_id != ""

    def test_custom_creation(self):
        """测试自定义创建"""
        result = SyncResult(
            total_docs=10,
            synced=8,
            outdated=1,
            conflicts=1,
            errors=0,
        )
        assert result.total_docs == 10
        assert result.synced == 8
        assert result.outdated == 1
        assert result.conflicts == 1


class TestDocSynchronizer:
    """测试文档同步器"""

    def test_initialization(self):
        """测试初始化"""
        sync = DocSynchronizer()
        assert len(sync.doc_status) == 0
        assert len(sync.changes) == 0
        assert len(sync.conflict_resolutions) == 0

    def test_detect_changes_outdated(self):
        """测试检测过时文档变更"""
        sync = DocSynchronizer()
        sync.doc_status["doc1"] = SyncStatus.OUTDATED
        changes = sync.detect_changes()
        assert len(changes) == 1
        assert changes[0].change_type == "update"
        assert "doc1" in changes[0].description

    def test_detect_changes_conflict(self):
        """测试检测冲突文档变更"""
        sync = DocSynchronizer()
        sync.doc_status["doc2"] = SyncStatus.CONFLICT
        changes = sync.detect_changes()
        assert len(changes) == 1
        assert changes[0].change_type == "conflict"

    def test_detect_changes_with_doc_type(self):
        """测试按文档类型检测变更"""
        sync = DocSynchronizer()
        sync.doc_status["doc3"] = SyncStatus.OUTDATED
        changes = sync.detect_changes(doc_type="api")
        assert len(changes) == 1
        assert changes[0].doc_type == "api"

    def test_detect_changes_no_changes(self):
        """测试无变更时检测"""
        sync = DocSynchronizer()
        sync.doc_status["doc4"] = SyncStatus.IN_SYNC
        changes = sync.detect_changes()
        assert len(changes) == 0

    def test_sync_doc_in_sync(self):
        """测试同步已同步文档"""
        sync = DocSynchronizer()
        sync.doc_status["doc1"] = SyncStatus.IN_SYNC
        status = sync.sync_doc("doc1")
        assert status == SyncStatus.IN_SYNC

    def test_sync_doc_outdated(self):
        """测试同步过时文档"""
        sync = DocSynchronizer()
        sync.doc_status["doc2"] = SyncStatus.OUTDATED
        status = sync.sync_doc("doc2")
        assert status == SyncStatus.IN_SYNC
        assert sync.doc_status["doc2"] == SyncStatus.IN_SYNC

    def test_sync_doc_conflict_unresolved(self):
        """测试同步未解决冲突的文档"""
        sync = DocSynchronizer()
        sync.doc_status["doc3"] = SyncStatus.CONFLICT
        status = sync.sync_doc("doc3")
        assert status == SyncStatus.CONFLICT

    def test_sync_doc_conflict_resolved(self):
        """测试同步已解决冲突的文档"""
        sync = DocSynchronizer()
        sync.doc_status["doc4"] = SyncStatus.CONFLICT
        sync.conflict_resolutions["doc4"] = "auto"
        status = sync.sync_doc("doc4")
        assert status == SyncStatus.IN_SYNC

    def test_sync_doc_error(self):
        """测试同步错误状态文档"""
        sync = DocSynchronizer()
        sync.doc_status["doc5"] = SyncStatus.ERROR
        status = sync.sync_doc("doc5")
        assert status == SyncStatus.ERROR

    def test_sync_doc_unknown(self):
        """测试同步未知文档"""
        sync = DocSynchronizer()
        status = sync.sync_doc("unknown_doc")
        assert status == SyncStatus.IN_SYNC

    def test_resolve_conflict_success(self):
        """测试解决冲突成功"""
        sync = DocSynchronizer()
        sync.doc_status["doc6"] = SyncStatus.CONFLICT
        result = sync.resolve_conflict("doc6", "manual")
        assert result is True
        assert sync.doc_status["doc6"] == SyncStatus.IN_SYNC
        assert sync.conflict_resolutions["doc6"] == "manual"

    def test_resolve_conflict_not_in_conflict(self):
        """测试解决非冲突文档"""
        sync = DocSynchronizer()
        sync.doc_status["doc7"] = SyncStatus.IN_SYNC
        result = sync.resolve_conflict("doc7")
        assert result is False

    def test_resolve_conflict_unknown_doc(self):
        """测试解决未知文档冲突"""
        sync = DocSynchronizer()
        result = sync.resolve_conflict("unknown_doc")
        assert result is False

    def test_get_sync_status(self):
        """测试获取同步状态"""
        sync = DocSynchronizer()
        sync.doc_status["doc8"] = SyncStatus.OUTDATED
        assert sync.get_sync_status("doc8") == SyncStatus.OUTDATED

    def test_get_sync_status_unknown(self):
        """测试获取未知文档同步状态"""
        sync = DocSynchronizer()
        assert sync.get_sync_status("unknown") == SyncStatus.IN_SYNC


class TestDocSyncService:
    """测试文档同步服务"""

    def test_initialization(self):
        """测试初始化"""
        service = DocSyncService()
        assert service.synchronizer is not None
        assert len(service.sync_history) == 0

    def test_sync_all(self):
        """测试同步所有文档"""
        service = DocSyncService()
        service.synchronizer.doc_status["doc1"] = SyncStatus.OUTDATED
        service.synchronizer.doc_status["doc2"] = SyncStatus.IN_SYNC
        result = service.sync_all(["doc1", "doc2"])
        assert result.total_docs == 2
        assert result.synced == 2
        assert len(service.sync_history) == 1

    def test_sync_all_with_conflicts(self):
        """测试同步含冲突的文档"""
        service = DocSyncService()
        service.synchronizer.doc_status["doc1"] = SyncStatus.OUTDATED
        service.synchronizer.doc_status["doc2"] = SyncStatus.CONFLICT
        result = service.sync_all(["doc1", "doc2"])
        assert result.synced >= 1
        assert result.conflicts >= 1

    def test_sync_all_with_errors(self):
        """测试同步含错误的文档"""
        service = DocSyncService()
        service.synchronizer.doc_status["doc1"] = SyncStatus.ERROR
        result = service.sync_all(["doc1"])
        assert result.errors == 1

    def test_get_status(self):
        """测试获取状态"""
        service = DocSyncService()
        service.synchronizer.doc_status["doc1"] = SyncStatus.OUTDATED
        assert service.get_status("doc1") == SyncStatus.OUTDATED

    def test_get_changes(self):
        """测试获取变更列表"""
        service = DocSyncService()
        service.synchronizer.doc_status["doc1"] = SyncStatus.OUTDATED
        service.synchronizer.detect_changes(doc_type="api")
        changes = service.get_changes(doc_type="api")
        assert len(changes) > 0

    def test_full_sync_workflow(self):
        """测试完整同步工作流"""
        service = DocSyncService()
        # 1. 设置文档状态
        service.synchronizer.doc_status["api_doc1"] = SyncStatus.OUTDATED
        service.synchronizer.doc_status["api_doc2"] = SyncStatus.CONFLICT
        service.synchronizer.doc_status["api_doc3"] = SyncStatus.IN_SYNC
        # 2. 检测变更
        changes = service.synchronizer.detect_changes(doc_type="api")
        assert len(changes) == 2
        # 3. 解决冲突
        service.synchronizer.resolve_conflict("api_doc2", "auto")
        # 4. 同步所有
        result = service.sync_all(["api_doc1", "api_doc2", "api_doc3"])
        assert result.synced == 3
        assert result.conflicts == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
