"""
阶段72验收测试：代码重复检测、冗余清理
"""

import pytest
from src.architecture.duplication_detector import (
    DuplicationType,
    DuplicationSeverity,
    DuplicationInstance,
    DuplicationDetector,
    DuplicationCleaner,
    DuplicationService,
)


class TestDuplicationType:
    """测试重复类型枚举"""

    def test_type_values(self):
        """测试重复类型枚举值"""
        assert DuplicationType.EXACT.value == "exact"
        assert DuplicationType.STRUCTURAL.value == "structural"
        assert DuplicationType.SEMANTIC.value == "semantic"

    def test_all_types(self):
        """测试所有类型"""
        types = list(DuplicationType)
        assert len(types) == 3


class TestDuplicationSeverity:
    """测试重复严重程度枚举"""

    def test_severity_values(self):
        """测试严重程度枚举值"""
        assert DuplicationSeverity.LOW.value == "low"
        assert DuplicationSeverity.MEDIUM.value == "medium"
        assert DuplicationSeverity.HIGH.value == "high"

    def test_all_severities(self):
        """测试所有严重程度"""
        severities = list(DuplicationSeverity)
        assert len(severities) == 3


class TestDuplicationInstance:
    """测试重复实例"""

    def test_default_creation(self):
        """测试默认创建"""
        inst = DuplicationInstance()
        assert inst.instance_id != ""
        assert inst.dup_type == DuplicationType.EXACT
        assert inst.locations == []
        assert inst.similarity == 0.0
        assert inst.line_count == 0
        assert inst.severity == DuplicationSeverity.LOW
        assert inst.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        inst = DuplicationInstance(
            dup_type=DuplicationType.STRUCTURAL,
            locations=["main.py:10", "utils.py:20"],
            similarity=0.85,
            line_count=15,
            severity=DuplicationSeverity.HIGH,
            description="结构重复",
        )
        assert inst.dup_type == DuplicationType.STRUCTURAL
        assert len(inst.locations) == 2
        assert inst.similarity == 0.85
        assert inst.line_count == 15
        assert inst.severity == DuplicationSeverity.HIGH

    def test_instance_id_unique(self):
        """测试实例ID唯一性"""
        inst1 = DuplicationInstance()
        inst2 = DuplicationInstance()
        assert inst1.instance_id != inst2.instance_id


class TestDuplicationDetector:
    """测试代码重复检测器"""

    def test_initialization(self):
        """测试初始化"""
        detector = DuplicationDetector()
        assert len(detector.instances) == 0
        assert detector.threshold == 0.8

    def test_detect_exact(self):
        """测试精确重复检测"""
        detector = DuplicationDetector()
        code_blocks = [
            {"content": "def foo():\n    return 1", "location": "a.py:1"},
            {"content": "def foo():\n    return 1", "location": "b.py:1"},
        ]
        instances = detector.detect(code_blocks)
        exact = [i for i in instances if i.dup_type == DuplicationType.EXACT]
        assert len(exact) > 0

    def test_detect_no_duplication(self):
        """测试无重复代码"""
        detector = DuplicationDetector()
        code_blocks = [
            {"content": "def foo():\n    return 1", "location": "a.py:1"},
            {"content": "def bar():\n    return 2", "location": "b.py:1"},
        ]
        instances = detector.detect(code_blocks)
        # 不应有精确重复
        exact = [i for i in instances if i.dup_type == DuplicationType.EXACT]
        assert len(exact) == 0

    def test_detect_structural(self):
        """测试结构重复检测"""
        detector = DuplicationDetector(threshold=0.3)
        code_blocks = [
            {"content": "x = 1\ny = 2\nz = x + y", "location": "a.py:1"},
            {"content": "x = 1\ny = 2\nz = x + y", "location": "b.py:1"},
        ]
        instances = detector.detect(code_blocks)
        assert len(instances) > 0

    def test_calculate_similarity_identical(self):
        """测试相同代码相似度"""
        detector = DuplicationDetector()
        code = "def foo():\n    return 1"
        similarity = detector.calculate_similarity(code, code)
        assert similarity == 1.0

    def test_calculate_similarity_different(self):
        """测试不同代码相似度"""
        detector = DuplicationDetector()
        code_a = "def foo():\n    return 1"
        code_b = "class Bar:\n    pass"
        similarity = detector.calculate_similarity(code_a, code_b)
        assert similarity < 1.0

    def test_calculate_similarity_empty(self):
        """测试空代码相似度"""
        detector = DuplicationDetector()
        similarity = detector.calculate_similarity("", "code")
        assert similarity == 0.0

    def test_generate_report(self):
        """测试生成报告"""
        detector = DuplicationDetector()
        code_blocks = [
            {"content": "def foo():\n    return 1", "location": "a.py:1"},
            {"content": "def foo():\n    return 1", "location": "b.py:1"},
        ]
        detector.detect(code_blocks)
        report = detector.generate_report()
        assert "total_instances" in report
        assert "exact_count" in report
        assert "structural_count" in report


class TestDuplicationCleaner:
    """测试代码重复清理器"""

    def test_initialization(self):
        """测试初始化"""
        cleaner = DuplicationCleaner()
        assert len(cleaner.cleanup_log) == 0

    def test_analyze_duplication(self):
        """测试分析重复情况"""
        cleaner = DuplicationCleaner()
        instances = [
            DuplicationInstance(
                dup_type=DuplicationType.EXACT,
                line_count=10,
                severity=DuplicationSeverity.HIGH,
            ),
        ]
        analysis = cleaner.analyze_duplication(instances)
        assert analysis["total_instances"] == 1
        assert analysis["total_duplicate_lines"] == 10
        assert analysis["high_severity_count"] == 1

    def test_analyze_duplication_empty(self):
        """测试分析空重复"""
        cleaner = DuplicationCleaner()
        analysis = cleaner.analyze_duplication([])
        assert analysis["total_instances"] == 0
        assert analysis["estimated_reduction"] == 0.0

    def test_suggest_cleanup(self):
        """测试清理建议"""
        cleaner = DuplicationCleaner()
        instances = [
            DuplicationInstance(
                dup_type=DuplicationType.EXACT,
                locations=["a.py:1", "b.py:1"],
            ),
        ]
        suggestions = cleaner.suggest_cleanup(instances)
        assert len(suggestions) == 1
        assert suggestions[0]["action"] == "extract"

    def test_suggest_cleanup_structural(self):
        """测试结构重复清理建议"""
        cleaner = DuplicationCleaner()
        instances = [
            DuplicationInstance(
                dup_type=DuplicationType.STRUCTURAL,
                similarity=0.85,
                locations=["a.py:1", "b.py:1"],
            ),
        ]
        suggestions = cleaner.suggest_cleanup(instances)
        assert len(suggestions) == 1
        assert suggestions[0]["action"] == "refactor"

    def test_execute_cleanup_exact(self):
        """测试执行精确重复清理"""
        cleaner = DuplicationCleaner()
        instances = [
            DuplicationInstance(
                dup_type=DuplicationType.EXACT,
                locations=["a.py:1", "b.py:1"],
            ),
        ]
        result = cleaner.execute_cleanup(instances)
        assert result["cleaned"] == 1
        assert result["total"] == 1

    def test_execute_cleanup_structural_high_similarity(self):
        """测试执行高相似度结构重复清理"""
        cleaner = DuplicationCleaner()
        instances = [
            DuplicationInstance(
                dup_type=DuplicationType.STRUCTURAL,
                similarity=0.95,
                locations=["a.py:1", "b.py:1"],
            ),
        ]
        result = cleaner.execute_cleanup(instances)
        assert result["cleaned"] == 1

    def test_execute_cleanup_structural_low_similarity(self):
        """测试执行低相似度结构重复跳过"""
        cleaner = DuplicationCleaner()
        instances = [
            DuplicationInstance(
                dup_type=DuplicationType.STRUCTURAL,
                similarity=0.82,
                locations=["a.py:1", "b.py:1"],
            ),
        ]
        result = cleaner.execute_cleanup(instances)
        assert result["skipped"] == 1


class TestDuplicationService:
    """测试代码重复检测与清理服务"""

    def test_initialization(self):
        """测试初始化"""
        service = DuplicationService()
        assert service.detector is not None
        assert service.cleaner is not None

    def test_process(self):
        """测试完整流程"""
        service = DuplicationService()
        code_blocks = [
            {"content": "def foo():\n    return 1", "location": "a.py:1"},
            {"content": "def foo():\n    return 1", "location": "b.py:1"},
        ]
        result = service.process(code_blocks)
        assert "instances_found" in result
        assert "analysis" in result
        assert "suggestions_count" in result
        assert "cleanup_result" in result

    def test_get_report(self):
        """测试获取报告"""
        service = DuplicationService()
        code_blocks = [
            {"content": "def foo():\n    return 1", "location": "a.py:1"},
            {"content": "def foo():\n    return 1", "location": "b.py:1"},
        ]
        service.process(code_blocks)
        report = service.get_report()
        assert "total_instances" in report

    def test_process_no_duplication(self):
        """测试无重复代码流程"""
        service = DuplicationService()
        code_blocks = [
            {"content": "def foo():\n    return 1", "location": "a.py:1"},
            {"content": "def bar():\n    return 2", "location": "b.py:1"},
        ]
        result = service.process(code_blocks)
        assert result["instances_found"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
