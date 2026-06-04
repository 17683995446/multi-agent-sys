"""
阶段33验收测试：架构Agent初始化

验收标准：
1. ✓ Agent类定义（完整配置）
2. ✓ 依赖分析能力（语义依赖）
3. ✓ 边界锁定（接口边界）
4. ✓ 方案输出（代码输出）
"""

import pytest
from src.architecture.architecture_agent import (
    DependencyType,
    BoundaryType,
    Dependency,
    Interface,
    Boundary,
    ArchitectureSchema,
    ArchitectureConfig,
    SemanticDependencyAnalyzer,
    InterfaceDetector,
    BoundaryIdentifier,
    ArchitectureGenerator,
    ArchitectureAgent,
    get_architecture_agent,
    reset_architecture_agent
)


class TestArchitectureConfig:
    """测试Agent类定义"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = ArchitectureConfig(name="ArchitectureAgent")
        
        assert config.name == "ArchitectureAgent"
        assert config.analyze_imports is True
        assert config.analyze_semantic is True
        assert config.output_code is True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = ArchitectureConfig(
            name="CustomArchAgent",
            analyze_semantic=False,
            output_code=False
        )
        
        assert config.name == "CustomArchAgent"
        assert config.analyze_semantic is False
        assert config.output_code is False


class TestSemanticDependencyAnalyzer:
    """测试语义依赖分析"""
    
    def test_analyze_semantic_dependencies(self):
        """测试语义依赖分析"""
        analyzer = SemanticDependencyAnalyzer()
        
        code = "This function will fetch data from the database and send response to client"
        
        deps = analyzer.analyze_semantic_dependencies(code, "test_module")
        
        assert len(deps) >= 1
        for dep in deps:
            assert dep.dep_type == DependencyType.SEMANTIC
            assert dep.source_module == "test_module"


class TestInterfaceDetector:
    """测试接口检测"""
    
    def test_detect_interfaces(self):
        """测试接口检测"""
        detector = InterfaceDetector()
        
        code = """
def get_user(user_id: int) -> User:
    pass

def save_user(user: User) -> bool:
    pass

def delete_user(user_id: int) -> None:
    pass
"""
        
        interfaces = detector.detect_interfaces(code, "user_module")
        
        assert len(interfaces) == 3
        interface_names = [i.name for i in interfaces]
        assert "get_user" in interface_names
        assert "save_user" in interface_names
        assert "delete_user" in interface_names


class TestBoundaryIdentifier:
    """测试边界识别"""
    
    def test_identify_boundaries(self):
        """测试边界识别"""
        identifier = BoundaryIdentifier()
        
        interface1 = Interface(name="func1", module="module_a", methods=["func1"])
        interface2 = Interface(name="func2", module="module_b", methods=["func2"])
        
        interfaces = [interface1, interface2]
        dependencies = []
        
        boundaries = identifier.identify_boundaries(interfaces, dependencies)
        
        assert len(boundaries) >= 2
        boundary_names = [b.name for b in boundaries]
        assert "module_a" in boundary_names
        assert "module_b" in boundary_names


class TestArchitectureGenerator:
    """测试方案输出"""
    
    def test_generate_documentation(self):
        """测试文档生成"""
        generator = ArchitectureGenerator()
        
        boundary = Boundary(
            name="test_boundary",
            boundary_type=BoundaryType.MODULE,
            modules=["module1"],
            public_api=["func1", "func2"]
        )
        
        schema = ArchitectureSchema(
            name="Test Architecture",
            boundaries=[boundary],
            modules=["module1"]
        )
        
        doc = generator.generate_documentation(schema)
        
        assert "ARCHITECTURE DESIGN" in doc
        assert "test_boundary" in doc
        assert "module1" in doc
    
    def test_generate_code(self):
        """测试代码生成"""
        generator = ArchitectureGenerator()
        
        interface = Interface(
            name="process_data",
            module="test_module",
            methods=["process_data"],
            parameters=["data"],
            return_type="bool"
        )
        
        boundary = Boundary(
            name="test_boundary",
            boundary_type=BoundaryType.MODULE,
            modules=["test_module"],
            interfaces=[interface],
            public_api=["process_data"]
        )
        
        schema = ArchitectureSchema(
            name="Test Architecture",
            boundaries=[boundary],
            modules=["test_module"]
        )
        
        code_files = generator.generate_code(schema)
        
        assert "interfaces.py" in code_files
        assert "boundaries.py" in code_files
        assert "dependencies.py" in code_files
        
        assert "process_data" in code_files["interfaces.py"]


class TestArchitectureAgent:
    """测试架构Agent"""
    
    def test_analyze_code(self):
        """测试代码分析"""
        config = ArchitectureConfig(name="TestAgent", detect_interfaces=True)
        agent = ArchitectureAgent(config)
        
        code = """
def calculate(x: int, y: int) -> int:
    return x + y

def validate_input(data: str) -> bool:
    return len(data) > 0
"""
        
        schema = agent.analyze_code(code, "calculator")
        
        assert schema is not None
        assert schema.name == "Architecture for calculator"
        assert len(schema.boundaries) >= 1
    
    def test_generate_output(self):
        """测试生成输出"""
        config = ArchitectureConfig(name="TestAgent", output_code=True)
        agent = ArchitectureAgent(config)
        
        schema = agent.analyze_code("def test(): pass", "test_module")
        output = agent.generate_output(schema)
        
        assert "documentation" in output
        assert "code_files" in output
        assert "schema" in output


class TestGlobalAgent:
    """测试全局Agent"""
    
    def test_get_global_agent(self):
        """测试获取全局Agent"""
        reset_architecture_agent()
        
        agent1 = get_architecture_agent()
        agent2 = get_architecture_agent()
        
        assert agent1 is agent2
    
    def test_reset_global_agent(self):
        """测试重置全局Agent"""
        agent1 = get_architecture_agent()
        reset_architecture_agent()
        agent2 = get_architecture_agent()
        
        assert agent1 is not agent2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
