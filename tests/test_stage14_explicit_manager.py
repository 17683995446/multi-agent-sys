import pytest
import tempfile
import os
from src.architecture import (
    ImplicitStateType,
    ImplicitState,
    TraceLink,
    ImplicitStateDetector,
    ExplicitConverter,
    TraceChain,
    ExplicitRule,
    ExplicitChecker,
    ExplicitManager,
    create_explicit_manager
)


class TestImplicitStateType:
    """测试隐式状态类型"""

    def test_implicit_state_types(self):
        """测试隐式状态类型枚举"""
        assert ImplicitStateType.GLOBAL_VARIABLE.value == "global_variable"
        assert ImplicitStateType.MODULE_LEVEL_STATE.value == "module_level_state"
        assert ImplicitStateType.CLASS_VARIABLE.value == "class_variable"
        assert ImplicitStateType.CACHING_RESULT.value == "caching_result"
        assert ImplicitStateType.SIDE_EFFECT.value == "side_effect"
        assert ImplicitStateType.MAGIC_NUMBER.value == "magic_number"
        assert ImplicitStateType.MAGIC_STRING.value == "magic_string"


class TestImplicitState:
    """测试隐式状态"""

    def test_create_implicit_state(self):
        """测试创建隐式状态"""
        state = ImplicitState(
            state_type=ImplicitStateType.GLOBAL_VARIABLE,
            location="test.py",
            line_number=10,
            description="全局变量",
            code_snippet="global x"
        )
        assert state.state_type == ImplicitStateType.GLOBAL_VARIABLE
        assert state.line_number == 10
        assert state.severity == "medium"

    def test_implicit_state_to_dict(self):
        """测试隐式状态转字典"""
        state = ImplicitState(
            state_type=ImplicitStateType.MAGIC_NUMBER,
            location="test.py",
            line_number=5,
            description="魔数",
            code_snippet="x = 42"
        )
        data = state.to_dict()
        assert data["state_type"] == "magic_number"
        assert data["location"] == "test.py"
        assert data["line_number"] == 5


class TestImplicitStateDetector:
    """测试隐式状态检测器"""

    def test_detect_global_variable(self):
        """测试检测全局变量"""
        detector = ImplicitStateDetector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("global x\n")
            f.write("x = 10\n")
            temp_file = f.name

        try:
            states = detector.detect_file(temp_file)
            assert len(states) > 0
            has_global = any(s.state_type == ImplicitStateType.GLOBAL_VARIABLE for s in states)
            assert has_global
        finally:
            os.unlink(temp_file)

    def test_detect_side_effect(self):
        """测试检测副作用"""
        detector = ImplicitStateDetector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')\n")
            f.write("with open('test.txt', 'w') as f:\n")
            f.write("    f.write('data')\n")
            temp_file = f.name

        try:
            states = detector.detect_file(temp_file)
            has_side_effect = any(s.state_type == ImplicitStateType.SIDE_EFFECT for s in states)
            assert has_side_effect
        finally:
            os.unlink(temp_file)

    def test_detect_magic_number(self):
        """测试检测魔数"""
        detector = ImplicitStateDetector()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x = 123\n")
            temp_file = f.name

        try:
            states = detector.detect_file(temp_file)
            has_magic = any(s.state_type == ImplicitStateType.MAGIC_NUMBER for s in states)
            assert has_magic
        finally:
            os.unlink(temp_file)


class TestExplicitConverter:
    """测试显式化转换器"""

    def test_convert_to_constant(self):
        """测试转换为常量"""
        converter = ExplicitConverter()
        result = converter.convert_to_constant("x = 42", "MAX_VALUE", 42)
        assert "MAX_VALUE" in result
        assert "42" in result

    def test_convert_global_to_parameter(self):
        """测试全局变量转参数"""
        converter = ExplicitConverter()
        code = "global x\nx = 10\n"
        result = converter.convert_global_to_parameter(code, "x")
        assert "已移除全局声明" in result


class TestTraceLink:
    """测试追溯链路"""

    def test_create_trace_link(self):
        """测试创建追溯链路"""
        link = TraceLink(
            trace_id="test-001",
            source="A",
            target="B",
            relationship="depends_on"
        )
        assert link.source == "A"
        assert link.target == "B"
        assert link.relationship == "depends_on"

    def test_trace_link_to_dict(self):
        """测试追溯链路转字典"""
        link = TraceLink(
            trace_id="test-001",
            source="A",
            target="B",
            relationship="depends_on"
        )
        data = link.to_dict()
        assert data["trace_id"] == "test-001"
        assert data["source"] == "A"
        assert data["target"] == "B"


class TestTraceChain:
    """测试追溯链"""

    def test_add_link(self):
        """测试添加链路"""
        chain = TraceChain()
        link = chain.add_link("A", "B", "depends_on")
        assert link.source == "A"
        assert link.target == "B"

    def test_get_trace(self):
        """测试获取链路"""
        chain = TraceChain()
        chain.add_link("A", "B", "depends_on")
        chain.add_link("A", "C", "uses")
        traces = chain.get_trace("A")
        assert len(traces) == 2

    def test_find_path(self):
        """测试查找路径"""
        chain = TraceChain()
        chain.add_link("A", "B", "depends_on")
        chain.add_link("B", "C", "depends_on")
        path = chain.find_path("A", "C")
        assert path is not None
        assert "A" in path
        assert "B" in path
        assert "C" in path

    def test_get_full_trace(self):
        """测试获取完整追溯信息"""
        chain = TraceChain()
        chain.add_link("A", "B", "depends_on")
        chain.add_link("C", "A", "creates")
        trace = chain.get_full_trace("A")
        assert trace["entity"] == "A"
        assert trace["trace_count"] == 2


class TestExplicitRule:
    """测试显式化规范"""

    def test_create_rule(self):
        """测试创建规范"""
        rule = ExplicitRule()
        assert rule.is_enabled("require_type_hints") is True
        assert rule.is_enabled("no_global_variables") is False

    def test_enable_disable_rule(self):
        """测试启用/禁用规则"""
        rule = ExplicitRule()
        rule.disable_rule("require_type_hints")
        assert rule.is_enabled("require_type_hints") is False
        rule.enable_rule("require_type_hints")
        assert rule.is_enabled("require_type_hints") is True

    def test_get_enabled_rules(self):
        """测试获取启用的规则"""
        rule = ExplicitRule()
        enabled = rule.get_enabled_rules()
        assert "require_type_hints" in enabled
        assert "no_global_variables" not in enabled


class TestExplicitChecker:
    """测试显式化检查器"""

    def test_create_checker(self):
        """测试创建检查器"""
        checker = ExplicitChecker()
        assert checker.rule is not None

    def test_check_file_type_hints(self):
        """测试检查类型提示"""
        checker = ExplicitChecker()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def func(x):\n    return x\n")
            temp_file = f.name

        try:
            violations = checker.check_file(temp_file)
            has_type_hint_violation = any(
                v["rule"] == "require_type_hints" for v in violations
            )
            assert has_type_hint_violation
        finally:
            os.unlink(temp_file)

    def test_check_file_docstrings(self):
        """测试检查文档字符串"""
        checker = ExplicitChecker()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def func(x):\n    return x\n")
            temp_file = f.name

        try:
            violations = checker.check_file(temp_file)
            has_docstring_violation = any(
                v["rule"] == "require_docstrings" for v in violations
            )
            assert has_docstring_violation
        finally:
            os.unlink(temp_file)


class TestExplicitManager:
    """测试显式化管理器"""

    def test_create_manager(self):
        """测试创建管理器"""
        manager = create_explicit_manager()
        assert manager is not None
        assert isinstance(manager, ExplicitManager)

    def test_scan_file(self):
        """测试扫描文件"""
        manager = create_explicit_manager()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("global x\nx = 42\nprint('hello')\n")
            temp_file = f.name

        try:
            result = manager.scan_file(temp_file)
            assert "implicit_states" in result
            assert "violations" in result
            assert "explicitness_score" in result
            assert result["total_implicit"] > 0 or result["total_violations"] > 0
        finally:
            os.unlink(temp_file)

    def test_add_trace(self):
        """测试添加追溯"""
        manager = create_explicit_manager()
        manager.add_trace("A", "B", "depends_on")
        trace = manager.get_trace("A")
        assert trace["trace_count"] > 0

    def test_calculate_score(self):
        """测试计算显式化得分"""
        manager = create_explicit_manager()
        score = manager._calculate_score(0, 0)
        assert score == 100.0
        score = manager._calculate_score(10, 5)
        assert score < 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
