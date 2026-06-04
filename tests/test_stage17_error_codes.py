import pytest
from src.architecture import (
    ErrorSeverity,
    ErrorCategory,
    ErrorCodes,
    ErrorContext,
    MASError,
    ErrorChain,
    ErrorRegistry,
    get_error_registry,
    reset_error_registry,
    create_error,
    format_error_for_display,
    ErrorHandler,
    get_error_handler
)


class TestErrorCodes:
    """测试错误码枚举"""

    def test_error_code_enum_values(self):
        """测试错误码枚举值"""
        assert ErrorCodes.INVALID_INPUT.value.code == "INP-001"
        assert ErrorCodes.TASK_FAILED.value.code == "TSK-002"
        assert ErrorCodes.FILE_NOT_FOUND.value.code == "FILE-001"

    def test_error_code_severity(self):
        """测试错误码严重级别"""
        assert ErrorCodes.INVALID_INPUT.value.severity == ErrorSeverity.ERROR
        assert ErrorCodes.TIMEOUT.value.severity == ErrorSeverity.WARNING
        assert ErrorCodes.RESOURCE_EXHAUSTED.value.severity == ErrorSeverity.CRITICAL

    def test_error_code_category(self):
        """测试错误码分类"""
        assert ErrorCodes.INVALID_INPUT.value.category == ErrorCategory.INPUT
        assert ErrorCodes.TASK_FAILED.value.category == ErrorCategory.TASK
        assert ErrorCodes.CONNECTION_FAILED.value.category == ErrorCategory.NETWORK

    def test_error_code_message_template(self):
        """测试错误码消息模板"""
        msg = ErrorCodes.INVALID_INPUT.value.message_template.format(
            field="name", value=""
        )
        assert "无效输入" in msg


class TestErrorContext:
    """测试错误上下文"""

    def test_create_context(self):
        """测试创建上下文"""
        ctx = ErrorContext()
        assert ctx.context_id is not None

    def test_add_and_get_attributes(self):
        """测试添加和获取属性"""
        ctx = ErrorContext()
        ctx.add("user", "alice").add("task_id", "123")
        
        assert ctx.get("user") == "alice"
        assert ctx.get("task_id") == "123"
        assert ctx.get("missing") is None

    def test_context_to_dict(self):
        """测试上下文转字典"""
        ctx = ErrorContext().add("user", "alice")
        data = ctx.to_dict()
        assert "context_id" in data
        assert data["attributes"]["user"] == "alice"


class TestMASError:
    """测试MASError异常"""

    def test_create_error(self):
        """测试创建错误"""
        err = MASError(
            ErrorCodes.INVALID_INPUT,
            message_args={"field": "name", "value": ""}
        )
        assert err.code == "INP-001"
        assert "无效输入" in err.message

    def test_error_with_context(self):
        """测试带上下文的错误"""
        ctx = ErrorContext().add("user", "alice")
        err = MASError(
            ErrorCodes.TASK_FAILED,
            message_args={"task_id": "123", "reason": "test"},
            context=ctx
        )
        assert err.context.get("user") == "alice"

    def test_error_with_cause(self):
        """测试带原因的错误"""
        try:
            raise ValueError("测试")
        except ValueError as ve:
            err = MASError(
                ErrorCodes.CODE_ERROR,
                message_args={"message": "error"},
                cause=ve
            )
        assert err.cause is not None
        assert isinstance(err.cause, ValueError)

    def test_error_to_dict(self):
        """测试错误转字典"""
        err = MASError(
            ErrorCodes.INVALID_INPUT,
            message_args={"field": "name", "value": ""}
        )
        data = err.to_dict()
        assert data["code"] == "INP-001"
        assert data["severity"] == "error"

    def test_error_str(self):
        """测试错误字符串表示"""
        err = MASError(
            ErrorCodes.INVALID_INPUT,
            message_args={"field": "name", "value": ""}
        )
        assert "INP-001" in str(err)


class TestErrorChain:
    """测试错误链"""

    def test_create_chain(self):
        """测试创建错误链"""
        chain = ErrorChain()
        assert chain.chain_id is not None
        assert not chain.has_errors()

    def test_add_errors_to_chain(self):
        """测试添加错误到链"""
        chain = ErrorChain()
        err1 = MASError(ErrorCodes.INVALID_INPUT, {"field": "a", "value": "1"})
        err2 = MASError(ErrorCodes.TASK_FAILED, {"task_id": "123", "reason": "x"})
        
        chain.add(err1).add(err2)
        assert chain.has_errors()
        assert len(chain.get_all()) == 2

    def test_get_latest_error(self):
        """测试获取最新错误"""
        chain = ErrorChain()
        err1 = MASError(ErrorCodes.INVALID_INPUT, {"field": "a", "value": "1"})
        err2 = MASError(ErrorCodes.TASK_FAILED, {"task_id": "123", "reason": "x"})
        
        chain.add(err1).add(err2)
        assert chain.get_latest() is err2

    def test_chain_to_dict(self):
        """测试错误链转字典"""
        chain = ErrorChain()
        chain.add(MASError(ErrorCodes.INVALID_INPUT, {"field": "a", "value": "1"}))
        data = chain.to_dict()
        assert "chain_id" in data
        assert data["count"] == 1


class TestErrorRegistry:
    """测试错误注册表"""

    def test_get_registry(self):
        """测试获取注册表"""
        reset_error_registry()
        registry = get_error_registry()
        assert isinstance(registry, ErrorRegistry)

    def test_list_all_error_codes(self):
        """测试列出所有错误码"""
        registry = get_error_registry()
        codes = registry.list_all()
        assert len(codes) > 0

    def test_find_by_category(self):
        """测试按分类查找"""
        registry = get_error_registry()
        task_errors = registry.find_by_category(ErrorCategory.TASK)
        assert len(task_errors) > 0
        for ec in task_errors:
            assert ec.category == ErrorCategory.TASK

    def test_find_by_severity(self):
        """测试按严重级别查找"""
        registry = get_error_registry()
        critical_errors = registry.find_by_severity(ErrorSeverity.CRITICAL)
        for ec in critical_errors:
            assert ec.severity == ErrorSeverity.CRITICAL

    def test_reset_registry(self):
        """测试重置注册表"""
        registry1 = get_error_registry()
        reset_error_registry()
        registry2 = get_error_registry()
        assert registry1 is not registry2


class TestCreateError:
    """测试create_error函数"""

    def test_create_error_function(self):
        """测试创建错误函数"""
        err = create_error(
            ErrorCodes.INVALID_INPUT,
            message_args={"field": "name", "value": ""}
        )
        assert isinstance(err, MASError)
        assert err.code == "INP-001"


class TestFormatErrorForDisplay:
    """测试错误显示格式化"""

    def test_format_error(self):
        """测试格式化错误"""
        err = MASError(
            ErrorCodes.INVALID_INPUT,
            message_args={"field": "name", "value": ""}
        )
        display = format_error_for_display(err)
        assert display["status"] == "error"
        assert "code" in display
        assert "message" in display

    def test_format_error_with_suggestions(self):
        """测试带建议的错误格式化"""
        err = MASError(
            ErrorCodes.CONNECTION_FAILED,
            message_args={"host": "localhost", "port": 8080}
        )
        display = format_error_for_display(err)
        assert "suggestions" in display


class TestErrorHandler:
    """测试错误处理器"""

    def test_create_handler(self):
        """测试创建处理器"""
        handler = ErrorHandler()
        assert handler is not None

    def test_register_and_call_handler(self):
        """测试注册和调用处理器"""
        handler = ErrorHandler()
        handled_errors = []
        
        def handle_func(err):
            handled_errors.append(err)
        
        handler.register(ErrorCategory.TASK, handle_func)
        
        err = MASError(
            ErrorCodes.TASK_FAILED,
            message_args={"task_id": "123", "reason": "test"}
        )
        handler.handle(err)
        assert len(handled_errors) == 1

    def test_register_and_call_default_handler(self):
        """测试注册和调用默认处理器"""
        handler = ErrorHandler()
        handled_default = []
        
        def default_func(err):
            handled_default.append(err)
        
        handler.register_default(default_func)
        
        err = MASError(ErrorCodes.INVALID_INPUT, {"field": "a", "value": "1"})
        handler.handle(err)
        assert len(handled_default) == 1

    def test_get_global_error_handler(self):
        """测试获取全局错误处理器"""
        global_handler = get_error_handler()
        assert global_handler is not None


class TestErrorSeverity:
    """测试错误严重级别"""

    def test_severity_enum_values(self):
        """测试严重级别枚举"""
        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorCategory:
    """测试错误分类"""

    def test_category_enum_values(self):
        """测试分类枚举"""
        assert ErrorCategory.SYSTEM.value == "system"
        assert ErrorCategory.INPUT.value == "input"
        assert ErrorCategory.TASK.value == "task"
        assert ErrorCategory.CODE.value == "code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
