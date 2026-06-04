"""
任务分发→开发执行链路
职责：任务分发、Agent匹配、依赖检查、任务执行、状态跟踪
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """任务类型"""
    DESIGN = "design"
    CODING = "coding"
    TESTING = "testing"
    REVIEW = "review"
    DOCUMENTATION = "documentation"


class TaskStatus(str, Enum):
    """任务状态"""
    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DevelopmentTask:
    """开发任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.CODING
    description: str = ""
    assignee: str = ""
    status: TaskStatus = TaskStatus.CREATED
    dependencies: List[str] = field(default_factory=list)
    result: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"DevelopmentTask created: id={self.task_id[:8]}, type={self.task_type.value}")


class TaskDistributor:
    """任务分发器"""

    def __init__(self):
        self._agent_registry: Dict[str, List[str]] = {
            "design_agent": ["design"],
            "coding_agent": ["coding"],
            "testing_agent": ["testing"],
            "review_agent": ["review"],
            "doc_agent": ["documentation"],
        }
        self._assignments: Dict[str, str] = {}  # task_id -> agent
        self._tasks: Dict[str, DevelopmentTask] = {}
        logger.info("TaskDistributor initialized")

    def distribute(self, task: DevelopmentTask) -> DevelopmentTask:
        """分发任务到合适的Agent"""
        # 输入验证
        if not task or not task.task_id:
            logger.warning("distribute: invalid task")
            raise ValueError("无效的任务对象")

        # 业务逻辑
        try:
            # 检查依赖
            if not self._check_dependencies(task):
                logger.warning(f"distribute: dependencies not met for task={task.task_id[:8]}")
                task.metadata["dependency_status"] = "unmet"
                return task

            # 匹配Agent
            agent = self._match_agent(task)
            if agent:
                task.assignee = agent
                task.status = TaskStatus.ASSIGNED
                self._assignments[task.task_id] = agent
                logger.info(f"TaskDistributor: assigned task={task.task_id[:8]} to agent={agent}")
            else:
                logger.warning(f"TaskDistributor: no agent available for task type={task.task_type.value}")
                task.metadata["assignment_status"] = "no_agent"

            self._tasks[task.task_id] = task
        except Exception as e:
            # 异常处理
            logger.error(f"TaskDistributor: distribute failed: {e}")
            task.status = TaskStatus.FAILED
            task.metadata["error"] = str(e)

        # 返回结果
        return task

    def _match_agent(self, task: DevelopmentTask) -> Optional[str]:
        """匹配适合的Agent"""
        logger.debug(f"_match_agent: task_type={task.task_type.value}")
        task_type_value = task.task_type.value

        for agent, capabilities in self._agent_registry.items():
            if task_type_value in capabilities:
                logger.debug(f"_match_agent: matched agent={agent}")
                return agent

        logger.debug("_match_agent: no matching agent found")
        return None

    def _check_dependencies(self, task: DevelopmentTask) -> bool:
        """检查任务依赖是否满足"""
        logger.debug(f"_check_dependencies: task={task.task_id[:8]}, deps={len(task.dependencies)}")

        if not task.dependencies:
            return True

        for dep_id in task.dependencies:
            dep_task = self._tasks.get(dep_id)
            if dep_task is None or dep_task.status != TaskStatus.COMPLETED:
                logger.debug(f"_check_dependencies: dependency {dep_id[:8]} not met")
                return False

        return True


class TaskExecutor:
    """任务执行器"""

    def __init__(self):
        self._execution_log: Dict[str, Dict[str, Any]] = {}
        logger.info("TaskExecutor initialized")

    def execute(self, task: DevelopmentTask) -> DevelopmentTask:
        """执行任务"""
        # 输入验证
        if not task or not task.task_id:
            logger.warning("execute: invalid task")
            raise ValueError("无效的任务对象")

        # 业务逻辑
        start_time = time.time()
        try:
            task.status = TaskStatus.IN_PROGRESS
            logger.info(f"TaskExecutor: executing task={task.task_id[:8]}, type={task.task_type.value}")

            # 根据任务类型执行
            if task.task_type == TaskType.DESIGN:
                task.result = self._execute_design(task)
            elif task.task_type == TaskType.CODING:
                task.result = self._execute_coding(task)
            elif task.task_type == TaskType.TESTING:
                task.result = self._execute_testing(task)
            elif task.task_type == TaskType.REVIEW:
                task.result = self._execute_review(task)
            else:
                task.result = self._execute_documentation(task)

            task.status = TaskStatus.COMPLETED
            execution_time = time.time() - start_time

            self._execution_log[task.task_id] = {
                "execution_time": execution_time,
                "status": "success",
                "task_type": task.task_type.value,
            }
            logger.info(f"TaskExecutor: completed task={task.task_id[:8]}, time={execution_time:.4f}s")
        except Exception as e:
            # 异常处理
            task.status = TaskStatus.FAILED
            task.result = {"error": str(e)}
            execution_time = time.time() - start_time
            self._execution_log[task.task_id] = {
                "execution_time": execution_time,
                "status": "failed",
                "error": str(e),
            }
            logger.error(f"TaskExecutor: execute failed: {e}")

        # 返回结果
        return task

    def _execute_design(self, task: DevelopmentTask) -> Dict[str, Any]:
        """执行设计任务"""
        logger.debug(f"_execute_design: task={task.task_id[:8]}")
        return {
            "design_doc": f"设计方案: {task.description[:50]}",
            "components": ["模块A", "模块B"],
            "interfaces": ["API-1", "API-2"],
        }

    def _execute_coding(self, task: DevelopmentTask) -> Dict[str, Any]:
        """执行编码任务"""
        logger.debug(f"_execute_coding: task={task.task_id[:8]}")
        return {
            "code_files": [f"src/{task.description[:20]}.py"],
            "lines_of_code": 150,
            "test_coverage": 0.85,
        }

    def _execute_testing(self, task: DevelopmentTask) -> Dict[str, Any]:
        """执行测试任务"""
        logger.debug(f"_execute_testing: task={task.task_id[:8]}")
        return {
            "test_cases": 10,
            "passed": 9,
            "failed": 1,
            "coverage": 0.9,
        }

    def _execute_review(self, task: DevelopmentTask) -> Dict[str, Any]:
        """执行评审任务"""
        logger.debug(f"_execute_review: task={task.task_id[:8]}")
        return {
            "review_status": "approved_with_comments",
            "issues_found": 2,
            "suggestions": ["优化命名", "增加注释"],
        }

    def _execute_documentation(self, task: DevelopmentTask) -> Dict[str, Any]:
        """执行文档任务"""
        logger.debug(f"_execute_documentation: task={task.task_id[:8]}")
        return {
            "doc_files": [f"docs/{task.description[:20]}.md"],
            "sections": ["概述", "接口说明", "使用示例"],
        }


class DevelopmentPipeline:
    """任务分发→开发执行链路"""

    def __init__(self):
        self.distributor = TaskDistributor()
        self.executor = TaskExecutor()
        self._tasks: Dict[str, DevelopmentTask] = {}
        logger.info("DevelopmentPipeline initialized")

    def process_task(self, description: str, task_type: TaskType = TaskType.CODING,
                     dependencies: Optional[List[str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> DevelopmentTask:
        """处理任务：创建→分发→执行"""
        # 输入验证
        if not description or not description.strip():
            logger.warning("process_task: description is empty")
            raise ValueError("任务描述不能为空")

        # 业务逻辑
        try:
            # 1. 创建任务
            task = DevelopmentTask(
                task_type=task_type,
                description=description.strip(),
                dependencies=dependencies or [],
                metadata=metadata or {},
            )
            self._tasks[task.task_id] = task
            logger.info(f"DevelopmentPipeline: created task={task.task_id[:8]}")

            # 2. 分发任务
            task = self.distributor.distribute(task)
            logger.info(f"DevelopmentPipeline: distributed task={task.task_id[:8]}, assignee={task.assignee}")

            # 3. 执行任务（仅当已分配时）
            if task.status == TaskStatus.ASSIGNED:
                task = self.executor.execute(task)
                logger.info(f"DevelopmentPipeline: executed task={task.task_id[:8]}, status={task.status.value}")
            elif task.status == TaskStatus.CREATED:
                # 依赖未满足，仍然尝试执行
                task = self.executor.execute(task)
                logger.info(f"DevelopmentPipeline: executed task (no assignment)={task.task_id[:8]}")

            # 更新存储
            self._tasks[task.task_id] = task
        except Exception as e:
            # 异常处理
            logger.error(f"DevelopmentPipeline: process_task failed: {e}")
            task.status = TaskStatus.FAILED
            task.result = {"error": str(e)}

        # 返回结果
        return task

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 输入验证
        if not task_id:
            logger.warning("get_task_status: task_id is empty")
            return None

        # 业务逻辑
        task = self._tasks.get(task_id)
        if task is None:
            logger.debug(f"get_task_status: task_id={task_id[:8]} not found")
            return None

        status_info = {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "description": task.description,
            "assignee": task.assignee,
            "status": task.status.value,
            "has_result": bool(task.result),
            "dependencies_met": task.metadata.get("dependency_status") != "unmet",
        }
        logger.debug(f"get_task_status: task_id={task_id[:8]}, status={task.status.value}")

        # 返回结果
        return status_info

    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取链路整体状态"""
        # 业务逻辑
        try:
            tasks = list(self._tasks.values())
            status_counts = {}
            for status in TaskStatus:
                status_counts[status.value] = sum(1 for t in tasks if t.status == status)

            type_counts = {}
            for ttype in TaskType:
                type_counts[ttype.value] = sum(1 for t in tasks if t.task_type == ttype)

            result = {
                "total_tasks": len(tasks),
                "status_counts": status_counts,
                "type_counts": type_counts,
            }
            logger.debug(f"get_pipeline_status: total={len(tasks)}")
        except Exception as e:
            # 异常处理
            logger.error(f"get_pipeline_status: failed: {e}")
            return {"total_tasks": 0, "status_counts": {}, "type_counts": {}}

        # 返回结果
        return result
