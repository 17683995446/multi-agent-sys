"""
代码自动整改引擎模块

职责：生成整改计划、执行整改、验证整改、回滚操作

基于第一性原理：简单、单一、可追溯、可组合
"""

import ast
import os
import shutil
import uuid
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class FixStatus(str, Enum):
    """整改状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class FixType(str, Enum):
    """整改类型"""
    ADD_COMMENT = "add_comment"
    FORMAT_CODE = "format_code"
    REFACTOR_METHOD = "refactor_method"
    EXTRACT_CLASS = "extract_class"
    REMOVE_DEAD_CODE = "remove_dead_code"
    CUSTOM = "custom"


@dataclass
class FixAction:
    """整改动作"""
    fix_type: FixType
    file_path: str
    line_start: int
    line_end: int
    original_content: str
    modified_content: str
    description: str = ""
    status: FixStatus = FixStatus.PENDING
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None


@dataclass
class FixPlan:
    """整改计划"""
    name: str = "Code Fix Plan"
    description: str = ""
    actions: List[FixAction] = field(default_factory=list)
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    auto_execute: bool = True


@dataclass
class Backup:
    """备份记录"""
    original_path: str
    backup_path: str
    backup_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FixResult:
    """整改结果"""
    plan_id: str
    success: bool
    message: str = ""
    executed_actions: int = 0
    failed_actions: int = 0
    syntax_valid: bool = True
    errors: List[str] = field(default_factory=list)
    backups: List[Backup] = field(default_factory=list)


class CodeRewriter:
    """代码重写器"""
    
    @staticmethod
    def replace_lines(file_path: str, line_start: int, line_end: int, new_content: str) -> str:
        """替换文件中的行数"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if line_start < 1 or line_end > len(lines):
            return ''.join(lines)
        
        new_lines = new_content.splitlines(True)
        result = lines[:line_start - 1] + new_lines + lines[line_end:]
        return ''.join(result)
    
    @staticmethod
    def insert_comment(file_path: str, line: int, comment: str) -> str:
        """插入注释"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if 1 <= line <= len(lines) + 1:
            lines.insert(line - 1, f"# {comment}\n")
        
        return ''.join(lines)


class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: Optional[str] = None):
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = Path.cwd() / ".code_fix_backups"
        
        self.backup_dir.mkdir(exist_ok=True)
        self.backups: List[Backup] = []
    
    def create_backup(self, file_path: str) -> Backup:
        """创建文件备份"""
        path = Path(file_path)
        backup_name = f"{path.stem}_{uuid.uuid4().hex[:8]}{path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        
        backup = Backup(
            original_path=str(path.absolute()),
            backup_path=str(backup_path.absolute())
        )
        
        self.backups.append(backup)
        return backup
    
    def restore_backup(self, backup: Backup) -> bool:
        """恢复备份"""
        try:
            if Path(backup.backup_path).exists():
                shutil.copy2(backup.backup_path, backup.original_path)
                return True
            return False
        except Exception:
            return False
    
    def clear_backups(self) -> None:
        """清除所有备份"""
        self.backups = []
        if self.backup_dir.exists():
            for file in self.backup_dir.iterdir():
                if file.is_file():
                    try:
                        file.unlink()
                    except Exception:
                        pass


class SyntaxValidator:
    """语法验证器"""
    
    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """验证文件语法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ast.parse(content)
            return (True, None)
        except SyntaxError as e:
            return (False, str(e))
        except Exception as e:
            return (False, str(e))
    
    @staticmethod
    def validate_content(content: str) -> Tuple[bool, Optional[str]]:
        """验证内容语法"""
        try:
            ast.parse(content)
            return (True, None)
        except SyntaxError as e:
            return (False, str(e))
        except Exception as e:
            return (False, str(e))


class FixPlanGenerator:
    """整改计划生成器"""
    
    @staticmethod
    def add_comment_plan(file_path: str, line: int, comment: str) -> FixPlan:
        """添加注释的整改计划"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_line = lines[line - 1] if 1 <= line <= len(lines) else ""
        
        action = FixAction(
            fix_type=FixType.ADD_COMMENT,
            file_path=file_path,
            line_start=line,
            line_end=line,
            original_content=original_line,
            modified_content=f"# {comment}\n{original_line}",
            description=f"Add comment at line {line}"
        )
        
        return FixPlan(name="Add Comment Plan", actions=[action])
    
    @staticmethod
    def custom_fix_plan(file_path: str, line_start: int, line_end: int, 
                       original: str, modified: str, description: str = "") -> FixPlan:
        """自定义整改计划"""
        action = FixAction(
            fix_type=FixType.CUSTOM,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            original_content=original,
            modified_content=modified,
            description=description or "Custom fix"
        )
        
        return FixPlan(name="Custom Fix Plan", actions=[action])


class FixExecutor:
    """整改执行器"""
    
    def __init__(self, backup_manager: Optional[BackupManager] = None):
        self.backup_manager = backup_manager or BackupManager()
        self.results: List[FixResult] = []
    
    def execute_plan(self, plan: FixPlan) -> FixResult:
        """执行整改计划"""
        result = FixResult(
            plan_id=plan.plan_id,
            success=True
        )
        
        try:
            for action in plan.actions:
                self._execute_action(action, result)
        except Exception as e:
            result.success = False
            result.message = str(e)
            result.errors.append(str(e))
        
        result.executed_actions = sum(
            1 for a in plan.actions if a.status == FixStatus.COMPLETED
        )
        result.failed_actions = sum(
            1 for a in plan.actions if a.status == FixStatus.FAILED
        )
        
        # 验证语法
        self._validate_syntax(plan, result)
        
        self.results.append(result)
        return result
    
    def _execute_action(self, action: FixAction, result: FixResult) -> None:
        """执行单个整改动作"""
        try:
            action.status = FixStatus.IN_PROGRESS
            
            # 创建备份
            backup = self.backup_manager.create_backup(action.file_path)
            result.backups.append(backup)
            
            # 应用修改
            if action.fix_type == FixType.CUSTOM or action.fix_type == FixType.ADD_COMMENT:
                new_content = CodeRewriter.replace_lines(
                    action.file_path,
                    action.line_start,
                    action.line_end,
                    action.modified_content
                )
                
                with open(action.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            action.status = FixStatus.COMPLETED
            action.executed_at = datetime.now()
            
        except Exception as e:
            action.status = FixStatus.FAILED
            result.errors.append(f"Failed to execute action {action.action_id}: {str(e)}")
            result.success = False
    
    def _validate_syntax(self, plan: FixPlan, result: FixResult) -> None:
        """验证语法"""
        files_checked = set()
        all_valid = True
        
        for action in plan.actions:
            if action.file_path not in files_checked:
                valid, _ = SyntaxValidator.validate_file(action.file_path)
                if not valid:
                    all_valid = False
                files_checked.add(action.file_path)
        
        result.syntax_valid = all_valid


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
    
    def rollback_plan(self, plan: FixPlan, result: FixResult) -> Tuple[bool, int]:
        """回滚整个计划"""
        success_count = 0
        all_success = True
        
        for backup in reversed(result.backups):
            if self.backup_manager.restore_backup(backup):
                success_count += 1
            else:
                all_success = False
        
        # 更新状态
        for action in plan.actions:
            if action.status == FixStatus.COMPLETED:
                action.status = FixStatus.ROLLED_BACK
        
        return (all_success, success_count)
    
    def rollback_single(self, action: FixAction, backup: Backup) -> bool:
        """回滚单个动作"""
        if self.backup_manager.restore_backup(backup):
            action.status = FixStatus.ROLLED_BACK
            return True
        return False


class CodeFixEngine:
    """代码整改引擎"""
    
    def __init__(self, backup_dir: Optional[str] = None):
        self.backup_manager = BackupManager(backup_dir)
        self.executor = FixExecutor(self.backup_manager)
        self.rollback_manager = RollbackManager(self.backup_manager)
        self.plans: List[FixPlan] = []
    
    def create_fix_plan(self, name: str, actions: List[FixAction], 
                       auto_execute: bool = True) -> FixPlan:
        """创建整改计划"""
        plan = FixPlan(
            name=name,
            actions=actions,
            auto_execute=auto_execute
        )
        self.plans.append(plan)
        return plan
    
    def execute_fix(self, plan: FixPlan) -> FixResult:
        """执行整改"""
        result = self.executor.execute_plan(plan)
        return result
    
    def rollback_fix(self, plan: FixPlan, result: FixResult) -> Tuple[bool, int]:
        """回滚整改"""
        return self.rollback_manager.rollback_plan(plan, result)
    
    def clear_all(self) -> None:
        """清除所有内容"""
        self.backup_manager.clear_backups()
        self.executor.results = []
        self.plans = []


# 全局引擎
_global_engine: Optional[CodeFixEngine] = None


def get_code_fix_engine(backup_dir: Optional[str] = None) -> CodeFixEngine:
    """获取全局整改引擎"""
    global _global_engine
    if _global_engine is None:
        _global_engine = CodeFixEngine(backup_dir)
    return _global_engine


def reset_code_fix_engine() -> None:
    """重置整改引擎"""
    global _global_engine
    if _global_engine:
        _global_engine.clear_all()
    _global_engine = None
