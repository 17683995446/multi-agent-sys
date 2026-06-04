"""
任务编排引擎
职责：任务编排计划管理、依赖解析、拓扑排序、执行顺序调度
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OrchestrationMode(str, Enum):
    """编排模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    HYBRID = "hybrid"


@dataclass
class TaskDependency:
    """任务依赖关系"""
    task_id: str = ""
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[str] = None


@dataclass
class OrchestrationPlan:
    """编排计划"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tasks: List[str] = field(default_factory=list)
    dependencies: List[TaskDependency] = field(default_factory=list)
    mode: OrchestrationMode = OrchestrationMode.SEQUENTIAL


class TaskOrchestrator:
    """任务编排器"""

    def __init__(self):
        self.plans: Dict[str, OrchestrationPlan] = {}
        self.completed_tasks: Dict[str, set] = {}
        logger.info("TaskOrchestrator初始化完成")

    def create_plan(self, name: str = "", mode: OrchestrationMode = OrchestrationMode.SEQUENTIAL) -> OrchestrationPlan:
        """创建编排计划"""
        plan = OrchestrationPlan(name=name, mode=mode)
        self.plans[plan.plan_id] = plan
        self.completed_tasks[plan.plan_id] = set()
        logger.info(f"创建编排计划: name={name}, plan_id={plan.plan_id}, mode={mode.value}")
        return plan

    def add_task(self, plan_id: str, task_id: str) -> bool:
        """向计划中添加任务"""
        if plan_id not in self.plans:
            logger.warning(f"添加任务失败: 计划不存在, plan_id={plan_id}")
            return False
        plan = self.plans[plan_id]
        if task_id not in plan.tasks:
            plan.tasks.append(task_id)
            logger.info(f"添加任务: plan_id={plan_id}, task_id={task_id}")
        else:
            logger.debug(f"任务已存在: plan_id={plan_id}, task_id={task_id}")
        return True

    def add_dependency(self, plan_id: str, task_id: str, depends_on: List[str],
                       condition: Optional[str] = None) -> bool:
        """添加任务依赖关系"""
        if plan_id not in self.plans:
            logger.warning(f"添加依赖失败: 计划不存在, plan_id={plan_id}")
            return False
        plan = self.plans[plan_id]
        dep = TaskDependency(task_id=task_id, depends_on=depends_on, condition=condition)
        plan.dependencies.append(dep)
        logger.info(f"添加依赖: plan_id={plan_id}, task_id={task_id}, depends_on={depends_on}")
        return True

    def resolve_execution_order(self, plan_id: str) -> Optional[List[str]]:
        """解析执行顺序（拓扑排序）"""
        if plan_id not in self.plans:
            logger.warning(f"解析执行顺序失败: 计划不存在, plan_id={plan_id}")
            return None
        plan = self.plans[plan_id]
        in_degree: Dict[str, int] = {task: 0 for task in plan.tasks}
        graph: Dict[str, List[str]] = {task: [] for task in plan.tasks}

        for dep in plan.dependencies:
            if dep.task_id in graph:
                for parent in dep.depends_on:
                    if parent in graph:
                        graph[parent].append(dep.task_id)
                        in_degree[dep.task_id] = in_degree.get(dep.task_id, 0) + 1

        queue = [task for task in plan.tasks if in_degree.get(task, 0) == 0]
        result = []

        while queue:
            queue.sort(key=lambda t: in_degree.get(t, 0))
            node = queue.pop(0)
            result.append(node)
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(plan.tasks):
            logger.warning(f"检测到循环依赖, plan_id={plan_id}")
            return None

        logger.info(f"解析执行顺序完成: plan_id={plan_id}, order={result}")
        return result

    def get_ready_tasks(self, plan_id: str) -> List[str]:
        """获取就绪任务（依赖已满足的任务）"""
        if plan_id not in self.plans:
            logger.warning(f"获取就绪任务失败: 计划不存在, plan_id={plan_id}")
            return []
        plan = self.plans[plan_id]
        completed = self.completed_tasks.get(plan_id, set())
        ready = []
        for task_id in plan.tasks:
            if task_id in completed:
                continue
            dep = next((d for d in plan.dependencies if d.task_id == task_id), None)
            if dep is None:
                ready.append(task_id)
            elif all(parent in completed for parent in dep.depends_on):
                ready.append(task_id)
        logger.debug(f"获取就绪任务: plan_id={plan_id}, ready={ready}")
        return ready

    def mark_completed(self, plan_id: str, task_id: str) -> bool:
        """标记任务完成"""
        if plan_id not in self.plans:
            logger.warning(f"标记完成失败: 计划不存在, plan_id={plan_id}")
            return False
        if plan_id not in self.completed_tasks:
            self.completed_tasks[plan_id] = set()
        self.completed_tasks[plan_id].add(task_id)
        logger.info(f"标记任务完成: plan_id={plan_id}, task_id={task_id}")
        return True


class OrchestrationService:
    """编排服务"""

    def __init__(self):
        self.orchestrator = TaskOrchestrator()
        logger.info("OrchestrationService初始化完成")

    def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """执行编排计划"""
        logger.info(f"开始执行编排计划: plan_id={plan_id}")
        order = self.orchestrator.resolve_execution_order(plan_id)
        if order is None:
            logger.error(f"执行编排计划失败: 无法解析执行顺序, plan_id={plan_id}")
            return {"success": False, "error": "无法解析执行顺序，可能存在循环依赖"}

        results = {}
        for task_id in order:
            results[task_id] = "completed"
            self.orchestrator.mark_completed(plan_id, task_id)
            logger.debug(f"执行任务: plan_id={plan_id}, task_id={task_id}")

        logger.info(f"编排计划执行完成: plan_id={plan_id}, tasks={len(order)}")
        return {"success": True, "execution_order": order, "results": results}

    def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """获取计划状态"""
        if plan_id not in self.orchestrator.plans:
            logger.warning(f"获取计划状态失败: 计划不存在, plan_id={plan_id}")
            return {"exists": False}
        plan = self.orchestrator.plans[plan_id]
        completed = self.orchestrator.completed_tasks.get(plan_id, set())
        total = len(plan.tasks)
        done = len(completed & set(plan.tasks))
        status = {
            "exists": True,
            "plan_id": plan_id,
            "name": plan.name,
            "mode": plan.mode.value,
            "total_tasks": total,
            "completed_tasks": done,
            "progress": done / total if total > 0 else 0.0,
        }
        logger.debug(f"获取计划状态: plan_id={plan_id}, progress={status['progress']:.2f}")
        return status
