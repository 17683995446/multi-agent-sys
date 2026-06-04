"""
阶段34验收测试：开发Agent初始化

验收标准：
1. ✓ Agent类定义（完整配置）
2. ✓ 代码生成能力（智能生成）
3. ✓ 代码修改能力（语义修改）
4. ✓ 重构能力（批量重构）
"""

import pytest
from src.architecture.development_agent import (
    GenerationType,
    ModificationType,
    RefactorType,
    GeneratedCode,
    CodeModification,
    RefactorPlan,
    DevelopmentConfig,
    CodeGenerator,
    ASTModifier,
    SemanticModifier,
    RefactoringEngine,
    DevelopmentAgent,
    get_development_agent,
    reset_development_agent
)


class TestDevelopmentConfig:
    """测试Agent类定义"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = DevelopmentConfig(name="DevelopmentAgent")
        
        assert config.name == "DevelopmentAgent"
        assert config.enable_intelligent_generation == True
        assert config.enable_ast_modification == True
        assert config.enable_batch_refactoring == True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = DevelopmentConfig(
            name="CustomDevAgent",
            enable_intelligent_generation=False,
            include_docstrings=False
        )
        
        assert config.name == "CustomDevAgent"
        assert config.enable_intelligent_generation == False


class TestCodeGenerator:
    """测试代码生成能力"""
    
    def test_generate_function(self):
        """测试生成函数"""
        generator = CodeGenerator()
        
        result = generator.generate_function(
            name="calculate_sum",
            params=["a", "b"],
            return_type="int",
            body="return a + b"
        )
        
        assert result.generation_type == GenerationType.FUNCTION
        assert "calculate_sum" in result.source_code
        assert "return a + b" in result.source_code
    
    def test_generate_class(self):
        """测试生成类"""
        generator = CodeGenerator()
        
        result = generator.generate_class(
            name="User",
            attributes=["name", "email"]
        )
        
        assert result.generation_type == GenerationType.CLASS
        assert "class User" in result.source_code
    
    def test_intelligent_generation(self):
        """测试智能生成"""
        generator = CodeGenerator()
        
        result1 = generator.generate_intelligent("save data to database")
        result2 = generator.generate_intelligent("create api endpoint")
        result3 = generator.generate_intelligent("validate input data")
        
        assert result1.generation_type == GenerationType.FUNCTION
        assert "save_to_database" in result1.source_code or "api_endpoint" in result2.source_code or "validate_data" in result3.source_code


class TestCodeModifiers:
    """测试代码修改能力"""
    
    def test_ast_modify(self):
        """测试AST修改"""
        modifier = ASTModifier()
        
        source = '''
def old_function():
    pass
'''
        
        modification = modifier.modify_function_name(
            source,
            "old_function",
            "new_function"
        )
        
        assert modification.modification_type == ModificationType.AST_MODIFY
        assert "new_function" in modification.modified_code
    
    def test_semantic_modify(self):
        """测试语义修改"""
        modifier = SemanticModifier()
        
        source = '''
def test_func():
    x = True
    if x == True:
        for i in range(len(items)):
            pass
'''
        
        modification = modifier.optimize_function(source)
        
        assert modification.modification_type == ModificationType.SEMANTIC_MODIFY


class TestRefactoringEngine:
    """测试重构能力"""
    
    def test_single_file_refactor(self):
        """测试单文件重构"""
        engine = RefactoringEngine()
        
        source = '''
def process_items(items):
    if x == True:
        for i in range(len(items)):
            print(items[i])
'''
        
        plan = engine.refactor_single_file(source)
        
        assert plan.refactor_type == RefactorType.SINGLE_FILE
        assert len(plan.changes) > 0
    
    def test_batch_refactor(self):
        """测试批量重构"""
        engine = RefactoringEngine()
        
        files = ["file1.py", "file2.py"]
        codes = {
            "file1.py": '''
def process_data(data):
    if x == True:
        pass
''',
            "file2.py": '''
def save_items(items):
    if x == True:
        for i in range(len(items)):
            pass
'''
        }
        
        plan = engine.refactor_batch(files, codes)
        
        assert plan.refactor_type == RefactorType.BATCH
        assert len(plan.target_files) == 2


class TestDevelopmentAgent:
    """测试开发Agent"""
    
    def test_generate_code(self):
        """测试生成代码"""
        config = DevelopmentConfig(name="TestAgent")
        agent = DevelopmentAgent(config)
        
        result = agent.generate_code("calculate something important")
        
        assert len(agent.generated_codes) == 1
        assert isinstance(result, GeneratedCode)
    
    def test_modify_code(self):
        """测试修改代码"""
        config = DevelopmentConfig(name="TestAgent")
        agent = DevelopmentAgent(config)
        
        source = '''
def old_func():
    pass
'''
        
        modification = agent.modify_code(
            source,
            ModificationType.AST_MODIFY,
            old_name="old_func",
            new_name="new_func"
        )
        
        assert isinstance(modification, CodeModification)
    
    def test_refactor(self):
        """测试重构"""
        config = DevelopmentConfig(name="TestAgent")
        agent = DevelopmentAgent(config)
        
        files = ["test.py"]
        codes = {
            "test.py": '''
def test():
    if x == True:
        for i in range(len(data)):
            pass
'''
        }
        
        plan = agent.refactor(files, codes)
        
        assert isinstance(plan, RefactorPlan)


class TestGlobalAgent:
    """测试全局Agent"""
    
    def test_get_global_agent(self):
        """测试获取全局Agent"""
        reset_development_agent()
        
        agent1 = get_development_agent()
        agent2 = get_development_agent()
        
        assert agent1 is agent2
    
    def test_reset_global_agent(self):
        """测试重置全局Agent"""
        agent1 = get_development_agent()
        reset_development_agent()
        agent2 = get_development_agent()
        
        assert agent1 is not agent2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
