"""
缺陷排查Agent模块

职责：日志解析、堆栈定位、根因分析、修复方案

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import re
import traceback
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class BugSeverity(str, Enum):
    """Bug严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """日志条目"""
    level: LogLevel = LogLevel.INFO
    message: str = ""
    timestamp: Optional[datetime] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    module: Optional[str] = None
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class StackFrame:
    """堆栈帧"""
    file_path: str = ""
    line_number: int = 0
    function_name: str = ""
    code_line: str = ""
    locals: Dict[str, Any] = field(default_factory=dict)
    frame_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class StackTrace:
    """堆栈跟踪"""
    exception_type: str = ""
    exception_message: str = ""
    frames: List[StackFrame] = field(default_factory=list)
    root_cause_file: Optional[str] = None
    root_cause_line: Optional[int] = None
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class BugFix:
    """Bug修复方案"""
    description: str = ""
    original_code: str = ""
    fixed_code: str = ""
    confidence: float = 0.5
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    fix_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class BugReport:
    """Bug报告"""
    severity: BugSeverity = BugSeverity.MEDIUM
    title: str = ""
    description: str = ""
    stack_trace: Optional[StackTrace] = None
    logs: List[LogEntry] = field(default_factory=list)
    root_cause: str = ""
    fixes: List[BugFix] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class DebugConfig:
    """缺陷排查Agent配置"""
    name: str
    enable_intelligent_log_parsing: bool = True
    enable_root_cause_analysis: bool = True
    enable_fix_generation: bool = True
    max_stack_depth: int = 10
    include_code_context: bool = True


class LogParser:
    """日志解析器"""
    
    def __init__(self):
        self.log_patterns = {
            "timestamp": r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}",
            "level": r"DEBUG|INFO|WARNING|ERROR|CRITICAL",
            "file_line": r"File \"([^\"]+)\", line (\d+)",
            "function": r"in (\w+)",
            "exception": r"(\w+):\s*(.*)"
        }
    
    def parse_log(self, log_content: str) -> List[LogEntry]:
        """解析日志"""
        entries = []
        
        lines = log_content.strip().split('\n')
        
        for line in lines:
            entry = self._parse_log_line(line)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_log_line(self, line: str) -> Optional[LogEntry]:
        """解析单行日志"""
        entry = LogEntry()
        
        level_match = re.search(self.log_patterns["level"], line, re.IGNORECASE)
        if level_match:
            level_str = level_match.group(0).upper()
            try:
                entry.level = LogLevel(level_str.lower())
            except ValueError:
                pass
        
        entry.message = line
        
        return entry if entry.message else None
    
    def intelligent_parse(self, log_content: str) -> Dict[str, List[LogEntry]]:
        """智能解析"""
        entries = self.parse_log(log_content)
        
        errors = [e for e in entries if e.level == LogLevel.ERROR]
        warnings = [e for e in entries if e.level == LogLevel.WARNING]
        critical = [e for e in entries if e.level == LogLevel.CRITICAL]
        
        return {
            "all": entries,
            "errors": errors,
            "warnings": warnings,
            "critical": critical
        }


class StackTraceAnalyzer:
    """堆栈跟踪分析器"""
    
    def __init__(self):
        self.stack_patterns = {
            "file_line": r'File "([^"]+)", line (\d+)',
            "function": r"in (\w+)",
            "code": r'\s*(\w.*)',
            "exception": r"(\w+):\s*(.*)"
        }
    
    def parse_stack_trace(self, stack_text: str) -> StackTrace:
        """解析堆栈跟踪"""
        stack_trace = StackTrace()
        
        lines = stack_text.strip().split('\n')
        
        for i, line in enumerate(lines):
            file_match = re.search(self.stack_patterns["file_line"], line)
            
            if file_match:
                frame = StackFrame()
                frame.file_path = file_match.group(1)
                frame.line_number = int(file_match.group(2))
                
                if i + 1 < len(lines):
                    func_match = re.search(self.stack_patterns["function"], lines[i + 1])
                    if func_match:
                        frame.function_name = func_match.group(1)
                
                stack_trace.frames.append(frame)
        
        for line in reversed(lines):
            exc_match = re.search(self.stack_patterns["exception"], line)
            if exc_match:
                stack_trace.exception_type = exc_match.group(1)
                stack_trace.exception_message = exc_match.group(2)
                break
        
        if stack_trace.frames:
            last_frame = stack_trace.frames[-1]
            stack_trace.root_cause_file = last_frame.file_path
            stack_trace.root_cause_line = last_frame.line_number
        
        return stack_trace
    
    def find_root_cause(self, stack_trace: StackTrace) -> Dict[str, Any]:
        """查找根因"""
        result = {
            "found": False,
            "file": None,
            "line": None,
            "function": None
        }
        
        if stack_trace.frames:
            last_frame = stack_trace.frames[-1]
            result["found"] = True
            result["file"] = last_frame.file_path
            result["line"] = last_frame.line_number
            result["function"] = last_frame.function_name
        
        return result


class FixGenerator:
    """修复方案生成器"""
    
    def __init__(self):
        self.fix_patterns = {
            "index_error": {
                "pattern": r"IndexError",
                "fix": "Check list length before indexing"
            },
            "key_error": {
                "pattern": r"KeyError",
                "fix": "Check if key exists in dictionary"
            },
            "type_error": {
                "pattern": r"TypeError",
                "fix": "Check type before operation"
            },
            "attribute_error": {
                "pattern": r"AttributeError",
                "fix": "Check if object has attribute"
            }
        }
    
    def generate_fix(self, stack_trace: StackTrace) -> List[BugFix]:
        """生成修复方案"""
        fixes = []
        
        exception_type = stack_trace.exception_type.lower()
        
        if "indexerror" in exception_type:
            fixes.append(self._generate_index_error_fix(stack_trace))
        
        if "keyerror" in exception_type:
            fixes.append(self._generate_key_error_fix(stack_trace))
        
        if "typeerror" in exception_type:
            fixes.append(self._generate_type_error_fix(stack_trace))
        
        if "attributeerror" in exception_type:
            fixes.append(self._generate_attribute_error_fix(stack_trace))
        
        if not fixes:
            fixes.append(self._generate_generic_fix(stack_trace))
        
        return fixes
    
    def _generate_index_error_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成IndexError修复"""
        return BugFix(
            description="Index out of range - add bounds checking",
            original_code="items[index] = value",
            fixed_code="if 0 <= index < len(items):\n    items[index] = value",
            confidence=0.8,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
    
    def _generate_key_error_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成KeyError修复"""
        return BugFix(
            description="Missing key - use .get() or check existence",
            original_code="value = dict_data[key]",
            fixed_code="value = dict_data.get(key, default_value)",
            confidence=0.8,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
    
    def _generate_type_error_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成TypeError修复"""
        return BugFix(
            description="Type mismatch - convert to expected type",
            original_code="result = func(input_value)",
            fixed_code="result = func(int(input_value))",
            confidence=0.7,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
    
    def _generate_attribute_error_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成AttributeError修复"""
        return BugFix(
            description="Missing attribute - use hasattr() check",
            original_code="obj.method()",
            fixed_code="if hasattr(obj, 'method'):\n    obj.method()",
            confidence=0.7,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
    
    def _generate_generic_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成通用修复"""
        return BugFix(
            description=f"Review code at {stack_trace.root_cause_file}:{stack_trace.root_cause_line}",
            original_code="# Original code here",
            fixed_code="# Fixed code here",
            confidence=0.5,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )


class DebugAgent:
    """缺陷排查Agent"""
    
    def __init__(self, config: DebugConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.log_parser = LogParser()
        self.stack_analyzer = StackTraceAnalyzer()
        self.fix_generator = FixGenerator()
        self.reports: List[BugReport] = []
    
    def analyze_logs(self, log_content: str) -> Dict[str, Any]:
        """分析日志"""
        parsed = self.log_parser.intelligent_parse(log_content)
        
        result = {
            "total_entries": len(parsed["all"]),
            "error_count": len(parsed["errors"]),
            "warning_count": len(parsed["warnings"]),
            "critical_count": len(parsed["critical"]),
            "parsed_entries": parsed
        }
        
        return result
    
    def analyze_stack_trace(self, stack_text: str) -> BugReport:
        """分析堆栈跟踪"""
        stack_trace = self.stack_analyzer.parse_stack_trace(stack_text)
        root_cause = self.stack_analyzer.find_root_cause(stack_trace)
        
        report = BugReport(
            severity=BugSeverity.MEDIUM,
            title=f"Exception: {stack_trace.exception_type}",
            description=stack_trace.exception_message,
            stack_trace=stack_trace
        )
        
        if root_cause["found"]:
            report.root_cause = f"Root cause at {root_cause['file']}:{root_cause['line']} in {root_cause['function']}"
        
        if self.config.enable_fix_generation:
            report.fixes = self.fix_generator.generate_fix(stack_trace)
        
        self.reports.append(report)
        return report
    
    def get_fixes(self, report: BugReport) -> List[BugFix]:
        """获取修复方案"""
        return report.fixes


_global_debug_agent: Optional[DebugAgent] = None


def get_debug_agent(config: Optional[DebugConfig] = None) -> DebugAgent:
    """获取全局缺陷排查Agent"""
    global _global_debug_agent
    if _global_debug_agent is None:
        if config is None:
            config = DebugConfig(name="DebugAgent")
        _global_debug_agent = DebugAgent(config)
    return _global_debug_agent


def reset_debug_agent() -> None:
    """重置缺陷排查Agent"""
    global _global_debug_agent
    _global_debug_agent = None
