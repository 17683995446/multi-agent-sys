"""
Stage 1: Environment Setup Tests

验证标准：
- Python版本 >= 3.11
- 所有核心依赖包可正常导入
- 配置系统正常工作
"""

import sys
from pathlib import Path


class TestPythonVersion:
    """测试Python版本要求"""

    def test_python_version(self):
        """验证Python版本 >= 3.11"""
        assert sys.version_info >= (3, 11), f"Python版本 {sys.version_info} 不满足要求 (需要 >= 3.11)"


class TestCoreDependencies:
    """测试核心依赖包"""

    def test_langgraph(self):
        """验证LangGraph安装"""
        from langgraph.graph import StateGraph
        assert StateGraph is not None

    def test_autogen(self):
        """验证AutoGen安装"""
        try:
            import autogen_agentchat
            assert True
        except ImportError:
            try:
                import autogen_core
                assert True
            except ImportError:
                assert False, "AutoGen未正确安装"

    def test_pydantic(self):
        """验证Pydantic安装"""
        import pydantic
        assert hasattr(pydantic, 'BaseModel')

    def test_yaml(self):
        """验证PyYAML安装"""
        import yaml
        assert hasattr(yaml, 'safe_load')

    def test_structlog(self):
        """验证structlog安装"""
        import structlog
        assert hasattr(structlog, 'get_logger')

    def test_pytest(self):
        """验证Pytest安装"""
        import pytest
        assert hasattr(pytest, '__version__')


class TestProjectStructure:
    """测试项目结构"""

    def test_project_root(self):
        """验证项目根目录存在"""
        project_root = Path(__file__).parent.parent
        assert project_root.exists()

    def test_pyproject_exists(self):
        """验证pyproject.toml存在"""
        project_root = Path(__file__).parent.parent
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml不存在"

    def test_requirements_exists(self):
        """验证requirements.txt存在"""
        project_root = Path(__file__).parent.parent
        requirements = project_root / "requirements.txt"
        assert requirements.exists(), "requirements.txt不存在"

    def test_src_package_exists(self):
        """验证src包存在"""
        project_root = Path(__file__).parent.parent
        src_package = project_root / "src"
        assert src_package.exists(), "src目录不存在"

    def test_src_package_importable(self):
        """验证src包可导入"""
        import src
        assert hasattr(src, '__version__')


class TestConfiguration:
    """测试配置系统"""

    def test_config_module_structure(self):
        """验证配置模块结构"""
        project_root = Path(__file__).parent.parent
        config_dir = project_root / "config"
        assert config_dir.exists(), "config目录不存在"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
