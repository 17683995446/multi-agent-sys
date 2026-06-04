"""
阶段97验收测试 - 系统冗余清理、轻量化
"""

import pytest
from src.architecture.system_slim import (
    RedundancyType,
    CleanupAction,
    RedundancyItem,
    SlimResult,
    SystemSlimmer,
    SystemSlimService,
)


class TestRedundancyType:
    """测试冗余类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RedundancyType.DEAD_CODE.value == "dead_code"
        assert RedundancyType.UNUSED_IMPORT.value == "unused_import"
        assert RedundancyType.DUPLICATE_LOGIC.value == "duplicate_logic"
        assert RedundancyType.ORPHAN_RESOURCE.value == "orphan_resource"
        assert RedundancyType.STALE_CONFIG.value == "stale_config"

    def test_all_types(self):
        """测试所有类型"""
        types = list(RedundancyType)
        assert len(types) == 5


class TestCleanupAction:
    """测试清理动作枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert CleanupAction.REMOVE.value == "remove"
        assert CleanupAction.CONSOLIDATE.value == "consolidate"
        assert CleanupAction.REPLACE.value == "replace"
        assert CleanupAction.ARCHIVE.value == "archive"

    def test_all_actions(self):
        """测试所有动作"""
        actions = list(CleanupAction)
        assert len(actions) == 4


class TestRedundancyItem:
    """测试冗余项"""

    def test_default_creation(self):
        """测试默认创建"""
        item = RedundancyItem()
        assert item.item_id != ""
        assert item.redundancy_type == RedundancyType.DEAD_CODE
        assert item.location == ""
        assert item.description == ""
        assert item.size_estimate == 0.0
        assert item.action == CleanupAction.REMOVE

    def test_custom_creation(self):
        """测试自定义创建"""
        item = RedundancyItem(
            redundancy_type=RedundancyType.DUPLICATE_LOGIC,
            location="src/utils.py",
            description="重复的工具函数",
            size_estimate=1024.0,
            action=CleanupAction.CONSOLIDATE,
        )
        assert item.redundancy_type == RedundancyType.DUPLICATE_LOGIC
        assert item.location == "src/utils.py"
        assert item.size_estimate == 1024.0
        assert item.action == CleanupAction.CONSOLIDATE

    def test_item_id_unique(self):
        """测试冗余项ID唯一性"""
        i1 = RedundancyItem()
        i2 = RedundancyItem()
        assert i1.item_id != i2.item_id


class TestSlimResult:
    """测试轻量化结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = SlimResult()
        assert result.total_items == 0
        assert result.removed_items == 0
        assert result.space_saved == 0.0
        assert result.performance_gain == 0.0
        assert result.items == []

    def test_custom_creation(self):
        """测试自定义创建"""
        items = [RedundancyItem(size_estimate=100.0)]
        result = SlimResult(
            total_items=1,
            removed_items=1,
            space_saved=100.0,
            performance_gain=1.0,
            items=items,
        )
        assert result.total_items == 1
        assert result.space_saved == 100.0


class TestSystemSlimmer:
    """测试系统轻量化器"""

    def test_initialization(self):
        """测试初始化"""
        slimmer = SystemSlimmer()
        assert len(slimmer._results) == 0

    def test_scan_empty(self):
        """测试扫描空数据"""
        slimmer = SystemSlimmer()
        items = slimmer.scan({})
        assert items == []

    def test_scan_dead_code(self):
        """测试扫描死代码"""
        slimmer = SystemSlimmer()
        data = {
            "dead_code": [
                {"location": "src/old.py", "description": "废弃代码", "size_estimate": 500.0},
            ],
        }
        items = slimmer.scan(data)
        dead_items = [i for i in items if i.redundancy_type == RedundancyType.DEAD_CODE]
        assert len(dead_items) == 1
        assert dead_items[0].action == CleanupAction.REMOVE

    def test_scan_unused_imports(self):
        """测试扫描未使用导入"""
        slimmer = SystemSlimmer()
        data = {
            "unused_imports": [
                {"location": "src/main.py", "description": "未使用导入", "size_estimate": 50.0},
            ],
        }
        items = slimmer.scan(data)
        import_items = [i for i in items if i.redundancy_type == RedundancyType.UNUSED_IMPORT]
        assert len(import_items) == 1

    def test_scan_duplicates(self):
        """测试扫描重复逻辑"""
        slimmer = SystemSlimmer()
        data = {
            "duplicates": [
                {"location": "src/a.py,src/b.py", "description": "重复函数", "size_estimate": 200.0},
            ],
        }
        items = slimmer.scan(data)
        dup_items = [i for i in items if i.redundancy_type == RedundancyType.DUPLICATE_LOGIC]
        assert len(dup_items) == 1
        assert dup_items[0].action == CleanupAction.CONSOLIDATE

    def test_scan_orphans(self):
        """测试扫描孤立资源"""
        slimmer = SystemSlimmer()
        data = {
            "orphans": [
                {"location": "assets/unused.png", "description": "孤立资源", "size_estimate": 1024.0},
            ],
        }
        items = slimmer.scan(data)
        orphan_items = [i for i in items if i.redundancy_type == RedundancyType.ORPHAN_RESOURCE]
        assert len(orphan_items) == 1
        assert orphan_items[0].action == CleanupAction.ARCHIVE

    def test_scan_stale_configs(self):
        """测试扫描过时配置"""
        slimmer = SystemSlimmer()
        data = {
            "stale_configs": [
                {"location": "config/old.yaml", "description": "过时配置", "size_estimate": 100.0},
            ],
        }
        items = slimmer.scan(data)
        config_items = [i for i in items if i.redundancy_type == RedundancyType.STALE_CONFIG]
        assert len(config_items) == 1
        assert config_items[0].action == CleanupAction.REPLACE

    def test_scan_multiple_types(self):
        """测试扫描多种冗余类型"""
        slimmer = SystemSlimmer()
        data = {
            "dead_code": [{"location": "a.py", "description": "死代码", "size_estimate": 100.0}],
            "unused_imports": [{"location": "b.py", "description": "未使用导入", "size_estimate": 50.0}],
            "duplicates": [{"location": "c.py", "description": "重复逻辑", "size_estimate": 200.0}],
        }
        items = slimmer.scan(data)
        assert len(items) == 3

    def test_cleanup(self):
        """测试执行清理"""
        slimmer = SystemSlimmer()
        items = [
            RedundancyItem(action=CleanupAction.REMOVE, size_estimate=100.0),
            RedundancyItem(action=CleanupAction.CONSOLIDATE, size_estimate=200.0),
            RedundancyItem(action=CleanupAction.ARCHIVE, size_estimate=50.0),
        ]
        result = slimmer.cleanup(items)
        assert result.total_items == 3
        assert result.removed_items == 2  # REMOVE + ARCHIVE
        assert result.space_saved == 350.0

    def test_cleanup_empty(self):
        """测试清理空列表"""
        slimmer = SystemSlimmer()
        result = slimmer.cleanup([])
        assert result.total_items == 0
        assert result.removed_items == 0

    def test_generate_report(self):
        """测试生成清理报告"""
        slimmer = SystemSlimmer()
        items = [
            RedundancyItem(redundancy_type=RedundancyType.DEAD_CODE,
                           action=CleanupAction.REMOVE, size_estimate=100.0),
            RedundancyItem(redundancy_type=RedundancyType.DUPLICATE_LOGIC,
                           action=CleanupAction.CONSOLIDATE, size_estimate=200.0),
        ]
        result = SlimResult(total_items=2, removed_items=1, space_saved=100.0, items=items)
        report = slimmer.generate_report(result)
        assert "total_items" in report
        assert "type_summary" in report
        assert "action_summary" in report
        assert "details" in report
        assert report["total_items"] == 2


class TestSystemSlimService:
    """测试系统轻量化服务"""

    def test_initialization(self):
        """测试初始化"""
        service = SystemSlimService()
        assert service.slimmer is not None

    def test_initialization_with_slimmer(self):
        """测试使用自定义轻量化器初始化"""
        slimmer = SystemSlimmer()
        service = SystemSlimService(slimmer=slimmer)
        assert service.slimmer is slimmer

    def test_slim(self):
        """测试执行轻量化"""
        service = SystemSlimService()
        data = {
            "dead_code": [{"location": "a.py", "description": "死代码", "size_estimate": 100.0}],
        }
        result = service.slim(data)
        assert result.total_items >= 1

    def test_get_result(self):
        """测试获取轻量化结果"""
        service = SystemSlimService()
        data = {
            "dead_code": [{"location": "a.py", "description": "死代码", "size_estimate": 100.0}],
        }
        service.slim(data)
        result = service.get_result()
        assert result is not None
        assert result.total_items >= 1

    def test_get_result_before_slim(self):
        """测试轻量化前获取结果"""
        service = SystemSlimService()
        result = service.get_result()
        assert result is None

    def test_get_report(self):
        """测试获取清理报告"""
        service = SystemSlimService()
        data = {
            "dead_code": [{"location": "a.py", "description": "死代码", "size_estimate": 100.0}],
        }
        service.slim(data)
        report = service.get_report()
        assert "total_items" in report

    def test_get_report_before_slim(self):
        """测试轻量化前获取报告"""
        service = SystemSlimService()
        report = service.get_report()
        assert "message" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
