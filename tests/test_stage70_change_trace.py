"""
阶段70验收测试：变更记录自动溯源
"""

import pytest
from src.architecture.change_trace import (
    ChangeType,
    ChangeRecord,
    ChangeGraph,
    ChangeTraceService,
)


class TestChangeType:
    """测试变更类型枚举"""

    def test_type_values(self):
        """测试变更类型枚举值"""
        assert ChangeType.ADD.value == "add"
        assert ChangeType.MODIFY.value == "modify"
        assert ChangeType.DELETE.value == "delete"
        assert ChangeType.REFACTOR.value == "refactor"
        assert ChangeType.MERGE.value == "merge"

    def test_all_types(self):
        """测试所有类型"""
        types = list(ChangeType)
        assert len(types) == 5


class TestChangeRecord:
    """测试变更记录"""

    def test_default_creation(self):
        """测试默认创建"""
        record = ChangeRecord()
        assert record.change_id != ""
        assert record.change_type == ChangeType.MODIFY
        assert record.file_path == ""
        assert record.author == ""
        assert record.description == ""
        assert record.timestamp > 0
        assert record.related_changes == []

    def test_custom_creation(self):
        """测试自定义创建"""
        record = ChangeRecord(
            change_type=ChangeType.ADD,
            file_path="src/main.py",
            author="developer",
            description="新增主模块",
            related_changes=["change-001"],
        )
        assert record.change_type == ChangeType.ADD
        assert record.file_path == "src/main.py"
        assert record.author == "developer"
        assert record.description == "新增主模块"
        assert len(record.related_changes) == 1

    def test_change_id_unique(self):
        """测试变更ID唯一性"""
        r1 = ChangeRecord()
        r2 = ChangeRecord()
        assert r1.change_id != r2.change_id


class TestChangeGraph:
    """测试变更图"""

    def test_initialization(self):
        """测试初始化"""
        graph = ChangeGraph()
        assert len(graph.changes) == 0
        assert len(graph.edges) == 0

    def test_add_change(self):
        """测试添加变更"""
        graph = ChangeGraph()
        record = ChangeRecord(
            change_type=ChangeType.ADD,
            file_path="src/main.py",
            description="新增文件",
        )
        change_id = graph.add_change(record)
        assert change_id in graph.changes
        assert graph.changes[change_id].file_path == "src/main.py"

    def test_add_change_with_relations(self):
        """测试添加带关联的变更"""
        graph = ChangeGraph()
        r1 = ChangeRecord(change_type=ChangeType.ADD, file_path="a.py")
        graph.add_change(r1)
        r2 = ChangeRecord(
            change_type=ChangeType.MODIFY,
            file_path="b.py",
            related_changes=[r1.change_id],
        )
        graph.add_change(r2)
        assert r1.change_id in graph.edges.get(r2.change_id, [])
        assert r2.change_id in graph.edges.get(r1.change_id, [])

    def test_get_change(self):
        """测试获取变更"""
        graph = ChangeGraph()
        record = ChangeRecord(file_path="test.py")
        graph.add_change(record)
        retrieved = graph.get_change(record.change_id)
        assert retrieved is not None
        assert retrieved.file_path == "test.py"

    def test_get_change_not_found(self):
        """测试获取不存在的变更"""
        graph = ChangeGraph()
        result = graph.get_change("nonexistent")
        assert result is None

    def test_trace_origin(self):
        """测试溯源变更来源"""
        graph = ChangeGraph()
        r1 = ChangeRecord(change_type=ChangeType.ADD, file_path="a.py",
                          description="初始添加")
        graph.add_change(r1)
        r2 = ChangeRecord(
            change_type=ChangeType.MODIFY,
            file_path="b.py",
            description="修改文件",
            related_changes=[r1.change_id],
        )
        graph.add_change(r2)
        origins = graph.trace_origin(r2.change_id)
        assert len(origins) >= 1
        assert any(o.change_id == r1.change_id for o in origins)

    def test_trace_origin_no_relations(self):
        """测试溯源无关联变更"""
        graph = ChangeGraph()
        record = ChangeRecord(file_path="standalone.py")
        graph.add_change(record)
        origins = graph.trace_origin(record.change_id)
        assert len(origins) == 0

    def test_trace_impact(self):
        """测试追踪变更影响"""
        graph = ChangeGraph()
        r1 = ChangeRecord(change_type=ChangeType.ADD, file_path="a.py")
        graph.add_change(r1)
        r2 = ChangeRecord(
            change_type=ChangeType.MODIFY,
            file_path="b.py",
            related_changes=[r1.change_id],
        )
        graph.add_change(r2)
        impact = graph.trace_impact(r1.change_id)
        assert len(impact) >= 1
        assert any(i.change_id == r2.change_id for i in impact)

    def test_trace_impact_no_impact(self):
        """测试追踪无影响变更"""
        graph = ChangeGraph()
        record = ChangeRecord(file_path="isolated.py")
        graph.add_change(record)
        impact = graph.trace_impact(record.change_id)
        assert len(impact) == 0

    def test_get_history(self):
        """测试获取变更历史"""
        graph = ChangeGraph()
        r1 = ChangeRecord(file_path="main.py", description="第一次修改")
        graph.add_change(r1)
        r2 = ChangeRecord(file_path="main.py", description="第二次修改")
        graph.add_change(r2)
        history = graph.get_history("main.py")
        assert len(history) == 2

    def test_get_history_all(self):
        """测试获取所有变更历史"""
        graph = ChangeGraph()
        graph.add_change(ChangeRecord(file_path="a.py"))
        graph.add_change(ChangeRecord(file_path="b.py"))
        history = graph.get_history()
        assert len(history) == 2

    def test_get_history_sorted_by_time(self):
        """测试历史按时间排序"""
        graph = ChangeGraph()
        r1 = ChangeRecord(file_path="main.py", timestamp=100.0)
        graph.add_change(r1)
        r2 = ChangeRecord(file_path="main.py", timestamp=200.0)
        graph.add_change(r2)
        history = graph.get_history("main.py")
        assert history[0].timestamp <= history[1].timestamp

    def test_get_history_no_match(self):
        """测试获取无匹配文件的历史"""
        graph = ChangeGraph()
        graph.add_change(ChangeRecord(file_path="a.py"))
        history = graph.get_history("nonexistent.py")
        assert len(history) == 0


class TestChangeTraceService:
    """测试变更溯源服务"""

    def test_initialization(self):
        """测试初始化"""
        service = ChangeTraceService()
        assert service.graph is not None

    def test_record_change(self):
        """测试记录变更"""
        service = ChangeTraceService()
        record = service.record_change(
            change_type=ChangeType.ADD,
            file_path="src/new_module.py",
            author="dev1",
            description="新增模块",
        )
        assert record.change_type == ChangeType.ADD
        assert record.file_path == "src/new_module.py"
        assert record.author == "dev1"
        assert record.change_id in service.graph.changes

    def test_record_change_with_relations(self):
        """测试记录带关联的变更"""
        service = ChangeTraceService()
        r1 = service.record_change(ChangeType.ADD, "a.py")
        r2 = service.record_change(
            ChangeType.MODIFY, "b.py",
            related_changes=[r1.change_id],
        )
        assert len(r2.related_changes) == 1

    def test_trace(self):
        """测试溯源变更"""
        service = ChangeTraceService()
        r1 = service.record_change(ChangeType.ADD, "base.py", description="基础模块")
        r2 = service.record_change(
            ChangeType.MODIFY, "derived.py",
            description="派生修改",
            related_changes=[r1.change_id],
        )
        result = service.trace(r2.change_id)
        assert result["change"] is not None
        assert result["change"].change_id == r2.change_id
        assert len(result["origins"]) >= 1
        assert len(result["impact"]) >= 0

    def test_trace_not_found(self):
        """测试溯源不存在的变更"""
        service = ChangeTraceService()
        result = service.trace("nonexistent")
        assert result["change"] is None
        assert result["origins"] == []
        assert result["impact"] == []

    def test_get_history(self):
        """测试获取变更历史"""
        service = ChangeTraceService()
        service.record_change(ChangeType.ADD, "module.py", description="添加")
        service.record_change(ChangeType.MODIFY, "module.py", description="修改")
        history = service.get_history("module.py")
        assert len(history) == 2

    def test_get_history_all(self):
        """测试获取所有历史"""
        service = ChangeTraceService()
        service.record_change(ChangeType.ADD, "a.py")
        service.record_change(ChangeType.MODIFY, "b.py")
        history = service.get_history()
        assert len(history) == 2

    def test_get_impact(self):
        """测试获取变更影响"""
        service = ChangeTraceService()
        r1 = service.record_change(ChangeType.ADD, "core.py")
        service.record_change(
            ChangeType.MODIFY, "app.py",
            related_changes=[r1.change_id],
        )
        impact = service.get_impact(r1.change_id)
        assert len(impact) >= 1

    def test_full_trace_workflow(self):
        """测试完整溯源工作流"""
        service = ChangeTraceService()
        # 1. 记录基础变更
        base = service.record_change(
            ChangeType.ADD, "base.py",
            author="dev1", description="基础模块",
        )
        # 2. 记录派生变更
        derived = service.record_change(
            ChangeType.MODIFY, "derived.py",
            author="dev2", description="派生修改",
            related_changes=[base.change_id],
        )
        # 3. 记录更多变更
        extended = service.record_change(
            ChangeType.REFACTOR, "extended.py",
            author="dev3", description="扩展重构",
            related_changes=[derived.change_id],
        )
        # 4. 溯源
        result = service.trace(extended.change_id)
        assert result["change"].change_id == extended.change_id
        # 5. 影响分析
        impact = service.get_impact(base.change_id)
        assert len(impact) >= 1
        # 6. 历史查询
        history = service.get_history()
        assert len(history) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
