# 全局唯一错误码体系

## 错误码格式规范

### 错误码结构
```
{前缀}-{序号}
```

### 前缀定义
| 前缀 | 分类 | 说明 |
|------|------|------|
| SYS | 系统 | 系统级错误 |
| INP | 输入 | 用户输入错误 |
| CFG | 配置 | 配置相关错误 |
| NET | 网络 | 网络通信错误 |
| AGT | Agent | Agent相关错误 |
| TSK | 任务 | 任务相关错误 |
| CODE | 代码 | 代码生成/解析错误 |
| FILE | 文件 | 文件操作错误 |
| PER | 权限 | 权限相关错误 |

## 错误码完整映射表

### SYS - 系统错误 (0xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| SYS-001 | SystemError | ERROR | 通用系统错误 |
| SYS-002 | SystemInitializationFailed | CRITICAL | 系统初始化失败 |
| SYS-003 | SystemShutdownFailed | ERROR | 系统关闭失败 |
| SYS-004 | ResourceExhausted | CRITICAL | 资源耗尽 |

### INP - 输入错误 (1xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| INP-001 | InvalidInput | ERROR | 无效输入 |
| INP-002 | MissingInput | ERROR | 缺少必需输入 |
| INP-003 | InvalidFormat | ERROR | 格式错误 |

### CFG - 配置错误 (2xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| CFG-001 | ConfigNotFound | ERROR | 配置文件未找到 |
| CFG-002 | InvalidConfig | ERROR | 配置无效 |
| CFG-003 | MissingConfig | CRITICAL | 缺少必需配置 |

### NET - 网络错误 (3xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| NET-001 | NetworkError | ERROR | 网络错误 |
| NET-002 | ConnectionFailed | ERROR | 连接失败 |
| NET-003 | Timeout | WARNING | 请求超时 |

### AGT - Agent错误 (4xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| AGT-001 | AgentNotFound | ERROR | Agent未找到 |
| AGT-002 | AgentError | ERROR | Agent错误 |
| AGT-003 | AgentTimeout | WARNING | Agent超时 |

### TSK - 任务错误 (5xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| TSK-001 | TaskNotFound | ERROR | 任务未找到 |
| TSK-002 | TaskFailed | ERROR | 任务失败 |
| TSK-003 | TaskInvalidState | ERROR | 任务状态无效 |
| TSK-004 | DependencyFailed | ERROR | 依赖任务失败 |

### CODE - 代码错误 (6xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| CODE-001 | CodeError | ERROR | 代码错误 |
| CODE-002 | ParseError | ERROR | 解析错误 |
| CODE-003 | CompileError | ERROR | 编译错误 |
| CODE-004 | CodeQualityError | WARNING | 代码质量问题 |

### FILE - 文件错误 (7xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| FILE-001 | FileNotFound | ERROR | 文件未找到 |
| FILE-002 | FilePermissionError | ERROR | 文件权限错误 |
| FILE-003 | FileIOError | ERROR | 文件IO错误 |

### PER - 权限错误 (8xx)
| 错误码 | 名称 | 严重级别 | 说明 |
|--------|------|----------|------|
| PER-001 | PermissionDenied | ERROR | 权限被拒绝 |
| PER-002 | Unauthorized | ERROR | 未授权访问 |

## 使用规范

### 创建错误
```python
from src.architecture import ErrorCodes, create_error, ErrorContext

err = create_error(
    ErrorCodes.INVALID_INPUT,
    message_args={"field": "name", "value": ""},
    context=ErrorContext().add("user", "alice")
)
```

### 抛出自定义异常
```python
from src.architecture import MASError, ErrorCodes

try:
    # 一些操作
except Exception as e:
    raise MASError(
        ErrorCodes.TASK_FAILED,
        message_args={"task_id": "123", "reason": str(e)},
        cause=e
    )
```

### 注册错误处理器
```python
from src.architecture import get_error_handler, ErrorCategory

handler = get_error_handler()
handler.register(ErrorCategory.TASK, lambda err: print(f"任务错误: {err}"))
```
