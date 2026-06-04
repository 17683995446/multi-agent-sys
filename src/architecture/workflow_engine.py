"""
工作流引擎
职责：工作流定义、步骤执行、上下文管理、暂停/恢复
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """工作流状态"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    handler_name: str = ""
    next_steps: List[str] = field(default_factory=list)
    condition: Optional[str] = None
    status: StepStatus = StepStatus.PENDING


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    initial_step: str = ""


@dataclass
class WorkflowContext:
    """工作流上下文"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_step: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.CREATED


class WorkflowEngine:
    """工作流引擎"""

    def __init__(self):
        self.definitions: Dict[str, WorkflowDefinition] = {}
        self.contexts: Dict[str, WorkflowContext] = {}
        self.handlers: Dict[str, Callable] = {}
        logger.info("WorkflowEngine初始化完成")

    def register_workflow(self, definition: WorkflowDefinition) -> bool:
        """注册工作流定义"""
        self.definitions[definition.workflow_id] = definition
        logger.info(f"注册工作流: workflow_id={definition.workflow_id}, name={definition.name}")
        return True

    def start_workflow(self, workflow_id: str, initial_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """启动工作流"""
        if workflow_id not in self.definitions:
            logger.warning(f"启动工作流失败: 定义不存在, workflow_id={workflow_id}")
            return None

        definition = self.definitions[workflow_id]
        context = WorkflowContext(
            workflow_id=str(uuid.uuid4()),
            current_step=definition.initial_step,
            data=initial_data or {},
            status=WorkflowStatus.RUNNING,
        )

        # 设置初始步骤为ACTIVE
        for step in definition.steps:
            if step.step_id == definition.initial_step:
                step.status = StepStatus.ACTIVE
                break

        self.contexts[context.workflow_id] = context
        logger.info(f"启动工作流: definition_id={workflow_id}, context_id={context.workflow_id}")
        return context.workflow_id

    def execute_step(self, context_id: str) -> Dict[str, Any]:
        """执行当前步骤"""
        if context_id not in self.contexts:
            logger.warning(f"执行步骤失败: 上下文不存在, context_id={context_id}")
            return {"success": False, "error": "上下文不存在"}

        context = self.contexts[context_id]
        if context.status != WorkflowStatus.RUNNING:
            logger.warning(f"执行步骤失败: 工作流未运行, status={context.status.value}")
            return {"success": False, "error": "工作流未运行"}

        # 查找工作流定义
        definition = None
        for defn in self.definitions.values():
            if context_id in [c_id for c_id in self.contexts]:
                definition = self.definitions.get(next(
                    (did for did, d in self.definitions.items()
                     if any(s.step_id == context.current_step for s in d.steps)), ""))
                break

        if definition is None:
            # 通过当前步骤查找定义
            for did, defn in self.definitions.items():
                if any(s.step_id == context.current_step for s in defn.steps):
                    definition = defn
                    break

        if definition is None:
            logger.error(f"执行步骤失败: 找不到工作流定义, context_id={context_id}")
            return {"success": False, "error": "找不到工作流定义"}

        # 查找当前步骤
        current_step = None
        for step in definition.steps:
            if step.step_id == context.current_step:
                current_step = step
                break

        if current_step is None:
            logger.error(f"执行步骤失败: 当前步骤不存在, step_id={context.current_step}")
            return {"success": False, "error": "当前步骤不存在"}

        logger.info(f"执行步骤: context_id={context_id}, step={current_step.name}")

        # 执行处理器
        try:
            handler = self.handlers.get(current_step.handler_name)
            if handler:
                result = handler(context.data)
                context.data.update(result if isinstance(result, dict) else {"result": result})
        except Exception as e:
            current_step.status = StepStatus.ERROR
            context.status = WorkflowStatus.FAILED
            logger.error(f"步骤执行异常: step={current_step.name}, error={e}")
            return {"success": False, "error": str(e)}

        # 记录历史
        context.history.append({
            "step_id": current_step.step_id,
            "step_name": current_step.name,
            "status": "completed",
        })

        current_step.status = StepStatus.DONE

        # 确定下一步
        if current_step.next_steps:
            next_step_id = current_step.next_steps[0]
            context.current_step = next_step_id
            for step in definition.steps:
                if step.step_id == next_step_id:
                    step.status = StepStatus.ACTIVE
                    break
            logger.info(f"步骤完成，进入下一步: next_step={next_step_id}")
        else:
            context.status = WorkflowStatus.COMPLETED
            logger.info(f"工作流完成: context_id={context_id}")

        return {"success": True, "current_step": context.current_step, "status": context.status.value}

    def get_context(self, context_id: str) -> Optional[WorkflowContext]:
        """获取工作流上下文"""
        context = self.contexts.get(context_id)
        if context:
            logger.debug(f"获取上下文: context_id={context_id}, status={context.status.value}")
        else:
            logger.warning(f"获取上下文失败: 不存在, context_id={context_id}")
        return context

    def pause_workflow(self, context_id: str) -> bool:
        """暂停工作流"""
        if context_id not in self.contexts:
            logger.warning(f"暂停工作流失败: 上下文不存在, context_id={context_id}")
            return False
        context = self.contexts[context_id]
        if context.status != WorkflowStatus.RUNNING:
            logger.warning(f"暂停工作流失败: 状态不允许, status={context.status.value}")
            return False
        context.status = WorkflowStatus.PAUSED
        logger.info(f"暂停工作流: context_id={context_id}")
        return True

    def resume_workflow(self, context_id: str) -> bool:
        """恢复工作流"""
        if context_id not in self.contexts:
            logger.warning(f"恢复工作流失败: 上下文不存在, context_id={context_id}")
            return False
        context = self.contexts[context_id]
        if context.status != WorkflowStatus.PAUSED:
            logger.warning(f"恢复工作流失败: 状态不允许, status={context.status.value}")
            return False
        context.status = WorkflowStatus.RUNNING
        logger.info(f"恢复工作流: context_id={context_id}")
        return True
