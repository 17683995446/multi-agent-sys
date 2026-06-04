"""
阶段84验收测试 - 自动生成重构对比报告
"""

import pytest
from src.architecture.refactor_diff import (
    DiffType,
    DiffEntry,
    RefactorDiffReport,
    RefactorDiffGenerator,
    RefactorDiffService,
)


class TestDiffType:
    """测试差异类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert DiffType.ADDED.value == "added"
        assert DiffType.REMOVED.value == "removed"
        assert DiffType.MODIFIED.value == "modified"
        assert DiffType.MOVED.value == "moved"
        assert DiffType.RENAMED.value == "renamed"

    def test_all_types(self):
        """测试所有差异类型"""
        types = list(DiffType)
        assert len(types) == 5


class TestDiffEntry:
    """测试差异条目"""

    def test_default_creation(self):
        """测试默认创建"""
        entry = DiffEntry()
        assert entry.entry_id != ""
        assert entry.diff_type == DiffType.MODIFIED
        assert entry.file_path == ""
        assert entry.before == ""
        assert entry.after == ""
        assert entry.description == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        entry = DiffEntry(
            diff_type=DiffType.ADDED,
            file_path="src/new_module.py",
            after="new content",
            description="新增模块文件",
        )
        assert entry.diff_type == DiffType.ADDED
        assert entry.file_path == "src/new_module.py"
        assert entry.after == "new content"
        assert entry.description == "新增模块文件"

    def test_unique_ids(self):
        """测试唯一ID"""
        entry1 = DiffEntry()
        entry2 = DiffEntry()
        assert entry1.entry_id != entry2.entry_id


class TestRefactorDiffReport:
    """测试重构差异报告"""

    def test_default_creation(self):
        """测试默认创建"""
        report = RefactorDiffReport()
        assert report.report_id != ""
        assert report.summary == ""
        assert report.entries == []
        assert report.statistics == {}
        assert report.recommendations == []

    def test_custom_creation(self):
        """测试自定义创建"""
        report = RefactorDiffReport(
            summary="重构完成",
            entries=[DiffEntry()],
            statistics={"total_changes": 1},
            recommendations=["建议1"],
        )
        assert report.summary == "重构完成"
        assert len(report.entries) == 1
        assert report.statistics["total_changes"] == 1
        assert len(report.recommendations) == 1


class TestRefactorDiffGenerator:
    """测试重构差异生成器"""

    def test_initialization(self):
        """测试初始化"""
        generator = RefactorDiffGenerator()
        assert generator._reports == []

    def test_generate_diff_no_changes(self):
        """测试无差异"""
        generator = RefactorDiffGenerator()
        before = {"files": {"a.py": "content"}, "modules": ["mod1"],
                  "classes": ["Class1"], "functions": ["func1"]}
        after = {"files": {"a.py": "content"}, "modules": ["mod1"],
                 "classes": ["Class1"], "functions": ["func1"]}
        entries = generator.generate_diff(before, after)
        assert len(entries) == 0

    def test_generate_diff_added_file(self):
        """测试新增文件差异"""
        generator = RefactorDiffGenerator()
        before = {"files": {"a.py": "old"}, "modules": [], "classes": [], "functions": []}
        after = {"files": {"a.py": "old", "b.py": "new"}, "modules": [], "classes": [], "functions": []}
        entries = generator.generate_diff(before, after)
        added = [e for e in entries if e.diff_type == DiffType.ADDED and "新增文件" in e.description]
        assert len(added) == 1
        assert added[0].file_path == "b.py"

    def test_generate_diff_removed_file(self):
        """测试删除文件差异"""
        generator = RefactorDiffGenerator()
        before = {"files": {"a.py": "old", "b.py": "new"}, "modules": [], "classes": [], "functions": []}
        after = {"files": {"a.py": "old"}, "modules": [], "classes": [], "functions": []}
        entries = generator.generate_diff(before, after)
        removed = [e for e in entries if e.diff_type == DiffType.REMOVED and "删除文件" in e.description]
        assert len(removed) == 1
        assert removed[0].file_path == "b.py"

    def test_generate_diff_modified_file(self):
        """测试修改文件差异"""
        generator = RefactorDiffGenerator()
        before = {"files": {"a.py": "old content"}, "modules": [], "classes": [], "functions": []}
        after = {"files": {"a.py": "new content"}, "modules": [], "classes": [], "functions": []}
        entries = generator.generate_diff(before, after)
        modified = [e for e in entries if e.diff_type == DiffType.MODIFIED and "修改文件" in e.description]
        assert len(modified) == 1
        assert modified[0].before == "old content"
        assert modified[0].after == "new content"

    def test_compare_structures_added_module(self):
        """测试新增模块"""
        generator = RefactorDiffGenerator()
        before = {"files": {}, "modules": ["mod1"]}
        after = {"files": {}, "modules": ["mod1", "mod2"]}
        entries = generator._compare_structures(before, after)
        added = [e for e in entries if "新增模块" in e.description]
        assert len(added) == 1

    def test_compare_structures_removed_module(self):
        """测试删除模块"""
        generator = RefactorDiffGenerator()
        before = {"files": {}, "modules": ["mod1", "mod2"]}
        after = {"files": {}, "modules": ["mod1"]}
        entries = generator._compare_structures(before, after)
        removed = [e for e in entries if "删除模块" in e.description]
        assert len(removed) == 1

    def test_compare_code_added_class(self):
        """测试新增类"""
        generator = RefactorDiffGenerator()
        before = {"classes": ["Class1"], "functions": []}
        after = {"classes": ["Class1", "Class2"], "functions": []}
        entries = generator._compare_code(before, after)
        added = [e for e in entries if "新增类" in e.description]
        assert len(added) == 1

    def test_compare_code_removed_class(self):
        """测试删除类"""
        generator = RefactorDiffGenerator()
        before = {"classes": ["Class1", "Class2"], "functions": []}
        after = {"classes": ["Class1"], "functions": []}
        entries = generator._compare_code(before, after)
        removed = [e for e in entries if "删除类" in e.description]
        assert len(removed) == 1

    def test_compare_code_added_function(self):
        """测试新增函数"""
        generator = RefactorDiffGenerator()
        before = {"classes": [], "functions": ["func1"]}
        after = {"classes": [], "functions": ["func1", "func2"]}
        entries = generator._compare_code(before, after)
        added = [e for e in entries if "新增函数" in e.description]
        assert len(added) == 1

    def test_compare_code_moved(self):
        """测试移动"""
        generator = RefactorDiffGenerator()
        before = {
            "classes": [],
            "functions": [],
            "moved": [{"path": "a.py", "from": "src/old", "to": "src/new"}],
        }
        after = {"classes": [], "functions": []}
        entries = generator._compare_code(before, after)
        moved = [e for e in entries if e.diff_type == DiffType.MOVED]
        assert len(moved) == 1

    def test_compare_code_renamed(self):
        """测试重命名"""
        generator = RefactorDiffGenerator()
        before = {
            "classes": [],
            "functions": [],
            "renamed": [{"path": "a.py", "old_name": "OldClass", "new_name": "NewClass"}],
        }
        after = {"classes": [], "functions": []}
        entries = generator._compare_code(before, after)
        renamed = [e for e in entries if e.diff_type == DiffType.RENAMED]
        assert len(renamed) == 1

    def test_calculate_statistics(self):
        """测试计算统计信息"""
        generator = RefactorDiffGenerator()
        entries = [
            DiffEntry(diff_type=DiffType.ADDED, file_path="a.py"),
            DiffEntry(diff_type=DiffType.ADDED, file_path="b.py"),
            DiffEntry(diff_type=DiffType.REMOVED, file_path="c.py"),
            DiffEntry(diff_type=DiffType.MODIFIED, file_path="d.py"),
        ]
        stats = generator._calculate_statistics(entries)
        assert stats["total_changes"] == 4
        assert stats["added_count"] == 2
        assert stats["removed_count"] == 1
        assert stats["modified_count"] == 1

    def test_generate_report(self):
        """测试生成报告"""
        generator = RefactorDiffGenerator()
        before = {"files": {"a.py": "old"}, "modules": [], "classes": [], "functions": []}
        after = {"files": {"a.py": "new", "b.py": "added"}, "modules": [], "classes": [], "functions": []}
        report = generator.generate_report(before, after)
        assert isinstance(report, RefactorDiffReport)
        assert len(report.entries) > 0
        assert "statistics" in report.statistics or report.statistics != {}
        assert report.summary != ""

    def test_generate_report_recommendations(self):
        """测试报告建议"""
        generator = RefactorDiffGenerator()
        before = {"files": {}, "modules": [], "classes": [], "functions": [],
                  "moved": [{"path": "a.py", "from": "old", "to": "new"}]}
        after = {"files": {}, "modules": [], "classes": [], "functions": []}
        report = generator.generate_report(before, after)
        assert len(report.recommendations) > 0


class TestRefactorDiffService:
    """测试重构差异服务"""

    def test_initialization(self):
        """测试初始化"""
        service = RefactorDiffService()
        assert service.generator is not None

    def test_initialization_with_generator(self):
        """测试使用自定义生成器初始化"""
        generator = RefactorDiffGenerator()
        service = RefactorDiffService(generator=generator)
        assert service.generator is generator

    def test_generate(self):
        """测试执行差异分析"""
        service = RefactorDiffService()
        before = {"files": {"a.py": "old"}, "modules": [], "classes": [], "functions": []}
        after = {"files": {"a.py": "new"}, "modules": [], "classes": [], "functions": []}
        report = service.generate(before, after)
        assert isinstance(report, RefactorDiffReport)
        assert len(report.entries) > 0

    def test_get_report(self):
        """测试获取报告"""
        service = RefactorDiffService()
        before = {"files": {"a.py": "old"}, "modules": [], "classes": [], "functions": []}
        after = {"files": {"a.py": "new"}, "modules": [], "classes": [], "functions": []}
        service.generate(before, after)
        report = service.get_report()
        assert report is not None

    def test_get_report_empty(self):
        """测试无报告时获取"""
        service = RefactorDiffService()
        report = service.get_report()
        assert report is None

    def test_get_statistics(self):
        """测试获取统计信息"""
        service = RefactorDiffService()
        before = {"files": {"a.py": "old"}, "modules": [], "classes": [], "functions": []}
        after = {"files": {"a.py": "new"}, "modules": [], "classes": [], "functions": []}
        service.generate(before, after)
        stats = service.get_statistics()
        assert "total_changes" in stats

    def test_get_statistics_empty(self):
        """测试无报告时获取统计"""
        service = RefactorDiffService()
        stats = service.get_statistics()
        assert stats == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
