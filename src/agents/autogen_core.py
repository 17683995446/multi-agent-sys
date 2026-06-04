"""
多Agent软件工程系统 - AutoGen通信核心模块

职责：使用AutoGen实现Agent会话通信
阶段4：接入AutoGen基础会话通信
"""

from typing import Any, Optional, Dict, List, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


@dataclass
class AgentMessage:
    """Agent消息实体"""
    role: MessageRole
    content: Any
    sender: str
    receiver: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "sender": self.sender,
            "receiver": self.receiver,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            sender=data["sender"],
            receiver=data.get("receiver"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            metadata=data.get("metadata", {})
        )


class MessageQueue:
    """消息队列（用于Agent间通信）"""

    def __init__(self):
        self._queue: List[AgentMessage] = []
        self._subscribers: Dict[str, List[Callable]] = {}

    def send(self, message: AgentMessage) -> None:
        """发送消息"""
        self._queue.append(message)
        # 通知订阅者
        if message.receiver in self._subscribers:
            for callback in self._subscribers[message.receiver]:
                callback(message)
        # 广播订阅者（receiver为None或*）
        if None in self._subscribers:
            for callback in self._subscribers[None]:
                callback(message)

    def subscribe(self, agent_id: Optional[str], callback: Callable) -> None:
        """订阅消息"""
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
        self._subscribers[agent_id].append(callback)

    def get_messages(self, agent_id: Optional[str] = None, limit: int = 100) -> List[AgentMessage]:
        """获取消息"""
        if agent_id:
            return [
                msg for msg in self._queue[-limit:]
                if msg.receiver == agent_id or msg.sender == agent_id
            ]
        return self._queue[-limit:]

    def clear(self) -> None:
        """清空队列"""
        self._queue.clear()


# 全局消息队列实例
_global_queue = MessageQueue()


def get_global_queue() -> MessageQueue:
    """获取全局消息队列"""
    return _global_queue
