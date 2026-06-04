# 阶段18完成报告：定义全局可追溯链路ID机制

## 阶段概述

本阶段实现了完整的全局可追溯链路ID机制，包括链路ID生成、上下文管理、链路存储和查询可视化支持。

## 完成的工作

### 1. 链路ID生成器

**核心组件：** `TraceIDGenerator`

**功能：**
- `generate_uuid()` - 生成标准UUID
- `generate_trace_id()` - 生成链路ID（基于UUID）
- `generate_span_id()` - 生成跨度ID（UUID短格式）
- `generate_distributed_id()` - 生成分布式ID（类似Snowflake）

### 2. 链路上下文管理和自动传播机制

**核心组件：**
- `TraceContext` - 链路上下文（线程本地存储）
- `TraceContextManager` - 上下文管理器

**功能：**
- 线程安全的上下文存储
- 上下文注入到载体（用于跨进程传播）
- 上下文从载体提取
- 自动链路ID和跨度ID管理

**传播机制：**
- 支持HTTP header传播（X-Trace-ID, X-Span-ID, X-Parent-Span-ID）
- 支持跨线程、跨进程的上下文传递

### 3. 链路存储

**核心组件：**
- `TraceStorage` - 链路存储（内存存储）
- `TraceExporter` - 链路导出器

**功能：**
- 保存和获取追踪
- 按服务名、操作名、状态、时间范围查询
- 自动清理旧追踪（LRU策略）
- 导出为JSON格式

### 4. 链路查询和可视化支持

**核心组件：**
- `TraceSpan` - 追踪跨度
- `Trace` - 追踪链路
- `TraceManager` - 链路管理器

**功能：**
- 跨度管理（开始、结束、添加标签、日志）
- 追踪生命周期管理
- 统计信息查询
- JSON导出

### 5. 追踪数据结构

**TraceSpan（跨度）：**
- 跨度ID、链路ID、父跨度ID
- 操作名称
- 开始时间、结束时间、持续时间
- 级别（DEBUG, INFO, WARNING, ERROR）
- 标签、日志
- 状态、错误信息

**Trace（追踪）：**
- 链路ID、根跨度ID
- 服务名称、操作名称
- 创建时间、更新时间
- 状态
- 所有跨度列表

### 6. 测试覆盖

**文件：** `tests/test_stage18_trace_manager.py`

**测试用例：** 31个，全部通过

**测试覆盖：**
- 链路级别枚举测试
- ID生成器测试
- 跨度测试
- 追踪测试
- 上下文测试
- 上下文管理器测试
- 存储测试
- 导出器测试
- 管理器测试
- 全局管理器测试

## 验收标准检查

| 验收项 | 完成状态 | 说明 |
|--------|----------|------|
| TraceID生成 | ✅ 完成 | UUID生成 + 分布式ID生成 |
| 链路传递 | ✅ 完成 | 上下文传递 + 自动传播（header） |
| 链路存储 | ✅ 完成 | 内存存储 + 持久化（JSON） |
| 链路查询 | ✅ 完成 | 日志查询 + JSON可视化 |

## 技术实现要点

### 1. 线程本地存储
```python
class TraceContext:
    _local = threading.local()
```

### 2. 链路ID生成
```python
@staticmethod
def generate_distributed_id(timestamp=None, worker_id=1, sequence=0):
    # Snowflake风格ID
    return str((timestamp << 22) | (worker_id << 12) | sequence)
```

### 3. 上下文传播
```python
def inject_context(self, carrier):
    carrier["X-Trace-ID"] = ctx.get_trace_id()
    carrier["X-Span-ID"] = ctx.get_span_id()
    return carrier
```

### 4. 跨度管理
```python
span = manager.start_span("operation")
span.add_tag("key", "value")
span.add_log("message")
manager.end_span(span, "completed")
```

## 使用示例

### 开始追踪
```python
from src.architecture import get_trace_manager

manager = get_trace_manager()
trace = manager.start_trace(
    "generate_code",
    "code-generator-service",
    tags={"env": "production"}
)
```

### 创建跨度
```python
span = manager.start_span(
    "parse_input",
    level=TraceLevel.INFO
)
span.add_tag("input_type", "python")
span.add_log("Parsing input file")
```

### 结束跨度
```python
manager.end_span(span, status="completed")
manager.end_trace(trace)
```

### 上下文传播（HTTP）
```python
# 在发送端
carrier = {}
manager.inject_context(carrier)
# carrier = {"X-Trace-ID": "...", "X-Span-ID": "..."}

# 在接收端
manager2 = TraceManager()
ctx = manager2.extract_context(carrier)
```

### 查询追踪
```python
traces = manager.query_traces(
    service_name="code-generator-service",
    status="completed",
    limit=100
)
```

### 导出追踪
```python
json_str = manager.export_trace(trace_id)
```

### 统计信息
```python
stats = manager.get_stats()
print(f"总追踪数: {stats['total_traces']}")
print(f"活跃追踪: {stats['active_traces']}")
```

## 文件清单

### 新增文件
- [`src/architecture/trace_manager.py`](file:///workspace/src/architecture/trace_manager.py) - 链路追踪核心实现
- [`tests/test_stage18_trace_manager.py`](file:///workspace/tests/test_stage18_trace_manager.py) - 阶段18验收测试

### 修改文件
- [`src/architecture/__init__.py`](file:///workspace/src/architecture/__init__.py) - 导出新增模块
- [`pyproject.toml`](file:///workspace/pyproject.toml) - 临时修改后已恢复

## 测试结果

```
============================== 31 passed in 0.13s ==============================
```

所有31个测试用例全部通过，包括：
- 链路级别枚举测试（1个）
- ID生成器测试（4个）
- 跨度测试（5个）
- 追踪测试（3个）
- 上下文测试（3个）
- 上下文管理器测试（4个）
- 存储测试（4个）
- 导出器测试（1个）
- 管理器测试（4个）
- 全局管理器测试（2个）

## 后续阶段建议

阶段18已完成，建议继续进行阶段19：搭建全局权限与读写约束。
