"""
原子执行层 (Executors Layer)

职责：代码解析、重构修改、规范校验、测试生成

依赖关系：
- 被依赖：agents (Agent层)
- 依赖：无 (最底层)

工具集：
- AST抽象语法树解析
- Tree-sitter跨语言解析
- Ruff静态代码检查
- Pytest自动化测试

第一性原理：
- 任务可分性：代码可分解为变量/方法/类/模块原子
- 成本最小：工具层无业务逻辑，纯工具能力
"""

from typing import Any, Dict, List, Optional, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass, field as dc_field
import ast

try:
    from pydantic import BaseModel, Field
    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False


if _HAS_PYDANTIC:
    class CodeEntity(BaseModel):
        """代码实体"""
        entity_type: str
        name: str
        file_path: str
        line_number: int
        content: str
        metadata: Dict[str, Any] = Field(default_factory=dict)

    class VariableAtom(BaseModel):
        """变量原子"""
        name: str
        type_annotation: Optional[str] = None
        scope: str = "local"
        is_mutable: bool = True

    class MethodAtom(BaseModel):
        """方法原子"""
        name: str
        parameters: List[str] = Field(default_factory=list)
        return_type: Optional[str] = None
        lines: int = 0
        responsibilities: List[str] = Field(default_factory=list)

    class ClassAtom(BaseModel):
        """类原子"""
        name: str
        constants: List[str] = Field(default_factory=list)
        attributes: List[str] = Field(default_factory=list)
        methods: List[str] = Field(default_factory=list)
        cohesion_score: float = 0.0

    class ModuleAtom(BaseModel):
        """模块原子"""
        name: str
        file_path: str
        imports: List[str] = Field(default_factory=list)
        exports: List[str] = Field(default_factory=list)
        dependencies: Set[str] = Field(default_factory=set)
else:
    @dataclass
    class CodeEntity:
        """代码实体"""
        entity_type: str = ""
        name: str = ""
        file_path: str = ""
        line_number: int = 0
        content: str = ""
        metadata: Dict[str, Any] = dc_field(default_factory=dict)

    @dataclass
    class VariableAtom:
        """变量原子"""
        name: str = ""
        type_annotation: Optional[str] = None
        scope: str = "local"
        is_mutable: bool = True

    @dataclass
    class MethodAtom:
        """方法原子"""
        name: str = ""
        parameters: List[str] = dc_field(default_factory=list)
        return_type: Optional[str] = None
        lines: int = 0
        responsibilities: List[str] = dc_field(default_factory=list)

    @dataclass
    class ClassAtom:
        """类原子"""
        name: str = ""
        constants: List[str] = dc_field(default_factory=list)
        attributes: List[str] = dc_field(default_factory=list)
        methods: List[str] = dc_field(default_factory=list)
        cohesion_score: float = 0.0

    @dataclass
    class ModuleAtom:
        """模块原子"""
        name: str = ""
        file_path: str = ""
        imports: List[str] = dc_field(default_factory=list)
        exports: List[str] = dc_field(default_factory=list)
        dependencies: Set[str] = dc_field(default_factory=set)


class ASTParser:
    """AST语法树解析器"""

    def parse_file(self, file_path: str) -> ast.Module:
        """解析Python文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return ast.parse(f.read(), filename=file_path)

    def extract_variables(self, node: ast.AST) -> List[VariableAtom]:
        """提取变量"""
        variables = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                variables.append(VariableAtom(name=child.id))
        return variables

    def extract_functions(self, node: ast.AST) -> List[MethodAtom]:
        """提取函数"""
        functions = []
        for child in ast.walk(node):
            if isinstance(child, ast.FunctionDef):
                params = [arg.arg for arg in child.args.args]
                return_annotation = ast.unparse(child.returns) if child.returns else None
                functions.append(MethodAtom(
                    name=child.name,
                    parameters=params,
                    return_type=return_annotation,
                    lines=child.end_lineno - child.lineno + 1 if hasattr(child, 'end_lineno') else 0
                ))
        return functions

    def extract_classes(self, node: ast.AST) -> List[ClassAtom]:
        """提取类"""
        classes = []
        for child in ast.walk(node):
            if isinstance(child, ast.ClassDef):
                methods = [n.name for n in child.body if isinstance(n, ast.FunctionDef)]
                attributes = [n.targets[0].id for n in child.body if isinstance(n, ast.Assign)]
                classes.append(ClassAtom(
                    name=child.name,
                    methods=methods,
                    attributes=attributes
                ))
        return classes


class CodeScanner(ABC):
    """代码扫描器基类"""

    @abstractmethod
    def scan(self, file_path: str) -> List[CodeEntity]:
        """扫描代码"""
        pass

    @abstractmethod
    def validate(self, entity: CodeEntity) -> bool:
        """验证实体"""
        pass


class PythonScanner(CodeScanner):
    """Python代码扫描器"""

    def __init__(self):
        self.parser = ASTParser()

    def scan(self, file_path: str) -> List[CodeEntity]:
        """扫描Python文件"""
        try:
            tree = self.parser.parse_file(file_path)
            entities = []

            for func in self.parser.extract_functions(tree):
                entities.append(CodeEntity(
                    entity_type="function",
                    name=func.name,
                    file_path=file_path,
                    line_number=0,
                    content=f"def {func.name}({', '.join(func.parameters)})"
                ))

            for cls in self.parser.extract_classes(tree):
                entities.append(CodeEntity(
                    entity_type="class",
                    name=cls.name,
                    file_path=file_path,
                    line_number=0,
                    content=f"class {cls.name}"
                ))

            return entities
        except Exception as e:
            return []

    def validate(self, entity: CodeEntity) -> bool:
        """验证代码实体"""
        return bool(entity.name and entity.entity_type)


class CodeFixer:
    """代码修复器"""

    def __init__(self):
        self.scanner = PythonScanner()

    def fix_variable_naming(self, entity: CodeEntity) -> str:
        """修复变量命名"""
        if entity.entity_type == "variable":
            return entity.name.lower().replace('_', '')
        return entity.content

    def fix_method_length(self, method: MethodAtom) -> bool:
        """检查方法长度是否合理"""
        return method.lines <= 50

    def fix_class_cohesion(self, cls: ClassAtom) -> bool:
        """检查类内聚性"""
        return cls.cohesion_score >= 0.5
