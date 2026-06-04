"""
阶段62验收测试 - 类级别解耦重构
"""

import pytest
from src.architecture.refactor_class import (
    CouplingType,
    DecouplingStrategy,
    ClassCouplingReport,
    ClassDecoupler,
    ClassRefactorService,
)


class TestCouplingType:
    """测试耦合类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert CouplingType.DATA.value == "data"
        assert CouplingType.CONTROL.value == "control"
        assert CouplingType.CONTENT.value == "content"
        assert CouplingType.COMMON.value == "common"
        assert CouplingType.CONTROL_FLOW.value == "control_flow"

    def test_all_types(self):
        """测试所有类型"""
        types = list(CouplingType)
        assert len(types) == 5


class TestDecouplingStrategy:
    """测试解耦策略枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert DecouplingStrategy.EXTRACT_CLASS.value == "extract_class"
        assert DecouplingStrategy.INTRODUCE_INTERFACE.value == "introduce_interface"
        assert DecouplingStrategy.MOVE_METHOD.value == "move_method"
        assert DecouplingStrategy.DELEGATE.value == "delegate"

    def test_all_strategies(self):
        """测试所有策略"""
        strategies = list(DecouplingStrategy)
        assert len(strategies) == 4


class TestClassCouplingReport:
    """测试类耦合报告"""

    def test_default_creation(self):
        """测试默认创建"""
        report = ClassCouplingReport()
        assert report.class_name == ""
        assert report.coupling_score == 0.0
        assert report.coupling_types == []
        assert report.dependencies == []

    def test_custom_creation(self):
        """测试自定义创建"""
        report = ClassCouplingReport(
            class_name="UserService",
            coupling_score=0.75,
            coupling_types=[CouplingType.DATA, CouplingType.CONTROL],
            dependencies=["Database", "Cache"],
        )
        assert report.class_name == "UserService"
        assert report.coupling_score == 0.75
        assert len(report.coupling_types) == 2
        assert len(report.dependencies) == 2


class TestClassDecoupler:
    """测试类解耦器"""

    def test_initialization(self):
        """测试初始化"""
        decoupler = ClassDecoupler()
        assert decoupler._reports == {}
        assert decoupler._decoupling_log == []

    def test_analyze_coupling_low(self):
        """测试分析低耦合类"""
        decoupler = ClassDecoupler()
        report = decoupler.analyze_coupling("SimpleClass", {
            "dependencies": ["Logger"],
        })
        assert report.class_name == "SimpleClass"
        assert report.coupling_score < 0.5
        assert len(report.coupling_types) == 0

    def test_analyze_coupling_high(self):
        """测试分析高耦合类"""
        decoupler = ClassDecoupler()
        report = decoupler.analyze_coupling("ComplexClass", {
            "dependencies": [f"Dep{i}" for i in range(8)],
            "has_control_flags": True,
            "accesses_internal": True,
            "shares_global": True,
            "control_flow_coupling": True,
        })
        assert report.coupling_score > 0.5
        assert len(report.coupling_types) >= 3

    def test_analyze_coupling_data(self):
        """测试分析数据耦合"""
        decoupler = ClassDecoupler()
        report = decoupler.analyze_coupling("DataClass", {
            "dependencies": [f"Dep{i}" for i in range(6)],
        })
        assert CouplingType.DATA in report.coupling_types

    def test_analyze_coupling_control(self):
        """测试分析控制耦合"""
        decoupler = ClassDecoupler()
        report = decoupler.analyze_coupling("ControlClass", {
            "dependencies": [],
            "has_control_flags": True,
        })
        assert CouplingType.CONTROL in report.coupling_types

    def test_analyze_coupling_content(self):
        """测试分析内容耦合"""
        decoupler = ClassDecoupler()
        report = decoupler.analyze_coupling("ContentClass", {
            "dependencies": [],
            "accesses_internal": True,
        })
        assert CouplingType.CONTENT in report.coupling_types

    def test_analyze_coupling_default(self):
        """测试分析默认信息"""
        decoupler = ClassDecoupler()
        report = decoupler.analyze_coupling("DefaultClass")
        assert report.class_name == "DefaultClass"
        assert report.coupling_score == 0.0

    def test_suggest_decoupling(self):
        """测试提供解耦建议"""
        decoupler = ClassDecoupler()
        report = ClassCouplingReport(
            class_name="TestClass",
            coupling_score=0.8,
            coupling_types=[CouplingType.DATA, CouplingType.CONTROL],
        )
        suggestions = decoupler.suggest_decoupling(report)
        assert len(suggestions) >= 2

    def test_suggest_decoupling_high_score(self):
        """测试高耦合分数时的建议"""
        decoupler = ClassDecoupler()
        report = ClassCouplingReport(
            class_name="HighCouplingClass",
            coupling_score=0.8,
            coupling_types=[CouplingType.DATA],
        )
        suggestions = decoupler.suggest_decoupling(report)
        # 应包含整体拆分的critical建议
        critical_suggestions = [s for s in suggestions if s.get("priority") == "critical"]
        assert len(critical_suggestions) >= 1

    def test_execute_decoupling_extract(self):
        """测试执行提取类解耦"""
        decoupler = ClassDecoupler()
        report = ClassCouplingReport(class_name="BigClass")
        result = decoupler.execute_decoupling(report, DecouplingStrategy.EXTRACT_CLASS)
        assert result["status"] == "completed"
        assert result["strategy"] == "extract_class"
        assert len(result["changes"]) > 0

    def test_execute_decoupling_interface(self):
        """测试执行引入接口解耦"""
        decoupler = ClassDecoupler()
        report = ClassCouplingReport(class_name="TightClass")
        result = decoupler.execute_decoupling(report, DecouplingStrategy.INTRODUCE_INTERFACE)
        assert result["status"] == "completed"
        assert len(result["changes"]) > 0

    def test_execute_decoupling_move_method(self):
        """测试执行移动方法解耦"""
        decoupler = ClassDecoupler()
        report = ClassCouplingReport(class_name="MisplacedClass")
        result = decoupler.execute_decoupling(report, DecouplingStrategy.MOVE_METHOD)
        assert result["status"] == "completed"

    def test_execute_decoupling_delegate(self):
        """测试执行委托解耦"""
        decoupler = ClassDecoupler()
        report = ClassCouplingReport(class_name="ControlClass")
        result = decoupler.execute_decoupling(report, DecouplingStrategy.DELEGATE)
        assert result["status"] == "completed"

    def test_verify_decoupling_improved(self):
        """测试验证解耦改进"""
        decoupler = ClassDecoupler()
        # 先分析原始类
        original = decoupler.analyze_coupling("TestClass", {
            "dependencies": [f"Dep{i}" for i in range(8)],
        })
        # 模拟解耦后的报告
        improved = ClassCouplingReport(
            class_name="TestClass",
            coupling_score=0.1,
            coupling_types=[],
        )
        result = decoupler.verify_decoupling(improved)
        assert result["verified"] is True
        assert result["improvement"] > 0


class TestClassRefactorService:
    """测试类重构服务"""

    def test_initialization(self):
        """测试初始化"""
        service = ClassRefactorService()
        assert service.decoupler is not None
        assert len(service._reports) == 0

    def test_analyze(self):
        """测试分析"""
        service = ClassRefactorService()
        report = service.analyze("MyClass", {
            "dependencies": ["DB", "Cache", "Logger"],
        })
        assert report.class_name == "MyClass"

    def test_refactor(self):
        """测试重构"""
        service = ClassRefactorService()
        service.analyze("BigClass", {
            "dependencies": [f"Dep{i}" for i in range(6)],
        })
        result = service.refactor("BigClass", DecouplingStrategy.EXTRACT_CLASS)
        assert result["status"] == "completed"

    def test_refactor_without_analysis(self):
        """测试未分析直接重构"""
        service = ClassRefactorService()
        result = service.refactor("UnknownClass")
        assert result is not None

    def test_get_report(self):
        """测试获取报告"""
        service = ClassRefactorService()
        service.analyze("TestClass")
        report = service.get_report("TestClass")
        assert report is not None
        assert report.class_name == "TestClass"

    def test_get_report_not_found(self):
        """测试获取不存在的报告"""
        service = ClassRefactorService()
        report = service.get_report("NonExistent")
        assert report is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
