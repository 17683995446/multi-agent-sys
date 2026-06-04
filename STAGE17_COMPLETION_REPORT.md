# 阶段17完成报告：定义全局唯一错误码体系

## 阶段概述

本阶段实现了完整的全局唯一错误码体系，包括错误码规范定义、动态注册机制、错误处理链和友好提示系统。

## 完成的工作

### 1. 错误码规范与枚举定义

**核心组件：**
- `ErrorSeverity` - 错误严重级别枚举（INFO, WARNING, ERROR, CRITICAL）
- `ErrorCategory` - 错误分类枚举（SYSTEM, INPUT, CONFIG, NETWORK, AGENT, TASK, CODE, FILE, PERMISSION）
- `ErrorCode` - 错误码数据类，包含完整的元信息
- `ErrorCodes` - 全局唯一错误码枚举，包含27个预定义错误码

**预定义错误码类别：**
- SYS-0xx - 系统错误
- INP-1xx - 输入错误
- CFG-2xx - 配置错误
- NET-3xx - 网络错误
- AGT-4xx - Agent错误
- TSK-5xx - 任务错误
- CODE-6xx - 代码错误
- FILE-7xx - 文件错误
- PER-8xx - 权限错误

**关键特性：**
- 每个错误码都有：唯一编码、名称、分类、严重级别、消息模板、描述、建议修复、元数据
- 完整的消息模板系统，支持参数化消息
- 内置建议修复方案

### 2. 错误码注册与动态映射机制

**核心组件：**
- `ErrorRegistry` - 错误码注册表
- 全局单例访问：`get_error_registry()` / `reset_error_registry()`

**功能：**
- 自动注册所有预定义错误码
- 支持按分类查找错误码
- 支持按严重级别查找错误码
- 支持列出所有错误码
- 支持动态注册新错误码

### 3. 完整错误处理链与异常链支持

**核心组件：**
- `ErrorContext` - 错误上下文，支持链式调用添加属性
- `MASError` - MA系统基础异常类
- `ErrorChain` - 错误链，支持存储和访问多个错误

**关键特性：**
- 完整的异常链支持（cause参数）
- 支持错误上下文传递（用户信息、任务ID等）
- 支持链式API设计
- 自动消息格式化
- 支持to_dict()方法序列化

**错误链功能：**
- 添加多个错误到链中
- 获取最新错误
- 获取所有错误
- 检查是否有错误
- 完整的链式记录

### 4. 错误可视化与友好提示系统

**核心组件：**
- `create_error()` - 快速创建错误的工厂函数
- `format_error_for_display()` - 格式化错误用于显示
- `ErrorHandler` - 错误处理器，支持按分类注册处理器
- `get_error_handler()` - 获取全局错误处理器

**功能：**
- 格式化错误为友好的显示格式
- 包含状态、错误码、严重级别、消息、建议、详细信息
- 支持按分类注册处理器
- 支持默认处理器
- 完整的全局错误处理系统

### 5. 测试覆盖

**文件：** `tests/test_stage17_error_codes.py`

**测试用例：** 30个，全部通过

**测试覆盖：**
- 错误码枚举测试
- 错误上下文测试
- MASError异常测试
- 错误链测试
- 错误注册表测试
- 创建错误函数测试
- 错误显示格式化测试
- 错误处理器测试
- 枚举值测试

### 6. 规范文档

**文件：** `ERROR_CODES.md`

**内容：**
- 错误码格式规范
- 完整的错误码映射表
- 使用规范和示例
- 前缀定义说明

## 验收标准检查

| 验收项 | 完成状态 | 说明 |
|--------|----------|------|
| 错误码规范 | ✅ 完成 | 完整的规范文档 + 完整映射表 |
| 错误码注册 | ✅ 完成 | 完整枚举定义 + 动态注册 |
| 错误处理链 | ✅ 完成 | 基本处理 + 完整异常链 |
| 错误可视化 | ✅ 完成 | 日志输出 + 友好提示 |

## 技术实现要点

### 1. 错误码设计
每个错误码包含：
```python
ErrorCode(
    code="TSK-001",
    name="TaskNotFound",
    category=ErrorCategory.TASK,
    severity=ErrorSeverity.ERROR,
    message_template="任务未找到: {task_id}",
    description="指定的任务不存在",
    suggested_fixes=["检查task_id是否正确"]
)
```

### 2. 上下文传递
支持链式API：
```python
context = ErrorContext().add("user", "alice").add("task", "123")
```

### 3. 异常链
支持cause参数：
```python
try:
    ...
except Exception as e:
    raise MASError(ErrorCodes.TASK_FAILED, ..., cause=e)
```

### 4. 错误处理注册
支持按分类注册：
```python
handler = get_error_handler()
handler.register(ErrorCategory.TASK, handler_func)
handler.register_default(default_handler)
```

## 使用示例

### 创建错误
```python
from src.architecture import ErrorCodes, create_error

err = create_error(
    ErrorCodes.INVALID_INPUT,
    message_args={"field": "name", "value": ""}
)
```

### 抛出自定义异常
```python
from src.architecture import MASError, ErrorCodes, ErrorContext

try:
    # 一些操作
except Exception as e:
    raise MASError(
        ErrorCodes.TASK_FAILED,
        message_args={"task_id": "123", "reason": str(e)},
        context=ErrorContext().add("user", "alice"),
        cause=e
    )
```

### 错误链使用
```python
from src.architecture import ErrorChain

chain = ErrorChain()
chain.add(err1).add(err2)
latest = chain.get_latest()
all_errors = chain.get_all()
```

### 错误处理
```python
from src.architecture import get_error_handler, ErrorCategory

def handle_task_error(err):
    print(f"处理任务错误: {err}")

handler = get_error_handler()
handler.register(ErrorCategory.TASK, handle_task_error)
handler.handle(err)
```

### 格式化显示
```python
from src.architecture import format_error_for_display

display = format_error_for_display(err)
print(display["friendly_message"])
```

### 查找错误码
```python
from src.architecture import get_error_registry, ErrorCategory

registry = get_error_registry()
task_errors = registry.find_by_category(ErrorCategory.TASK)
```

## 文件清单

### 新增文件
- [`src/architecture/error_codes.py`](file:///workspace/src/architecture/error_codes.py) - 错误码核心实现
- [`tests/test_stage17_error_codes.py`](file:///workspace/tests/test_stage17_error_codes.py) - 阶段17验收测试
- [`ERROR_CODES.md`](file:///workspace/ERROR_CODES.md) - 错误码规范文档

### 修改文件
- [`src/architecture/__init__.py`](file:///workspace/src/architecture/__init__.py) - 导出新增模块
- [`pyproject.toml`](file:///workspace/pyproject.toml) - 临时修改后已恢复

## 测试结果

```
============================== 30 passed in 0.10s ==============================
```

所有30个测试用例全部通过，包括：
- 错误码枚举测试（4个）
- 错误上下文测试（3个）
- MASError异常测试（5个）
- 错误链测试（4个）
- 错误注册表测试（5个）
- 创建错误函数测试（1个）
- 错误显示格式化测试（2个）
- 错误处理器测试（4个）
- 枚举值测试（2个）

## 后续阶段建议

阶段17已完成，建议继续进行阶段18：定义全局可追溯链路ID机制。
