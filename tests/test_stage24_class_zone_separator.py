"""
阶段24验收测试 - 【类原子】三区分离（常量/状态/方法）

验收标准：
1. ✓ 类区域识别（基本识别/智能识别）
2. ✓ 常量区提取（静态常量/配置常量）
3. ✓ 状态区提取（实例变量/类变量）
4. ✓ 方法区组织（分组组织/语义分组）
"""

import pytest
import ast
from src.architecture import (
    ZoneType,
    MethodGroupType,
    ConstantType,
    StateType,
    ClassConstant,
    ClassState,
    ClassMethod,
    ClassZone,
    ClassStructure,
    RefactoredClass,
    ClassZoneIdentifier,
    ClassStructureAnalyzer,
    ClassZoneTemplate,
    ClassZoneValidator,
    ClassZoneRefactorEngine,
    get_class_zone_refactor_engine,
    reset_class_zone_refactor_engine
)


class TestClassZoneIdentifier:
    """测试类区域识别器"""

    def test_identify_constants(self):
        """测试识别类常量"""
        class_code = """
class TestClass:
    # Static constants
    MAX_VALUE = 100
    MIN_VALUE = 0
    PI = 3.14159
    
    # Config constants
    CONFIG_TIMEOUT = 30
    CONFIG_RETRIES = 3
    
    # Magic constants
    __VERSION__ = "1.0.0"
"""
        tree = ast.parse(class_code)
        class_node = tree.body[0]
        
        identifier = ClassZoneIdentifier()
        constants = identifier.identify_constants(class_node)
        
        assert len(constants) >= 3
        static_consts = [c for c in constants if c.constant_type == ConstantType.STATIC]
        assert len(static_consts) >= 2

    def test_identify_state(self):
        """测试识别类状态"""
        class_code = """
class TestClass:
    # Class variable
    class_var = "shared"
    
    def __init__(self):
        # Instance variables
        self.name = "test"
        self.age = 0
        self.data = None
"""
        tree = ast.parse(class_code)
        class_node = tree.body[0]
        
        identifier = ClassZoneIdentifier()
        states = identifier.identify_state(class_node)
        
        assert len(states) >= 2
        class_vars = [s for s in states if s.state_type == StateType.CLASS]
        instance_vars = [s for s in states if s.state_type == StateType.INSTANCE]
        assert len(class_vars) >= 1
        assert len(instance_vars) >= 1

    def test_identify_methods(self):
        """测试识别类方法"""
        class_code = """
class TestClass:
    def __init__(self):
        pass
    
    @property
    def name(self):
        pass
    
    def do_something(self):
        pass
    
    @classmethod
    def from_config(cls):
        pass
    
    @staticmethod
    def helper():
        pass
    
    def _private_helper(self):
        pass
"""
        tree = ast.parse(class_code)
        class_node = tree.body[0]
        
        identifier = ClassZoneIdentifier()
        methods = identifier.identify_methods(class_node)
        
        assert len(methods) >= 4
        constructors = [m for m in methods if m.method_group == MethodGroupType.CONSTRUCTOR]
        business_methods = [m for m in methods if m.method_group == MethodGroupType.BUSINESS]
        utility_methods = [m for m in methods if m.method_group == MethodGroupType.UTILITY]
        property_methods = [m for m in methods if m.method_group == MethodGroupType.PROPERTY]
        
        assert len(constructors) == 1
        assert len(business_methods) >= 1
        assert len(utility_methods) >= 1


class TestClassStructureAnalyzer:
    """测试类结构分析器"""

    def test_analyze_class_structure(self):
        """测试分析类结构"""
        class_code = """
class UserService:
    \"\"\"User service class\"\"\"
    MAX_USERS = 1000
    DEFAULT_TIMEOUT = 30
    
    cache_enabled = False
    
    def __init__(self, config):
        self.config = config
        self.users = []
        self.initialized = False
    
    def get_user(self, user_id):
        pass
    
    def _validate_user(self, user):
        pass
"""
        analyzer = ClassStructureAnalyzer()
        structure = analyzer.analyze_structure(class_code)
        
        assert structure.class_name == "UserService"
        assert structure.documentation is not None
        assert structure.validation_passed
        assert ZoneType.CONSTANTS in structure.zones
        assert ZoneType.STATE in structure.zones
        assert ZoneType.METHODS in structure.zones


class TestClassZoneTemplate:
    """测试类区域模板"""

    def test_generate_three_zone_template(self):
        """测试生成三区模板"""
        from src.architecture.class_zone_separator import ClassConstant, ClassState, ClassMethod
        
        constants = [
            ClassConstant(name="MAX_SIZE", value="100", constant_type=ConstantType.STATIC)
        ]
        states = [
            ClassState(name="count", state_type=StateType.CLASS, initial_value="0"),
            ClassState(name="data", state_type=StateType.INSTANCE)
        ]
        methods = [
            ClassMethod(name="__init__", method_group=MethodGroupType.CONSTRUCTOR),
            ClassMethod(name="process", method_group=MethodGroupType.BUSINESS)
        ]
        
        zones = {
            ZoneType.CONSTANTS: ClassZone(zone_type=ZoneType.CONSTANTS, items=constants),
            ZoneType.STATE: ClassZone(zone_type=ZoneType.STATE, items=states),
            ZoneType.METHODS: ClassZone(zone_type=ZoneType.METHODS, items=methods)
        }
        
        code = ClassZoneTemplate.get_template(
            "TestService",
            ["object"],
            "Test service",
            zones
        )
        
        assert "class TestService" in code
        assert "CONSTANTS ZONE" in code
        assert "STATE ZONE" in code
        assert "METHODS ZONE" in code


class TestClassZoneValidator:
    """测试类区域验证器"""

    def test_validate_valid_syntax(self):
        """测试验证有效语法"""
        validator = ClassZoneValidator()
        valid_code = """
class TestClass:
    pass
"""
        is_valid, error = validator.validate_syntax(valid_code)
        assert is_valid
        assert error is None

    def test_validate_invalid_syntax(self):
        """测试验证无效语法"""
        validator = ClassZoneValidator()
        invalid_code = """
class TestClass
    pass
"""
        is_valid, error = validator.validate_syntax(invalid_code)
        assert not is_valid
        assert error is not None

    def test_validate_three_zone_structure(self):
        """测试验证三区结构"""
        validator = ClassZoneValidator()
        valid_code = """
class TestClass:
    # === CONSTANTS ZONE ===
    MAX_VALUE = 100
    
    # === STATE ZONE ===
    count = 0
    
    # === METHODS ZONE ===
    def method(self):
        pass
"""
        is_valid, issues = validator.validate_three_zone_structure(valid_code)
        assert is_valid
        assert len(issues) == 0


class TestClassZoneRefactorEngine:
    """测试类三区分离重构引擎"""

    def test_refactor_class(self):
        """测试重构类"""
        class_code = """
class DataProcessor:
    \"\"\"Process data from various sources\"\"\"
    
    MAX_RETRIES = 3
    TIMEOUT = 10
    
    source_type = "file"
    
    def __init__(self, config):
        self.config = config
        self.data = []
        self.processed = False
    
    def process(self):
        pass
    
    def _helper(self):
        pass
    
    @classmethod
    def from_dict(cls, data):
        pass
"""
        engine = ClassZoneRefactorEngine()
        result = engine.refactor_class(class_code, validate=True)
        
        assert result.original_structure is not None
        assert result.refactored_code
        assert ZoneType.CONSTANTS in result.applied_zones
        assert ZoneType.STATE in result.applied_zones
        assert ZoneType.METHODS in result.applied_zones
        assert "CONSTANTS ZONE" in result.refactored_code
        assert "STATE ZONE" in result.refactored_code
        assert "METHODS ZONE" in result.refactored_code


class TestGlobalEngine:
    """测试全局引擎"""

    def test_get_and_reset_engine(self):
        """测试获取和重置引擎"""
        reset_class_zone_refactor_engine()
        engine1 = get_class_zone_refactor_engine()
        engine2 = get_class_zone_refactor_engine()
        
        assert engine1 is engine2
        
        reset_class_zone_refactor_engine()
        engine3 = get_class_zone_refactor_engine()
        
        assert engine3 is not engine1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
