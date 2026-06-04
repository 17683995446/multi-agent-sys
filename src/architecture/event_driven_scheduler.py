"""
事件驱动调度
职责：事件发布/订阅、事件处理、任务调度、代理状态管理
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型"""
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_AVAILABLE = "agent_available"
    AGENT_BUSY = "agent_busy"
    DEADLINE_APPROACHING = "deadline_approaching"


@dataclass
class Event:
    """事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.TASK_CREATED
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: int = 0


@dataclass
class EventHandler:
    """事件处理器"""
    handler_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.TASK_CREATED
    callback: Optional[Callable] = None
    priority: int = 0


class EventBus:
    """事件总线"""

    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}
        logger.info("EventBus初始化完成")

    def subscribe(self, event_type: EventType, callback: Callable, priority: int = 0) -> str:
        """订阅事件"""
        handler = EventHandler(event_type=event_type, callback=callback, priority=priority)
        if event_type.value not in self.handlers:
            self.handlers[event_type.value] = []
        self.handlers[event_type.value].append(handler)
        # 按优先级排序
        self.handlers[event_type.value].sort(key=lambda h: h.priority, reverse=True)
        logger.info(f"订阅事件: event_type={event_type.value}, handler_id={handler.handler_id}")
        return handler.handler_id

    def unsubscribe(self, handler_id: str) -> bool:
        """取消订阅"""
        for event_type, handler_list in self.handlers.items():
            for i, handler in enumerate(handler_list):
                if handler.handler_id == handler_id:
                    handler_list.pop(i)
                    logger.info(f"取消订阅: handler_id={handler_id}, event_type={event_type}")
                    return True
        logger.warning(f"取消订阅失败: handler_id={handler_id}不存在")
        return False

    def publish(self, event: Event) -> int:
        """发布事件"""
        handler_list = self.handlers.get(event.event_type.value, [])
        count = 0
        for handler in handler_list:
            try:
                self.process_event(event, handler)
                count += 1
            except Exception as e:
                logger.error(f"事件处理异常: handler_id={handler.handler_id}, error={e}")
        logger.info(f"发布事件: event_type={event.event_type.value}, handlers_called={count}")
        return count

    def process_event(self, event: Event, handler: EventHandler) -> Any:
        """处理事件"""
        if handler.callback is None:
            logger.warning(f"处理器无回调: handler_id={handler.handler_id}")
            return None
        result = handler.callback(event)
        logger.debug(f"事件处理完成: event_id={event.event_id}, handler_id={handler.handler_id}")
        return result


class EventDrivenScheduler:
    """事件驱动调度器"""

    def __init__(self):
        self.event_bus = EventBus()
        self.task_queue: List[Dict[str, Any]] = []
        self.agents: Dict[str, Dict[str, Any]] = {}
        self._setup_handlers()
        logger.info("EventDrivenScheduler初始化完成")

    def _setup_handlers(self):
        """设置内置事件处理器"""
        self.event_bus.subscribe(EventType.TASK_CREATED, self.on_task_created)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self.on_task_completed)
        self.event_bus.subscribe(EventType.AGENT_AVAILABLE, self.on_agent_available)
        logger.info("内置事件处理器设置完成")

    def on_task_created(self, event: Event) -> Dict[str, Any]:
        """任务创建事件处理"""
        task = event.data
        self.task_queue.append(task)
        logger.info(f"任务创建: task_id={task.get('task_id', 'unknown')}")
        self.schedule_next()
        return {"action": "queued", "task_id": task.get("task_id", "")}

    def on_task_completed(self, event: Event) -> Dict[str, Any]:
        """任务完成事件处理"""
        task = event.data
        agent_id = task.get("agent_id", "")
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = "available"
            logger.info(f"任务完成，代理释放: agent_id={agent_id}")
        self.schedule_next()
        return {"action": "completed", "task_id": task.get("task_id", "")}

    def on_agent_available(self, event: Event) -> Dict[str, Any]:
        """代理可用事件处理"""
        agent_id = event.data.get("agent_id", "")
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = "available"
            logger.info(f"代理可用: agent_id={agent_id}")
        self.schedule_next()
        return {"action": "agent_available", "agent_id": agent_id}

    def schedule_next(self) -> Optional[Dict[str, Any]]:
        """调度下一个任务"""
        available_agents = [
            aid for aid, info in self.agents.items()
            if info.get("status") == "available"
        ]

        if not self.task_queue or not available_agents:
            logger.debug("调度: 无可用任务或代理")
            return None

        task = self.task_queue.pop(0)
        agent_id = available_agents[0]
        self.agents[agent_id]["status"] = "busy"
        task["agent_id"] = agent_id
        task["status"] = "assigned"
        logger.info(f"调度任务: task_id={task.get('task_id', '')}, agent_id={agent_id}")
        return {"task": task, "agent_id": agent_id}
