"""
阶段74验收测试：循环依赖全自动斩断
"""

import pytest
from src.architecture.cycle_breaker import (
    CycleType,
    CycleStatus,
    CycleRecord,
    CycleDetector,
    CycleBreaker,
    CycleBreakService,
)


class TestCycleType:
    """测试循环类型枚举"""

    def test_type_values(self):
        """测试循环类型枚举值"""
        assert CycleType.DIRECT.value == "direct"
        assert CycleType.INDIRECT.value == "indirect"
        assert CycleType.SELF.value == "self"

    def test_all_types(self):
        """测试所有类型"""
        types = list(CycleType)
        assert len(types) == 3


class TestCycleStatus:
    """测试循环状态枚举"""

    def test_status_values(self):
        """测试循环状态枚举值"""
        assert CycleStatus.DETECTED.value == "detected"
        assert CycleStatus.BREAKING.value == "breaking"
        assert CycleStatus.BROKEN.value == "broken"
        assert CycleStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(CycleStatus)
        assert len(statuses) == 4


class TestCycleRecord:
    """测试循环依赖记录"""

    def test_default_creation(self):
        """测试默认创建"""
        record = CycleRecord()
        assert record.cycle_id != ""
        assert record.cycle_type == CycleType.DIRECT
        assert record.nodes == []
        assert record.edges == []
        assert record.status == CycleStatus.DETECTED
        assert record.break_strategy == ""
        assert record.created_at > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        record = CycleRecord(
            cycle_type=CycleType.INDIRECT,
            nodes=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C"), ("C", "A")],
            status=CycleStatus.DETECTED,
        )
        assert record.cycle_type == CycleType.INDIRECT
        assert len(record.nodes) == 3
        assert len(record.edges) == 3

    def test_cycle_id_unique(self):
        """测试循环ID唯一性"""
        r1 = CycleRecord()
        r2 = CycleRecord()
        assert r1.cycle_id != r2.cycle_id


class TestCycleDetector:
    """测试循环依赖检测器"""

    def test_initialization(self):
        """测试初始化"""
        detector = CycleDetector()
        assert len(detector.records) == 0

    def test_detect_direct_cycle(self):
        """测试检测直接循环"""
        detector = CycleDetector()
        graph = {
            "A": ["B"],
            "B": ["A"],
        }
        records = detector.detect_cycles(graph)
        assert len(records) > 0
        assert any(r.cycle_type == CycleType.DIRECT for r in records)

    def test_detect_indirect_cycle(self):
        """测试检测间接循环"""
        detector = CycleDetector()
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
        }
        records = detector.detect_cycles(graph)
        assert len(records) > 0
        assert any(r.cycle_type == CycleType.INDIRECT for r in records)

    def test_detect_self_cycle(self):
        """测试检测自引用循环"""
        detector = CycleDetector()
        graph = {
            "A": ["A"],
        }
        records = detector.detect_cycles(graph)
        assert len(records) > 0
        assert any(r.cycle_type == CycleType.SELF for r in records)

    def test_detect_no_cycle(self):
        """测试无循环依赖"""
        detector = CycleDetector()
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": [],
        }
        records = detector.detect_cycles(graph)
        assert len(records) == 0

    def test_detect_multiple_cycles(self):
        """测试检测多个循环"""
        detector = CycleDetector()
        graph = {
            "A": ["B"],
            "B": ["A"],
            "C": ["D"],
            "D": ["C"],
        }
        records = detector.detect_cycles(graph)
        assert len(records) >= 2

    def test_get_cycle_graph(self):
        """测试获取循环依赖图"""
        detector = CycleDetector()
        graph = {
            "A": ["B"],
            "B": ["A"],
        }
        detector.detect_cycles(graph)
        cycle_graph = detector.get_cycle_graph()
        assert "nodes" in cycle_graph
        assert "edges" in cycle_graph
        assert cycle_graph["cycle_count"] > 0


class TestCycleBreaker:
    """测试循环依赖斩断器"""

    def test_initialization(self):
        """测试初始化"""
        breaker = CycleBreaker()
        assert len(breaker.break_log) == 0

    def test_break_self_cycle(self):
        """测试斩断自引用循环"""
        breaker = CycleBreaker()
        record = CycleRecord(
            cycle_type=CycleType.SELF,
            nodes=["A"],
            edges=[("A", "A")],
        )
        result = breaker.break_cycle(record)
        assert result.status == CycleStatus.BROKEN
        assert "接口" in result.break_strategy

    def test_break_direct_cycle(self):
        """测试斩断直接循环"""
        breaker = CycleBreaker()
        record = CycleRecord(
            cycle_type=CycleType.DIRECT,
            nodes=["A", "B"],
            edges=[("A", "B"), ("B", "A")],
        )
        result = breaker.break_cycle(record)
        assert result.status == CycleStatus.BROKEN
        assert "共享模块" in result.break_strategy

    def test_break_indirect_cycle(self):
        """测试斩断间接循环"""
        breaker = CycleBreaker()
        record = CycleRecord(
            cycle_type=CycleType.INDIRECT,
            nodes=["A", "B", "C"],
            edges=[("A", "B"), ("B", "C"), ("C", "A")],
        )
        result = breaker.break_cycle(record)
        assert result.status == CycleStatus.BROKEN
        assert "重排" in result.break_strategy

    def test_verify_broken(self):
        """测试验证斩断结果"""
        breaker = CycleBreaker()
        records = [
            CycleRecord(cycle_type=CycleType.DIRECT, nodes=["A", "B"],
                        status=CycleStatus.BROKEN),
            CycleRecord(cycle_type=CycleType.INDIRECT, nodes=["C", "D", "E"],
                        status=CycleStatus.FAILED),
        ]
        result = breaker.verify_broken(records)
        assert result["total"] == 2
        assert result["broken"] == 1
        assert result["failed"] == 1

    def test_verify_broken_empty(self):
        """测试验证空列表"""
        breaker = CycleBreaker()
        result = breaker.verify_broken([])
        assert result["success_rate"] == 1.0


class TestCycleBreakService:
    """测试循环依赖斩断服务"""

    def test_initialization(self):
        """测试初始化"""
        service = CycleBreakService()
        assert service.detector is not None
        assert service.breaker is not None

    def test_process(self):
        """测试完整流程"""
        service = CycleBreakService()
        graph = {
            "A": ["B"],
            "B": ["A"],
        }
        result = service.process(graph)
        assert result["cycles_found"] > 0
        assert "verification" in result

    def test_process_no_cycle(self):
        """测试无循环流程"""
        service = CycleBreakService()
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": [],
        }
        result = service.process(graph)
        assert result["cycles_found"] == 0

    def test_get_cycles(self):
        """测试获取循环记录"""
        service = CycleBreakService()
        graph = {
            "A": ["B"],
            "B": ["A"],
        }
        service.process(graph)
        cycles = service.get_cycles()
        assert len(cycles) > 0

    def test_get_report(self):
        """测试获取报告"""
        service = CycleBreakService()
        graph = {
            "A": ["B"],
            "B": ["A"],
        }
        service.process(graph)
        report = service.get_report()
        assert "cycle_graph" in report
        assert "verification" in report
        assert "records" in report

    def test_full_workflow(self):
        """测试完整工作流"""
        service = CycleBreakService()
        graph = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"],
            "D": ["D"],
        }
        result = service.process(graph)
        assert result["cycles_found"] >= 1
        cycles = service.get_cycles()
        assert len(cycles) >= 1
        report = service.get_report()
        assert report["cycle_graph"]["cycle_count"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
