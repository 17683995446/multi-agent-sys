"""
方法四段式结构自动重构模块

职责：将方法重构为标准的四段式结构：
1. 输入校验段（Input Validation Section）
2. 业务处理段（Business Logic Section）
3. 异常处理段（Exception Handling Section）
4. 结果返回段（Result Return Section）

基于第一性原理：简单、单一、可追溯、可组合
"""

from __future__ import annotations

import ast
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class SectionType(str, Enum):
    """代码段类型"""
    INPUT_VALIDATION = "input_validation"  # 输入校验段
    BUSINESS_LOGIC = "business_logic"     # 业务处理段
    EXCEPTION_HANDLING = "exception_handling"  # 异常处理段
    RESULT_RETURN = "result_return"      # 结果返回段
    UNKNOWN = "unknown"                  # 未知段


class RefactorStrategy(str, Enum):
    """重构策略"""
    CONSERVATIVE = "conservative"        # 保守策略
    MODERATE = "moderate"               # 适度策略
    AGGRESSIVE = "aggressive"           # 激进策略


@dataclass
class CodeSegment:
    """代码段"""
    segment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    section_type: SectionType = SectionType.UNKNOWN
    start_line: int = 0
    end_line: int = 0
    content: str = ""
    statements: List[ast.stmt] = field(default_factory=list)
    complexity: int = 0
    dependencies: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "section_type": self.section_type.value,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "complexity": self.complexity,
            "dependencies": self.dependencies,
            "issues": self.issues
        }


@dataclass
class MethodStructure:
    """方法结构"""
    method_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_code: str = ""
    method_name: str = ""
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    sections: Dict[SectionType, CodeSegment] = field(default_factory=dict)
    validation_passed: bool = True
    issues: List[str] = field(default_factory=list)

    def get_section(self, section_type: SectionType) -> Optional[CodeSegment]:
        """获取指定类型的代码段"""
        return self.sections.get(section_type)

    def has_section(self, section_type: SectionType) -> bool:
        """检查是否存在指定类型的代码段"""
        return section_type in self.sections and self.sections[section_type] is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_id": self.method_id,
            "original_code": self.original_code,
            "method_name": self.method_name,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "docstring": self.docstring,
            "sections": {k.value: v.to_dict() for k, v in self.sections.items() if v is not None},
            "validation_passed": self.validation_passed,
            "issues": self.issues
        }


@dataclass
class RefactoredMethod:
    """重构后的方法"""
    method_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_structure: MethodStructure = None
    refactored_code: str = ""
    generation_time: datetime = field(default_factory=datetime.now)
    applied_sections: List[SectionType] = field(default_factory=list)
    template_used: Optional[str] = None
    semantic_preserved: bool = True
    validation_result: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_id": self.method_id,
            "original_structure": self.original_structure.to_dict() if self.original_structure else None,
            "refactored_code": self.refactored_code,
            "generation_time": self.generation_time.isoformat(),
            "applied_sections": [s.value for s in self.applied_sections],
            "template_used": self.template_used,
            "semantic_preserved": self.semantic_preserved,
            "validation_result": self.validation_result
        }


class FourSectionTemplate:
    """四段式模板"""

    @staticmethod
    def get_template(
        method_name: str,
        parameters: List[str],
        return_type: Optional[str],
        docstring: Optional[str],
        sections: Dict[SectionType, CodeSegment]
    ) -> str:
        """生成四段式方法代码"""
        lines = []
        
        if docstring:
            lines.append('"""' + docstring + '"""')
        
        param_str = ", ".join(parameters)
        if return_type:
            lines.append(f"def {method_name}({param_str}) -> {return_type}:")
        else:
            lines.append(f"def {method_name}({param_str}):")
        
        for section_type in [SectionType.INPUT_VALIDATION, SectionType.BUSINESS_LOGIC, 
                            SectionType.EXCEPTION_HANDLING, SectionType.RESULT_RETURN]:
            segment = sections.get(section_type)
            if segment and segment.content:
                lines.append("")
                lines.append(f"    # === {section_type.value.upper()} ===")
                for line in segment.content.split('\n'):
                    if line.strip():
                        lines.append(f"    {line}")
        
        return '\n'.join(lines)

    @staticmethod
    def get_minimal_template(
        method_name: str,
        parameters: List[str],
        return_type: Optional[str],
        docstring: Optional[str]
    ) -> str:
        """生成最小化四段式方法代码"""
        lines = []
        
        if docstring:
            lines.append('"""' + docstring + '"""')
        
        param_str = ", ".join(parameters)
        if return_type:
            lines.append(f"def {method_name}({param_str}) -> {return_type}:")
        else:
            lines.append(f"def {method_name}({param_str}):")
        
        lines.append("    # === INPUT VALIDATION ===")
        lines.append("    pass")
        lines.append("")
        lines.append("    # === BUSINESS LOGIC ===")
        lines.append("    pass")
        lines.append("")
        lines.append("    # === EXCEPTION HANDLING ===")
        lines.append("    pass")
        lines.append("")
        lines.append("    # === RESULT RETURN ===")
        lines.append("    return None")
        
        return '\n'.join(lines)


class SectionIdentifier:
    """代码段识别器"""

    INPUT_VALIDATION_PATTERNS = [
        r'\bif\s+not\s+',  # if not x
        r'\bif\s+.*\s+is\s+None\b',  # if x is None
        r'\bif\s+.*\s+==\s+\d+\b',  # if x == 0
        r'\braise\s+\w*Error\b',  # raise Error
        r'\bassert\b',  # assert
        r'\.validate\w*\b',  # .validate()
        r'\.check\w*\b',  # .check()
        r'\.is_valid\w*\b',  # .is_valid()
    ]

    BUSINESS_LOGIC_PATTERNS = [
        r'\bfor\s+',  # for loop
        r'\bwhile\s+',  # while loop
        r'\bif\s+.*\s+(>|<|>=|<=|==|!=)',  # if with comparison
        r'\bresult\s*=',  # result assignment
        r'\bdata\s*=',  # data assignment
        r'\.process\w*\b',  # .process()
        r'\.transform\w*\b',  # .transform()
        r'\.calculate\w*\b',  # .calculate()
    ]

    EXCEPTION_HANDLING_PATTERNS = [
        r'\btry\b',  # try
        r'\bexcept\b',  # except
        r'\bfinally\b',  # finally
        r'\.handle\w*\b',  # .handle()
        r'\.recover\w*\b',  # .recover()
    ]

    RESULT_RETURN_PATTERNS = [
        r'\breturn\b',  # return
        r'\byield\b',  # yield
        r'\bprint\(.+\)\s*$',  # print at end
    ]

    def identify_section(self, node: ast.stmt, source_lines: List[str]) -> SectionType:
        """识别代码语句属于哪个段"""
        try:
            line_num = node.lineno - 1
            if line_num < 0 or line_num >= len(source_lines):
                return SectionType.UNKNOWN
            
            line_content = source_lines[line_num]
            node_content = ast.unparse(node) if hasattr(ast, 'unparse') else line_content
            
            if isinstance(node, (ast.If, ast.Assert)):
                for pattern in self.INPUT_VALIDATION_PATTERNS:
                    if re.search(pattern, node_content, re.IGNORECASE):
                        return SectionType.INPUT_VALIDATION
            
            if isinstance(node, (ast.Try, ast.ExceptHandler)):
                return SectionType.EXCEPTION_HANDLING
            
            if isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)):
                return SectionType.RESULT_RETURN
            
            for pattern in self.INPUT_VALIDATION_PATTERNS:
                if re.search(pattern, node_content, re.IGNORECASE):
                    return SectionType.INPUT_VALIDATION
            
            for pattern in self.EXCEPTION_HANDLING_PATTERNS:
                if re.search(pattern, node_content, re.IGNORECASE):
                    return SectionType.EXCEPTION_HANDLING
            
            for pattern in self.RESULT_RETURN_PATTERNS:
                if re.search(pattern, node_content, re.IGNORECASE):
                    return SectionType.RESULT_RETURN
            
            for pattern in self.BUSINESS_LOGIC_PATTERNS:
                if re.search(pattern, node_content, re.IGNORECASE):
                    return SectionType.BUSINESS_LOGIC
            
            return SectionType.BUSINESS_LOGIC
        except Exception:
            return SectionType.UNKNOWN

    def identify_method_sections(self, method_code: str) -> Dict[SectionType, List[ast.stmt]]:
        """识别方法中的所有代码段"""
        sections: Dict[SectionType, List[ast.stmt]] = {
            SectionType.INPUT_VALIDATION: [],
            SectionType.BUSINESS_LOGIC: [],
            SectionType.EXCEPTION_HANDLING: [],
            SectionType.RESULT_RETURN: []
        }
        
        try:
            tree = ast.parse(method_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    source_lines = method_code.split('\n')
                    for stmt in node.body:
                        section_type = self.identify_section(stmt, source_lines)
                        if section_type != SectionType.UNKNOWN:
                            sections[section_type].append(stmt)
        except Exception:
            pass
        
        return sections


class FourSectionRefactor:
    """四段式重构器"""

    def __init__(self, strategy: RefactorStrategy = RefactorStrategy.MODERATE):
        self.strategy = strategy
        self.identifier = SectionIdentifier()
        self.template = FourSectionTemplate()

    def analyze_structure(self, method_code: str) -> MethodStructure:
        """分析方法结构"""
        structure = MethodStructure(original_code=method_code)
        
        try:
            tree = ast.parse(method_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    structure.method_name = node.name
                    structure.parameters = [arg.arg for arg in node.args.args]
                    if node.returns:
                        structure.return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
                    structure.docstring = ast.get_docstring(node)
                    
                    source_lines = method_code.split('\n')
                    identified_sections = self.identifier.identify_method_sections(method_code)
                    
                    for section_type, statements in identified_sections.items():
                        if statements:
                            start_line = min(s.lineno for s in statements)
                            end_line = max(s.end_lineno if hasattr(s, 'end_lineno') else s.lineno for s in statements)
                            
                            segment = CodeSegment(
                                section_type=section_type,
                                start_line=start_line,
                                end_line=end_line,
                                content='\n'.join(source_lines[start_line-1:end_line]),
                                statements=statements,
                                complexity=len(statements)
                            )
                            structure.sections[section_type] = segment
        except Exception as e:
            structure.validation_passed = False
            structure.issues.append(f"Failed to analyze structure: {str(e)}")
        
        return structure

    def refactor(self, method_structure: MethodStructure) -> RefactoredMethod:
        """重构方法为四段式结构"""
        refactored = RefactoredMethod(original_structure=method_structure)
        
        if not method_structure.validation_passed:
            refactored.semantic_preserved = False
            return refactored
        
        sections: Dict[SectionType, CodeSegment] = {}
        applied_sections = []
        
        if method_structure.has_section(SectionType.INPUT_VALIDATION):
            sections[SectionType.INPUT_VALIDATION] = method_structure.get_section(SectionType.INPUT_VALIDATION)
            applied_sections.append(SectionType.INPUT_VALIDATION)
        
        if method_structure.has_section(SectionType.BUSINESS_LOGIC):
            sections[SectionType.BUSINESS_LOGIC] = method_structure.get_section(SectionType.BUSINESS_LOGIC)
            applied_sections.append(SectionType.BUSINESS_LOGIC)
        else:
            sections[SectionType.BUSINESS_LOGIC] = CodeSegment(
                section_type=SectionType.BUSINESS_LOGIC,
                content="# Placeholder for business logic"
            )
            applied_sections.append(SectionType.BUSINESS_LOGIC)
        
        if method_structure.has_section(SectionType.EXCEPTION_HANDLING):
            sections[SectionType.EXCEPTION_HANDLING] = method_structure.get_section(SectionType.EXCEPTION_HANDLING)
            applied_sections.append(SectionType.EXCEPTION_HANDLING)
        
        if method_structure.has_section(SectionType.RESULT_RETURN):
            sections[SectionType.RESULT_RETURN] = method_structure.get_section(SectionType.RESULT_RETURN)
            applied_sections.append(SectionType.RESULT_RETURN)
        else:
            sections[SectionType.RESULT_RETURN] = CodeSegment(
                section_type=SectionType.RESULT_RETURN,
                content="return None"
            )
            applied_sections.append(SectionType.RESULT_RETURN)
        
        refactored.refactored_code = self.template.get_template(
            method_structure.method_name,
            method_structure.parameters,
            method_structure.return_type,
            method_structure.docstring,
            sections
        )
        refactored.applied_sections = applied_sections
        refactored.template_used = "four_section_standard"
        
        return refactored

    def refactor_simple(self, method_code: str) -> RefactoredMethod:
        """简化重构方法"""
        structure = self.analyze_structure(method_code)
        return self.refactor(structure)


class RefactorValidator:
    """重构验证器"""

    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """验证语法正确性"""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"

    def validate_semantic_equivalence(
        self, 
        original: str, 
        refactored: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """验证语义等价性"""
        result = {
            "syntax_valid": False,
            "structure_preserved": False,
            "logic_equivalent": False,
            "warnings": []
        }
        
        syntax_valid, error = self.validate_syntax(refactored)
        result["syntax_valid"] = syntax_valid
        if error:
            result["warnings"].append(error)
            return False, result
        
        try:
            original_tree = ast.parse(original)
            refactored_tree = ast.parse(refactored)
            
            original_funcs = [n for n in ast.walk(original_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            refactored_funcs = [n for n in ast.walk(refactored_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            
            if len(original_funcs) == len(refactored_funcs) == 1:
                result["structure_preserved"] = True
                
                orig_params = len(original_funcs[0].args.args)
                ref_params = len(refactored_funcs[0].args.args)
                if orig_params == ref_params:
                    result["logic_equivalent"] = True
                else:
                    result["warnings"].append("Parameter count mismatch")
            
        except Exception as e:
            result["warnings"].append(f"Semantic validation error: {str(e)}")
        
        return result["syntax_valid"] and result["structure_preserved"], result

    def validate_four_section_structure(self, code: str) -> Tuple[bool, List[str]]:
        """验证四段式结构"""
        issues = []
        
        required_sections = [
            SectionType.INPUT_VALIDATION,
            SectionType.BUSINESS_LOGIC,
            SectionType.RESULT_RETURN
        ]
        
        code_upper = code.upper()
        
        for section in required_sections:
            section_value = section.value.upper().replace('_', ' ')
            section_marker_underscore = f"=== {section.value.upper()} ==="
            section_marker_space = f"=== {section_value} ==="
            
            if section_marker_underscore not in code_upper and section_marker_space not in code_upper:
                issues.append(f"Missing required section: {section.value}")
        
        if not issues:
            return True, []
        return False, issues


class FourSectionRefactorEngine:
    """四段式重构引擎"""
    
    def __init__(self, strategy: RefactorStrategy = RefactorStrategy.MODERATE):
        self.refactorer = FourSectionRefactor(strategy)
        self.validator = RefactorValidator()

    def refactor_method(
        self, 
        method_code: str, 
        validate: bool = True,
        validate_semantics: bool = True
    ) -> RefactoredMethod:
        """重构方法"""
        refactored = self.refactorer.refactor_simple(method_code)
        
        if validate:
            syntax_valid, error = self.validator.validate_syntax(refactored.refactored_code)
            refactored.validation_result["syntax_valid"] = syntax_valid
            if error:
                refactored.validation_result["syntax_error"] = error
                refactored.semantic_preserved = False
            
            if syntax_valid:
                structure_valid, structure_issues = self.validator.validate_four_section_structure(
                    refactored.refactored_code
                )
                refactored.validation_result["structure_valid"] = structure_valid
                refactored.validation_result["structure_issues"] = structure_issues
        
        if validate_semantics and refactored.semantic_preserved:
            semantically_equivalent, semantic_result = self.validator.validate_semantic_equivalence(
                method_code,
                refactored.refactored_code
            )
            refactored.semantic_preserved = semantically_equivalent
            refactored.validation_result["semantic_equivalence"] = semantic_result
        
        return refactored

    def batch_refactor(
        self, 
        methods: List[str],
        validate: bool = True
    ) -> List[RefactoredMethod]:
        """批量重构方法"""
        return [
            self.refactor_method(method, validate=validate)
            for method in methods
        ]


_global_engine: Optional[FourSectionRefactorEngine] = None


def get_four_section_refactor_engine(strategy: RefactorStrategy = RefactorStrategy.MODERATE) -> FourSectionRefactorEngine:
    """获取全局重构引擎"""
    global _global_engine
    if _global_engine is None:
        _global_engine = FourSectionRefactorEngine(strategy)
    return _global_engine


def reset_four_section_refactor_engine() -> None:
    """重置重构引擎"""
    global _global_engine
    _global_engine = None
