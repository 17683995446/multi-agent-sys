"""
阶段4：接入AutoGen基础会话通信 测试文件

验收标准：
1. AutoGen-core 成功安装（>= 0.2.0）
2. 基础Agent类实现
3. 消息收发接口实现
4. Agent注册机制
"""

import sys
from pathlib import Path
import pytest
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestAutoGenInstallation:
    """测试AutoGen安装"""

    def test_autogen_core_import(self):
        """验证autogen_core可导入"""
        import autogen_core
        assert autogen_core is not None

    def test_autogen_agentchat_import(self):
        """验证autogen_agentchat可导入"""
        import autogen_agentchat
        assert autogen_agentchat is not None


class TestAutoGenCoreClasses:
    """测试AutoGen核心类"""

    def test_message_role_enum(self):
        """验证MessageRole枚举"""
        from agents import MessageRole

        assert hasattr(MessageRole, "USER")
        assert hasattr(MessageRole, "ASSISTANT")
        assert hasattr(MessageRole, "SYSTEM")
        assert hasattr(MessageRole, "FUNCTION")

    def test_agent_message_creation(self):
        """验证AgentMessage创建"""
        from agents import AutoGenAgentMessage, MessageRole

        message = AutoGenAgentMessage(
            role=MessageRole.USER,
            content="Hello",
            sender="user1",
            receiver="agent1"
        )

        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.sender == "user1"
        assert message.receiver == "agent1"

    def test_message_to_dict_and_back(self):
        """验证消息序列化/反序列化"""
        from agents import AutoGenAgentMessage, MessageRole

        original = AutoGenAgentMessage(
            role=MessageRole.USER,
            content="Hello",
            sender="user1",
            receiver="agent1",
            metadata={"test": "value"}
        )

        data = original.to_dict()
        assert data["role"] == "user"
        assert data["content"] == "Hello"
        assert data["sender"] == "user1"
        assert data["receiver"] == "agent1"
        assert data["metadata"]["test"] == "value"

        restored = AutoGenAgentMessage.from_dict(data)
        assert restored.role == original.role
        assert restored.content == original.content
        assert restored.sender == original.sender
        assert restored.receiver == original.receiver

    def test_message_queue(self):
        """验证消息队列"""
        from agents import MessageQueue, AutoGenAgentMessage, MessageRole

        queue = MessageQueue()
        message1 = AutoGenAgentMessage(
            role=MessageRole.USER,
            content="First message",
            sender="user1",
            receiver="agent1"
        )
        message2 = AutoGenAgentMessage(
            role=MessageRole.ASSISTANT,
            content="Second message",
            sender="agent1",
            receiver="user1"
        )

        queue.send(message1)
        queue.send(message2)

        messages = queue.get_messages()
        assert len(messages) == 2

        agent1_messages = queue.get_messages("agent1")
        assert len(agent1_messages) >= 1
        assert any(msg.sender == "user1" for msg in agent1_messages)


class TestAutoGenAgentClasses:
    """测试AutoGen Agent类"""

    def test_simple_agent_creation(self):
        """验证SimpleAutoGenAgent创建"""
        from agents import SimpleAutoGenAgent

        agent = SimpleAutoGenAgent("agent1", "Test Agent")
        assert agent.agent_id == "agent1"
        assert agent.name == "Test Agent"

    def test_agent_send_message(self):
        """验证Agent发送消息"""
        from agents import SimpleAutoGenAgent, AutoGenAgentMessage, MessageRole

        agent = SimpleAutoGenAgent("agent1", "Test Agent")
        message = agent.send_message(
            content="Test message",
            receiver="user1"
        )

        assert message is not None
        assert message.sender == "agent1"
        assert message.receiver == "user1"
        assert message.content == "Test message"

    def test_agent_message_history(self):
        """验证Agent消息历史"""
        from agents import SimpleAutoGenAgent, AutoGenAgentMessage, MessageRole

        agent = SimpleAutoGenAgent("agent1", "Test Agent")

        agent.send_message("Msg1", receiver="user1")
        agent.send_message("Msg2", receiver="user2")

        history = agent.get_message_history()
        assert len(history) == 2

    def test_agent_response_callback(self):
        """验证Agent响应回调"""
        from agents import SimpleAutoGenAgent, AutoGenAgentMessage, MessageRole

        def my_callback(content):
            return f"Received: {content}"

        agent = SimpleAutoGenAgent("agent1", "Test Agent", response_callback=my_callback)

        incoming_msg = AutoGenAgentMessage(
            role=MessageRole.USER,
            content="Hello",
            sender="user1",
            receiver="agent1"
        )

        reply = agent.process_message(incoming_msg)
        assert reply is not None
        assert reply.content == "Received: Hello"

    def test_base_agent_abstract(self):
        """验证BaseAutoGenAgent是抽象类"""
        from agents import BaseAutoGenAgent

        with pytest.raises(TypeError):
            # 不能直接实例化抽象类
            BaseAutoGenAgent("agent1", "Test")


class TestAgentConversation:
    """测试Agent会话管理"""

    def test_conversation_creation(self):
        """验证会话创建"""
        from agents import AgentConversation

        conv = AgentConversation()
        assert conv.conversation_id is not None

    def test_conversation_add_participant(self):
        """验证添加参与者"""
        from agents import AgentConversation, SimpleAutoGenAgent

        conv = AgentConversation()
        agent1 = SimpleAutoGenAgent("agent1", "Agent 1")
        agent2 = SimpleAutoGenAgent("agent2", "Agent 2")

        conv.add_participant(agent1)
        conv.add_participant(agent2)

        assert agent1.agent_id in conv._participants
        assert agent2.agent_id in conv._participants

    def test_conversation_removal(self):
        """验证移除参与者"""
        from agents import AgentConversation, SimpleAutoGenAgent

        conv = AgentConversation()
        agent1 = SimpleAutoGenAgent("agent1", "Agent 1")

        conv.add_participant(agent1)
        result = conv.remove_participant("agent1")

        assert result is True
        assert "agent1" not in conv._participants

    def test_conversation_message_history(self):
        """验证会话消息历史"""
        from agents import (
            AgentConversation, SimpleAutoGenAgent,
            AutoGenAgentMessage, MessageRole
        )

        conv = AgentConversation()
        agent1 = SimpleAutoGenAgent("agent1", "Agent 1")
        agent2 = SimpleAutoGenAgent("agent2", "Agent 2")

        conv.add_participant(agent1)
        conv.add_participant(agent2)

        initial_msg = AutoGenAgentMessage(
            role=MessageRole.USER,
            content="Hello!",
            sender="user1",
            receiver="agent1"
        )

        conv.start_conversation(initial_msg, max_rounds=2)
        messages = conv.get_messages()

        assert len(messages) >= 1  # 至少有初始消息


class TestRegistration:
    """测试全局队列和注册机制"""

    def test_global_queue_singleton(self):
        """验证全局队列是单例"""
        from agents import get_global_queue

        q1 = get_global_queue()
        q2 = get_global_queue()
        assert q1 is q2

    def test_agent_initialization(self):
        """验证Agent初始化正常"""
        from agents import SimpleAutoGenAgent

        agent = SimpleAutoGenAgent("agent_sub", "Sub Agent")

        # 这个测试主要验证Agent能正常初始化
        assert agent.agent_id == "agent_sub"
        assert agent.active is True


class TestIntegration:
    """集成测试"""

    def test_two_agent_communication(self):
        """测试两个Agent之间通信"""
        from agents import SimpleAutoGenAgent, AutoGenAgentMessage, MessageRole

        agent1 = SimpleAutoGenAgent("agent1", "Agent 1")
        agent2 = SimpleAutoGenAgent("agent2", "Agent 2")

        # agent1 发送消息给 agent2
        msg = agent1.send_message("Hi from agent1!", receiver="agent2")
        assert msg.sender == "agent1"
        assert msg.receiver == "agent2"

    def test_conversation_rounds(self):
        """测试会话轮次"""
        from agents import (
            AgentConversation, SimpleAutoGenAgent,
            AutoGenAgentMessage, MessageRole
        )

        conv = AgentConversation()

        def callback1(content):
            return f"Agent1: {content}"

        def callback2(content):
            return f"Agent2: {content}"

        agent1 = SimpleAutoGenAgent("agent1", "Agent 1", response_callback=callback1)
        agent2 = SimpleAutoGenAgent("agent2", "Agent 2", response_callback=callback2)

        conv.add_participant(agent1)
        conv.add_participant(agent2)

        initial_msg = AutoGenAgentMessage(
            role=MessageRole.USER,
            content="Start conversation!",
            sender="user",
            receiver="agent1"
        )

        conv.start_conversation(initial_msg, max_rounds=3)
        messages = conv.get_messages()
        assert len(messages) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
