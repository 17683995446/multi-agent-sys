"""
优先级调度与资源分配
职责：优先级队列、资源管理、资源分配、任务调度
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PriorityLevel(int, Enum):
    """优先级级别"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class ResourceType(str, Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    NETWORK = "network"


@dataclass
class Resource:
    """资源"""
    resource_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    resource_type: ResourceType = ResourceType.CPU
    capacity: float = 0.0
    allocated: float = 0.0
    available: float = 0.0


@dataclass
class ResourceRequest:
    """资源请求"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    resource_type: ResourceType = ResourceType.CPU
    amount: float = 0.0
    priority: PriorityLevel = PriorityLevel.MEDIUM


@dataclass
class ResourceAllocation:
    """资源分配"""
    allocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    resource_id: str = ""
    amount: float = 0.0
    status: str = "pending"


class PriorityQueue:
    """优先级队列"""

    def __init__(self):
        self.queue: List[ResourceRequest] = []
        logger.info("PriorityQueue初始化完成")

    def enqueue(self, request: ResourceRequest) -> bool:
        """入队"""
        self.queue.append(request)
        self.queue.sort(key=lambda r: r.priority.value)
        logger.info(f"入队: request_id={request.request_id}, priority={request.priority.name}")
        return True

    def dequeue(self) -> Optional[ResourceRequest]:
        """出队"""
        if not self.queue:
            logger.debug("出队: 队列为空")
            return None
        request = self.queue.pop(0)
        logger.info(f"出队: request_id={request.request_id}, priority={request.priority.name}")
        return request

    def peek(self) -> Optional[ResourceRequest]:
        """查看队首"""
        if not self.queue:
            logger.debug("查看队首: 队列为空")
            return None
        return self.queue[0]

    def size(self) -> int:
        """获取队列大小"""
        return len(self.queue)

    def is_empty(self) -> bool:
        """判断队列是否为空"""
        return len(self.queue) == 0

    def reorder(self) -> bool:
        """重新排序"""
        self.queue.sort(key=lambda r: r.priority.value)
        logger.info("优先级队列重新排序完成")
        return True


class ResourceManager:
    """资源管理器"""

    def __init__(self):
        self.resources: Dict[str, Resource] = {}
        self.allocations: Dict[str, ResourceAllocation] = {}
        logger.info("ResourceManager初始化完成")

    def register_resource(self, resource: Resource) -> bool:
        """注册资源"""
        if resource.resource_id in self.resources:
            logger.warning(f"注册资源失败: 资源已存在, resource_id={resource.resource_id}")
            return False
        resource.available = resource.capacity - resource.allocated
        self.resources[resource.resource_id] = resource
        logger.info(f"注册资源: resource_id={resource.resource_id}, type={resource.resource_type.value}, capacity={resource.capacity}")
        return True

    def allocate(self, request: ResourceRequest) -> Optional[ResourceAllocation]:
        """分配资源"""
        # 查找匹配类型的资源
        for resource_id, resource in self.resources.items():
            if resource.resource_type == request.resource_type and resource.available >= request.amount:
                resource.allocated += request.amount
                resource.available -= request.amount
                allocation = ResourceAllocation(
                    request_id=request.request_id,
                    resource_id=resource_id,
                    amount=request.amount,
                    status="allocated",
                )
                self.allocations[allocation.allocation_id] = allocation
                logger.info(f"分配资源: allocation_id={allocation.allocation_id}, resource_id={resource_id}, amount={request.amount}")
                return allocation

        logger.warning(f"分配资源失败: 无可用资源, type={request.resource_type.value}, amount={request.amount}")
        return None

    def release(self, allocation_id: str) -> bool:
        """释放资源"""
        if allocation_id not in self.allocations:
            logger.warning(f"释放资源失败: 分配不存在, allocation_id={allocation_id}")
            return False

        allocation = self.allocations[allocation_id]
        resource = self.resources.get(allocation.resource_id)
        if resource:
            resource.allocated -= allocation.amount
            resource.available += allocation.amount
            allocation.status = "released"
            logger.info(f"释放资源: allocation_id={allocation_id}, resource_id={allocation.resource_id}, amount={allocation.amount}")
        return True

    def get_available(self, resource_type: Optional[ResourceType] = None) -> List[Resource]:
        """获取可用资源"""
        if resource_type:
            available = [r for r in self.resources.values()
                         if r.resource_type == resource_type and r.available > 0]
        else:
            available = [r for r in self.resources.values() if r.available > 0]
        logger.debug(f"获取可用资源: type={resource_type.value if resource_type else 'all'}, count={len(available)}")
        return available


class PriorityScheduler:
    """优先级调度器"""

    def __init__(self):
        self.queue = PriorityQueue()
        self.resource_manager = ResourceManager()
        self.submitted_tasks: Dict[str, Dict[str, Any]] = {}
        logger.info("PriorityScheduler初始化完成")

    def submit_task(self, task_id: str, resource_type: ResourceType,
                    amount: float, priority: PriorityLevel = PriorityLevel.MEDIUM) -> str:
        """提交任务"""
        request = ResourceRequest(
            task_id=task_id,
            resource_type=resource_type,
            amount=amount,
            priority=priority,
        )
        self.queue.enqueue(request)
        self.submitted_tasks[task_id] = {
            "request_id": request.request_id,
            "status": "queued",
            "priority": priority,
        }
        logger.info(f"提交任务: task_id={task_id}, priority={priority.name}, resource={resource_type.value}")
        return request.request_id

    def schedule_next(self) -> Optional[Dict[str, Any]]:
        """调度下一个任务"""
        request = self.queue.dequeue()
        if request is None:
            logger.debug("调度: 队列为空")
            return None

        allocation = self.resource_manager.allocate(request)
        if allocation is None:
            # 无法分配，重新入队
            self.queue.enqueue(request)
            logger.warning(f"调度失败，重新入队: task_id={request.task_id}")
            return None

        self.submitted_tasks[request.task_id]["status"] = "scheduled"
        result = {
            "task_id": request.task_id,
            "allocation_id": allocation.allocation_id,
            "resource_id": allocation.resource_id,
            "amount": allocation.amount,
        }
        logger.info(f"调度成功: task_id={request.task_id}, allocation_id={allocation.allocation_id}")
        return result

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        status = self.submitted_tasks.get(task_id)
        if status:
            logger.debug(f"获取任务状态: task_id={task_id}, status={status['status']}")
        else:
            logger.warning(f"获取任务状态失败: 任务不存在, task_id={task_id}")
        return status
