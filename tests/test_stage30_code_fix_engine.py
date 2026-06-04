"""
阶段30验收测试：构建代码自动整改引擎

验收标准：
1. ✓ 整改计划生成（自动执行）
2. ✓ 整改执行（批量）
3. ✓ 整改验证（功能验证）
4. ✓ 整改回滚（一键回滚）
"""

import pytest
import os
import tempfile
from src.architecture.code_fix_engine import (
    FixStatus,
    FixType,
    FixAction,
    FixPlan,
    Backup,
    FixResult,
    CodeRewriter,
    BackupManager,
    SyntaxValidator,
    FixPlanGenerator,
    FixExecutor,
    RollbackManager,
    CodeFixEngine,
    get_code_fix_engine,
    reset_code_fix_engine
)

# 测试代码
TEST_CODE = """def test_function():
    x = 1
    y = 2
    return x + y
"""


class TestFixPlanGenerator:
    """测试整改计划生成"""
    
    def test_add_comment_plan(self):
        """测试添加注释计划"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write(TEST_CODE)
            
            plan = FixPlanGenerator.add_comment_plan(test_file, 2, "Test comment")
            
            assert len(plan.actions) == 1
            assert plan.actions[0].fix_type == FixType.ADD_COMMENT
            assert plan.auto_execute is True
    
    def test_custom_fix_plan(self):
        """测试自定义整改计划"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write(TEST_CODE)
            
            plan = FixPlanGenerator.custom_fix_plan(
                test_file,
                2,
                2,
                "    x = 1\n",
                "    y = 1\n    x = 1\n",
                "Change variable name"
            )
            
            assert len(plan.actions) == 1
            assert plan.actions[0].fix_type == FixType.CUSTOM


class TestSyntaxValidator:
    """测试语法验证"""
    
    def test_validate_valid_content(self):
        """测试验证有效内容"""
        content = "x = 1\ny = 2\nprint(x)\n"
        valid, error = SyntaxValidator.validate_content(content)
        assert valid is True
        assert error is None
    
    def test_validate_invalid_content(self):
        """测试验证无效内容"""
        content = "x = 1\ny = 2\nprint(x)\ninvalid syntax!!!"
        valid, error = SyntaxValidator.validate_content(content)
        assert valid is False
        assert error is not None
    
    def test_validate_file(self):
        """测试验证文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write(TEST_CODE)
            
            valid, error = SyntaxValidator.validate_file(test_file)
            assert valid is True


class TestBackupManager:
    """测试备份管理器"""
    
    def test_create_backup(self):
        """测试创建备份"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write(TEST_CODE)
            
            backup_dir = os.path.join(tmpdir, "backups")
            manager = BackupManager(backup_dir)
            
            backup = manager.create_backup(test_file)
            
            assert os.path.exists(backup.backup_path)
            assert len(manager.backups) == 1
    
    def test_restore_backup(self):
        """测试恢复备份"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            original_content = "original"
            with open(test_file, 'w') as f:
                f.write(original_content)
            
            backup_dir = os.path.join(tmpdir, "backups")
            manager = BackupManager(backup_dir)
            
            backup = manager.create_backup(test_file)
            
            # 修改文件
            with open(test_file, 'w') as f:
                f.write("modified")
            
            # 恢复备份
            assert manager.restore_backup(backup) is True
            
            with open(test_file, 'r') as f:
                assert f.read() == original_content


class TestFixExecutor:
    """测试整改执行器"""
    
    def test_execute_plan(self):
        """测试执行计划"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            with open(test_file, 'w') as f:
                f.write(TEST_CODE)
            
            backup_dir = os.path.join(tmpdir, "backups")
            manager = BackupManager(backup_dir)
            executor = FixExecutor(manager)
            
            action = FixAction(
                fix_type=FixType.CUSTOM,
                file_path=test_file,
                line_start=2,
                line_end=2,
                original_content="    x = 1\n",
                modified_content="    x = 100\n",
                description="Change x value"
            )
            
            plan = FixPlan(name="Test Plan", actions=[action])
            result = executor.execute_plan(plan)
            
            assert result.success is True
            assert result.executed_actions == 1
            assert len(result.backups) >= 1


class TestRollbackManager:
    """测试回滚管理器"""
    
    def test_rollback_plan(self):
        """测试回滚计划"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            original_content = TEST_CODE
            with open(test_file, 'w') as f:
                f.write(original_content)
            
            backup_dir = os.path.join(tmpdir, "backups")
            backup_manager = BackupManager(backup_dir)
            executor = FixExecutor(backup_manager)
            rollback_manager = RollbackManager(backup_manager)
            
            action = FixAction(
                fix_type=FixType.CUSTOM,
                file_path=test_file,
                line_start=2,
                line_end=2,
                original_content="    x = 1\n",
                modified_content="    x = 999\n",
                description="Change x value"
            )
            
            plan = FixPlan(name="Test Plan", actions=[action])
            result = executor.execute_plan(plan)
            
            # 回滚
            success, count = rollback_manager.rollback_plan(plan, result)
            assert count >= 1
            
            with open(test_file, 'r') as f:
                assert f.read() == original_content


class TestCodeFixEngine:
    """测试代码整改引擎"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.py")
            original_content = TEST_CODE
            with open(test_file, 'w') as f:
                f.write(original_content)
            
            engine = CodeFixEngine(tmpdir)
            
            # 创建计划
            action = FixAction(
                fix_type=FixType.CUSTOM,
                file_path=test_file,
                line_start=2,
                line_end=2,
                original_content="    x = 1\n",
                modified_content="    value = 42\n    x = value\n",
                description="Refactor variable"
            )
            
            plan = engine.create_fix_plan("Test Fix Plan", [action])
            
            # 执行
            result = engine.execute_fix(plan)
            assert result.success is True
            assert result.executed_actions == 1
            
            # 验证语法
            assert result.syntax_valid is True
            
            # 回滚
            success, count = engine.rollback_fix(plan, result)
            assert count >= 1
            
            with open(test_file, 'r') as f:
                assert f.read() == original_content


class TestGlobalEngine:
    """测试全局引擎"""
    
    def test_get_global_engine(self):
        """测试获取全局引擎"""
        reset_code_fix_engine()
        
        engine1 = get_code_fix_engine()
        engine2 = get_code_fix_engine()
        
        assert engine1 is engine2
    
    def test_reset_global_engine(self):
        """测试重置全局引擎"""
        engine1 = get_code_fix_engine()
        reset_code_fix_engine()
        engine2 = get_code_fix_engine()
        
        assert engine1 is not engine2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
