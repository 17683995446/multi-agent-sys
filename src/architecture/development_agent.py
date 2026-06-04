"""
开发Agent模块

职责：代码生成、代码修改、重构

基于第一性原理：简单、单一、可追溯、可组合
"""

import ast
import uuid
import re
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class GenerationType(str, Enum):
    """生成类型"""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    UTILITY = "utility"
    TEST = "test"


class ModificationType(str, Enum):
    """修改类型"""
    AST_MODIFY = "ast_modify"
    SEMANTIC_MODIFY = "semantic_modify"
    REFACTOR = "refactor"


class RefactorType(str, Enum):
    """重构类型"""
    SINGLE_FILE = "single_file"
    BATCH = "batch"


@dataclass
class GeneratedCode:
    """生成的代码"""
    source_code: str = ""
    generation_type: GenerationType = GenerationType.FUNCTION
    name: str = ""
    language: str = "python"
    code_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CodeModification:
    """代码修改"""
    original_code: str = ""
    modified_code: str = ""
    modification_type: ModificationType = ModificationType.AST_MODIFY
    description: str = ""
    applied_at: Optional[datetime] = None
    modification_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class RefactorPlan:
    """重构计划"""
    refactor_type: RefactorType = RefactorType.SINGLE_FILE
    target_files: List[str] = field(default_factory=list)
    changes: List[CodeModification] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class DevelopmentConfig:
    """开发Agent配置"""
    name: str
    enable_intelligent_generation: bool = True
    enable_ast_modification: bool = True
    enable_batch_refactoring: bool = True
    include_comments: bool = True
    include_docstrings: bool = True


class CodeGenerator:
    """代码生成器"""
    
    def __init__(self):
        self.templates = {
            "function": '''
def {name}({params}) -> {return_type}:
    """{docstring}"""
    {body}
''',
            "class": '''
class {name}:
    """{docstring}"""
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}
''',
            "utility": '''
"""Utility module: {module_name}"""
{imports}

{functions}
''',
            "test": '''
"""Test module: {module_name}"""
import pytest
from {module_name} import {imports}

def test_{name}():
    {body}
'''
        }
    
    def generate_function(self, name: str, params: List[str] = None, 
                        return_type: str = "None", body: str = "pass", 
                        docstring: str = "Function description") -> GeneratedCode:
        """生成函数"""
        params_str = ", ".join(params or [])
        
        code = self.templates["function"].format(
            name=name,
            params=params_str,
            return_type=return_type,
            docstring=docstring,
            body=body
        )
        
        return GeneratedCode(
            source_code=code.strip(),
            generation_type=GenerationType.FUNCTION,
            name=name
        )
    
    def generate_class(self, name: str, attributes: List[str] = None, 
                     methods: List[str] = None, docstring: str = "Class description") -> GeneratedCode:
        """生成类"""
        attrs = attributes or []
        init_params = ", ".join([f"{attr}: Any = None" for attr in attrs])
        init_body = "\n        ".join([f"self.{attr} = {attr}" for attr in attrs]) or "pass"
        methods_str = "\n    ".join(methods or [])
        
        code = self.templates["class"].format(
            name=name,
            docstring=docstring,
            init_params=f", {init_params}" if init_params else "",
            init_body=init_body,
            methods=methods_str
        )
        
        return GeneratedCode(
            source_code=code.strip(),
            generation_type=GenerationType.CLASS,
            name=name
        )
    
    def generate_intelligent(self, requirement: str, gen_type: GenerationType = GenerationType.FUNCTION) -> GeneratedCode:
        """智能生成"""
        
        if "database" in requirement.lower() or "db" in requirement.lower():
            return self._generate_db_code(requirement)
        elif "api" in requirement.lower() or "endpoint" in requirement.lower():
            return self._generate_api_code(requirement)
        elif "validate" in requirement.lower() or "check" in requirement.lower():
            return self._generate_validation_code(requirement)
        else:
            name = "".join(word.capitalize() for word in requirement.split()[:3])
            return self.generate_function(name=name)
    
    def _generate_db_code(self, requirement: str) -> GeneratedCode:
        """生成数据库代码"""
        code = '''
def save_to_database(data: dict) -> bool:
    """Save data to database"""
    try:
        print(f"Saving data: {data}")
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False
'''
        return GeneratedCode(
            source_code=code.strip(),
            generation_type=GenerationType.FUNCTION,
            name="save_to_database"
        )
    
    def _generate_api_code(self, requirement: str) -> GeneratedCode:
        """生成API代码"""
        code = '''
def api_endpoint(request: dict) -> dict:
    """Process API request"""
    try:
        response = {
            "status": "success",
            "data": "Processed successfully"
        }
        return response
    except Exception as e:
        return {"status": "error", "message": str(e)}
'''
        return GeneratedCode(
            source_code=code.strip(),
            generation_type=GenerationType.FUNCTION,
            name="api_endpoint"
        )
    
    def _generate_validation_code(self, requirement: str) -> GeneratedCode:
        """生成验证代码"""
        code = '''
def validate_data(data: dict, required_fields: List[str] = None) -> bool:
    """Validate data against required fields"""
    required = required_fields or ["id", "name"]
    for field in required:
        if field not in data or data[field] is None:
            return False
    return True
'''
        return GeneratedCode(
            source_code=code.strip(),
            generation_type=GenerationType.FUNCTION,
            name="validate_data"
        )


class ASTModifier:
    """AST修改器"""
    
    def __init__(self):
        pass
    
    def modify_function_name(self, source_code: str, old_name: str, new_name: str) -> CodeModification:
        """修改函数名"""
        modified_code = source_code.replace(f"def {old_name}", f"def {new_name}")
        
        return CodeModification(
            original_code=source_code,
            modified_code=modified_code,
            modification_type=ModificationType.AST_MODIFY,
            description=f"Renamed function {old_name} to {new_name}"
        )
    
    def add_parameter(self, source_code: str, func_name: str, param_name: str, 
                   param_default: str = "None") -> CodeModification:
        """添加参数"""
        
        def find_func_params(code: str, name: str) -> Optional[Tuple[int, int]]:
            pattern = rf"def {name}\(([^)]*)\)"
            match = re.search(pattern, code)
            if match:
                return (match.start(1), match.end(1))
            return None
        
        pos = find_func_params(source_code, func_name)
        if pos:
            start, end = pos
            existing_params = source_code[start:end].strip()
            new_params = existing_params
            if existing_params:
                new_params += f", {param_name}: Any = {param_default}"
            else:
                new_params = f"{param_name}: Any = {param_default}"
            
            modified_code = source_code[:start] + new_params + source_code[end:]
            return CodeModification(
                original_code=source_code,
                modified_code=modified_code,
                modification_type=ModificationType.AST_MODIFY,
                description=f"Added parameter {param_name} to {func_name}"
            )
        
        return CodeModification(
            original_code=source_code,
            modified_code=source_code,
            modification_type=ModificationType.AST_MODIFY,
            description=f"Function {func_name} not found"
        )


class SemanticModifier:
    """语义修改器"""
    
    def __init__(self):
        pass
    
    def optimize_function(self, source_code: str) -> CodeModification:
        """语义优化"""
        modified = source_code
        
        if "for i in range(len(" in modified:
            modified = re.sub(r"for i in range\(len\((\w+)\)\):", r"for i, item in enumerate(\1):", modified)
        
        if "if x == True" in modified:
            modified = modified.replace("if x == True", "if x")
        
        if "if x == False" in modified:
            modified = modified.replace("if x == False", "if not x")
        
        return CodeModification(
            original_code=source_code,
            modified_code=modified,
            modification_type=ModificationType.SEMANTIC_MODIFY,
            description="Applied semantic optimizations"
        )


class RefactoringEngine:
    """重构引擎"""
    
    def __init__(self):
        self.ast_modifier = ASTModifier()
        self.semantic_modifier = SemanticModifier()
    
    def refactor_single_file(self, source_code: str) -> RefactorPlan:
        """单文件重构"""
        changes = []
        
        change1 = self.semantic_modifier.optimize_function(source_code)
        changes.append(change1)
        
        plan = RefactorPlan(
            refactor_type=RefactorType.SINGLE_FILE,
            target_files=["target_file.py"],
            changes=changes,
            description="Single file refactoring"
        )
        
        return plan
    
    def refactor_batch(self, files: List[str], source_codes: Dict[str, str]) -> RefactorPlan:
        """批量重构"""
        changes = []
        
        for file_path in files:
            if file_path in source_codes:
                change = self.semantic_modifier.optimize_function(source_codes[file_path])
                changes.append(change)
        
        plan = RefactorPlan(
            refactor_type=RefactorType.BATCH,
            target_files=files,
            changes=changes,
            description="Batch refactoring"
        )
        
        return plan


class DevelopmentAgent:
    """开发Agent"""
    
    def __init__(self, config: DevelopmentConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.code_generator = CodeGenerator()
        self.refactoring_engine = RefactoringEngine()
        self.generated_codes: List[GeneratedCode] = []
        self.refactor_plans: List[RefactorPlan] = []
    
    def generate_code(self, requirement: str, gen_type: GenerationType = GenerationType.FUNCTION) -> GeneratedCode:
        """生成代码"""
        if self.config.enable_intelligent_generation:
            result = self.code_generator.generate_intelligent(requirement, gen_type)
        else:
            name = "".join(word.capitalize() for word in requirement.split()[:2])
            result = self.code_generator.generate_function(name=name)
        
        self.generated_codes.append(result)
        return result
    
    def modify_code(self, source_code: str, modify_type: ModificationType = ModificationType.AST_MODIFY, 
                  **kwargs) -> CodeModification:
        """修改代码"""
        if modify_type == ModificationType.AST_MODIFY:
            old_name = kwargs.get("old_name", "old_func")
            new_name = kwargs.get("new_name", "new_func")
            return self.refactoring_engine.ast_modifier.modify_function_name(
                source_code, old_name, new_name
            )
        else:
            return self.refactoring_engine.semantic_modifier.optimize_function(source_code)
    
    def refactor(self, files: List[str], source_codes: Dict[str, str] = None, 
               refactor_type: RefactorType = RefactorType.SINGLE_FILE) -> RefactorPlan:
        """重构"""
        if refactor_type == RefactorType.SINGLE_FILE and files:
            source = source_codes.get(files[0], "") if source_codes else ""
            plan = self.refactoring_engine.refactor_single_file(source)
        else:
            plan = self.refactoring_engine.refactor_batch(files, source_codes or {})
        
        self.refactor_plans.append(plan)
        return plan


_global_development_agent: Optional[DevelopmentAgent] = None


def get_development_agent(config: Optional[DevelopmentConfig] = None) -> DevelopmentAgent:
    """获取全局开发Agent"""
    global _global_development_agent
    if _global_development_agent is None:
        if config is None:
            config = DevelopmentConfig(name="DevelopmentAgent")
        _global_development_agent = DevelopmentAgent(config)
    return _global_development_agent


def reset_development_agent() -> None:
    """重置开发Agent"""
    global _global_development_agent
    _global_development_agent = None
