"""
阶段54验收测试：事件驱动调度
"""

import pytest
from src.architecture.event_driven_scheduler import (
    EventType,
    Event,
    EventHandler,
    EventBus,
    EventDrivenScheduler,
)


class TestEventType:
    """测试事件类型枚举"""

    def test_event_type_values(self):
        """测试事件类型枚举值"""
        assert EventType.TASK_CREATED.value == "task_created"
        assert EventType.TASK_COMPLETED.value == "task_completed"
        assert EventType.TASK_FAILED.value == "task_failed"
        assert EventType.AGENT_AVAILABLE.value == "agent_available"
        assert EventType.AGENT_BUSY.value == "agent_busy"
        assert EventType.DEADLINE_APPROACHING.value == "deadline_approaching"

    def test_all_event_types(self):
        """测试所有事件类型"""
        types = list(EventType)
        assert len(types) == 6


class TestEvent:
    """测试事件"""

    def test_default_creation(self):
        """测试默认创建"""
        event = Event()
        assert event.event_id != ""
        assert event.event_type == EventType.TASK_CREATED
        assert event.source == ""
        assert event.data == {}
        assert event.timestamp > 0
        assert event.priority == 0

    def test_custom_creation(self):
        """测试自定义创建"""
        event = Event(
            event_type=EventType.TASK_COMPLETED,
            source="agent1",
            data={"task_id": "t1"},
            priority=5,
        )
        assert event.event_type == EventType.TASK_COMPLETED
        assert event.source == "agent1"
        assert event.data["task_id"] == "t1"
        assert event.priority == 5


class TestEventHandler:
    """测试事件处理器"""

    def test_default_creation(self):
        """测试默认创建"""
        handler = EventHandler()
        assert handler.handler_id != ""
        assert handler.event_type == EventType.TASK_CREATED
        assert handler.callback is None
        assert handler.priority == 0

    def test_custom_creation(self):
        """测试自定义创建"""
        def my_callback(event):
            return event.data

        handler = EventHandler(event_type=EventType.TASK_COMPLETED, callback=my_callback, priority=10)
        assert handler.event_type == EventType.TASK_COMPLETED
        assert handler.callback is not None
        assert handler.priority == 10


class TestEventBus:
    """测试事件总线"""

    def test_subscribe(self):
        """测试订阅事件"""
        bus = EventBus()
        handler_id = bus.subscribe(EventType.TASK_CREATED, lambda e: None)
        assert handler_id != ""
        assert EventType.TASK_CREATED.value in bus.handlers
        assert len(bus.handlers[EventType.TASK_CREATED.value]) == 1

    def test_subscribe_multiple(self):
        """测试多次订阅"""
        bus = EventBus()
        bus.subscribe(EventType.TASK_CREATED, lambda e: None)
        bus.subscribe(EventType.TASK_CREATED, lambda e: None)
        assert len(bus.handlers[EventType.TASK_CREATED.value]) == 2

    def test_unsubscribe(self):
        """测试取消订阅"""
        bus = EventBus()
        handler_id = bus.subscribe(EventType.TASK_CREATED, lambda e: None)
        result = bus.unsubscribe(handler_id)
        assert result is True
        assert len(bus.handlers[EventType.TASK_CREATED.value]) == 0

    def test_unsubscribe_nonexistent(self):
        """测试取消不存在的订阅"""
        bus = EventBus()
        result = bus.unsubscribe("nonexistent")
        assert result is False

    def test_publish(self):
        """测试发布事件"""
        bus = EventBus()
        results = []
        bus.subscribe(EventType.TASK_CREATED, lambda e: results.append(e.data))
        event = Event(event_type=EventType.TASK_CREATED, data={"key": "value"})
        count = bus.publish(event)
        assert count == 1
        assert len(results) == 1
        assert results[0]["key"] == "value"

    def test_publish_no_handlers(self):
        """测试发布无处理器的事件"""
        bus = EventBus()
        event = Event(event_type=EventType.TASK_CREATED)
        count = bus.publish(event)
        assert count == 0

    def test_publish_multiple_handlers(self):
        """测试发布事件到多个处理器"""
        bus = EventBus()
        results1 = []
        results2 = []
        bus.subscribe(EventType.TASK_CREATED, lambda e: results1.append("h1"))
        bus.subscribe(EventType.TASK_CREATED, lambda e: results2.append("h2"))
        event = Event(event_type=EventType.TASK_CREATED)
        count = bus.publish(event)
        assert count == 2
        assert len(results1) == 1
        assert len(results2) == 1

    def test_process_event(self):
        """测试处理事件"""
        bus = EventBus()
        handler = EventHandler(event_type=EventType.TASK_CREATED, callback=lambda e: e.data)
        event = Event(event_type=EventType.TASK_CREATED, data={"result": "ok"})
        result = bus.process_event(event, handler)
        assert result["result"] == "ok"

    def test_process_event_no_callback(self):
        """测试处理无回调的事件"""
        bus = EventBus()
        handler = EventHandler(event_type=EventType.TASK_CREATED, callback=None)
        event = Event(event_type=EventType.TASK_CREATED)
        result = bus.process_event(event, handler)
        assert result is None

    def test_handler_priority(self):
        """测试处理器优先级排序"""
        bus = EventBus()
        results = []
        bus.subscribe(EventType.TASK_CREATED, lambda e: results.append("low"), priority=1)
        bus.subscribe(EventType.TASK_CREATED, lambda e: results.append("high"), priority=10)
        event = Event(event_type=EventType.TASK_CREATED)
        bus.publish(event)
        assert results[0] == "high"
        assert results[1] == "low"


class TestEventDrivenScheduler:
    """测试事件驱动调度器"""

    def test_initial_state(self):
        """测试初始状态"""
        scheduler = EventDrivenScheduler()
        assert len(scheduler.task_queue) == 0
        assert len(scheduler.agents) == 0

    def test_on_task_created(self):
        """测试任务创建事件处理"""
        scheduler = EventDrivenScheduler()
        event = Event(
            event_type=EventType.TASK_CREATED,
            data={"task_id": "t1", "name": "任务1"},
        )
        result = scheduler.on_task_created(event)
        assert result["action"] == "queued"
        assert len(scheduler.task_queue) == 1

    def test_on_task_completed(self):
        """测试任务完成事件处理"""
        scheduler = EventDrivenScheduler()
        scheduler.agents["agent1"] = {"status": "busy"}
        event = Event(
            event_type=EventType.TASK_COMPLETED,
            data={"task_id": "t1", "agent_id": "agent1"},
        )
        result = scheduler.on_task_completed(event)
        assert result["action"] == "completed"
        assert scheduler.agents["agent1"]["status"] == "available"

    def test_on_agent_available(self):
        """测试代理可用事件处理"""
        scheduler = EventDrivenScheduler()
        scheduler.agents["agent1"] = {"status": "busy"}
        event = Event(
            event_type=EventType.AGENT_AVAILABLE,
            data={"agent_id": "agent1"},
        )
        result = scheduler.on_agent_available(event)
        assert result["action"] == "agent_available"
        assert scheduler.agents["agent1"]["status"] == "available"

    def test_schedule_next(self):
        """测试调度下一个任务"""
        scheduler = EventDrivenScheduler()
        scheduler.agents["agent1"] = {"status": "available"}
        scheduler.task_queue.append({"task_id": "t1", "name": "任务1"})
        result = scheduler.schedule_next()
        assert result is not None
        assert result["agent_id"] == "agent1"
        assert result["task"]["task_id"] == "t1"
        assert scheduler.agents["agent1"]["status"] == "busy"

    def test_schedule_next_no_agents(self):
        """测试无可用代理时调度"""
        scheduler = EventDrivenScheduler()
        scheduler.task_queue.append({"task_id": "t1"})
        result = scheduler.schedule_next()
        assert result is None

    def test_schedule_next_no_tasks(self):
        """测试无任务时调度"""
        scheduler = EventDrivenScheduler()
        scheduler.agents["agent1"] = {"status": "available"}
        result = scheduler.schedule_next()
        assert result is None

    def test_full_event_workflow(self):
        """测试完整事件驱动工作流"""
        scheduler = EventDrivenScheduler()
        scheduler.agents["agent1"] = {"status": "available"}

        # 创建任务
        event = Event(
            event_type=EventType.TASK_CREATED,
            data={"task_id": "t1", "name": "任务1"},
        )
        scheduler.event_bus.publish(event)
        # 任务应该被自动调度
        assert len(scheduler.task_queue) == 0  # 已被调度
        assert scheduler.agents["agent1"]["status"] == "busy"

        # 完成任务
        event = Event(
            event_type=EventType.TASK_COMPLETED,
            data={"task_id": "t1", "agent_id": "agent1"},
        )
        scheduler.event_bus.publish(event)
        assert scheduler.agents["agent1"]["status"] == "available"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
