from __future__ import annotations

import json
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class TraceLevel(str, Enum):
    """链路级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TraceSpan:
    """追踪跨度"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    level: TraceLevel = TraceLevel.INFO
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "started"
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str = "completed", error: Optional[str] = None) -> None:
        """结束跨度"""
        self.end_time = datetime.now()
        self.status = status
        if error:
            self.error = error
            self.level = TraceLevel.ERROR

    def add_tag(self, key: str, value: str) -> "TraceSpan":
        """添加标签"""
        self.tags[key] = value
        return self

    def add_log(self, message: str, **kwargs: Any) -> "TraceSpan":
        """添加日志"""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            **kwargs
        })
        return self

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.get_duration_ms(),
            "level": self.level.value,
            "tags": self.tags,
            "logs": self.logs,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata
        }

    def get_duration_ms(self) -> Optional[float]:
        """获取持续时间（毫秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None


@dataclass
class Trace:
    """追踪链路"""
    trace_id: str
    root_span_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
    service_name: str = ""
    operation_name: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    spans: List[TraceSpan] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: TraceSpan) -> None:
        """添加跨度"""
        self.spans.append(span)
        self.updated_at = datetime.now()

    def finish(self, status: str = "completed") -> None:
        """结束追踪"""
        self.status = status
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "root_span_id": self.root_span_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "service_name": self.service_name,
            "operation_name": self.operation_name,
            "tags": self.tags,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
            "total_spans": len(self.spans)
        }


class TraceIDGenerator:
    """链路ID生成器"""

    @staticmethod
    def generate_uuid() -> str:
        """生成UUID"""
        return str(uuid.uuid4())

    @staticmethod
    def generate_trace_id() -> str:
        """生成链路ID（使用UUID）"""
        return TraceIDGenerator.generate_uuid()

    @staticmethod
    def generate_span_id() -> str:
        """生成跨度ID（使用UUID短格式）"""
        return TraceIDGenerator.generate_uuid()[:16]

    @staticmethod
    def generate_distributed_id(
        timestamp: Optional[int] = None,
        worker_id: int = 1,
        sequence: int = 0
    ) -> str:
        """生成分布式ID（类似Snowflake）"""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        # 简化版：timestamp(41bits) + worker(10bits) + sequence(12bits)
        distributed_id = (
            (timestamp << 22) |
            (worker_id << 12) |
            sequence
        )
        return str(distributed_id)


class TraceContext:
    """链路上下文"""

    _local = threading.local()

    def __init__(self):
        self._trace_id: Optional[str] = None
        self._span_id: Optional[str] = None
        self._parent_span_id: Optional[str] = None

    @classmethod
    def get_current(cls) -> Optional["TraceContext"]:
        """获取当前上下文"""
        return getattr(cls._local, "context", None)

    @classmethod
    def set_current(cls, context: "TraceContext") -> None:
        """设置当前上下文"""
        cls._local.context = context

    @classmethod
    def clear_current(cls) -> None:
        """清除当前上下文"""
        if hasattr(cls._local, "context"):
            del cls._local.context

    def get_trace_id(self) -> Optional[str]:
        """获取链路ID"""
        return self._trace_id

    def get_span_id(self) -> Optional[str]:
        """获取跨度ID"""
        return self._span_id

    def get_parent_span_id(self) -> Optional[str]:
        """获取父跨度ID"""
        return self._parent_span_id

    def set_trace_id(self, trace_id: str) -> None:
        """设置链路ID"""
        self._trace_id = trace_id

    def set_span_id(self, span_id: str) -> None:
        """设置跨度ID"""
        self._span_id = span_id

    def set_parent_span_id(self, parent_span_id: str) -> None:
        """设置父跨度ID"""
        self._parent_span_id = parent_span_id

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self._trace_id,
            "span_id": self._span_id,
            "parent_span_id": self._parent_span_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceContext":
        """从字典创建"""
        ctx = cls()
        ctx._trace_id = data.get("trace_id")
        ctx._span_id = data.get("span_id")
        ctx._parent_span_id = data.get("parent_span_id")
        return ctx


class TraceContextManager:
    """链路上下文管理器"""

    def __init__(self):
        self._contexts: Dict[str, TraceContext] = {}

    def create_context(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None
    ) -> TraceContext:
        """创建新的上下文"""
        context = TraceContext()
        context._trace_id = trace_id or TraceIDGenerator.generate_trace_id()
        context._span_id = span_id or TraceIDGenerator.generate_span_id()
        context._parent_span_id = parent_span_id
        
        if context._trace_id not in self._contexts:
            self._contexts[context._trace_id] = context
        
        TraceContext.set_current(context)
        return context

    def get_context(self, trace_id: str) -> Optional[TraceContext]:
        """获取指定链路ID的上下文"""
        return self._contexts.get(trace_id)

    def remove_context(self, trace_id: str) -> None:
        """移除上下文"""
        if trace_id in self._contexts:
            del self._contexts[trace_id]

    def inject_context(self, carrier: Dict[str, str]) -> Dict[str, str]:
        """注入上下文到载体（用于跨进程传播）"""
        ctx = TraceContext.get_current()
        if ctx:
            carrier["X-Trace-ID"] = ctx.get_trace_id() or ""
            carrier["X-Span-ID"] = ctx.get_span_id() or ""
            parent_id = ctx.get_parent_span_id()
            if parent_id:
                carrier["X-Parent-Span-ID"] = parent_id
        return carrier

    def extract_context(self, carrier: Dict[str, str]) -> Optional[TraceContext]:
        """从载体中提取上下文"""
        trace_id = carrier.get("X-Trace-ID")
        if not trace_id:
            return None

        span_id = carrier.get("X-Span-ID")
        parent_span_id = carrier.get("X-Parent-Span-ID")
        
        return self.create_context(trace_id, span_id, parent_span_id)


class TraceStorage:
    """链路存储"""

    def __init__(self, max_traces: int = 1000):
        self._traces: Dict[str, Trace] = {}
        self._spans_by_trace: Dict[str, List[TraceSpan]] = defaultdict(list)
        self._lock = threading.RLock()
        self._max_traces = max_traces

    def save_trace(self, trace: Trace) -> None:
        """保存追踪"""
        with self._lock:
            self._traces[trace.trace_id] = trace
            self._spans_by_trace[trace.trace_id] = trace.spans
            self._cleanup_old_traces()

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """获取追踪"""
        with self._lock:
            return self._traces.get(trace_id)

    def get_spans(self, trace_id: str) -> List[TraceSpan]:
        """获取追踪的所有跨度"""
        with self._lock:
            return list(self._spans_by_trace.get(trace_id, []))

    def query_traces(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Trace]:
        """查询追踪"""
        with self._lock:
            results = []
            for trace in self._traces.values():
                if service_name and trace.service_name != service_name:
                    continue
                if operation_name and trace.operation_name != operation_name:
                    continue
                if status and trace.status != status:
                    continue
                if start_time and trace.created_at < start_time:
                    continue
                if end_time and trace.created_at > end_time:
                    continue
                results.append(trace)
            
            results.sort(key=lambda t: t.created_at, reverse=True)
            return results[:limit]

    def get_trace_count(self) -> int:
        """获取追踪数量"""
        with self._lock:
            return len(self._traces)

    def clear(self) -> None:
        """清空所有追踪"""
        with self._lock:
            self._traces.clear()
            self._spans_by_trace.clear()

    def _cleanup_old_traces(self) -> None:
        """清理旧追踪"""
        if len(self._traces) > self._max_traces:
            traces_to_remove = sorted(
                self._traces.values(),
                key=lambda t: t.created_at
            )[:len(self._traces) - self._max_traces]
            
            for trace in traces_to_remove:
                if trace.trace_id in self._traces:
                    del self._traces[trace.trace_id]
                if trace.trace_id in self._spans_by_trace:
                    del self._spans_by_trace[trace.trace_id]


class TraceExporter:
    """链路导出器"""

    def __init__(self, storage: TraceStorage):
        self._storage = storage

    def export_to_json(self, trace_id: str) -> Optional[str]:
        """导出为JSON"""
        trace = self._storage.get_trace(trace_id)
        if trace:
            return json.dumps(trace.to_dict(), indent=2, ensure_ascii=False)
        return None

    def export_all_to_json(self) -> str:
        """导出所有追踪为JSON"""
        traces = list(self._storage._traces.values())
        return json.dumps(
            [t.to_dict() for t in traces],
            indent=2,
            ensure_ascii=False
        )

    def export_to_dict(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """导出为字典"""
        trace = self._storage.get_trace(trace_id)
        if trace:
            return trace.to_dict()
        return None


class TraceManager:
    """链路管理器"""

    def __init__(self):
        self._storage = TraceStorage()
        self._context_manager = TraceContextManager()
        self._exporter = TraceExporter(self._storage)

    def start_trace(
        self,
        operation_name: str,
        service_name: str = "",
        trace_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Trace:
        """开始追踪"""
        trace_id = trace_id or TraceIDGenerator.generate_trace_id()
        span_id = TraceIDGenerator.generate_span_id()
        
        trace = Trace(
            trace_id=trace_id,
            root_span_id=span_id,
            service_name=service_name,
            operation_name=operation_name,
            tags=tags or {}
        )
        
        self._context_manager.create_context(trace_id, span_id)
        self._storage.save_trace(trace)
        
        return trace

    def start_span(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        level: TraceLevel = TraceLevel.INFO,
        tags: Optional[Dict[str, str]] = None
    ) -> TraceSpan:
        """开始跨度"""
        ctx = TraceContext.get_current()
        if not ctx:
            raise RuntimeError("No active trace context")
        
        trace_id = ctx.get_trace_id()
        span_id = TraceIDGenerator.generate_span_id()
        
        span = TraceSpan(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id or ctx.get_parent_span_id(),
            operation_name=operation_name,
            level=level,
            tags=tags or {}
        )
        
        ctx.set_span_id(span_id)
        ctx.set_parent_span_id(span_id)
        
        trace = self._storage.get_trace(trace_id)
        if trace:
            trace.add_span(span)
        
        return span

    def end_span(self, span: TraceSpan, status: str = "completed", error: Optional[str] = None) -> None:
        """结束跨度"""
        span.finish(status, error)

    def end_trace(self, trace: Trace, status: str = "completed") -> None:
        """结束追踪"""
        trace.finish(status)
        TraceContext.clear_current()

    def inject_context(self, carrier: Dict[str, str]) -> Dict[str, str]:
        """注入上下文到载体"""
        return self._context_manager.inject_context(carrier)

    def extract_context(self, carrier: Dict[str, str]) -> Optional[TraceContext]:
        """从载体提取上下文"""
        return self._context_manager.extract_context(carrier)

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """获取追踪"""
        return self._storage.get_trace(trace_id)

    def query_traces(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Trace]:
        """查询追踪"""
        return self._storage.query_traces(
            service_name=service_name,
            operation_name=operation_name,
            status=status,
            limit=limit
        )

    def export_trace(self, trace_id: str) -> Optional[str]:
        """导出追踪"""
        return self._exporter.export_to_json(trace_id)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_traces": self._storage.get_trace_count(),
            "active_traces": len(self._storage.query_traces(status="active"))
        }


_global_manager: Optional[TraceManager] = None


def get_trace_manager() -> TraceManager:
    """获取全局链路管理器"""
    global _global_manager
    if _global_manager is None:
        _global_manager = TraceManager()
    return _global_manager


def reset_trace_manager() -> None:
    """重置全局链路管理器"""
    global _global_manager
    _global_manager = None
