from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


# ==================== 日志系统 ====================
class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    console: bool = True,
    file_path: Optional[Path] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S",
) -> logging.Logger:
    """设置统一的全局日志系统"""
    logger = logging.getLogger("multi_agent_engineering_system")
    logger.setLevel(level.value)
    logger.handlers = []
    logger.propagate = False

    formatter = logging.Formatter(log_format, date_format)

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level.value)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if file_path:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(level.value)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取统一的日志记录器"""
    if name:
        return logging.getLogger(f"multi_agent_engineering_system.{name}")
    return logging.getLogger("multi_agent_engineering_system")


# ==================== 异常体系 ====================
class MAESError(Exception):
    """多Agent工程系统基础异常类"""
    def __init__(self, message: str, code: str = "E001", details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(MAESError):
    """配置错误"""
    def __init__(self, message: str, key: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message, code="E002", details=details)
        self.key = key


class InvalidPathError(MAESError):
    """路径错误"""
    def __init__(self, message: str, path: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message, code="E003", details=details)
        self.path = path


class AgentError(MAESError):
    """Agent错误"""
    def __init__(self, message: str, agent_name: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message, code="E004", details=details)
        self.agent_name = agent_name


class TaskError(MAESError):
    """任务错误"""
    def __init__(self, message: str, task_id: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message, code="E005", details=details)
        self.task_id = task_id


class CodeError(MAESError):
    """代码错误"""
    def __init__(self, message: str, file: Optional[str] = None, line: Optional[int] = None, details: Optional[Dict] = None):
        super().__init__(message, code="E006", details=details)
        self.file = file
        self.line = line


# ==================== 配置管理 ====================
@dataclass
class Config:
    """统一配置类"""
    project_root: Path = field(default_factory=lambda: Path.cwd())
    log_level: LogLevel = LogLevel.INFO
    log_dir: Optional[Path] = None
    data_dir: Optional[Path] = None
    config_dir: Optional[Path] = None
    test_dir: Optional[Path] = None
    
    def __post_init__(self):
        if self.config_dir is None:
            self.config_dir = self.project_root / "config"
        if self.log_dir is None:
            self.log_dir = self.project_root / "logs"
        if self.data_dir is None:
            self.data_dir = self.project_root / "data"
        if self.test_dir is None:
            self.test_dir = self.project_root / "tests"
    
    @classmethod
    def from_env(cls) -> Config:
        """从环境变量加载配置"""
        config = cls()
        
        if "MAES_PROJECT_ROOT" in os.environ:
            config.project_root = Path(os.environ["MAES_PROJECT_ROOT"])
        
        if "MAES_LOG_LEVEL" in os.environ:
            level_str = os.environ["MAES_LOG_LEVEL"].upper()
            config.log_level = LogLevel[level_str]
        
        for dir_name in ["log", "data", "config", "test"]:
            env_var = f"MAES_{dir_name.upper()}_DIR"
            if env_var in os.environ:
                setattr(config, f"{dir_name}_dir", Path(os.environ[env_var]))
        
        return config
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> Config:
        """从配置文件加载"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise ConfigurationError(f"配置文件不存在: {file_path}", key=str(file_path))
        
        if file_path.suffix in [".yaml", ".yml"]:
            return cls._from_yaml(file_path)
        elif file_path.suffix == ".json":
            return cls._from_json(file_path)
        elif file_path.suffix in [".toml"]:
            return cls._from_toml(file_path)
        else:
            raise ConfigurationError(f"不支持的配置文件格式: {file_path.suffix}", key=str(file_path))
    
    @classmethod
    def _from_yaml(cls, file_path: Path) -> Config:
        """从YAML加载配置"""
        config = cls()
        try:
            import yaml
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if data and isinstance(data, dict):
                config._update_from_dict(data)
        except ImportError:
            get_logger("config").warning("PyYAML不可用，使用默认配置")
        
        return config
    
    @classmethod
    def _from_json(cls, file_path: Path) -> Config:
        """从JSON加载配置"""
        import json
        config = cls()
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if data and isinstance(data, dict):
            config._update_from_dict(data)
        
        return config
    
    @classmethod
    def _from_toml(cls, file_path: Path) -> Config:
        """从TOML加载配置"""
        import tomllib
        config = cls()
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        
        if data and isinstance(data, dict):
            if "tool" in data and "maes" in data["tool"]:
                config._update_from_dict(data["tool"]["maes"])
        
        return config
    
    def _update_from_dict(self, data: Dict[str, Any]):
        """从字典更新配置"""
        if "project_root" in data:
            self.project_root = Path(data["project_root"])
        if "log_level" in data:
            level_str = data["log_level"].upper()
            self.log_level = LogLevel[level_str]
        
        for dir_name in ["log", "data", "config", "test"]:
            key = f"{dir_name}_dir"
            if key in data:
                setattr(self, dir_name, Path(data[key]))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "project_root": str(self.project_root),
            "log_level": self.log_level.name,
            "log_dir": str(self.log_dir) if self.log_dir else None,
            "data_dir": str(self.data_dir) if self.data_dir else None,
            "config_dir": str(self.config_dir) if self.config_dir else None,
            "test_dir": str(self.test_dir) if self.test_dir else None,
        }


# ==================== 路径管理 ====================
class PathManager:
    """统一的路径管理器"""
    
    def __init__(self, config: Config):
        self.config = config
        self._cached_paths: Dict[str, Path] = {}
        self.logger = get_logger("paths")
    
    def get_project_root(self) -> Path:
        """获取项目根目录"""
        return self._cached("project_root", lambda: self.config.project_root)
    
    def get_log_dir(self) -> Path:
        """获取日志目录"""
        return self._cached("log_dir", lambda: self.config.log_dir or (self.config.project_root / "logs"))
    
    def get_data_dir(self) -> Path:
        """获取数据目录"""
        return self._cached("data_dir", lambda: self.config.data_dir or (self.config.project_root / "data"))
    
    def get_config_dir(self) -> Path:
        """获取配置目录"""
        return self._cached("config_dir", lambda: self.config.config_dir or (self.config.project_root / "config"))
    
    def get_test_dir(self) -> Path:
        """获取测试目录"""
        return self._cached("test_dir", lambda: self.config.test_dir or (self.config.project_root / "tests"))
    
    def get_source_dir(self) -> Path:
        """获取源代码目录"""
        return self._cached("source_dir", lambda: self.config.project_root / "src")
    
    def get_temp_dir(self) -> Path:
        """获取临时目录"""
        temp_dir = self._cached("temp_dir", lambda: self.config.project_root / "tmp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir
    
    def ensure_dir(self, path: Union[str, Path]) -> Path:
        """确保目录存在"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def resolve_relative(self, relative_path: Union[str, Path]) -> Path:
        """解析相对路径为绝对路径"""
        if Path(relative_path).is_absolute():
            return Path(relative_path)
        return (self.get_project_root() / relative_path).resolve()
    
    def _cached(self, key: str, creator: Callable[[], Path]) -> Path:
        """缓存路径创建结果"""
        if key not in self._cached_paths:
            path = creator()
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.logger.warning(f"创建目录 {path} 失败: {e}")
            self._cached_paths[key] = path.resolve()
        return self._cached_paths[key]


# ==================== 全局初始化 ====================
_global_config: Optional[Config] = None
_global_logger: Optional[logging.Logger] = None
_global_path_manager: Optional[PathManager] = None


def initialize(config: Optional[Config] = None) -> None:
    """初始化全局系统"""
    global _global_config, _global_logger, _global_path_manager
    
    if config is None:
        config = Config()
    
    _global_config = config
    _global_logger = setup_logging(
        level=config.log_level,
        console=True,
        file_path=config.log_dir / "app.log" if config.log_dir else None
    )
    _global_path_manager = PathManager(config)
    
    _global_logger.info("多Agent工程系统初始化完成")


def get_config() -> Config:
    """获取全局配置"""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def get_path_manager() -> PathManager:
    """获取全局路径管理器"""
    global _global_path_manager
    if _global_path_manager is None:
        _global_path_manager = PathManager(get_config())
    return _global_path_manager
