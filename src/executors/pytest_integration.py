from __future__ import annotations

import importlib
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class TestStatus(Enum):
    """测试状态"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """单个测试结果"""
    name: str
    status: TestStatus
    duration: float = 0.0
    error_message: Optional[str] = None
    nodeid: str = ""


@dataclass
class TestSuiteResult:
    """测试套件结果"""
    test_results: List[TestResult] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests


@dataclass
class FixtureDef:
    """Fixture定义"""
    name: str
    scope: str = "function"  # function, class, module, session
    autouse: bool = False
    factory: Optional[Callable] = None
    params: List[Any] = field(default_factory=list)


class PytestRunner:
    """Pytest测试运行器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.verbosity: int = 1
        self.capture: str = "fd"  # no, fd, sys, tee-sys
        self.tb_style: str = "long"  # short, long, line, native, no
        self.addopts: List[str] = []
        self.fixtures: Dict[str, FixtureDef] = {}
    
    def discover_tests(self, directory: Optional[Path] = None) -> List[str]:
        """发现测试文件"""
        test_dir = directory or self.project_root / "tests"
        if not test_dir.exists():
            return []
        
        test_files = []
        for path in test_dir.rglob("test_*.py"):
            test_files.append(str(path))
        return test_files
    
    def run_tests(
        self,
        test_files_or_dirs: Optional[List[str]] = None,
        verbose: bool = False,
        capture_output: bool = True,
        with_coverage: bool = False,
    ) -> TestSuiteResult:
        """运行测试"""
        cmd = [sys.executable, "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.extend(["-q", "-q"])
        
        if not capture_output:
            cmd.extend(["-s", "--no-header", "--no-summary"])
        
        if with_coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        
        if test_files_or_dirs:
            cmd.extend(test_files_or_dirs)
        else:
            cmd.append("tests/")
        
        cmd.extend(self.addopts)
        
        result = TestSuiteResult()
        
        try:
            process_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )
            
            stdout = process_result.stdout
            stderr = process_result.stderr
            
            # 解析测试结果（简化版）
            self._parse_test_output(stdout, stderr, result)
            
        except Exception as e:
            result.errors += 1
            result.duration = 0.0
        
        return result
    
    def _parse_test_output(
        self,
        stdout: str,
        stderr: str,
        result: TestSuiteResult,
    ) -> None:
        """解析测试输出"""
        # 简化版解析，实际可使用pytest插件或json输出
        if "collected" in stdout:
            # 尝试从输出中提取一些信息
            lines = stdout.splitlines()
            
            passed_count = 0
            failed_count = 0
            skipped_count = 0
            
            for line in lines:
                if line.startswith("."):
                    passed_count += line.count(".")
                elif line.startswith("F"):
                    failed_count += line.count("F")
                elif line.startswith("s"):
                    skipped_count += line.count("s")
            
            if passed_count > 0 or failed_count > 0 or skipped_count > 0:
                result.passed = passed_count
                result.failed = failed_count
                result.skipped = skipped_count
                result.total_tests = passed_count + failed_count + skipped_count
    
    def add_fixture(self, fixture: FixtureDef) -> "PytestRunner":
        """添加自定义fixture"""
        self.fixtures[fixture.name] = fixture
        return self
    
    def add_option(self, option: str) -> "PytestRunner":
        """添加pytest命令行选项"""
        self.addopts.append(option)
        return self
    
    def set_verbosity(self, level: int) -> "PytestRunner":
        """设置详细程度"""
        self.verbosity = level
        return self


class TestCollector:
    """测试收集器"""
    
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path.cwd()
    
    def collect_test_classes(self, module_path: str) -> List[str]:
        """收集测试类"""
        classes = []
        try:
            module_name = self._file_to_module_name(module_path)
            module = importlib.import_module(module_name)
            
            for attr_name in dir(module):
                if attr_name.startswith("Test"):
                    classes.append(attr_name)
        except Exception:
            pass
        return classes
    
    def collect_test_functions(self, module_path: str) -> List[str]:
        """收集测试函数"""
        functions = []
        try:
            module_name = self._file_to_module_name(module_path)
            module = importlib.import_module(module_name)
            
            for attr_name in dir(module):
                if attr_name.startswith("test_"):
                    functions.append(attr_name)
        except Exception:
            pass
        return functions
    
    def _file_to_module_name(self, file_path: str) -> str:
        """文件路径转模块名"""
        path = Path(file_path)
        parts = list(path.parts)
        
        # 查找项目根目录
        if "tests" in parts:
            idx = parts.index("tests")
            parts = parts[idx:]
        
        # 去掉.py后缀
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        
        return ".".join(parts)


class FixtureRegistry:
    """Fixture注册表"""
    
    def __init__(self):
        self._fixtures: Dict[str, FixtureDef] = {}
    
    def register(self, fixture: FixtureDef) -> "FixtureRegistry":
        """注册fixture"""
        self._fixtures[fixture.name] = fixture
        return self
    
    def unregister(self, name: str) -> "FixtureRegistry":
        """注销fixture"""
        if name in self._fixtures:
            del self._fixtures[name]
        return self
    
    def get(self, name: str) -> Optional[FixtureDef]:
        """获取fixture"""
        return self._fixtures.get(name)
    
    def list_all(self) -> List[FixtureDef]:
        """列出所有fixture"""
        return list(self._fixtures.values())


class CoverageConfig:
    """覆盖率配置"""
    
    def __init__(self):
        self.source: List[str] = ["src"]
        self.omit: List[str] = ["*/tests/*", "*/test_*.py"]
        self.minimum_percent: float = 80.0
        self.report_formats: List[str] = ["term-missing"]
    
    def to_pytest_args(self) -> List[str]:
        """转换为pytest参数"""
        args = []
        for source in self.source:
            args.extend(["--cov", source])
        for fmt in self.report_formats:
            args.extend(["--cov-report", fmt])
        return args


class PytestIntegration:
    """Pytest集成入口"""
    
    def __init__(self):
        self.runner = PytestRunner()
        self.collector = TestCollector()
        self.fixture_registry = FixtureRegistry()
        self.coverage_config = CoverageConfig()
    
    def run_full_test_suite(
        self,
        with_coverage: bool = False,
    ) -> TestSuiteResult:
        """运行完整测试套件"""
        test_files = self.runner.discover_tests()
        return self.runner.run_tests(
            test_files,
            with_coverage=with_coverage,
        )
    
    def run_specific_tests(
        self,
        test_patterns: List[str],
    ) -> TestSuiteResult:
        """运行特定测试"""
        return self.runner.run_tests(test_patterns)
    
    def register_custom_fixtures(self) -> None:
        """注册自定义fixture"""
        # 可在这里添加项目特定的fixture
        pass


# 常用fixture工厂
def temp_file_fixture(tmp_path):
    """临时文件fixture"""
    return tmp_path / "test_file.txt"


def sample_data_fixture():
    """示例数据fixture"""
    return {"key": "value", "list": [1, 2, 3]}
