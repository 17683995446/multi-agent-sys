
"""
Debug Agent 复杂场景深度测试套件
发现真实运行时的bug - 修复版本
"""

import pytest
import random
import string
import logging
from datetime import datetime
from src.architecture.debug_agent_logged import (
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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ComplexTest")


class TestComplexStackTraceScenarios:
    """复杂堆栈跟踪场景测试"""
    
    def test_multiprocessing_stack(self):
        """测试多进程堆栈"""
        logger.info("=" * 80)
        logger.info("TEST: Multiprocessing stack")
        logger.info("=" * 80)
        
        analyzer = StackTraceAnalyzer()
        
        multiprocess_stack = """
Traceback (most recent call last):
  File "multiprocessing\\spawn.py", line 127, in _main
    child_process.start()
  File "multiprocessing\\context.py", line 282, in start
    result = self._target(self._args)
  File "worker.py", line 15, in run_worker
    result = process_batch(data)
  File "worker.py", line 42, in process_batch
    items[0]
IndexError: list index out of range
"""
        
        logger.info("Testing multiprocessing stack")
        
        result = analyzer.parse_stack_trace(multiprocess_stack)
        
        assert result is not None
        assert len(result.frames) > 0
        
        logger.info(f"Parsed multiprocess stack: {len(result.frames)} frames")
        logger.info("✓ Multiprocessing stack test PASSED")
    
    def test_async_stack_trace(self):
        """测试异步堆栈跟踪"""
        logger.info("=" * 80)
        logger.info("TEST: Async stack trace")
        logger.info("=" * 80)
        
        analyzer = StackTraceAnalyzer()
        
        async_stack = """
Traceback (most recent call last):
  File "asyncio\\events.py", line 80, in _run
    self._context.run(self._callback, *self._args)
  File "asyncio\\coroutines.py", line 178, in send
    self.close()
  File "coroutines.py", line 257, in close
    return self.close()
RuntimeError: coroutine closed badly
"""
        
        logger.info("Testing async stack")
        
        result = analyzer.parse_stack_trace(async_stack)
        
        assert result is not None
        
        logger.info(f"Parsed async stack: {result.exception_type}")
        logger.info("✓ Async stack trace test PASSED")
    
    def test_sql_error_stack(self):
        """测试SQL错误堆栈"""
        logger.info("=" * 80)
        logger.info("TEST: SQL error stack")
        logger.info("=" * 80)
        
        analyzer = StackTraceAnalyzer()
        
        sql_stack = """
Traceback (most recent call last):
  File "db.py", line 15, in execute_query
    cursor.execute(query, params)
  File "postgresql\\client.py", line 234, in execute
    return self._execute_impl(query, params)
  File "postgresql\\client.py", line 456, in _execute_impl
    raise error
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "users_email_key"
DETAIL: Key (email)=(test@example.com) already exists.
"""
        
        logger.info("Testing SQL error stack")
        
        result = analyzer.parse_stack_trace(sql_stack)
        
        assert result is not None
        assert "UniqueViolation" in result.exception_type
        
        logger.info(f"Detected SQL error: {result.exception_type}")
        logger.info("✓ SQL error stack test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
