"""
阶段23验收测试 - 方法四段式结构自动重构

验收标准：
1. ✓ 四段式模板定义完整
2. ✓ 自动识别段功能实现
3. ✓ 自动重构功能实现
4. ✓ 重构验证功能实现
"""

import pytest
import ast
from src.architecture import (
    SectionType,
    RefactorStrategy,
    CodeSegment,
    MethodStructure,
    RefactoredMethod,
    FourSectionTemplate,
    SectionIdentifier,
    FourSectionRefactor,
    RefactorValidator,
    FourSectionRefactorEngine,
    get_four_section_refactor_engine,
    reset_four_section_refactor_engine
)


class TestSectionIdentifier:
    """测试代码段识别器"""
    
    def test_identify_validation_section(self):
        """测试识别输入校验段"""
        source_code = """
def validate_input(x):
    if not x:
        raise ValueError("Invalid input")
    if x < 0:
        raise ValueError("Negative not allowed")
    return x
"""
        identifier = SectionIdentifier()
        sections = identifier.identify_method_sections(source_code)
        
        assert SectionType.INPUT_VALIDATION in sections
        assert len(sections[SectionType.INPUT_VALIDATION]) > 0
    
    def test_identify_business_logic_section(self):
        """测试识别业务处理段"""
        source_code = """
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
"""
        identifier = SectionIdentifier()
        sections = identifier.identify_method_sections(source_code)
        
        assert SectionType.BUSINESS_LOGIC in sections
        assert len(sections[SectionType.BUSINESS_LOGIC]) > 0
    
    def test_identify_exception_handling_section(self):
        """测试识别异常处理段"""
        source_code = """
def safe_operation():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        result = 0
    return result
"""
        identifier = SectionIdentifier()
        sections = identifier.identify_method_sections(source_code)
        
        assert SectionType.EXCEPTION_HANDLING in sections
    
    def test_identify_return_section(self):
        """测试识别结果返回段"""
        source_code = """
def get_value():
    return 42
"""
        identifier = SectionIdentifier()
        sections = identifier.identify_method_sections(source_code)
        
        assert SectionType.RESULT_RETURN in sections


class TestFourSectionTemplate:
    """测试四段式模板"""
    
    def test_generate_standard_template(self):
        """测试生成标准模板"""
        sections = {
            SectionType.INPUT_VALIDATION: CodeSegment(
                section_type=SectionType.INPUT_VALIDATION,
                content="if not x:\n    raise ValueError()"
            ),
            SectionType.BUSINESS_LOGIC: CodeSegment(
                section_type=SectionType.BUSINESS_LOGIC,
                content="result = x * 2"
            ),
            SectionType.RESULT_RETURN: CodeSegment(
                section_type=SectionType.RESULT_RETURN,
                content="return result"
            )
        }
        
        code = FourSectionTemplate.get_template(
            "test_method",
            ["x"],
            "int",
            "Test method",
            sections
        )
        
        assert "def test_method" in code
        assert "INPUT_VALIDATION" in code
        assert "BUSINESS_LOGIC" in code
        assert "RESULT_RETURN" in code
    
    def test_generate_minimal_template(self):
        """测试生成最小模板"""
        code = FourSectionTemplate.get_minimal_template(
            "minimal_method",
            ["x", "y"],
            "str",
            "Minimal template"
        )
        
        assert "def minimal_method" in code
        assert "=== INPUT VALIDATION ===" in code
        assert "=== BUSINESS LOGIC ===" in code
        assert "=== EXCEPTION HANDLING ===" in code
        assert "=== RESULT RETURN ===" in code


class TestFourSectionRefactor:
    """测试四段式重构器"""
    
    def test_analyze_simple_method(self):
        """测试分析简单方法"""
        method_code = """
def add_numbers(a, b):
    if a is None or b is None:
        raise ValueError("Parameters cannot be None")
    return a + b
"""
        refactorer = FourSectionRefactor()
        structure = refactorer.analyze_structure(method_code)
        
        assert structure.method_name == "add_numbers"
        assert len(structure.parameters) == 2
        assert structure.validation_passed
    
    def test_refactor_simple_method(self):
        """测试重构简单方法"""
        method_code = """
def multiply(x, y):
    if not x or not y:
        raise ValueError("Invalid input")
    result = x * y
    return result
"""
        refactorer = FourSectionRefactor()
        structure = refactorer.analyze_structure(method_code)
        refactored = refactorer.refactor(structure)
        
        assert refactored.refactored_code
        assert "def multiply" in refactored.refactored_code
        assert len(refactored.applied_sections) > 0


class TestRefactorValidator:
    """测试重构验证器"""
    
    def test_validate_valid_syntax(self):
        """测试验证有效语法"""
        validator = RefactorValidator()
        valid_code = """
def test_func(x):
    return x * 2
"""
        is_valid, error = validator.validate_syntax(valid_code)
        assert is_valid
        assert error is None
    
    def test_validate_invalid_syntax(self):
        """测试验证无效语法"""
        validator = RefactorValidator()
        invalid_code = """
def test_func(x)
    return x * 2
"""
        is_valid, error = validator.validate_syntax(invalid_code)
        assert not is_valid
        assert error is not None
    
    def test_validate_four_section_structure(self):
        """测试验证四段式结构"""
        validator = RefactorValidator()
        code = """
def test_method(x):
    # === INPUT VALIDATION ===
    if not x:
        raise ValueError()
    
    # === BUSINESS LOGIC ===
    result = x * 2
    
    # === RESULT RETURN ===
    return result
"""
        is_valid, issues = validator.validate_four_section_structure(code)
        assert is_valid
        assert len(issues) == 0


class TestFourSectionRefactorEngine:
    """测试四段式重构引擎"""
    
    def test_refactor_with_validation(self):
        """测试带验证的重构"""
        engine = FourSectionRefactorEngine()
        method_code = """
def calculate(a, b):
    if a is None or b is None:
        raise ValueError("Invalid input")
    result = a + b
    return result
"""
        refactored = engine.refactor_method(method_code, validate=True)
        
        assert refactored.refactored_code
        assert refactored.validation_result.get("syntax_valid", False)
    
    def test_batch_refactor(self):
        """测试批量重构"""
        engine = FourSectionRefactorEngine()
        methods = [
            "def method1(x): return x * 2",
            "def method2(x): return x / 2",
            "def method3(x): return x + 2"
        ]
        
        refactored_methods = engine.batch_refactor(methods)
        
        assert len(refactored_methods) == 3
        for method in refactored_methods:
            assert method.refactored_code


class TestGlobalEngine:
    """测试全局引擎"""
    
    def test_get_and_reset_engine(self):
        """测试获取和重置引擎"""
        reset_four_section_refactor_engine()
        engine1 = get_four_section_refactor_engine()
        engine2 = get_four_section_refactor_engine()
        
        assert engine1 is engine2
        
        reset_four_section_refactor_engine()
        engine3 = get_four_section_refactor_engine()
        
        assert engine3 is not engine1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
