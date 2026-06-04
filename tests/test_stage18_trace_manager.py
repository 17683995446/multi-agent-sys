import pytest
import threading
import time
from src.architecture import (
    TraceLevel,
    TraceSpan,
    Trace,
    TraceIDGenerator,
    TraceContext,
    TraceContextManager,
    TraceStorage,
    TraceExporter,
    TraceManager,
    get_trace_manager,
    reset_trace_manager
)


class TestTraceLevel:
    """测试链路级别"""

    def test_trace_level_enum_values(self):
        """测试链路级别枚举值"""
        assert TraceLevel.DEBUG.value == "debug"
        assert TraceLevel.INFO.value == "info"
        assert TraceLevel.WARNING.value == "warning"
        assert TraceLevel.ERROR.value == "error"


class TestTraceIDGenerator:
    """测试链路ID生成器"""

    def test_generate_uuid(self):
        """测试生成UUID"""
        uuid1 = TraceIDGenerator.generate_uuid()
        uuid2 = TraceIDGenerator.generate_uuid()
        assert uuid1 != uuid2
        assert len(uuid1) == 36

    def test_generate_trace_id(self):
        """测试生成链路ID"""
        trace_id = TraceIDGenerator.generate_trace_id()
        assert trace_id is not None
        assert len(trace_id) == 36

    def test_generate_span_id(self):
        """测试生成跨度ID"""
        span_id = TraceIDGenerator.generate_span_id()
        assert span_id is not None
        assert len(span_id) == 16

    def test_generate_distributed_id(self):
        """测试生成分布式ID"""
        dist_id = TraceIDGenerator.generate_distributed_id()
        assert dist_id is not None
        assert dist_id.isdigit()


class TestTraceSpan:
    """测试追踪跨度"""

    def test_create_span(self):
        """测试创建跨度"""
        span = TraceSpan(
            span_id="span-1",
            trace_id="trace-1",
            parent_span_id=None,
            operation_name="test_operation"
        )
        assert span.span_id == "span-1"
        assert span.operation_name == "test_operation"

    def test_span_add_tag(self):
        """测试跨度添加标签"""
        span = TraceSpan(
            span_id="span-1",
            trace_id="trace-1",
            parent_span_id=None,
            operation_name="test"
        )
        span.add_tag("key", "value")
        assert span.tags["key"] == "value"

    def test_span_add_log(self):
        """测试跨度添加日志"""
        span = TraceSpan(
            span_id="span-1",
            trace_id="trace-1",
            parent_span_id=None,
            operation_name="test"
        )
        span.add_log("test message", data="value")
        assert len(span.logs) == 1
        assert span.logs[0]["message"] == "test message"

    def test_span_finish(self):
        """测试跨度结束"""
        span = TraceSpan(
            span_id="span-1",
            trace_id="trace-1",
            parent_span_id=None,
            operation_name="test"
        )
        time.sleep(0.01)
        span.finish("completed")
        assert span.status == "completed"
        assert span.end_time is not None
        assert span.get_duration_ms() is not None
        assert span.get_duration_ms() > 0

    def test_span_to_dict(self):
        """测试跨度转字典"""
        span = TraceSpan(
            span_id="span-1",
            trace_id="trace-1",
            parent_span_id=None,
            operation_name="test"
        )
        data = span.to_dict()
        assert "span_id" in data
        assert "trace_id" in data
        assert "start_time" in data


class TestTrace:
    """测试追踪链路"""

    def test_create_trace(self):
        """测试创建追踪"""
        trace = Trace(
            trace_id="trace-1",
            root_span_id="root-span",
            service_name="test-service",
            operation_name="test-operation"
        )
        assert trace.trace_id == "trace-1"
        assert trace.service_name == "test-service"

    def test_trace_add_span(self):
        """测试追踪添加跨度"""
        trace = Trace(
            trace_id="trace-1",
            root_span_id="root-span"
        )
        span = TraceSpan(
            span_id="span-1",
            trace_id="trace-1",
            parent_span_id=None,
            operation_name="child"
        )
        trace.add_span(span)
        assert len(trace.spans) == 1

    def test_trace_to_dict(self):
        """测试追踪转字典"""
        trace = Trace(
            trace_id="trace-1",
            root_span_id="root-span"
        )
        data = trace.to_dict()
        assert "trace_id" in data
        assert "spans" in data
        assert data["total_spans"] == 0


class TestTraceContext:
    """测试链路上下文"""

    def test_set_and_get_trace_id(self):
        """测试设置和获取链路ID"""
        ctx = TraceContext()
        ctx.set_trace_id("trace-123")
        assert ctx.get_trace_id() == "trace-123"

    def test_context_to_dict(self):
        """测试上下文转字典"""
        ctx = TraceContext()
        ctx.set_trace_id("trace-123")
        data = ctx.to_dict()
        assert data["trace_id"] == "trace-123"

    def test_context_from_dict(self):
        """测试从字典创建上下文"""
        data = {"trace_id": "trace-456", "span_id": "span-789"}
        ctx = TraceContext.from_dict(data)
        assert ctx.get_trace_id() == "trace-456"
        assert ctx.get_span_id() == "span-789"


class TestTraceContextManager:
    """测试链路上下文管理器"""

    def test_create_context(self):
        """测试创建上下文"""
        manager = TraceContextManager()
        ctx = manager.create_context("trace-1")
        assert ctx.get_trace_id() == "trace-1"
        assert ctx.get_span_id() is not None

    def test_get_context(self):
        """测试获取上下文"""
        manager = TraceContextManager()
        ctx = manager.create_context("trace-1")
        retrieved = manager.get_context("trace-1")
        assert retrieved is ctx

    def test_inject_context(self):
        """测试注入上下文"""
        manager = TraceContextManager()
        manager.create_context("trace-1")
        carrier = {}
        injected = manager.inject_context(carrier)
        assert "X-Trace-ID" in injected
        assert injected["X-Trace-ID"] == "trace-1"

    def test_extract_context(self):
        """测试提取上下文"""
        manager = TraceContextManager()
        carrier = {"X-Trace-ID": "trace-extracted", "X-Span-ID": "span-extracted"}
        ctx = manager.extract_context(carrier)
        assert ctx is not None
        assert ctx.get_trace_id() == "trace-extracted"


class TestTraceStorage:
    """测试链路存储"""

    def test_save_and_get_trace(self):
        """测试保存和获取追踪"""
        storage = TraceStorage()
        trace = Trace(trace_id="trace-1", root_span_id="root")
        storage.save_trace(trace)
        
        retrieved = storage.get_trace("trace-1")
        assert retrieved is not None
        assert retrieved.trace_id == "trace-1"

    def test_query_traces_by_service(self):
        """测试按服务名查询追踪"""
        storage = TraceStorage()
        
        trace1 = Trace(trace_id="trace-1", root_span_id="r1", service_name="service-a")
        trace2 = Trace(trace_id="trace-2", root_span_id="r2", service_name="service-b")
        
        storage.save_trace(trace1)
        storage.save_trace(trace2)
        
        results = storage.query_traces(service_name="service-a")
        assert len(results) == 1
        assert results[0].service_name == "service-a"

    def test_get_trace_count(self):
        """测试获取追踪数量"""
        storage = TraceStorage()
        trace1 = Trace(trace_id="t1", root_span_id="r1")
        trace2 = Trace(trace_id="t2", root_span_id="r2")
        storage.save_trace(trace1)
        storage.save_trace(trace2)
        
        assert storage.get_trace_count() == 2

    def test_clear(self):
        """测试清空存储"""
        storage = TraceStorage()
        storage.save_trace(Trace(trace_id="t1", root_span_id="r1"))
        storage.clear()
        assert storage.get_trace_count() == 0


class TestTraceExporter:
    """测试链路导出器"""

    def test_export_to_json(self):
        """测试导出为JSON"""
        storage = TraceStorage()
        storage.save_trace(Trace(trace_id="t1", root_span_id="r1", service_name="test"))
        
        exporter = TraceExporter(storage)
        json_str = exporter.export_to_json("t1")
        assert json_str is not None
        assert "t1" in json_str
        assert "test" in json_str


class TestTraceManager:
    """测试链路管理器"""

    def test_start_trace(self):
        """测试开始追踪"""
        manager = TraceManager()
        trace = manager.start_trace("test-operation", "test-service")
        assert trace.trace_id is not None
        assert trace.operation_name == "test-operation"

    def test_start_and_end_span(self):
        """测试开始和结束跨度"""
        manager = TraceManager()
        trace = manager.start_trace("test-op", "test-service")
        
        span = manager.start_span("child-span")
        assert span.trace_id == trace.trace_id
        assert span.operation_name == "child-span"
        
        manager.end_span(span)
        assert span.status == "completed"

    def test_trace_lifecycle(self):
        """测试追踪生命周期"""
        manager = TraceManager()
        
        trace = manager.start_trace("lifecycle-test", "test-service")
        span = manager.start_span("span-1")
        manager.end_span(span)
        manager.end_trace(trace)
        
        assert trace.status == "completed"

    def test_inject_and_extract_context(self):
        """测试上下文注入和提取"""
        manager = TraceManager()
        manager.start_trace("test-op", "test-service")
        
        carrier = {}
        injected = manager.inject_context(carrier)
        assert "X-Trace-ID" in injected
        
        manager.end_trace(manager.get_trace(injected["X-Trace-ID"]))
        
        manager2 = TraceManager()
        extracted = manager2.extract_context(injected)
        assert extracted is not None


class TestGlobalTraceManager:
    """测试全局链路管理器"""

    def test_get_global_manager(self):
        """测试获取全局管理器"""
        reset_trace_manager()
        manager = get_trace_manager()
        assert isinstance(manager, TraceManager)
        assert get_trace_manager() is manager

    def test_reset_global_manager(self):
        """测试重置全局管理器"""
        manager1 = get_trace_manager()
        reset_trace_manager()
        manager2 = get_trace_manager()
        assert manager1 is not manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
