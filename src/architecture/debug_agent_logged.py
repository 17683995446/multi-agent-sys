"""
Debug Agent 日志追踪版本
每个函数调用都记录详细日志
"""

import uuid
import re
import traceback
import logging
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger("DebugAgent")


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
    """日志解析器 - 带日志追踪"""
    
    def __init__(self):
        logger.debug("LogParser.__init__ called")
        self.log_patterns = {
            "timestamp": r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}",
            "level": r"DEBUG|INFO|WARNING|ERROR|CRITICAL",
            "file_line": r'File "([^"]+)", line (\d+)',
            "function": r"in (\w+)",
            "exception": r"(\w+):\s*(.*)"
        }
        logger.info(f"LogParser initialized with patterns: {list(self.log_patterns.keys())}")
    
    def parse_log(self, log_content: str) -> List[LogEntry]:
        """解析日志"""
        logger.info(f"parse_log called with content length: {len(log_content)}")
        
        entries = []
        lines = log_content.strip().split('\n')
        logger.debug(f"Split into {len(lines)} lines")
        
        for i, line in enumerate(lines):
            logger.debug(f"Processing line {i}: {line[:50]}...")
            entry = self._parse_log_line(line)
            if entry:
                logger.debug(f"Created LogEntry: level={entry.level}, message={entry.message[:30]}")
                entries.append(entry)
        
        logger.info(f"parse_log completed: {len(entries)} entries created")
        return entries
    
    def _parse_log_line(self, line: str) -> Optional[LogEntry]:
        """解析单行日志"""
        logger.debug(f"_parse_log_line called with: {line[:100]}")
        
        entry = LogEntry()
        entry.message = line
        
        level_match = re.search(self.log_patterns["level"], line, re.IGNORECASE)
        if level_match:
            level_str = level_match.group(0).upper()
            logger.debug(f"Found level match: {level_str}")
            try:
                entry.level = LogLevel(level_str.lower())
                logger.debug(f"Set entry.level to {entry.level}")
            except ValueError as e:
                logger.warning(f"Failed to set level: {e}")
        
        if entry.message:
            logger.debug(f"Returning LogEntry with message length: {len(entry.message)}")
            return entry
        
        logger.warning("Empty message, returning None")
        return None
    
    def intelligent_parse(self, log_content: str) -> Dict[str, List[LogEntry]]:
        """智能解析"""
        logger.info("intelligent_parse called")
        
        entries = self.parse_log(log_content)
        logger.debug(f"Parsed {len(entries)} total entries")
        
        errors = [e for e in entries if e.level == LogLevel.ERROR]
        warnings = [e for e in entries if e.level == LogLevel.WARNING]
        critical = [e for e in entries if e.level == LogLevel.CRITICAL]
        
        logger.info(f"Categorized: {len(errors)} errors, {len(warnings)} warnings, {len(critical)} critical")
        
        return {
            "all": entries,
            "errors": errors,
            "warnings": warnings,
            "critical": critical
        }


class StackTraceAnalyzer:
    """堆栈跟踪分析器 - 带日志追踪"""
    
    def __init__(self):
        logger.debug("StackTraceAnalyzer.__init__ called")
        self.stack_patterns = {
            "file_line": r'File "([^"]+)", line (\d+)',
            "function": r"in (\w+)",
            "code": r'\s*(\w.*)',
            "exception": r"(\w+):\s*(.*)"
        }
        logger.info(f"StackTraceAnalyzer initialized with patterns: {list(self.stack_patterns.keys())}")
    
    def parse_stack_trace(self, stack_text: str) -> StackTrace:
        """解析堆栈跟踪"""
        logger.info(f"parse_stack_trace called with stack length: {len(stack_text)}")
        
        stack_trace = StackTrace()
        lines = stack_text.strip().split('\n')
        
        logger.debug(f"Split stack into {len(lines)} lines")
        
        for i, line in enumerate(lines):
            logger.debug(f"Processing stack line {i}: {line[:80]}")
            
            file_match = re.search(self.stack_patterns["file_line"], line)
            
            if file_match:
                logger.debug(f"Found file pattern match: {file_match.groups()}")
                frame = StackFrame()
                frame.file_path = file_match.group(1)
                frame.line_number = int(file_match.group(2))
                
                if i + 1 < len(lines):
                    func_match = re.search(self.stack_patterns["function"], lines[i + 1])
                    if func_match:
                        frame.function_name = func_match.group(1)
                        logger.debug(f"Found function: {frame.function_name}")
                
                stack_trace.frames.append(frame)
                logger.debug(f"Added StackFrame: {frame.file_path}:{frame.line_number} in {frame.function_name}")
        
        for i, line in enumerate(reversed(lines)):
            logger.debug(f"Searching for exception in line {len(lines)-1-i}: {line[:80]}")
            
            exc_match = re.search(self.stack_patterns["exception"], line)
            if exc_match:
                potential_type = exc_match.group(1)
                potential_msg = exc_match.group(2)
                
                # Skip DETAIL lines in PostgreSQL errors
                if potential_type == "DETAIL":
                    continue
                
                stack_trace.exception_type = potential_type
                stack_trace.exception_message = potential_msg
                logger.info(f"Found exception: {stack_trace.exception_type}: {stack_trace.exception_message}")
                break
        
        if stack_trace.frames:
            last_frame = stack_trace.frames[-1]
            stack_trace.root_cause_file = last_frame.file_path
            stack_trace.root_cause_line = last_frame.line_number
            logger.info(f"Root cause identified: {stack_trace.root_cause_file}:{stack_trace.root_cause_line}")
        else:
            logger.warning("No frames found in stack trace")
        
        logger.info(f"parse_stack_trace completed: {len(stack_trace.frames)} frames")
        return stack_trace
    
    def find_root_cause(self, stack_trace: StackTrace) -> Dict[str, Any]:
        """查找根因"""
        logger.info("find_root_cause called")
        
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
            logger.info(f"Root cause found: {result}")
        else:
            logger.warning("No frames to analyze for root cause")
        
        return result


class FixGenerator:
    """修复方案生成器 - 带日志追踪"""
    
    def __init__(self):
        logger.debug("FixGenerator.__init__ called")
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
        logger.info(f"FixGenerator initialized with {len(self.fix_patterns)} patterns")
    
    def generate_fix(self, stack_trace: StackTrace) -> List[BugFix]:
        """生成修复方案"""
        logger.info(f"generate_fix called for exception: {stack_trace.exception_type}")
        
        fixes = []
        exception_type = stack_trace.exception_type.lower()
        logger.debug(f"Normalized exception type: {exception_type}")
        
        if "indexerror" in exception_type:
            logger.info("Detected IndexError, generating fix...")
            fixes.append(self._generate_index_error_fix(stack_trace))
        
        if "keyerror" in exception_type:
            logger.info("Detected KeyError, generating fix...")
            fixes.append(self._generate_key_error_fix(stack_trace))
        
        if "typeerror" in exception_type:
            logger.info("Detected TypeError, generating fix...")
            fixes.append(self._generate_type_error_fix(stack_trace))
        
        if "attributeerror" in exception_type:
            logger.info("Detected AttributeError, generating fix...")
            fixes.append(self._generate_attribute_error_fix(stack_trace))
        
        if not fixes:
            logger.warning("No specific fix pattern matched, generating generic fix")
            fixes.append(self._generate_generic_fix(stack_trace))
        
        logger.info(f"generate_fix completed: {len(fixes)} fixes generated")
        return fixes
    
    def _generate_index_error_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成IndexError修复"""
        logger.debug(f"_generate_index_error_fix called for {stack_trace.root_cause_file}:{stack_trace.root_cause_line}")
        
        fix = BugFix(
            description="Index out of range - add bounds checking",
            original_code="items[index] = value",
            fixed_code="if 0 <= index < len(items):\n    items[index] = value",
            confidence=0.8,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
        
        logger.debug(f"Created IndexError fix with confidence {fix.confidence}")
        return fix
    
    def _generate_key_error_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成KeyError修复"""
        logger.debug(f"_generate_key_error_fix called for {stack_trace.root_cause_file}:{stack_trace.root_cause_line}")
        
        fix = BugFix(
            description="Missing key - use .get() or check existence",
            original_code="value = dict_data[key]",
            fixed_code="value = dict_data.get(key, default_value)",
            confidence=0.8,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
        
        logger.debug(f"Created KeyError fix with confidence {fix.confidence}")
        return fix
    
    def _generate_type_error_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成TypeError修复"""
        logger.debug(f"_generate_type_error_fix called for {stack_trace.root_cause_file}:{stack_trace.root_cause_line}")
        
        fix = BugFix(
            description="Type mismatch - convert to expected type",
            original_code="result = func(input_value)",
            fixed_code="result = func(int(input_value))",
            confidence=0.7,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
        
        logger.debug(f"Created TypeError fix with confidence {fix.confidence}")
        return fix
    
    def _generate_attribute_error_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成AttributeError修复"""
        logger.debug(f"_generate_attribute_error_fix called for {stack_trace.root_cause_file}:{stack_trace.root_cause_line}")
        
        fix = BugFix(
            description="Missing attribute - use hasattr() check",
            original_code="obj.method()",
            fixed_code="if hasattr(obj, 'method'):\n    obj.method()",
            confidence=0.7,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
        
        logger.debug(f"Created AttributeError fix with confidence {fix.confidence}")
        return fix
    
    def _generate_generic_fix(self, stack_trace: StackTrace) -> BugFix:
        """生成通用修复"""
        logger.debug(f"_generate_generic_fix called for {stack_trace.root_cause_file}:{stack_trace.root_cause_line}")
        
        fix = BugFix(
            description=f"Review code at {stack_trace.root_cause_file}:{stack_trace.root_cause_line}",
            original_code="# Original code here",
            fixed_code="# Fixed code here",
            confidence=0.5,
            file_path=stack_trace.root_cause_file,
            line_number=stack_trace.root_cause_line
        )
        
        logger.debug(f"Created generic fix with confidence {fix.confidence}")
        return fix


class DebugAgent:
    """缺陷排查Agent - 带完整日志追踪"""
    
    def __init__(self, config: DebugConfig):
        logger.info(f"DebugAgent.__init__ called with config: {config.name}")
        
        self.config = config
        self.agent_id = str(uuid.uuid4())
        logger.debug(f"Generated agent_id: {self.agent_id}")
        
        self.log_parser = LogParser()
        logger.debug("Initialized log_parser")
        
        self.stack_analyzer = StackTraceAnalyzer()
        logger.debug("Initialized stack_analyzer")
        
        self.fix_generator = FixGenerator()
        logger.debug("Initialized fix_generator")
        
        self.reports: List[BugReport] = []
        logger.info("DebugAgent initialization complete")
    
    def analyze_logs(self, log_content: str) -> Dict[str, Any]:
        """分析日志"""
        logger.info("analyze_logs called")
        logger.debug(f"Log content preview: {log_content[:100]}...")
        
        parsed = self.log_parser.intelligent_parse(log_content)
        logger.debug(f"Parsed {parsed['total_entries'] if 'total_entries' in parsed else 'N/A'} entries")
        
        result = {
            "total_entries": len(parsed["all"]),
            "error_count": len(parsed["errors"]),
            "warning_count": len(parsed["warnings"]),
            "critical_count": len(parsed["critical"]),
            "parsed_entries": parsed
        }
        
        logger.info(f"analyze_logs completed: {result}")
        return result
    
    def analyze_stack_trace(self, stack_text: str) -> BugReport:
        """分析堆栈跟踪"""
        logger.info("analyze_stack_trace called")
        logger.debug(f"Stack trace preview: {stack_text[:100]}...")
        
        stack_trace = self.stack_analyzer.parse_stack_trace(stack_text)
        logger.debug(f"Parsed stack trace: {len(stack_trace.frames)} frames")
        
        root_cause = self.stack_analyzer.find_root_cause(stack_trace)
        logger.debug(f"Root cause: {root_cause}")
        
        report = BugReport(
            severity=BugSeverity.MEDIUM,
            title=f"Exception: {stack_trace.exception_type}",
            description=stack_trace.exception_message,
            stack_trace=stack_trace
        )
        
        if root_cause["found"]:
            report.root_cause = f"Root cause at {root_cause['file']}:{root_cause['line']} in {root_cause['function']}"
            logger.info(f"Report root cause: {report.root_cause}")
        
        if self.config.enable_fix_generation:
            logger.info("Fix generation enabled, generating fixes...")
            report.fixes = self.fix_generator.generate_fix(stack_trace)
            logger.info(f"Generated {len(report.fixes)} fixes")
        else:
            logger.info("Fix generation disabled")
        
        self.reports.append(report)
        logger.info(f"Report {report.report_id} added to reports list (total: {len(self.reports)})")
        
        return report
    
    def get_fixes(self, report: BugReport) -> List[BugFix]:
        """获取修复方案"""
        logger.info(f"get_fixes called for report {report.report_id}")
        logger.debug(f"Report has {len(report.fixes)} fixes")
        
        return report.fixes


_global_debug_agent: Optional[DebugAgent] = None


def get_debug_agent(config: Optional[DebugConfig] = None) -> DebugAgent:
    """获取全局缺陷排查Agent"""
    logger.info(f"get_debug_agent called with config: {config}")
    
    global _global_debug_agent
    if _global_debug_agent is None:
        logger.info("Creating new DebugAgent instance")
        if config is None:
            config = DebugConfig(name="DebugAgent")
        _global_debug_agent = DebugAgent(config)
    else:
        logger.debug("Reusing existing DebugAgent instance")
    
    return _global_debug_agent


def reset_debug_agent() -> None:
    """重置缺陷排查Agent"""
    logger.info("reset_debug_agent called")
    
    global _global_debug_agent
    _global_debug_agent = None
    
    logger.info("DebugAgent reset complete")
