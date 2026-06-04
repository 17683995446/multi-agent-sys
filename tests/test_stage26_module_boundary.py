"""
阶段26验收测试 - 【模块原子】边界识别

验收标准：
1. ✓ 模块边界检测（目录边界+语义边界）
2. ✓ 接口识别（公共API+完整接口）
3. ✓ 边界验证（导入检查+依赖验证）
4. ✓ 边界报告（文本报告+图形报告）
"""

import pytest
import os
from src.architecture import (
    InterfaceType,
    BoundaryType,
    ModuleInterface,
    ModuleBoundary,
    ModuleInfo,
    BoundaryReport,
    DirectoryBoundaryDetector,
    SemanticBoundaryDetector,
    InterfaceRecognizer,
    BoundaryValidator,
    BoundaryReporter,
    ModuleBoundaryAnalyzer,
    get_module_boundary_analyzer,
    reset_module_boundary_analyzer
)


class TestInterfaceRecognizer:
    """测试接口识别器"""
    
    def test_recognize_public_interface(self):
        """测试识别公共接口"""
        recognizer = InterfaceRecognizer()
        
        # 类名通常以大写字母开头
        assert recognizer.recognize("MyClass") == InterfaceType.PUBLIC
        assert recognizer.recognize("MyInterface") == InterfaceType.PUBLIC
        # 以下划线开头的是私有或受保护
        assert recognizer.recognize("_private_func") == InterfaceType.PROTECTED
    
    def test_recognize_private_interface(self):
        """测试识别私有接口"""
        recognizer = InterfaceRecognizer()
        
        # 全大写的是私有
        assert recognizer.recognize("_PRIVATE_CONSTANT") == InterfaceType.PRIVATE
    
    def test_recognize_magic_interface(self):
        """测试识别魔术接口"""
        recognizer = InterfaceRecognizer()
        
        assert recognizer.recognize("__init__") == InterfaceType.MAGIC
        assert recognizer.recognize("__str__") == InterfaceType.MAGIC
    
    def test_is_public(self):
        """测试判断公共接口"""
        recognizer = InterfaceRecognizer()
        
        assert recognizer.is_public("MyClass") == True
        assert recognizer.is_public("_private") == False


class TestSemanticBoundaryDetector:
    """测试语义边界检测器"""
    
    def test_detect_boundaries(self):
        """测试检测语义边界"""
        source_code = """
class MyClass:
    def __init__(self):
        pass
    
    def public_method(self):
        pass
    
    def _private_method(self):
        pass

def public_function():
    pass

def _private_function():
    pass
"""
        detector = SemanticBoundaryDetector()
        boundary = detector.detect_boundaries(source_code, "test_module")
        
        assert boundary.module_name == "test_module"
        assert boundary.boundary_type == BoundaryType.SEMANTIC
        assert len(boundary.interfaces) > 0
    
    def test_extract_public_api(self):
        """测试提取公共 API"""
        source_code = """
class PublicClass:
    pass

def public_func():
    pass

class _PrivateClass:
    pass

def _private_func():
    pass
"""
        detector = SemanticBoundaryDetector()
        interfaces = detector._extract_public_api(source_code)
        
        public_interfaces = [i for i in interfaces if i.interface_type == InterfaceType.PUBLIC]
        assert len(public_interfaces) >= 2


class TestBoundaryValidator:
    """测试边界验证器"""
    
    def test_validate_boundary_valid(self):
        """测试验证有效边界"""
        boundary = ModuleBoundary(
            boundary_id="test",
            module_name="test_module",
            boundary_type=BoundaryType.SEMANTIC,
            path="test/path",
            interfaces=[
                ModuleInterface("Class1", InterfaceType.PUBLIC, "loc"),
                ModuleInterface("func1", InterfaceType.PUBLIC, "loc"),
            ],
            dependencies=["dep1", "dep2"]
        )
        
        validator = BoundaryValidator()
        is_valid, issues = validator.validate_boundary(boundary)
        
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_boundary_too_many_interfaces(self):
        """测试验证接口过多"""
        boundary = ModuleBoundary(
            boundary_id="test",
            module_name="test_module",
            boundary_type=BoundaryType.SEMANTIC,
            path="test/path",
            interfaces=[
                ModuleInterface(f"Class{i}", InterfaceType.PUBLIC, "loc")
                for i in range(25)
            ],
            dependencies=["dep1"]
        )
        
        validator = BoundaryValidator()
        is_valid, issues = validator.validate_boundary(boundary)
        
        assert not is_valid
        assert len(issues) > 0
    
    def test_validate_boundary_too_many_dependencies(self):
        """测试验证依赖过多"""
        boundary = ModuleBoundary(
            boundary_id="test",
            module_name="test_module",
            boundary_type=BoundaryType.SEMANTIC,
            path="test/path",
            interfaces=[
                ModuleInterface("Class1", InterfaceType.PUBLIC, "loc")
            ],
            dependencies=[f"dep{i}" for i in range(15)]
        )
        
        validator = BoundaryValidator()
        is_valid, issues = validator.validate_boundary(boundary)
        
        assert not is_valid
        assert len(issues) > 0


class TestBoundaryReporter:
    """测试边界报告生成器"""
    
    def test_generate_text_report(self):
        """测试生成文本报告"""
        module_info = ModuleInfo(
            module_name="test_module",
            module_path="/test/path",
            public_classes=["Class1", "Class2"],
            public_functions=["func1"],
            dependencies=["dep1", "dep2"]
        )
        
        report = BoundaryReport(
            module_info=module_info,
            issues=["Issue 1", "Issue 2"]
        )
        
        reporter = BoundaryReporter()
        text = reporter.generate_text_report(report)
        
        assert "test_module" in text
        assert "Class1" in text
        assert "dep1" in text
        assert "Issue 1" in text
    
    def test_generate_json_report(self):
        """测试生成 JSON 报告"""
        module_info = ModuleInfo(
            module_name="test_module",
            module_path="/test/path",
            public_classes=["Class1"],
            public_functions=["func1"]
        )
        
        boundary = ModuleBoundary(
            boundary_id="b1",
            module_name="test",
            boundary_type=BoundaryType.SEMANTIC,
            path="/path",
            interfaces=[ModuleInterface("Class1", InterfaceType.PUBLIC, "loc")],
            dependencies=["d1"]
        )
        
        report = BoundaryReport(
            module_info=module_info,
            boundaries=[boundary]
        )
        
        reporter = BoundaryReporter()
        json_report = reporter.generate_json_report(report)
        
        assert json_report["module_info"]["module_name"] == "test_module"
        assert len(json_report["boundaries"]) == 1


class TestModuleBoundaryAnalyzer:
    """测试模块边界分析器"""
    
    def test_analyze_file(self):
        """测试分析文件"""
        # 创建一个临时文件用于测试
        test_code = """
class TestClass:
    def __init__(self):
        pass
    
    def public_method(self):
        pass

def public_function():
    pass
"""
        # 写入临时文件
        test_file = "/tmp/test_module.py"
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        analyzer = ModuleBoundaryAnalyzer()
        report = analyzer.analyze_module(test_file, "test_module")
        
        assert report.module_info is not None
        assert report.module_info.module_name == "test_module"
        assert len(report.boundaries) > 0
        
        # 清理
        os.remove(test_file)
    
    def test_generate_report(self):
        """测试生成报告"""
        analyzer = ModuleBoundaryAnalyzer()
        
        test_code = """
class MyClass:
    def method(self):
        pass
"""
        test_file = "/tmp/test_report.py"
        with open(test_file, 'w') as f:
            f.write(test_code)
        
        report = analyzer.analyze_module(test_file)
        
        # 生成文本报告
        text_report = report.to_text()
        assert "MODULE BOUNDARY" in text_report
        
        # 生成 JSON 报告
        reporter = BoundaryReporter()
        json_report = reporter.generate_json_report(report)
        assert "module_info" in json_report
        
        # 清理
        os.remove(test_file)


class TestGlobalAnalyzer:
    """测试全局分析器"""
    
    def test_get_and_reset(self):
        """测试获取和重置分析器"""
        reset_module_boundary_analyzer()
        analyzer1 = get_module_boundary_analyzer("/tmp")
        analyzer2 = get_module_boundary_analyzer("/tmp")
        
        assert analyzer1 is analyzer2
        
        reset_module_boundary_analyzer()
        analyzer3 = get_module_boundary_analyzer("/tmp")
        
        assert analyzer3 is not analyzer1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
