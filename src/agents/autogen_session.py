"""
多Agent软件工程系统 - AutoGen Agent会话管理

职责：基于AutoGen的Agent会话实现
"""

from typing import Any, Optional, Dict, List
from abc import ABC, abstractmethod
from datetime import datetime
from .autogen_core import (
    AgentMessage, MessageRole, MessageQueue, get_global_queue
)


class BaseAutoGenAgent(ABC):
    """
    基于AutoGen的Agent基类
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.config = config or {}

        self._message_history: List[AgentMessage] = []
        self._active = True

        # 订阅全局队列
        queue = get_global_queue()
        queue.subscribe(self.agent_id, self._handle_message)

    @abstractmethod
    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        处理收到的消息，子类必须实现
        """
        pass

    def send_message(
        self,
        content: Any,
        receiver: Optional[str] = None,
        role: MessageRole = MessageRole.ASSISTANT,
        metadata: Optional[Dict[str, Any]] = None,
        do_not_process: bool = False
    ) -> AgentMessage:
        """
        发送消息

        Args:
            do_not_process: 如果为True，不触发处理循环，用于防止递归
        """
        message = AgentMessage(
            role=role,
            content=content,
            sender=self.agent_id,
            receiver=receiver,
            metadata=metadata
        )
        self._message_history.append(message)

        if not do_not_process:
            queue = get_global_queue()
            queue.send(message)

        return message

    def _handle_message(self, message: AgentMessage) -> None:
        """
        内部消息处理方法
        """
        if not self._active:
            return

        # 不处理自己发送的消息，防止循环
        if message.sender == self.agent_id:
            return

        self._message_history.append(message)

        reply = self.process_message(message)
        if reply is not None:
            # 发送回复时，直接记录到队列但不触发处理循环
            reply.sender = self.agent_id
            reply.receiver = message.sender
            self.send_message(
                reply.content,
                receiver=reply.receiver,
                role=reply.role,
                metadata=reply.metadata,
                do_not_process=True  # 防止递归
            )

    def get_message_history(self, limit: int = 100) -> List[AgentMessage]:
        """获取消息历史"""
        return self._message_history[-limit:]

    def reset(self) -> None:
        """重置Agent状态"""
        self._message_history.clear()

    @property
    def active(self) -> bool:
        """是否活跃"""
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self._active = value


class SimpleAutoGenAgent(BaseAutoGenAgent):
    """
    简单的AutoGen Agent实现（用于基础测试）
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        response_callback: Optional[callable] = None
    ):
        super().__init__(agent_id, name)
        self.response_callback = response_callback

    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """简单的消息处理"""
        if self.response_callback:
            response_content = self.response_callback(message.content)
        else:
            response_content = f"Received from {message.sender}: {message.content}"

        return AgentMessage(
            role=MessageRole.ASSISTANT,
            content=response_content,
            sender=self.agent_id,
            receiver=message.sender
        )


class AgentConversation:
    """
    Agent会话管理
    """

    def __init__(self, conversation_id: str = None):
        self.conversation_id = conversation_id or f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._messages: List[AgentMessage] = []
        self._participants: Dict[str, BaseAutoGenAgent] = {}

    def add_participant(self, agent: BaseAutoGenAgent) -> None:
        """添加参与者"""
        self._participants[agent.agent_id] = agent

    def remove_participant(self, agent_id: str) -> bool:
        """移除参与者"""
        if agent_id in self._participants:
            del self._participants[agent_id]
            return True
        return False

    def start_conversation(
        self,
        initial_message: AgentMessage,
        max_rounds: int = 10
    ) -> List[AgentMessage]:
        """开始会话 - 使用简化的非队列方式"""
        self._messages.append(initial_message)

        current_round = 0
        last_message = initial_message

        while current_round < max_rounds and len(self._participants) > 0:
            # 找到接收者并处理
            if last_message.receiver and last_message.receiver in self._participants:
                target_agent = self._participants[last_message.receiver]
                reply = target_agent.process_message(last_message)

                if reply:
                    reply.sender = target_agent.agent_id
                    self._messages.append(reply)
                    last_message = reply
                else:
                    break
            else:
                # 如果没有明确接收者，尝试找第一个不是发送者的Agent
                for agent_id, agent in self._participants.items():
                    if agent_id != last_message.sender:
                        reply = agent.process_message(last_message)
                        if reply:
                            self._messages.append(reply)
                            last_message = reply
                            break
                else:
                    break

            current_round += 1

        return self._messages

    def get_messages(self) -> List[AgentMessage]:
        """获取会话消息"""
        return list(self._messages)
