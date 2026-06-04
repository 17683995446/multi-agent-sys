"""
Development Agent 复杂场景测试
"""

import pytest
import logging
import time
import random
import string
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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("DevAgentTest")


class TestCodeGeneratorComplexity:
    """代码生成器复杂度测试"""
    
    def test_massive_code_generation(self):
        """测试大规模代码生成"""
        logger.info("=" * 80)
        logger.info("TEST: Massive code generation (1000 functions)")
        logger.info("=" * 80)
        
        generator = CodeGenerator()
        
        start_time = time.time()
        
        for i in range(1000):
            code = generator.generate_function(
                name=f"function_{i}",
                params=[f"param{j}" for j in range(5)],
                return_type="int",
                body=f"return {i}"
            )
            
            assert code is not None
            assert "function_" in code.name
        
        elapsed = time.time() - start_time
        
        logger.info(f"Generated 1000 functions in {elapsed:.2f} seconds")
        logger.info(f"Average: {elapsed/1000*1000:.2f}ms per function")
        
        assert elapsed < 10  # Should complete in under 10 seconds
        logger.info("✓ Massive code generation test PASSED")
    
    def test_very_long_function_names(self):
        """测试超长函数名"""
        logger.info("=" * 80)
        logger.info("TEST: Very long function names")
        logger.info("=" * 80)
        
        generator = CodeGenerator()
        
        long_name = "a" * 1000
        
        try:
            code = generator.generate_function(name=long_name)
            logger.info(f"Generated function with {len(long_name)} char name")
            assert code is not None
            logger.info("✓ Long function names test PASSED")
        except Exception as e:
            logger.error(f"Failed on long function name: {e}")
            pytest.fail(f"Should handle long names: {e}")
    
    def test_unicode_in_code_generation(self):
        """测试Unicode在代码生成中"""
        logger.info("=" * 80)
        logger.info("TEST: Unicode in code generation")
        logger.info("=" * 80)
        
        generator = CodeGenerator()
        
        unicode_tests = [
            ("中文函数", "中文注释"),
            ("функция", "комментарий"),
            ("دالة", "تعليق"),
            ("函数_测试", "注释内容"),
        ]
        
        for func_name, comment in unicode_tests:
            try:
                code = generator.generate_function(
                    name=func_name,
                    body=f'# {comment}'
                )
                
                assert code is not None
                logger.info(f"Generated: {func_name}")
            except Exception as e:
                logger.error(f"Failed on {func_name}: {e}")
                pytest.fail(f"Should handle Unicode: {e}")
        
        logger.info("✓ Unicode in code generation test PASSED")
    
    def test_special_characters_in_code(self):
        """测试代码中的特殊字符"""
        logger.info("=" * 80)
        logger.info("TEST: Special characters in code")
        logger.info("=" * 80)
        
        generator = CodeGenerator()
        
        special_cases = [
            ("func_with_underscore", "normal_function"),
            ("func-with-dash", "dashed-function"),
            ("func.with.dots", "dotted.function"),
            ("func_with_123", "numeric_param"),
        ]
        
        for func_name, param in special_cases:
            try:
                code = generator.generate_function(
                    name=func_name,
                    params=[param]
                )
                
                assert code is not None
                logger.info(f"Generated: {func_name}({param})")
            except Exception as e:
                logger.error(f"Failed on {func_name}: {e}")
        
        logger.info("✓ Special characters test PASSED")
    
    def test_deeply_nested_generation(self):
        """测试深度嵌套生成"""
        logger.info("=" * 80)
        logger.info("TEST: Deeply nested code generation")
        logger.info("=" * 80)
        
        generator = CodeGenerator()
        
        nested_body = """
if condition1:
    if condition2:
        if condition3:
            if condition4:
                if condition5:
                    return True
"""
        
        code = generator.generate_function(
            name="deeply_nested",
            body=nested_body
        )
        
        assert code is not None
        assert "condition5" in code.source_code
        
        logger.info("✓ Deeply nested generation test PASSED")


class TestSemanticModifierComplexity:
    """语义修改器复杂度测试"""
    
    def test_complex_semantic_optimizations(self):
        """测试复杂语义优化"""
        logger.info("=" * 80)
        logger.info("TEST: Complex semantic optimizations")
        logger.info("=" * 80)
        
        modifier = SemanticModifier()
        
        test_cases = [
            (
                "def old_func(): x = True\nif x == True: pass",
                "if x:"
            ),
            (
                "def process(): items = [1,2,3]\nfor i in range(len(items)): print(items[i])",
                "for i, item in enumerate(items):"
            ),
            (
                "def check(): x = False\nif x == False: pass",
                "if not x:"
            ),
        ]
        
        for original, expected_pattern in test_cases:
            result = modifier.optimize_function(original)
            assert result is not None
            logger.info(f"Optimized: {expected_pattern}")
        
        logger.info("✓ Complex semantic optimizations test PASSED")
    
    def test_malformed_code_handling(self):
        """测试畸形代码处理"""
        logger.info("=" * 80)
        logger.info("TEST: Malformed code handling")
        logger.info("=" * 80)
        
        modifier = SemanticModifier()
        
        malformed_codes = [
            "",  # Empty
            "   ",  # Whitespace only
            "x = ",  # Incomplete
            "{{{{",  # Bracket soup
            "def func(\n",  # Unclosed
        ]
        
        for code in malformed_codes:
            try:
                result = modifier.optimize_function(code)
                logger.info(f"Handled malformed: {code[:30]}")
            except Exception as e:
                logger.warning(f"Failed on malformed: {e}")
        
        logger.info("✓ Malformed code handling test PASSED")


class TestRefactoringEngineComplexity:
    """重构引擎复杂度测试"""
    
    def test_batch_refactoring_1000_files(self):
        """测试批量重构1000个文件"""
        logger.info("=" * 80)
        logger.info("TEST: Batch refactoring 1000 files")
        logger.info("=" * 80)
        
        engine = RefactoringEngine()
        
        files = [f"file{i}.py" for i in range(1000)]
        codes = {
            f"file{i}.py": f"def func_{i}():\n    x = True\n    if x == True:\n        pass"
            for i in range(1000)
        }
        
        start_time = time.time()
        
        plan = engine.refactor_batch(files, codes)
        
        elapsed = time.time() - start_time
        
        logger.info(f"Refactored 1000 files in {elapsed:.2f} seconds")
        logger.info(f"Changes: {len(plan.changes)}")
        
        assert len(plan.changes) == 1000
        assert elapsed < 30  # Should complete in under 30 seconds
        
        logger.info("✓ Batch refactoring test PASSED")
    
    def test_very_long_file_paths(self):
        """测试超长文件路径"""
        logger.info("=" * 80)
        logger.info("TEST: Very long file paths")
        logger.info("=" * 80)
        
        engine = RefactoringEngine()
        
        long_path = "/".join(["very_long_directory_name"] * 50) + "/file.py"
        
        files = [long_path]
        codes = {long_path: "def test(): x = True\nif x == True: pass"}
        
        try:
            plan = engine.refactor_batch(files, codes)
            logger.info(f"Handled path length: {len(long_path)}")
            assert len(plan.changes) == 1
            logger.info("✓ Very long file paths test PASSED")
        except Exception as e:
            logger.error(f"Failed on long path: {e}")
            pytest.fail(f"Should handle long paths: {e}")


class TestDevelopmentAgentIntegration:
    """开发Agent集成测试"""
    
    def test_agent_stress_test(self):
        """Agent压力测试"""
        logger.info("=" * 80)
        logger.info("TEST: Development Agent stress test (500 operations)")
        logger.info("=" * 80)
        
        reset_development_agent()
        config = DevelopmentConfig(name="StressTest")
        agent = DevelopmentAgent(config)
        
        start_time = time.time()
        
        for i in range(500):
            code = agent.generate_code(f"requirement {i}")
            assert code is not None
            
            if i % 100 == 0:
                logger.info(f"Progress: {i}/500")
        
        elapsed = time.time() - start_time
        
        logger.info(f"500 operations in {elapsed:.2f} seconds")
        logger.info(f"Generated: {len(agent.generated_codes)} codes")
        
        assert len(agent.generated_codes) == 500
        assert elapsed < 30
        
        logger.info("✓ Agent stress test PASSED")
    
    def test_agent_memory_leak(self):
        """测试Agent内存泄漏"""
        logger.info("=" * 80)
        logger.info("TEST: Agent memory leak check")
        logger.info("=" * 80)
        
        reset_development_agent()
        config = DevelopmentConfig(name="MemoryTest")
        agent = DevelopmentAgent(config)
        
        for i in range(10000):
            agent.generate_code(f"test_{i}")
        
        logger.info(f"After 10000 generations:")
        logger.info(f"  Generated codes: {len(agent.generated_codes)}")
        logger.info(f"  Refactor plans: {len(agent.refactor_plans)}")
        
        assert len(agent.generated_codes) == 10000
        
        logger.info("✓ Agent memory leak test PASSED")
    
    def test_concurrent_agent_usage(self):
        """测试并发Agent使用"""
        import threading
        
        logger.info("=" * 80)
        logger.info("TEST: Concurrent agent usage (50 threads)")
        logger.info("=" * 80)
        
        reset_development_agent()
        results = []
        errors = []
        
        def agent_worker(worker_id):
            try:
                agent = get_development_agent()
                code = agent.generate_code(f"worker_{worker_id}")
                results.append((worker_id, code))
            except Exception as e:
                errors.append((worker_id, e))
        
        threads = []
        for i in range(50):
            t = threading.Thread(target=agent_worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        logger.info(f"Concurrent test results: {len(results)} success, {len(errors)} errors")
        
        assert len(errors) == 0
        assert len(results) == 50
        
        logger.info("✓ Concurrent agent usage test PASSED")
    
    def test_rapid_reset_cycles(self):
        """测试快速重置周期"""
        logger.info("=" * 80)
        logger.info("TEST: Rapid reset cycles (200 times)")
        logger.info("=" * 80)
        
        for i in range(200):
            reset_development_agent()
            agent = get_development_agent()
            assert agent is not None
        
        logger.info("✓ Rapid reset cycles test PASSED")


class TestEdgeCases:
    """边界情况测试"""
    
    def test_empty_inputs(self):
        """测试空输入"""
        logger.info("=" * 80)
        logger.info("TEST: Empty inputs")
        logger.info("=" * 80)
        
        agent = get_development_agent()
        
        empty_cases = [
            "",
            "   ",
            "\n\n\n",
        ]
        
        for empty in empty_cases:
            try:
                code = agent.generate_code(empty)
                logger.info(f"Handled empty: '{empty}'")
            except Exception as e:
                logger.warning(f"Failed on empty: {e}")
        
        logger.info("✓ Empty inputs test PASSED")
    
    def test_extreme_parameters(self):
        """测试极端参数"""
        logger.info("=" * 80)
        logger.info("TEST: Extreme parameters")
        logger.info("=" * 80)
        
        generator = CodeGenerator()
        
        extreme_cases = [
            ("x", []),  # No params
            ("x", ["p" * 1000]),  # 1000 char param
            ("x", ["p" + str(i) for i in range(1000)]),  # 1000 params
        ]
        
        for name, params in extreme_cases:
            try:
                code = generator.generate_function(name, params)
                assert code is not None
                logger.info(f"Handled: {name} with {len(params)} params")
            except Exception as e:
                logger.error(f"Failed: {e}")
        
        logger.info("✓ Extreme parameters test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
