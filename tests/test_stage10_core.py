import logging
import os
import tempfile
from pathlib import Path
from typing import Dict
import pytest

from src.core import (
    # 日志系统
    LogLevel,
    setup_logging,
    get_logger,
    # 异常体系
    MAESError,
    ConfigurationError,
    InvalidPathError,
    AgentError,
    TaskError,
    CodeError,
    # 配置管理
    Config,
    # 路径管理
    PathManager,
    # 全局初始化
    initialize,
    get_config,
    get_path_manager,
)


class TestLoggingSystem:
    """测试日志系统"""
    
    def test_log_level_enum(self):
        """测试日志级别枚举"""
        assert LogLevel.DEBUG.value == logging.DEBUG
        assert LogLevel.INFO.value == logging.INFO
        assert LogLevel.WARNING.value == logging.WARNING
        assert LogLevel.ERROR.value == logging.ERROR
        assert LogLevel.CRITICAL.value == logging.CRITICAL
    
    def test_setup_logging(self):
        """测试设置日志"""
        logger = setup_logging(level=LogLevel.DEBUG, console=True, file_path=None)
        assert logger is not None
        assert logger.name == "multi_agent_engineering_system"
        assert logger.level == logging.DEBUG
    
    def test_get_logger(self):
        """测试获取日志记录器"""
        root_logger = get_logger()
        assert root_logger.name == "multi_agent_engineering_system"
        
        child_logger = get_logger("test")
        assert child_logger.name == "multi_agent_engineering_system.test"
    
    def test_logging_works(self):
        """测试日志实际可用"""
        logger = get_logger("test_logging")
        logger.info("测试消息")
        # 只要没有抛出异常，日志就工作正常
        assert True


class TestExceptionSystem:
    """测试异常体系"""
    
    def test_base_exception(self):
        """测试基础异常"""
        ex = MAESError("测试消息", code="E123", details={"key": "value"})
        assert ex.message == "测试消息"
        assert ex.code == "E123"
        assert ex.details == {"key": "value"}
        assert str(ex) == "测试消息"
    
    def test_configuration_error(self):
        """测试配置错误"""
        ex = ConfigurationError("配置错误", key="test_key")
        assert ex.code == "E002"
        assert ex.key == "test_key"
    
    def test_invalid_path_error(self):
        """测试路径错误"""
        ex = InvalidPathError("路径错误", path="/test/path")
        assert ex.code == "E003"
        assert ex.path == "/test/path"
    
    def test_agent_error(self):
        """测试Agent错误"""
        ex = AgentError("Agent错误", agent_name="test_agent")
        assert ex.code == "E004"
        assert ex.agent_name == "test_agent"
    
    def test_task_error(self):
        """测试任务错误"""
        ex = TaskError("任务错误", task_id="task_123")
        assert ex.code == "E005"
        assert ex.task_id == "task_123"
    
    def test_code_error(self):
        """测试代码错误"""
        ex = CodeError("代码错误", file="test.py", line=42)
        assert ex.code == "E006"
        assert ex.file == "test.py"
        assert ex.line == 42


class TestConfigSystem:
    """测试配置系统"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        assert config.project_root == Path.cwd()
        assert config.log_level == LogLevel.INFO
        assert config.log_dir is not None
        assert config.data_dir is not None
        assert config.config_dir is not None
        assert config.test_dir is not None
    
    def test_config_from_env(self):
        """测试从环境变量加载配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            os.environ["MAES_PROJECT_ROOT"] = str(temp_path)
            os.environ["MAES_LOG_LEVEL"] = "DEBUG"
            
            config = Config.from_env()
            
            assert config.project_root == temp_path
            assert config.log_level == LogLevel.DEBUG
            
            # 清理环境变量
            os.environ.pop("MAES_PROJECT_ROOT", None)
            os.environ.pop("MAES_LOG_LEVEL", None)
    
    def test_config_to_dict(self):
        """测试配置转换为字典"""
        config = Config()
        config_dict = config.to_dict()
        assert "project_root" in config_dict
        assert "log_level" in config_dict
        assert "log_dir" in config_dict
        assert "data_dir" in config_dict
        assert config_dict["log_level"] == "INFO"
    
    def test_config_update_from_dict(self):
        """测试从字典更新配置"""
        config = Config()
        update_data: Dict = {
            "log_level": "WARNING",
        }
        config._update_from_dict(update_data)
        assert config.log_level == LogLevel.WARNING


class TestPathManager:
    """测试路径管理"""
    
    def test_path_manager_init(self):
        """测试路径管理器初始化"""
        config = Config()
        path_manager = PathManager(config)
        assert path_manager.config == config
    
    def test_get_project_root(self):
        """测试获取项目根目录"""
        config = Config()
        path_manager = PathManager(config)
        project_root = path_manager.get_project_root()
        assert project_root == Path.cwd()
    
    def test_get_log_dir(self):
        """测试获取日志目录"""
        config = Config()
        path_manager = PathManager(config)
        log_dir = path_manager.get_log_dir()
        assert log_dir is not None
    
    def test_get_data_dir(self):
        """测试获取数据目录"""
        config = Config()
        path_manager = PathManager(config)
        data_dir = path_manager.get_data_dir()
        assert data_dir is not None
    
    def test_get_source_dir(self):
        """测试获取源代码目录"""
        config = Config()
        path_manager = PathManager(config)
        source_dir = path_manager.get_source_dir()
        assert source_dir == Path.cwd() / "src"
    
    def test_get_test_dir(self):
        """测试获取测试目录"""
        config = Config()
        path_manager = PathManager(config)
        test_dir = path_manager.get_test_dir()
        assert test_dir == Path.cwd() / "tests"
    
    def test_resolve_relative_path(self):
        """测试解析相对路径"""
        config = Config()
        path_manager = PathManager(config)
        
        relative = "test/path"
        resolved = path_manager.resolve_relative(relative)
        assert resolved.is_absolute()
        assert resolved == (Path.cwd() / relative).resolve()
    
    def test_resolve_absolute_path(self):
        """测试解析绝对路径"""
        config = Config()
        path_manager = PathManager(config)
        
        absolute = Path("/test/absolute/path")
        resolved = path_manager.resolve_relative(absolute)
        assert resolved == absolute
    
    def test_ensure_dir(self):
        """测试确保目录存在"""
        config = Config()
        path_manager = PathManager(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / "new_dir"
            assert not test_path.exists()
            
            result = path_manager.ensure_dir(test_path)
            assert result.exists()
            assert result.is_dir()
    
    def test_get_temp_dir(self):
        """测试获取临时目录"""
        config = Config()
        path_manager = PathManager(config)
        
        temp_dir = path_manager.get_temp_dir()
        assert temp_dir.exists()
        assert temp_dir.is_dir()


class TestGlobalInitialization:
    """测试全局初始化"""
    
    def test_get_config(self):
        """测试获取全局配置"""
        config = get_config()
        assert config is not None
    
    def test_get_path_manager(self):
        """测试获取全局路径管理器"""
        path_manager = get_path_manager()
        assert path_manager is not None
    
    def test_initialize(self):
        """测试全局初始化"""
        initialize()
        config = get_config()
        path_manager = get_path_manager()
        assert config is not None
        assert path_manager is not None


class TestIntegration:
    """测试集成使用"""
    
    def test_log_and_error_together(self):
        """测试日志和异常一起使用"""
        logger = get_logger("integration")
        
        try:
            raise ConfigurationError("测试配置错误", key="test_key")
        except ConfigurationError as e:
            logger.error(f"发生错误: {e} (代码: {e.code})")
            assert e.code == "E002"
            assert e.key == "test_key"
    
    def test_config_and_paths_together(self):
        """测试配置和路径一起使用"""
        config = Config()
        path_manager = PathManager(config)
        
        log_dir = path_manager.get_log_dir()
        data_dir = path_manager.get_data_dir()
        
        assert log_dir is not None
        assert data_dir is not None
