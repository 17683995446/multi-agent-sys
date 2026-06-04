
"""
阶段46验收测试：协商结果持久化与恢复
"""

import pytest
import time
import uuid
import os
import shutil

from src.architecture.negotiation_persistence import (
    StorageType, SerializationFormat,
    PersistedSession, PersistedProposal,
    PersistenceBackend, MemoryPersistenceBackend, FilePersistenceBackend,
    SessionSerializer, NegotiationPersistenceService,
    get_persistence_service, reset_persistence_service
)
from src.architecture.negotiation_engine import (
    NegotiationPhase, NegotiationStatus, NegotiationStrategy, MessageType,
    NegotiationIssue, NegotiationProposal, NegotiationMessage, NegotiationAgent,
    NegotiationHistory, NegotiationStrategyEngine, NegotiationSession,
    NegotiationProtocol, NegotiationService,
    get_negotiation_service, reset_negotiation_service
)


class TestPersistedDataStructures:
    """测试持久化数据结构"""

    def test_persisted_session_creation(self):
        """测试持久化会话创建"""
        record = PersistedSession(session_id="test", topic="test_topic")
        assert record.session_id == "test"
        assert record.topic == "test_topic"
        assert record.status == ""
        assert record.record_id is not None

    def test_persisted_session_to_dict(self):
        """测试持久化会话序列化"""
        record = PersistedSession(
            session_id="s1",
            topic="price",
            status="active",
            agents_snapshot=[{"agent_id": "a1"}],
        )
        d = record.to_dict()
        assert d["session_id"] == "s1"
        assert d["topic"] == "price"
        assert d["status"] == "active"
        assert len(d["agents_snapshot"]) == 1

    def test_persisted_session_from_dict(self):
        """测试持久化会话反序列化"""
        data = {
            "record_id": "r1",
            "session_id": "s1",
            "topic": "test",
            "status": "active",
            "phase": "proposal",
            "agents_snapshot": [],
            "issues_snapshot": [],
            "history_snapshot": {},
            "consensus_proposal": None,
            "metadata": {},
            "created_at": 1000.0,
            "updated_at": 1000.0,
        }
        record = PersistedSession.from_dict(data)
        assert record.session_id == "s1"
        assert record.topic == "test"
        assert record.created_at == 1000.0

    def test_persisted_proposal_creation(self):
        """测试持久化提案创建"""
        record = PersistedProposal(
            session_id="s1",
            proposal_id="p1",
            proposer_id="a1",
            issue_values={"price": 200},
            utility=0.8,
        )
        assert record.session_id == "s1"
        assert record.proposal_id == "p1"
        assert record.utility == 0.8
        assert record.accepted == False

    def test_persisted_proposal_to_dict_and_back(self):
        """测试持久化提案序列化与反序列化"""
        record = PersistedProposal(
            session_id="s1",
            proposal_id="p1",
            proposer_id="a1",
            issue_values={"price": 200},
            utility=0.8,
            accepted=True,
        )
        d = record.to_dict()
        restored = PersistedProposal.from_dict(d)
        assert restored.session_id == "s1"
        assert restored.proposal_id == "p1"
        assert restored.utility == 0.8
        assert restored.accepted == True


class TestMemoryPersistenceBackend:
    """测试内存持久化后端"""

    def setup_method(self):
        self.backend = MemoryPersistenceBackend()

    def test_save_and_load_session(self):
        """测试保存和加载会话"""
        record = PersistedSession(session_id="s1", topic="test")
        assert self.backend.save_session(record) == True
        loaded = self.backend.load_session("s1")
        assert loaded is not None
        assert loaded.session_id == "s1"
        assert loaded.topic == "test"

    def test_load_nonexistent_session(self):
        """测试加载不存在的会话"""
        result = self.backend.load_session("nonexistent")
        assert result is None

    def test_delete_session(self):
        """测试删除会话"""
        record = PersistedSession(session_id="s1", topic="test")
        self.backend.save_session(record)
        assert self.backend.delete_session("s1") == True
        assert self.backend.load_session("s1") is None

    def test_delete_nonexistent_session(self):
        """测试删除不存在的会话"""
        assert self.backend.delete_session("nonexistent") == False

    def test_list_sessions(self):
        """测试列出所有会话"""
        self.backend.save_session(PersistedSession(session_id="s1", topic="t1"))
        self.backend.save_session(PersistedSession(session_id="s2", topic="t2"))
        sessions = self.backend.list_sessions()
        assert len(sessions) == 2

    def test_save_and_load_proposals(self):
        """测试保存和加载提案"""
        proposal = PersistedProposal(session_id="s1", proposal_id="p1", proposer_id="a1")
        assert self.backend.save_proposal(proposal) == True
        proposals = self.backend.load_proposals("s1")
        assert len(proposals) == 1
        assert proposals[0].proposal_id == "p1"

    def test_load_proposals_empty(self):
        """测试加载空提案列表"""
        proposals = self.backend.load_proposals("nonexistent")
        assert len(proposals) == 0


class TestFilePersistenceBackend:
    """测试文件持久化后端"""

    def setup_method(self):
        self.test_dir = f"/tmp/test_negotiation_persistence_{uuid.uuid4().hex[:8]}"
        self.backend = FilePersistenceBackend(base_dir=self.test_dir)

    def teardown_method(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_load_session(self):
        """测试保存和加载会话"""
        record = PersistedSession(session_id="s1", topic="file_test")
        assert self.backend.save_session(record) == True
        loaded = self.backend.load_session("s1")
        assert loaded is not None
        assert loaded.session_id == "s1"
        assert loaded.topic == "file_test"

    def test_load_nonexistent_session(self):
        """测试加载不存在的会话"""
        result = self.backend.load_session("nonexistent")
        assert result is None

    def test_delete_session(self):
        """测试删除会话"""
        record = PersistedSession(session_id="s1", topic="test")
        self.backend.save_session(record)
        assert self.backend.delete_session("s1") == True
        assert self.backend.load_session("s1") is None

    def test_list_sessions(self):
        """测试列出所有会话"""
        self.backend.save_session(PersistedSession(session_id="s1", topic="t1"))
        self.backend.save_session(PersistedSession(session_id="s2", topic="t2"))
        sessions = self.backend.list_sessions()
        assert len(sessions) == 2

    def test_save_and_load_proposals(self):
        """测试保存和加载提案"""
        proposal = PersistedProposal(session_id="s1", proposal_id="p1", proposer_id="a1")
        assert self.backend.save_proposal(proposal) == True
        proposals = self.backend.load_proposals("s1")
        assert len(proposals) == 1


class TestSessionSerializer:
    """测试会话序列化器"""

    def test_serialize_session(self):
        """测试序列化协商会话"""
        issue = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        agent = NegotiationAgent(agent_id="a1", name="buyer", strategy=NegotiationStrategy.COLLABORATIVE, issues=[issue])

        session = NegotiationSession(topic="test_serialize")
        session.add_agent(agent)
        session.add_issue(issue)
        session.start()

        proposal = NegotiationProposal(proposer_id="a1", issue_values={"price": 200})
        session.history.add_proposal(proposal)

        record = SessionSerializer.serialize_session(session)
        assert record.session_id == session.session_id
        assert record.topic == "test_serialize"
        assert record.status == "active"
        assert len(record.agents_snapshot) == 1
        assert len(record.issues_snapshot) == 1
        assert record.history_snapshot["proposal_count"] == 1

    def test_serialize_proposal(self):
        """测试序列化提案"""
        proposal = NegotiationProposal(proposer_id="a1", issue_values={"price": 200}, utility=0.8)
        record = SessionSerializer.serialize_proposal("s1", proposal, accepted=True)
        assert record.session_id == "s1"
        assert record.proposer_id == "a1"
        assert record.utility == 0.8
        assert record.accepted == True


class TestPersistenceService:
    """测试持久化服务"""

    def setup_method(self):
        reset_persistence_service()
        reset_negotiation_service()
        self.service = NegotiationPersistenceService(storage_type=StorageType.MEMORY)

    def test_save_and_load_session(self):
        """测试保存和加载协商会话"""
        issue = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        agent = NegotiationAgent(agent_id="a1", name="buyer", issues=[issue])

        session = NegotiationSession(topic="persistence_test")
        session.add_agent(agent)
        session.add_issue(issue)
        session.start()

        proposal = NegotiationProposal(proposer_id="a1", issue_values={"price": 200})
        session.history.add_proposal(proposal)

        result = self.service.save_session(session)
        assert result == True

        loaded = self.service.load_session(session.session_id)
        assert loaded is not None
        assert loaded.topic == "persistence_test"

    def test_recover_session(self):
        """测试恢复协商会话"""
        issue = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        agent1 = NegotiationAgent(agent_id="a1", name="buyer", strategy=NegotiationStrategy.COLLABORATIVE, issues=[issue])
        agent2 = NegotiationAgent(agent_id="a2", name="seller", strategy=NegotiationStrategy.COMPETITIVE, issues=[issue])

        session = NegotiationSession(topic="recovery_test")
        session.add_agent(agent1)
        session.add_agent(agent2)
        session.add_issue(issue)
        session.start()

        proposal = NegotiationProposal(proposer_id="a1", issue_values={"price": 200}, utility=0.5)
        session.history.add_proposal(proposal)

        self.service.save_session(session)

        recovered = self.service.recover_session(session.session_id)
        assert recovered is not None
        assert recovered.topic == "recovery_test"
        assert len(recovered.agents) == 2
        assert len(recovered.issues) == 1

    def test_recover_nonexistent_session(self):
        """测试恢复不存在的会话"""
        result = self.service.recover_session("nonexistent")
        assert result is None

    def test_delete_session(self):
        """测试删除会话"""
        session = NegotiationSession(topic="delete_test")
        self.service.save_session(session)
        assert self.service.delete_session(session.session_id) == True
        assert self.service.load_session(session.session_id) is None

    def test_list_sessions(self):
        """测试列出所有会话"""
        s1 = NegotiationSession(topic="t1")
        s2 = NegotiationSession(topic="t2")
        self.service.save_session(s1)
        self.service.save_session(s2)
        sessions = self.service.list_sessions()
        assert len(sessions) == 2

    def test_get_session_history(self):
        """测试获取会话历史摘要"""
        issue = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        agent = NegotiationAgent(agent_id="a1", name="buyer", issues=[issue])
        session = NegotiationSession(topic="history_test")
        session.add_agent(agent)
        session.add_issue(issue)
        session.start()

        proposal = NegotiationProposal(proposer_id="a1", issue_values={"price": 200})
        session.history.add_proposal(proposal)

        self.service.save_session(session)

        history = self.service.get_session_history(session.session_id)
        assert history["session_id"] == session.session_id
        assert history["topic"] == "history_test"
        assert history["agent_count"] == 1
        assert history["total_proposals"] == 1

    def test_replay_session(self):
        """测试回放会话提案历史"""
        session = NegotiationSession(topic="replay_test")
        p1 = NegotiationProposal(proposer_id="a1", issue_values={"price": 100}, utility=0.3)
        p2 = NegotiationProposal(proposer_id="a2", issue_values={"price": 200}, utility=0.6)
        session.history.add_proposal(p1)
        session.history.add_proposal(p2)

        self.service.save_session(session)

        replay = self.service.replay_session(session.session_id)
        assert len(replay) == 2

    def test_persistence_with_file_backend(self):
        """测试文件后端持久化"""
        test_dir = f"/tmp/test_persistence_svc_{uuid.uuid4().hex[:8]}"
        try:
            service = NegotiationPersistenceService(storage_type=StorageType.FILE, base_dir=test_dir)
            session = NegotiationSession(topic="file_test")
            service.save_session(session)

            loaded = service.load_session(session.session_id)
            assert loaded is not None
            assert loaded.topic == "file_test"
        finally:
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)


class TestPersistenceIntegration:
    """持久化集成测试"""

    def setup_method(self):
        reset_persistence_service()
        reset_negotiation_service()

    def test_full_negotiation_with_persistence(self):
        """测试完整协商流程与持久化"""
        issue = NegotiationIssue(name="price", possible_values=[100, 200, 300])
        agent1 = NegotiationAgent(agent_id="a1", name="buyer", strategy=NegotiationStrategy.COLLABORATIVE, issues=[issue])
        agent2 = NegotiationAgent(agent_id="a2", name="seller", strategy=NegotiationStrategy.COLLABORATIVE, issues=[issue])

        neg_service = get_negotiation_service()
        session = neg_service.create_negotiation(
            topic="persistence_integration",
            agents=[agent1, agent2],
            issues=[issue]
        )
        neg_service.start_negotiation(session.session_id)

        # 保存
        persistence = NegotiationPersistenceService(storage_type=StorageType.MEMORY)
        persistence.save_session(session)

        # 加载并恢复
        recovered = persistence.recover_session(session.session_id)
        assert recovered is not None
        assert recovered.topic == "persistence_integration"
        assert len(recovered.agents) == 2

    def test_save_load_recover_cycle(self):
        """测试保存-加载-恢复完整周期"""
        issue = NegotiationIssue(name="quality", possible_values=["low", "medium", "high"])
        agent = NegotiationAgent(agent_id="a1", name="tester", issues=[issue])

        session = NegotiationSession(topic="cycle_test")
        session.add_agent(agent)
        session.add_issue(issue)
        session.start()

        proposal = NegotiationProposal(proposer_id="a1", issue_values={"quality": "high"}, utility=1.0)
        session.history.add_proposal(proposal)
        session.history.accept_proposal(proposal)

        persistence = NegotiationPersistenceService(storage_type=StorageType.MEMORY)
        persistence.save_session(session)

        # 恢复
        recovered = persistence.recover_session(session.session_id)
        assert recovered is not None
        assert len(recovered.history.proposals) == 1
