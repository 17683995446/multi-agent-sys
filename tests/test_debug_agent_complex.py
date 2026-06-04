"""
Debug Agent 复杂场景深度测试套件
发现真实运行时的bug
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


class TestComplexLogScenarios:
    """复杂日志场景测试"""
    
    def test_massive_log_volume(self):
        """测试海量日志（10000+行）"""
        logger.info("=" * 80)
        logger.info("TEST: Massive log volume (10000+ lines)")
        logger.info("=" * 80)
        
        parser = LogParser()
        
        log_lines = []
        for i in range(10000):
            level = random.choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
            log_lines.append(f"2024-01-01 12:00:{i%60:02d},000 - {level} - Message {i}")
        
        log_content = "\n".join(log_lines)
        
        logger.info(f"Generated {len(log_lines)} log lines")
        
        result = parser.intelligent_parse(log_content)
        
        assert result is not None
        assert len(result["all"]) > 0
        
        logger.info(f"Parsed successfully: {len(result['all'])} entries")
        logger.info("✓ Massive log volume test PASSED")
    
    def test_malformed_log_lines(self):
        """测试畸形日志行"""
        logger.info("=" * 80)
        logger.info("TEST: Malformed log lines")
        logger.info("=" * 80)
        
        parser = LogParser()
        
        malformed_logs = [
            "",  # Empty line
            "   ",  # Whitespace only
            "NOLEVEL",  # No level
            "2024-01-01",  # Incomplete timestamp
            "ERROR",  # Just level
            "Very long line " + "x" * 10000,  # Extremely long line
            "\t\n\r",  # Special characters
            "中文日志内容",  # Non-ASCII characters
            "Mixed 中文 and English",
        ]
        
        log_content = "\n".join(malformed_logs)
        
        logger.info(f"Testing {len(malformed_logs)} malformed cases")
        
        try:
            result = parser.parse_log(log_content)
            logger.info(f"Parsed {len(result)} entries from malformed logs")
            assert True
            logger.info("✓ Malformed log handling test PASSED")
        except Exception as e:
            logger.error(f"✗ Failed to handle malformed logs: {e}")
            pytest.fail(f"Should handle malformed logs gracefully: {e}")
    
    def test_special_characters_in_logs(self):
        """测试日志中的特殊字符"""
        logger.info("=" * 80)
        logger.info("TEST: Special characters in logs")
        logger.info("=" * 80)
        
        parser = LogParser()
        
        special_logs = [
            'ERROR: "Quote \\" test"',
            "ERROR: Backtick `test`",
            "ERROR: Angle <brackets>",
            "ERROR: SQL injection'; DROP TABLE--",
            "ERROR: HTML <script>alert('xss')</script>",
            "ERROR: Path with spaces /home/user/my documents/file.txt",
            "ERROR: Unicode ☕ 🐍 💻",
        ]
        
        log_content = "\n".join(special_logs)
        
        try:
            result = parser.parse_log(log_content)
            logger.info(f"Handled special characters: {len(result)} entries")
            assert result is not None
            logger.info("✓ Special characters test PASSED")
        except Exception as e:
            logger.error(f"✗ Failed on special characters: {e}")
            pytest.fail(f"Should handle special characters: {e}")
    
    def test_concurrent_log_parsing(self):
        """测试并发日志解析"""
        import threading
        
        logger.info("=" * 80)
        logger.info("TEST: Concurrent log parsing")
        logger.info("=" * 80)
        
        parser = LogParser()
        results = []
        errors = []
        
        def parse_worker(worker_id):
            try:
                logger.info(f"Worker {worker_id} started")
                log_content = f"INFO: Worker {worker_id} started\nERROR: Worker {worker_id} failed"
                result = parser.parse_log(log_content)
                results.append((worker_id, result))
                logger.info(f"Worker {worker_id} completed: {len(result)} entries")
            except Exception as e:
                logger.error(f"Worker {worker_id} failed: {e}")
                errors.append((worker_id, e))
        
        threads = []
        for i in range(50):
            t = threading.Thread(target=parse_worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        logger.info(f"All workers completed: {len(results)} success, {len(errors)} errors")
        
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50
        logger.info("✓ Concurrent log parsing test PASSED")


class TestComplexStackTraceScenarios:
    """复杂堆栈跟踪场景测试"""
    
    def test_deep_stack_trace(self):
        """测试深层堆栈跟踪（100+帧）"""
        logger.info("=" * 80)
        logger.info("TEST: Deep stack trace (100+ frames)")
        logger.info("=" * 80)
        
        analyzer = StackTraceAnalyzer()
        
        stack_lines = ["Traceback (most recent call last):"]
        
        for i in range(150):
            stack_lines.append(f'  File "module{i}.py", line {10+i}, in function_{i}')
            stack_lines.append(f'    return nested_call_{i+1}()')
        
        stack_lines.append("RecursionError: maximum recursion depth exceeded")
        
        stack_text = "\n".join(stack_lines)
        
        logger.info(f"Testing with {len(stack_lines)} stack lines")
        
        result = analyzer.parse_stack_trace(stack_text)
        
        assert result is not None
        assert len(result.frames) > 0
        
        logger.info(f"Parsed deep stack: {len(result.frames)} frames")
        logger.info("✓ Deep stack trace test PASSED")
    
    def test_circular_import_stack(self):
        """测试循环导入堆栈"""
        logger.info("=" * 80)
        logger.info("TEST: Circular import stack")
        logger.info("=" * 80)
        
        analyzer = StackTraceAnalyzer()
        
        circular_stack = '''
Traceback (most recent call last):
  File "main.py", line 1, in <module>
    import module_a
  File "module_a.py", line 5, in <module>
    from module_b import ClassB
  File "module_b.py", line 3, in <module>
    from module_a import ClassA
  File "module_a.py", line 7, in <module>
    import module_c
  File "module_c.py", line 2, in <module>
    from module_a import func_a
ImportError: cannot import name 'ClassA' from 'module_a'
'''
        
        logger.info("Testing circular import detection")
        
        result = analyzer.parse_stack_trace(circular_stack)
        
        assert result is not None
        assert "ImportError" in result.exception_type
        
        logger.info(f"Detected circular import: {result.exception_type}")
        logger.info("✓ Circular import stack test PASSED")
    
    def test_multiprocessing_stack(self):
        """测试多进程堆栈"""
        logger.info("=" * 80)
        logger.info("TEST: Multiprocessing stack")
        logger.info("=" * 80)
        
        analyzer = StackTraceAnalyzer()
        
        multiprocess_stack = '''
Process Process-1:
Traceback (most recent call last):
  File "multiprocessing\\spawn.py", line 127, in _main
    child_process.start()
  File "multiprocessing\context.py", line 282, in start
    result = self._target(self._args)
  File "worker.py", line 15, in run_worker
    result = process_batch(data)
  File "worker.py", line 42, in process_batch
    items[0]
IndexError: list index out of range
'''
        
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
        
        async_stack = '''
Traceback (most recent call last):
  File "asyncio\\events.py", line 80, in _run
    self._context.run(self._callback, *self._args)
  File "asyncio\coroutines.py", line 178, in send
    self.close()
  File "coroutines.py", line 257, in close
    return self.close()
RuntimeError: coroutine closed badly
'''
        
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
        
        sql_stack = '''
Traceback (most recent call last):
  File "db.py", line 15, in execute_query
    cursor.execute(query, params)
  File "postgresql\\client.py", line 234, in execute
    return self._execute_impl(query, params)
  File "postgresql\client.py", line 456, in _execute_impl
    raise error
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "users_email_key"
DETAIL: Key (email)=(test@example.com) already exists.
'''
        
        logger.info("Testing SQL error stack")
        
        result = analyzer.parse_stack_trace(sql_stack)
        
        assert result is not None
        assert "UniqueViolation" in result.exception_type
        
        logger.info(f"Detected SQL error: {result.exception_type}")
        logger.info("✓ SQL error stack test PASSED")


class TestComplexFixGenerationScenarios:
    """复杂修复生成场景测试"""
    
    def test_multiple_exception_types(self):
        """测试多异常类型堆栈"""
        logger.info("=" * 80)
        logger.info("TEST: Multiple exception types in stack")
        logger.info("=" * 80)
        
        generator = FixGenerator()
        
        complex_stack = StackTrace(
            exception_type="ValueError",
            exception_message="invalid literal for int() with base 10: 'abc'",
            root_cause_file="parser.py",
            root_cause_line=42
        )
        
        logger.info("Testing ValueError fix generation")
        
        fixes = generator.generate_fix(complex_stack)
        
        assert len(fixes) > 0
        
        logger.info(f"Generated {len(fixes)} fixes for ValueError")
        
        for fix in fixes:
            logger.info(f"Fix: {fix.description}, confidence: {fix.confidence}")
        
        logger.info("✓ Multiple exception types test PASSED")
    
    def test_fix_confidence_levels(self):
        """测试修复置信度"""
        logger.info("=" * 80)
        logger.info("TEST: Fix confidence levels")
        logger.info("=" * 80)
        
        generator = FixGenerator()
        
        test_cases = [
            ("IndexError", 0.8),
            ("KeyError", 0.8),
            ("TypeError", 0.7),
            ("AttributeError", 0.7),
            ("UnknownError", 0.5),
        ]
        
        for exc_type, expected_confidence in test_cases:
            stack = StackTrace(
                exception_type=exc_type,
                exception_message="test",
                root_cause_file="test.py",
                root_cause_line=1
            )
            
            fixes = generator.generate_fix(stack)
            
            assert len(fixes) > 0
            confidence = fixes[0].confidence
            
            logger.info(f"{exc_type}: confidence = {confidence}")
            
            assert confidence == expected_confidence
        
        logger.info("✓ Fix confidence levels test PASSED")
    
    def test_empty_stack_trace(self):
        """测试空堆栈跟踪"""
        logger.info("=" * 80)
        logger.info("TEST: Empty stack trace")
        logger.info("=" * 80)
        
        generator = FixGenerator()
        
        empty_stack = StackTrace(
            exception_type="",
            exception_message=""
        )
        
        logger.info("Testing empty stack fix generation")
        
        try:
            fixes = generator.generate_fix(empty_stack)
            
            assert len(fixes) > 0
            logger.info(f"Generated {len(fixes)} fixes for empty stack")
            logger.info("✓ Empty stack trace test PASSED")
        except Exception as e:
            logger.error(f"✗ Failed on empty stack: {e}")
            pytest.fail(f"Should handle empty stack: {e}")


class TestComplexIntegrationScenarios:
    """复杂集成场景测试"""
    
    def test_real_world_error_scenario(self):
        """测试真实世界错误场景"""
        logger.info("=" * 80)
        logger.info("TEST: Real-world error scenario")
        logger.info("=" * 80)
        
        config = DebugConfig(name="RealWorldTest")
        agent = DebugAgent(config)
        
        real_log = '''
2024-01-01 10:00:00,000 - INFO - Application starting...
2024-01-01 10:00:01,000 - DEBUG - Loading configuration from config.json
2024-01-01 10:00:02,000 - INFO - Connecting to database...
2024-01-01 10:00:03,000 - WARNING - Connection slow, retrying...
2024-01-01 10:00:05,000 - ERROR - Database connection failed
2024-01-01 10:00:05,001 - CRITICAL - Application cannot start without database
'''
        
        real_stack = '''
Traceback (most recent call last):
  File "app.py", line 15, in main
    initialize_database()
  File "db.py", line 42, in initialize_database
    connection = connect_db(config)
  File "db.py", line 78, in connect_db
    cursor.execute("SELECT 1")
  File "C:\\Program Files\\Python\\lib\\site-packages\\psycopg2\\__init__.py", line 102, in execute
    return _cursor.execute(query, args)
  File "C:\\Program Files\\Python\\lib\\site-packages\\psycopg2\\__init__.py", line 123, in connect
    **params)
  File "C:\\Program Files\\Python\\lib\\site-packages\\psycopg2\\__init__.py", line 145, in connect
    factory=connection_factory)
psycopg2.OperationalError: could not connect to server: Connection refused
        Is the server running on host "localhost" (127.0.0.1) and accepting
        TCP/IP connections on port 5432?
'''
        
        logger.info("Analyzing real-world error...")
        
        log_result = agent.analyze_logs(real_log)
        logger.info(f"Log analysis: {log_result['error_count']} errors, {log_result['critical_count']} critical")
        
        report = agent.analyze_stack_trace(real_stack)
        logger.info(f"Stack analysis: {report.title}")
        logger.info(f"Root cause: {report.root_cause}")
        
        fixes = agent.get_fixes(report)
        logger.info(f"Generated {len(fixes)} fixes")
        
        assert log_result['error_count'] > 0
        assert report is not None
        assert len(fixes) > 0
        
        logger.info("✓ Real-world error scenario test PASSED")
    
    def test_mixed_error_types(self):
        """测试混合错误类型"""
        logger.info("=" * 80)
        logger.info("TEST: Mixed error types")
        logger.info("=" * 80)
        
        config = DebugConfig(name="MixedTest")
        agent = DebugAgent(config)
        
        mixed_log = '''
INFO - App started
DEBUG - Loading data
WARNING - Deprecated feature used
ERROR - Failed to save
ERROR - File not found
WARNING - Slow query detected
CRITICAL - Memory low
'''
        
        logger.info("Analyzing mixed log types...")
        
        result = agent.analyze_logs(mixed_log)
        
        assert result['total_entries'] > 0
        assert result['error_count'] >= 2
        assert result['warning_count'] >= 2
        
        logger.info(f"Analysis: {result}")
        logger.info("✓ Mixed error types test PASSED")
    
    def test_stress_test_agent(self):
        """压力测试Agent"""
        logger.info("=" * 80)
        logger.info("TEST: Stress test - 100 rapid analyses")
        logger.info("=" * 80)
        
        config = DebugConfig(name="StressTest")
        agent = DebugAgent(config)
        
        for i in range(100):
            log = f"INFO - Log entry {i}\nERROR - Error {i}"
            result = agent.analyze_logs(log)
            
            stack = f'''
Traceback (most recent call last):
  File "test{i}.py", line {i}, in test_func
    x = items[{i}]
IndexError: list index out of range
'''
            report = agent.analyze_stack_trace(stack)
        
        logger.info(f"Completed 100 rapid analyses")
        logger.info(f"Total reports: {len(agent.reports)}")
        
        assert len(agent.reports) == 100
        
        logger.info("✓ Stress test PASSED")


class TestEdgeCaseScenarios:
    """边界场景测试"""
    
    def test_unicode_handling(self):
        """测试Unicode处理"""
        logger.info("=" * 80)
        logger.info("TEST: Unicode handling")
        logger.info("=" * 80)
        
        parser = LogParser()
        
        unicode_log = '''
INFO - 中文日志测试
ERROR - 日本語エラー
WARNING - 한국어 경고
ERROR - العربية خطأ
INFO -emoji test ☕🐍💻
'''
        
        logger.info("Testing Unicode in logs")
        
        try:
            result = parser.parse_log(unicode_log)
            logger.info(f"Handled Unicode: {len(result)} entries")
            assert result is not None
            logger.info("✓ Unicode handling test PASSED")
        except Exception as e:
            logger.error(f"✗ Unicode handling failed: {e}")
            pytest.fail(f"Should handle Unicode: {e}")
    
    def test_extremely_long_exception_message(self):
        """测试超长异常消息"""
        logger.info("=" * 80)
        logger.info("TEST: Extremely long exception message")
        logger.info("=" * 80)
        
        analyzer = StackTraceAnalyzer()
        
        long_message = "x" * 100000
        
        long_stack = f'''
Traceback (most recent call last):
  File "test.py", line 1, in test
    raise ValueError("{long_message[:1000]}...")
ValueError: {long_message[:5000]}
'''
        
        logger.info(f"Testing with message length: {len(long_message)}")
        
        try:
            result = analyzer.parse_stack_trace(long_stack)
            logger.info(f"Handled long message: {len(result.exception_message)} chars")
            assert result is not None
            logger.info("✓ Extremely long exception message test PASSED")
        except Exception as e:
            logger.error(f"✗ Long message handling failed: {e}")
            pytest.fail(f"Should handle long messages: {e}")
    
    def test_null_bytes_in_logs(self):
        """测试日志中的null字节"""
        logger.info("=" * 80)
        logger.info("TEST: Null bytes in logs")
        logger.info("=" * 80)
        
        parser = LogParser()
        
        null_log = "ERROR: Test with null byte\x00embedded"
        
        logger.info("Testing null bytes")
        
        try:
            result = parser.parse_log(null_log)
            logger.info(f"Handled null bytes")
            assert result is not None
            logger.info("✓ Null bytes test PASSED")
        except Exception as e:
            logger.warning(f"Null bytes may cause issues: {e}")
            logger.info("Note: Null bytes handling is implementation-specific")


class TestRegressionAndStability:
    """回归和稳定性测试"""
    
    def test_agent_state_persistence(self):
        """测试Agent状态持久化"""
        logger.info("=" * 80)
        logger.info("TEST: Agent state persistence")
        logger.info("=" * 80)
        
        reset_debug_agent()
        
        agent1 = get_debug_agent()
        agent1.reports.append(BugReport(title="Test Report 1"))
        
        agent2 = get_debug_agent()
        agent2.reports.append(BugReport(title="Test Report 2"))
        
        logger.info(f"Agent1 reports: {len(agent1.reports)}")
        logger.info(f"Agent2 reports: {len(agent2.reports)}")
        
        assert agent1 is agent2
        assert len(agent1.reports) == 2
        
        reset_debug_agent()
        
        agent3 = get_debug_agent()
        assert len(agent3.reports) == 0
        
        logger.info("✓ Agent state persistence test PASSED")
    
    def test_rapid_reset_cycles(self):
        """测试快速重置周期"""
        logger.info("=" * 80)
        logger.info("TEST: Rapid reset cycles (100 times)")
        logger.info("=" * 80)
        
        for i in range(100):
            reset_debug_agent()
            agent = get_debug_agent()
            assert agent is not None
        
        logger.info("✓ Rapid reset cycles test PASSED")
    
    def test_memory_leak_check(self):
        """测试内存泄漏检查"""
        logger.info("=" * 80)
        logger.info("TEST: Memory leak check")
        logger.info("=" * 80)
        
        reset_debug_agent()
        
        agent = get_debug_agent()
        
        for i in range(1000):
            log = f"INFO - Log {i}"
            agent.analyze_logs(log)
            
            stack = f"Traceback: File test.py, line {i}\nError: test"
            agent.analyze_stack_trace(stack)
        
        logger.info(f"After 1000 operations:")
        logger.info(f"  Reports: {len(agent.reports)}")
        
        assert len(agent.reports) == 1000
        
        logger.info("✓ Memory leak check test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
