"""
阶段35验收测试：缺陷排查Agent初始化

验收标准：
1. ✓ Agent类定义（完整配置）
2. ✓ 日志解析能力（智能解析）
3. ✓ 堆栈定位能力（根因定位）
4. ✓ 修复方案输出（代码方案）
"""

import pytest
from src.architecture.debug_agent import (
    BugSeverity,
    LogLevel,
    LogEntry,
    StackFrame,
    StackTrace,
    BugFix,
    BugReport,
    DebugConfig,
    LogParser,
    StackTraceAnalyzer,
    FixGenerator,
    DebugAgent,
    get_debug_agent,
    reset_debug_agent
)


class TestDebugConfig:
    """测试Agent类定义"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = DebugConfig(name="DebugAgent")
        
        assert config.name == "DebugAgent"
        assert config.enable_intelligent_log_parsing == True
        assert config.enable_root_cause_analysis == True
        assert config.enable_fix_generation == True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = DebugConfig(
            name="CustomDebugAgent",
            enable_fix_generation=False,
            max_stack_depth=20
        )
        
        assert config.name == "CustomDebugAgent"
        assert config.enable_fix_generation == False


class TestLogParser:
    """测试日志解析能力"""
    
    def test_parse_log(self):
        """测试解析日志"""
        parser = LogParser()
        
        log_content = '''
INFO: Application started
WARNING: Deprecated API used
ERROR: Failed to connect to database
CRITICAL: System shutdown
'''
        
        entries = parser.parse_log(log_content)
        
        assert len(entries) > 0
    
    def test_intelligent_parse(self):
        """测试智能解析"""
        parser = LogParser()
        
        log_content = '''
INFO: App started
WARNING: Deprecated feature
ERROR: Connection failed
CRITICAL: Crash
'''
        
        parsed = parser.intelligent_parse(log_content)
        
        assert "errors" in parsed
        assert "warnings" in parsed


class TestStackTraceAnalyzer:
    """测试堆栈定位能力"""
    
    def test_parse_stack_trace(self):
        """测试解析堆栈跟踪"""
        analyzer = StackTraceAnalyzer()
        
        stack_text = '''
Traceback (most recent call last):
  File "main.py", line 10, in main
    result = process_data(data)
  File "module.py", line 25, in process_data
    return items[5]
IndexError: list index out of range
'''
        
        stack_trace = analyzer.parse_stack_trace(stack_text)
        
        assert len(stack_trace.frames) > 0
        assert "IndexError" in stack_trace.exception_type
    
    def test_find_root_cause(self):
        """测试查找根因"""
        analyzer = StackTraceAnalyzer()
        
        stack_text = '''
Traceback (most recent call last):
  File "main.py", line 10, in main
    result = func()
  File "module.py", line 25, in func
    return items[100]
IndexError: list index out of range
'''
        
        stack_trace = analyzer.parse_stack_trace(stack_text)
        root_cause = analyzer.find_root_cause(stack_trace)
        
        assert root_cause["found"] == True
        assert root_cause["file"] is not None
        assert root_cause["line"] > 0


class TestFixGenerator:
    """测试修复方案输出"""
    
    def test_generate_fix_index_error(self):
        """测试生成IndexError修复"""
        generator = FixGenerator()
        
        stack_trace = StackTrace(
            exception_type="IndexError",
            exception_message="list index out of range",
            root_cause_file="module.py",
            root_cause_line=25
        )
        
        fixes = generator.generate_fix(stack_trace)
        
        assert len(fixes) > 0
        assert any("Index" in f.description for f in fixes)
    
    def test_generate_fix_key_error(self):
        """测试生成KeyError修复"""
        generator = FixGenerator()
        
        stack_trace = StackTrace(
            exception_type="KeyError",
            exception_message="missing_key",
            root_cause_file="data.py",
            root_cause_line=15
        )
        
        fixes = generator.generate_fix(stack_trace)
        
        assert len(fixes) > 0


class TestDebugAgent:
    """测试缺陷排查Agent"""
    
    def test_analyze_logs(self):
        """测试分析日志"""
        config = DebugConfig(name="TestAgent")
        agent = DebugAgent(config)
        
        log_content = '''
INFO: Started
ERROR: Failed to connect
WARNING: Slow response
'''
        
        result = agent.analyze_logs(log_content)
        
        assert result["total_entries"] > 0
        assert result["error_count"] > 0
    
    def test_analyze_stack_trace(self):
        """测试分析堆栈跟踪"""
        config = DebugConfig(name="TestAgent")
        agent = DebugAgent(config)
        
        stack_text = '''
Traceback (most recent call last):
  File "test.py", line 5, in <module>
    x = [1, 2, 3][10]
IndexError: list index out of range
'''
        
        report = agent.analyze_stack_trace(stack_text)
        
        assert report is not None
        assert report.stack_trace is not None
        assert len(agent.reports) == 1
    
    def test_get_fixes(self):
        """测试获取修复方案"""
        config = DebugConfig(name="TestAgent")
        agent = DebugAgent(config)
        
        stack_text = '''
Traceback (most recent call last):
  File "test.py", line 10, in test
    d = {}; d['missing']
KeyError: 'missing'
'''
        
        report = agent.analyze_stack_trace(stack_text)
        fixes = agent.get_fixes(report)
        
        assert len(fixes) > 0


class TestGlobalAgent:
    """测试全局Agent"""
    
    def test_get_global_agent(self):
        """测试获取全局Agent"""
        reset_debug_agent()
        
        agent1 = get_debug_agent()
        agent2 = get_debug_agent()
        
        assert agent1 is agent2
    
    def test_reset_global_agent(self):
        """测试重置全局Agent"""
        agent1 = get_debug_agent()
        reset_debug_agent()
        agent2 = get_debug_agent()
        
        assert agent1 is not agent2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
