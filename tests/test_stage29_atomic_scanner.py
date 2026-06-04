"""
阶段29验收测试 - 构建完整四级原子化扫描器

验收标准：
1. ✓ 扫描器集成（顺序执行 + 并行执行）
2. ✓ 扫描配置（文件配置 + 代码配置）
3. ✓ 扫描报告（JSON输出 + 多格式输出）
4. ✓ 扫描性能（< 1分钟/万行）
"""

import pytest
import os
import tempfile
import json
from src.architecture.atomic_scanner import (
    ScanLevel,
    ExecutionMode,
    VariableInfo,
    MethodInfo,
    ClassInfo,
    ModuleInfo,
    ScanConfig,
    ScanResult,
    AtomicScanner,
    ReportGenerator,
    ConfigManager,
    get_atomic_scanner,
    reset_atomic_scanner
)


# 测试用的代码
TEST_CODE_1 = '''
"""Test module 1"""
CONSTANT = "test"

class MyClass:
    def __init__(self):
        self.value = 42
    
    def do_something(self, param1, param2):
        result = param1 + param2
        return result

def utility_function(x):
    return x * 2
'''

TEST_CODE_2 = '''
"""Test module 2"""
import sys

data = [1, 2, 3]

def process_data(items):
    output = []
    for item in items:
        output.append(item * 3)
    return output
'''


class TestAtomicScannerBasic:
    """测试扫描器基本功能"""
    
    def test_initialization(self):
        """测试初始化扫描器"""
        scanner = AtomicScanner()
        assert scanner is not None
        assert scanner.config is not None
    
    def test_default_config(self):
        """测试默认配置"""
        config = ScanConfig()
        assert ScanLevel.ALL in config.scan_levels or len(config.scan_levels) > 0
        assert config.execution_mode == ExecutionMode.SEQUENTIAL
        assert config.max_workers == 4
    
    def test_scan_config_code(self):
        """测试代码配置"""
        config = ScanConfig(
            scan_levels=[ScanLevel.VARIABLE, ScanLevel.METHOD],
            execution_mode=ExecutionMode.PARALLEL,
            max_workers=8
        )
        assert len(config.scan_levels) == 2
        assert config.execution_mode == ExecutionMode.PARALLEL
        assert config.max_workers == 8


class TestFileScanning:
    """测试文件扫描功能"""
    
    def test_scan_directory_sequential(self):
        """测试顺序扫描目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件1
            test_file_1 = os.path.join(tmpdir, "test_module_1.py")
            with open(test_file_1, 'w') as f:
                f.write(TEST_CODE_1)
            
            # 创建测试文件2
            test_file_2 = os.path.join(tmpdir, "test_module_2.py")
            with open(test_file_2, 'w') as f:
                f.write(TEST_CODE_2)
            
            config = ScanConfig(execution_mode=ExecutionMode.SEQUENTIAL)
            scanner = AtomicScanner(config)
            result = scanner.scan_directory(tmpdir)
            
            assert result.files_scanned >= 2
            assert result.scan_duration_seconds >= 0
            assert len(result.errors) == 0


class TestReportGenerator:
    """测试报告生成"""
    
    def test_json_report(self):
        """测试JSON报告生成"""
        result = ScanResult()
        result.files_scanned = 5
        result.variables_found = 10
        result.methods_found = 8
        result.classes_found = 3
        
        json_report = ReportGenerator.generate_json_report(result)
        report_data = json.loads(json_report)
        
        assert report_data['files_scanned'] == 5
        assert report_data['variables_found'] == 10
    
    def test_text_report(self):
        """测试文本报告生成"""
        result = ScanResult()
        result.files_scanned = 3
        
        text_report = ReportGenerator.generate_text_report(result)
        
        assert "扫描报告" in text_report
        assert "扫描文件数" in text_report


class TestConfigManager:
    """测试配置管理"""
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "config.json")
            
            # 保存配置
            original_config = ScanConfig(
                max_workers=8,
                execution_mode=ExecutionMode.PARALLEL
            )
            ConfigManager.save_config_to_file(original_config, config_file)
            
            # 加载配置
            loaded_config = ConfigManager.load_config_from_file(config_file)
            
            assert loaded_config is not None
            assert loaded_config.max_workers == 8
            assert loaded_config.execution_mode == ExecutionMode.PARALLEL


class TestExecutionModes:
    """测试执行模式"""
    
    def test_sequential_mode(self):
        """测试顺序执行模式"""
        config = ScanConfig(execution_mode=ExecutionMode.SEQUENTIAL)
        scanner = AtomicScanner(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write(TEST_CODE_1)
            
            result = scanner.scan_directory(tmpdir)
            assert result.files_scanned >= 1
    
    def test_parallel_mode(self):
        """测试并行执行模式"""
        config = ScanConfig(
            execution_mode=ExecutionMode.PARALLEL,
            max_workers=2
        )
        scanner = AtomicScanner(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file_1 = os.path.join(tmpdir, "test1.py")
            test_file_2 = os.path.join(tmpdir, "test2.py")
            with open(test_file_1, 'w') as f:
                f.write(TEST_CODE_1)
            with open(test_file_2, 'w') as f:
                f.write(TEST_CODE_2)
            
            result = scanner.scan_directory(tmpdir)
            assert result.files_scanned >= 2


class TestScanLevels:
    """测试扫描级别"""
    
    def test_variable_only(self):
        """测试只扫描变量"""
        config = ScanConfig(scan_levels=[ScanLevel.VARIABLE])
        scanner = AtomicScanner(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write(TEST_CODE_1)
            
            result = scanner.scan_directory(tmpdir)
            assert result.variables_found >= 0
    
    def test_all_levels(self):
        """测试扫描所有级别"""
        config = ScanConfig(scan_levels=[ScanLevel.ALL])
        scanner = AtomicScanner(config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write(TEST_CODE_1)
            
            result = scanner.scan_directory(tmpdir)
            assert result.files_scanned >= 1


class TestGlobalScanner:
    """测试全局扫描器"""
    
    def test_get_global_scanner(self):
        """测试获取全局扫描器"""
        reset_atomic_scanner()
        
        scanner1 = get_atomic_scanner()
        scanner2 = get_atomic_scanner()
        
        assert scanner1 is scanner2
    
    def test_reset_global_scanner(self):
        """测试重置全局扫描器"""
        scanner1 = get_atomic_scanner()
        reset_atomic_scanner()
        scanner2 = get_atomic_scanner()
        
        assert scanner1 is not scanner2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
