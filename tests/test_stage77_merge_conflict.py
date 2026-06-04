"""
阶段77验收测试 - 分支合并冲突预检测
"""

import pytest
from src.architecture.merge_conflict import (
    ConflictType,
    ConflictSeverity,
    MergeConflict,
    ConflictDetector,
    ConflictResolver,
    MergeConflictService,
)


class TestConflictType:
    """测试冲突类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ConflictType.TEXT.value == "text"
        assert ConflictType.SEMANTIC.value == "semantic"
        assert ConflictType.DEPENDENCY.value == "dependency"
        assert ConflictType.LOGIC.value == "logic"

    def test_all_types(self):
        """测试所有冲突类型"""
        types = list(ConflictType)
        assert len(types) == 4


class TestConflictSeverity:
    """测试冲突严重程度枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ConflictSeverity.AUTO_RESOLVABLE.value == "auto_resolvable"
        assert ConflictSeverity.MANUAL_REQUIRED.value == "manual_required"
        assert ConflictSeverity.BLOCKING.value == "blocking"

    def test_all_severities(self):
        """测试所有严重程度"""
        severities = list(ConflictSeverity)
        assert len(severities) == 3


class TestMergeConflict:
    """测试合并冲突记录"""

    def test_default_creation(self):
        """测试默认创建"""
        conflict = MergeConflict()
        assert conflict.conflict_id != ""
        assert conflict.conflict_type == ConflictType.TEXT
        assert conflict.severity == ConflictSeverity.MANUAL_REQUIRED
        assert conflict.file_path == ""
        assert conflict.description == ""
        assert conflict.resolution_suggestion == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        conflict = MergeConflict(
            conflict_type=ConflictType.SEMANTIC,
            severity=ConflictSeverity.BLOCKING,
            file_path="api/handler.py",
            description="接口签名冲突",
            resolution_suggestion="协调接口兼容性",
        )
        assert conflict.conflict_type == ConflictType.SEMANTIC
        assert conflict.severity == ConflictSeverity.BLOCKING
        assert conflict.file_path == "api/handler.py"

    def test_conflict_id_unique(self):
        """测试冲突ID唯一性"""
        c1 = MergeConflict()
        c2 = MergeConflict()
        assert c1.conflict_id != c2.conflict_id


class TestConflictDetector:
    """测试冲突检测器"""

    def test_initialization(self):
        """测试初始化"""
        detector = ConflictDetector()
        assert detector._conflicts == []

    def test_detect_text_conflicts(self):
        """测试检测文本冲突"""
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts(
            "feature", "main", ["src/app.py", "src/utils.js"])
        text_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.TEXT]
        assert len(text_conflicts) > 0
        assert text_conflicts[0].severity == ConflictSeverity.AUTO_RESOLVABLE

    def test_detect_semantic_conflicts(self):
        """测试检测语义冲突"""
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts(
            "feature", "main", ["api/handler.py", "interface/service.py"])
        semantic_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.SEMANTIC]
        assert len(semantic_conflicts) > 0
        assert semantic_conflicts[0].severity == ConflictSeverity.MANUAL_REQUIRED

    def test_detect_dependency_conflicts(self):
        """测试检测依赖冲突"""
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts(
            "feature", "main", ["requirements.txt", "package.json"])
        dep_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.DEPENDENCY]
        assert len(dep_conflicts) > 0
        assert dep_conflicts[0].severity == ConflictSeverity.BLOCKING

    def test_detect_no_conflicts_same_branch(self):
        """测试同一分支无冲突"""
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts(
            "feature", "feature", ["src/app.py"])
        text_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.TEXT]
        assert len(text_conflicts) == 0

    def test_detect_multiple_conflict_types(self):
        """测试检测多种冲突类型"""
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts(
            "feature", "main",
            ["src/app.py", "api/handler.py", "requirements.txt"])
        types = set(c.conflict_type for c in conflicts)
        assert len(types) >= 2

    def test_get_conflicts(self):
        """测试获取所有冲突"""
        detector = ConflictDetector()
        detector.detect_conflicts("feature", "main", ["src/app.py"])
        conflicts = detector.get_conflicts()
        assert len(conflicts) > 0

    def test_detect_empty_files(self):
        """测试空文件列表"""
        detector = ConflictDetector()
        conflicts = detector.detect_conflicts("feature", "main", [])
        assert isinstance(conflicts, list)


class TestConflictResolver:
    """测试冲突解决器"""

    def test_initialization(self):
        """测试初始化"""
        resolver = ConflictResolver()
        assert resolver._resolved == []

    def test_resolve_auto_resolvable(self):
        """测试自动解决冲突"""
        resolver = ConflictResolver()
        conflict = MergeConflict(
            conflict_type=ConflictType.TEXT,
            severity=ConflictSeverity.AUTO_RESOLVABLE,
            file_path="app.py",
            description="文本冲突",
        )
        result = resolver.resolve(conflict)
        assert result["status"] == "auto_resolved"
        assert result["resolution"] is not None

    def test_resolve_manual_required(self):
        """测试手动解决建议"""
        resolver = ConflictResolver()
        conflict = MergeConflict(
            conflict_type=ConflictType.SEMANTIC,
            severity=ConflictSeverity.MANUAL_REQUIRED,
            file_path="api.py",
            description="语义冲突",
            resolution_suggestion="协调接口兼容性",
        )
        result = resolver.resolve(conflict)
        assert result["status"] == "manual_suggested"
        assert result["resolution"] is not None

    def test_resolve_blocking(self):
        """测试阻塞级别冲突"""
        resolver = ConflictResolver()
        conflict = MergeConflict(
            conflict_type=ConflictType.DEPENDENCY,
            severity=ConflictSeverity.BLOCKING,
            file_path="requirements.txt",
            description="依赖冲突",
        )
        result = resolver.resolve(conflict)
        assert result["status"] == "blocking"

    def test_verify_resolution_success(self):
        """测试验证解决方案成功"""
        resolver = ConflictResolver()
        conflict = MergeConflict(
            severity=ConflictSeverity.AUTO_RESOLVABLE,
        )
        result = resolver.verify_resolution(conflict, "已合并")
        assert result["verified"] is True

    def test_verify_resolution_empty(self):
        """测试验证空解决方案"""
        resolver = ConflictResolver()
        conflict = MergeConflict(severity=ConflictSeverity.AUTO_RESOLVABLE)
        result = resolver.verify_resolution(conflict, "")
        assert result["verified"] is False

    def test_verify_resolution_blocking(self):
        """测试验证阻塞级别解决方案"""
        resolver = ConflictResolver()
        conflict = MergeConflict(severity=ConflictSeverity.BLOCKING)
        result = resolver.verify_resolution(conflict, "some resolution")
        assert result["verified"] is False

    def test_auto_resolve_text(self):
        """测试自动解决文本冲突"""
        resolver = ConflictResolver()
        conflict = MergeConflict(
            conflict_type=ConflictType.TEXT,
            file_path="app.py",
        )
        resolution = resolver._auto_resolve(conflict)
        assert "app.py" in resolution

    def test_suggest_resolution(self):
        """测试提供解决建议"""
        resolver = ConflictResolver()
        conflict = MergeConflict(
            conflict_type=ConflictType.SEMANTIC,
            resolution_suggestion="协调接口",
        )
        suggestion = resolver._suggest_resolution(conflict)
        assert "协调接口" in suggestion


class TestMergeConflictService:
    """测试合并冲突服务"""

    def test_initialization(self):
        """测试初始化"""
        service = MergeConflictService()
        assert service.detector is not None
        assert service.resolver is not None

    def test_detect(self):
        """测试检测冲突"""
        service = MergeConflictService()
        conflicts = service.detect("feature", "main", ["src/app.py"])
        assert len(conflicts) > 0

    def test_resolve(self):
        """测试解决冲突"""
        service = MergeConflictService()
        conflict = MergeConflict(
            severity=ConflictSeverity.AUTO_RESOLVABLE,
            file_path="app.py",
        )
        result = service.resolve(conflict)
        assert result["status"] == "auto_resolved"

    def test_get_conflicts(self):
        """测试获取冲突列表"""
        service = MergeConflictService()
        service.detect("feature", "main", ["src/app.py"])
        conflicts = service.get_conflicts()
        assert len(conflicts) > 0

    def test_detect_and_resolve_flow(self):
        """测试检测并解决的完整流程"""
        service = MergeConflictService()
        conflicts = service.detect("feature", "main", ["src/app.py"])
        for conflict in conflicts:
            result = service.resolve(conflict)
            assert result["status"] in ("auto_resolved", "manual_suggested", "blocking")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
