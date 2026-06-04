from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable, Type


class ErrorSeverity(enum.Enum):
    """错误严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(enum.Enum):
    """错误分类"""
    SYSTEM = "system"
    INPUT = "input"
    CONFIG = "config"
    NETWORK = "network"
    AGENT = "agent"
    TASK = "task"
    CODE = "code"
    FILE = "file"
    PERMISSION = "permission"


@dataclass
class ErrorCode:
    """错误码定义"""
    code: str
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    message_template: str
    description: str = ""
    suggested_fixes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorCodes(enum.Enum):
    """全局唯一错误码枚举"""
    # SYSTEM - 系统错误 (0xx)
    SYSTEM_ERROR = ErrorCode(
        code="SYS-001",
        name="SystemError",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.ERROR,
        message_template="系统错误: {message}",
        description="通用系统错误"
    )
    SYSTEM_INITIALIZATION_FAILED = ErrorCode(
        code="SYS-002",
        name="SystemInitializationFailed",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.CRITICAL,
        message_template="系统初始化失败: {message}",
        description="系统组件初始化失败"
    )
    SYSTEM_SHUTDOWN_FAILED = ErrorCode(
        code="SYS-003",
        name="SystemShutdownFailed",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.ERROR,
        message_template="系统关闭失败: {message}",
        description="系统组件关闭失败"
    )
    RESOURCE_EXHAUSTED = ErrorCode(
        code="SYS-004",
        name="ResourceExhausted",
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.CRITICAL,
        message_template="资源耗尽: {resource}",
        description="系统资源耗尽",
        suggested_fixes=["增加资源配额", "优化资源使用"]
    )
    
    # INPUT - 输入错误 (1xx)
    INVALID_INPUT = ErrorCode(
        code="INP-001",
        name="InvalidInput",
        category=ErrorCategory.INPUT,
        severity=ErrorSeverity.ERROR,
        message_template="无效输入: {field} = {value}",
        description="用户输入验证失败",
        suggested_fixes=["检查输入格式", "提供有效参数"]
    )
    MISSING_INPUT = ErrorCode(
        code="INP-002",
        name="MissingInput",
        category=ErrorCategory.INPUT,
        severity=ErrorSeverity.ERROR,
        message_template="缺少必需输入: {field}",
        description="必需字段缺失"
    )
    INVALID_FORMAT = ErrorCode(
        code="INP-003",
        name="InvalidFormat",
        category=ErrorCategory.INPUT,
        severity=ErrorSeverity.ERROR,
        message_template="格式错误: {format} 格式不正确",
        description="数据格式不符合要求"
    )
    
    # CONFIG - 配置错误 (2xx)
    CONFIG_NOT_FOUND = ErrorCode(
        code="CFG-001",
        name="ConfigNotFound",
        category=ErrorCategory.CONFIG,
        severity=ErrorSeverity.ERROR,
        message_template="配置文件未找到: {path}",
        description="配置文件不存在"
    )
    INVALID_CONFIG = ErrorCode(
        code="CFG-002",
        name="InvalidConfig",
        category=ErrorCategory.CONFIG,
        severity=ErrorSeverity.ERROR,
        message_template="配置无效: {key} = {value}",
        description="配置参数无效"
    )
    MISSING_CONFIG = ErrorCode(
        code="CFG-003",
        name="MissingConfig",
        category=ErrorCategory.CONFIG,
        severity=ErrorSeverity.CRITICAL,
        message_template="缺少必需配置: {key}",
        description="必需配置项缺失"
    )
    
    # NETWORK - 网络错误 (3xx)
    NETWORK_ERROR = ErrorCode(
        code="NET-001",
        name="NetworkError",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        message_template="网络错误: {message}",
        description="网络通信错误"
    )
    CONNECTION_FAILED = ErrorCode(
        code="NET-002",
        name="ConnectionFailed",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        message_template="连接失败: {host}:{port}",
        description="无法建立网络连接",
        suggested_fixes=["检查网络连接", "验证主机地址"]
    )
    TIMEOUT = ErrorCode(
        code="NET-003",
        name="Timeout",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.WARNING,
        message_template="请求超时: {operation} ({timeout}s)",
        description="操作超时"
    )
    
    # AGENT - Agent错误 (4xx)
    AGENT_NOT_FOUND = ErrorCode(
        code="AGT-001",
        name="AgentNotFound",
        category=ErrorCategory.AGENT,
        severity=ErrorSeverity.ERROR,
        message_template="Agent未找到: {agent}",
        description="指定的Agent不存在"
    )
    AGENT_ERROR = ErrorCode(
        code="AGT-002",
        name="AgentError",
        category=ErrorCategory.AGENT,
        severity=ErrorSeverity.ERROR,
        message_template="Agent错误: {agent} - {message}",
        description="Agent执行错误"
    )
    AGENT_TIMEOUT = ErrorCode(
        code="AGT-003",
        name="AgentTimeout",
        category=ErrorCategory.AGENT,
        severity=ErrorSeverity.WARNING,
        message_template="Agent超时: {agent} - 超时 {timeout}s",
        description="Agent执行超时"
    )
    
    # TASK - 任务错误 (5xx)
    TASK_NOT_FOUND = ErrorCode(
        code="TSK-001",
        name="TaskNotFound",
        category=ErrorCategory.TASK,
        severity=ErrorSeverity.ERROR,
        message_template="任务未找到: {task_id}",
        description="指定的任务不存在"
    )
    TASK_FAILED = ErrorCode(
        code="TSK-002",
        name="TaskFailed",
        category=ErrorCategory.TASK,
        severity=ErrorSeverity.ERROR,
        message_template="任务失败: {task_id} - {reason}",
        description="任务执行失败"
    )
    TASK_INVALID_STATE = ErrorCode(
        code="TSK-003",
        name="TaskInvalidState",
        category=ErrorCategory.TASK,
        severity=ErrorSeverity.ERROR,
        message_template="任务状态无效: {task_id} - 状态 {state}",
        description="任务状态不允许该操作"
    )
    DEPENDENCY_FAILED = ErrorCode(
        code="TSK-004",
        name="DependencyFailed",
        category=ErrorCategory.TASK,
        severity=ErrorSeverity.ERROR,
        message_template="依赖任务失败: {dependency_id}",
        description="任务依赖失败"
    )
    
    # CODE - 代码错误 (6xx)
    CODE_ERROR = ErrorCode(
        code="CODE-001",
        name="CodeError",
        category=ErrorCategory.CODE,
        severity=ErrorSeverity.ERROR,
        message_template="代码错误: {message}",
        description="代码生成或解析错误"
    )
    PARSE_ERROR = ErrorCode(
        code="CODE-002",
        name="ParseError",
        category=ErrorCategory.CODE,
        severity=ErrorSeverity.ERROR,
        message_template="解析错误: {file} @ {line}",
        description="代码解析失败"
    )
    COMPILE_ERROR = ErrorCode(
        code="CODE-003",
        name="CompileError",
        category=ErrorCategory.CODE,
        severity=ErrorSeverity.ERROR,
        message_template="编译错误: {message}",
        description="代码编译失败"
    )
    CODE_QUALITY_ERROR = ErrorCode(
        code="CODE-004",
        name="CodeQualityError",
        category=ErrorCategory.CODE,
        severity=ErrorSeverity.WARNING,
        message_template="代码质量问题: {issue}",
        description="代码质量不符合标准"
    )
    
    # FILE - 文件错误 (7xx)
    FILE_NOT_FOUND = ErrorCode(
        code="FILE-001",
        name="FileNotFound",
        category=ErrorCategory.FILE,
        severity=ErrorSeverity.ERROR,
        message_template="文件未找到: {path}",
        description="文件不存在"
    )
    FILE_PERMISSION_ERROR = ErrorCode(
        code="FILE-002",
        name="FilePermissionError",
        category=ErrorCategory.FILE,
        severity=ErrorSeverity.ERROR,
        message_template="文件权限错误: {path}",
        description="文件访问权限不足"
    )
    FILE_IO_ERROR = ErrorCode(
        code="FILE-003",
        name="FileIOError",
        category=ErrorCategory.FILE,
        severity=ErrorSeverity.ERROR,
        message_template="文件IO错误: {path} - {reason}",
        description="文件读写错误"
    )
    
    # PERMISSION - 权限错误 (8xx)
    PERMISSION_DENIED = ErrorCode(
        code="PER-001",
        name="PermissionDenied",
        category=ErrorCategory.PERMISSION,
        severity=ErrorSeverity.ERROR,
        message_template="权限被拒绝: {action} on {resource}",
        description="权限不足"
    )
    UNAUTHORIZED = ErrorCode(
        code="PER-002",
        name="Unauthorized",
        category=ErrorCategory.PERMISSION,
        severity=ErrorSeverity.ERROR,
        message_template="未授权访问: {resource}",
        description="未授权访问资源"
    )


@dataclass
class ErrorContext:
    """错误上下文"""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def add(self, key: str, value: Any) -> "ErrorContext":
        """添加上下文属性"""
        self.attributes[key] = value
        return self
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文属性"""
        return self.attributes.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "context_id": self.context_id,
            "timestamp": self.timestamp.isoformat(),
            "attributes": self.attributes
        }


class MASError(Exception):
    """MA系统基础异常类"""
    
    def __init__(
        self,
        error_code: ErrorCodes,
        message_args: Optional[Dict[str, Any]] = None,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        self.error_code = error_code
        self.code = error_code.value.code
        self.severity = error_code.value.severity
        self.category = error_code.value.category
        self.message_args = message_args or {}
        self.context = context or ErrorContext()
        self.cause = cause
        
        # 格式化消息
        self.message = error_code.value.message_template.format(**self.message_args)
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "code": self.code,
            "name": self.error_code.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "description": self.error_code.value.description,
            "context": self.context.to_dict()
        }
        if self.error_code.value.suggested_fixes:
            result["suggested_fixes"] = self.error_code.value.suggested_fixes
        if self.cause:
            result["cause"] = str(self.cause)
        return result
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
    
    def __repr__(self) -> str:
        return f"MASError({self.error_code}, message_args={self.message_args})"


class ErrorChain:
    """错误链"""
    
    def __init__(self):
        self.errors: List[MASError] = []
        self.chain_id: str = str(uuid.uuid4())
    
    def add(self, error: MASError) -> "ErrorChain":
        """添加错误到链中"""
        self.errors.append(error)
        return self
    
    def get_latest(self) -> Optional[MASError]:
        """获取最新的错误"""
        return self.errors[-1] if self.errors else None
    
    def get_all(self) -> List[MASError]:
        """获取所有错误"""
        return list(self.errors)
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self.errors) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chain_id": self.chain_id,
            "errors": [err.to_dict() for err in self.errors],
            "count": len(self.errors)
        }


class ErrorRegistry:
    """错误码注册表"""
    
    def __init__(self):
        self.registered: Dict[str, ErrorCode] = {}
        for err_code in ErrorCodes:
            self.register(err_code.value)
    
    def register(self, error_code: ErrorCode) -> None:
        """注册错误码"""
        self.registered[error_code.code] = error_code
    
    def get(self, code: str) -> Optional[ErrorCode]:
        """获取错误码"""
        return self.registered.get(code)
    
    def list_all(self) -> List[ErrorCode]:
        """列出所有错误码"""
        return list(self.registered.values())
    
    def find_by_category(self, category: ErrorCategory) -> List[ErrorCode]:
        """按分类查找错误码"""
        return [ec for ec in self.registered.values() if ec.category == category]
    
    def find_by_severity(self, severity: ErrorSeverity) -> List[ErrorCode]:
        """按严重级别查找错误码"""
        return [ec for ec in self.registered.values() if ec.severity == severity]


_global_registry: Optional[ErrorRegistry] = None


def get_error_registry() -> ErrorRegistry:
    """获取全局错误注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ErrorRegistry()
    return _global_registry


def reset_error_registry() -> None:
    """重置全局错误注册表"""
    global _global_registry
    _global_registry = None


def create_error(
    error_code: ErrorCodes,
    message_args: Optional[Dict[str, Any]] = None,
    **kwargs
) -> MASError:
    """创建错误"""
    return MASError(error_code, message_args=message_args, **kwargs)


def format_error_for_display(error: MASError) -> Dict[str, Any]:
    """格式化错误用于显示"""
    result = {
        "status": "error",
        "code": error.code,
        "severity": error.severity.value.upper(),
        "message": str(error),
        "friendly_message": error.message
    }
    
    if error.error_code.value.suggested_fixes:
        result["suggestions"] = error.error_code.value.suggested_fixes
    
    if error.context.attributes:
        result["details"] = error.context.attributes
    
    return result


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.handlers: Dict[ErrorCategory, List[Callable[[MASError], None]]] = {}
        self.default_handlers: List[Callable[[MASError], None]] = []
    
    def register(self, category: ErrorCategory, handler: Callable[[MASError], None]) -> None:
        """注册处理器"""
        if category not in self.handlers:
            self.handlers[category] = []
        self.handlers[category].append(handler)
    
    def register_default(self, handler: Callable[[MASError], None]) -> None:
        """注册默认处理器"""
        self.default_handlers.append(handler)
    
    def handle(self, error: MASError) -> None:
        """处理错误"""
        # 调用特定分类的处理器
        if error.category in self.handlers:
            for handler in self.handlers[error.category]:
                try:
                    handler(error)
                except Exception:
                    pass
        
        # 调用默认处理器
        for handler in self.default_handlers:
            try:
                handler(error)
            except Exception:
                pass


_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler
