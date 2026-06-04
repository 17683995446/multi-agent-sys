"""
输入收敛层 (Input Layer)

职责：统一接收任务、类型判定、基础预处理

依赖关系：
- 被依赖：无
- 依赖：scheduler (调度层)

第一性原理：
- 任务可分性：输入任务可拆分为子任务
- 信息最小熵：所有输入信息显式化
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    """任务输入模型"""
    task_id: str = Field(..., description="唯一任务标识")
    task_type: str = Field(..., description="任务类型")
    task_data: Dict[str, Any] = Field(default_factory=dict, description="任务数据")
    priority: int = Field(default=0, description="优先级")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class TaskClassifier:
    """任务分类器"""

    TASK_TYPES = {
        "requirement": "需求开发",
        "refactor": "代码重构",
        "bug_fix": "缺陷修复",
        "review": "代码评审",
        "test": "测试任务"
    }

    def classify(self, task: TaskInput) -> str:
        """分类任务"""
        return self.TASK_TYPES.get(task.task_type, "unknown")

    def validate(self, task: TaskInput) -> bool:
        """验证任务合法性"""
        return bool(task.task_id and task.task_type)


class InputPreprocessor:
    """输入预处理器"""

    def preprocess(self, task: TaskInput) -> TaskInput:
        """预处理任务"""
        if not task.task_id:
            raise ValueError("task_id不能为空")
        return task

    def normalize(self, task: TaskInput) -> Dict[str, Any]:
        """标准化任务数据"""
        return task.model_dump()
