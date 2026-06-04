
"""
协商结果持久化与恢复
职责：协商会话的序列化存储、恢复重建、历史查询与回放
"""

import uuid
import time
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class StorageType(str, Enum):
    """存储类型"""
    MEMORY = "memory"
    FILE = "file"


class SerializationFormat(str, Enum):
    """序列化格式"""
    JSON = "json"


@dataclass
class PersistedSession:
    """持久化会话记录"""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    topic: str = ""
    status: str = ""
    phase: str = ""
    agents_snapshot: List[Dict[str, Any]] = field(default_factory=list)
    issues_snapshot: List[Dict[str, Any]] = field(default_factory=list)
    history_snapshot: Dict[str, Any] = field(default_factory=dict)
    consensus_proposal: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "record_id": self.record_id,
            "session_id": self.session_id,
            "topic": self.topic,
            "status": self.status,
            "phase": self.phase,
            "agents_snapshot": self.agents_snapshot,
            "issues_snapshot": self.issues_snapshot,
            "history_snapshot": self.history_snapshot,
            "consensus_proposal": self.consensus_proposal,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersistedSession":
        """从字典反序列化"""
        return cls(
            record_id=data.get("record_id", str(uuid.uuid4())),
            session_id=data.get("session_id", ""),
            topic=data.get("topic", ""),
            status=data.get("status", ""),
            phase=data.get("phase", ""),
            agents_snapshot=data.get("agents_snapshot", []),
            issues_snapshot=data.get("issues_snapshot", []),
            history_snapshot=data.get("history_snapshot", {}),
            consensus_proposal=data.get("consensus_proposal"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


@dataclass
class PersistedProposal:
    """持久化提案记录"""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    proposal_id: str = ""
    proposer_id: str = ""
    issue_values: Dict[str, Any] = field(default_factory=dict)
    utility: float = 0.0
    timestamp: float = field(default_factory=time.time)
    accepted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "record_id": self.record_id,
            "session_id": self.session_id,
            "proposal_id": self.proposal_id,
            "proposer_id": self.proposer_id,
            "issue_values": self.issue_values,
            "utility": self.utility,
            "timestamp": self.timestamp,
            "accepted": self.accepted,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersistedProposal":
        """从字典反序列化"""
        return cls(
            record_id=data.get("record_id", str(uuid.uuid4())),
            session_id=data.get("session_id", ""),
            proposal_id=data.get("proposal_id", ""),
            proposer_id=data.get("proposer_id", ""),
            issue_values=data.get("issue_values", {}),
            utility=data.get("utility", 0.0),
            timestamp=data.get("timestamp", time.time()),
            accepted=data.get("accepted", False),
        )


class PersistenceBackend(ABC):
    """持久化后端抽象基类"""

    @abstractmethod
    def save_session(self, record: PersistedSession) -> bool:
        """保存会话"""
        pass

    @abstractmethod
    def load_session(self, session_id: str) -> Optional[PersistedSession]:
        """加载会话"""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass

    @abstractmethod
    def list_sessions(self) -> List[PersistedSession]:
        """列出所有会话"""
        pass

    @abstractmethod
    def save_proposal(self, record: PersistedProposal) -> bool:
        """保存提案"""
        pass

    @abstractmethod
    def load_proposals(self, session_id: str) -> List[PersistedProposal]:
        """加载会话的所有提案"""
        pass


class MemoryPersistenceBackend(PersistenceBackend):
    """内存持久化后端"""

    def __init__(self):
        self._sessions: Dict[str, PersistedSession] = {}
        self._proposals: Dict[str, List[PersistedProposal]] = {}
        logger.debug("MemoryPersistenceBackend initialized")

    def save_session(self, record: PersistedSession) -> bool:
        """保存会话"""
        self._sessions[record.session_id] = record
        logger.info(f"MemoryBackend: session {record.session_id[:8]} saved")
        return True

    def load_session(self, session_id: str) -> Optional[PersistedSession]:
        """加载会话"""
        record = self._sessions.get(session_id)
        if record:
            logger.info(f"MemoryBackend: session {session_id[:8]} loaded")
        else:
            logger.warning(f"MemoryBackend: session {session_id[:8]} not found")
        return record

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._proposals.pop(session_id, None)
            logger.info(f"MemoryBackend: session {session_id[:8]} deleted")
            return True
        return False

    def list_sessions(self) -> List[PersistedSession]:
        """列出所有会话"""
        return list(self._sessions.values())

    def save_proposal(self, record: PersistedProposal) -> bool:
        """保存提案"""
        if record.session_id not in self._proposals:
            self._proposals[record.session_id] = []
        self._proposals[record.session_id].append(record)
        logger.debug(f"MemoryBackend: proposal {record.proposal_id[:8]} saved")
        return True

    def load_proposals(self, session_id: str) -> List[PersistedProposal]:
        """加载会话的所有提案"""
        return self._proposals.get(session_id, [])


class FilePersistenceBackend(PersistenceBackend):
    """文件持久化后端"""

    def __init__(self, base_dir: str = "/tmp/negotiation_persistence"):
        self.base_dir = base_dir
        self._sessions_dir = os.path.join(base_dir, "sessions")
        self._proposals_dir = os.path.join(base_dir, "proposals")
        os.makedirs(self._sessions_dir, exist_ok=True)
        os.makedirs(self._proposals_dir, exist_ok=True)
        logger.info(f"FilePersistenceBackend initialized at {base_dir}")

    def save_session(self, record: PersistedSession) -> bool:
        """保存会话"""
        try:
            filepath = os.path.join(self._sessions_dir, f"{record.session_id}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"FileBackend: session {record.session_id[:8]} saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"FileBackend: save failed - {e}")
            return False

    def load_session(self, session_id: str) -> Optional[PersistedSession]:
        """加载会话"""
        try:
            filepath = os.path.join(self._sessions_dir, f"{session_id}.json")
            if not os.path.exists(filepath):
                logger.warning(f"FileBackend: session {session_id[:8]} not found")
                return None
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"FileBackend: session {session_id[:8]} loaded")
            return PersistedSession.from_dict(data)
        except Exception as e:
            logger.error(f"FileBackend: load failed - {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            filepath = os.path.join(self._sessions_dir, f"{session_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"FileBackend: session {session_id[:8]} deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"FileBackend: delete failed - {e}")
            return False

    def list_sessions(self) -> List[PersistedSession]:
        """列出所有会话"""
        sessions = []
        try:
            for filename in os.listdir(self._sessions_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self._sessions_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    sessions.append(PersistedSession.from_dict(data))
        except Exception as e:
            logger.error(f"FileBackend: list failed - {e}")
        return sessions

    def save_proposal(self, record: PersistedProposal) -> bool:
        """保存提案"""
        try:
            session_proposals_dir = os.path.join(self._proposals_dir, record.session_id)
            os.makedirs(session_proposals_dir, exist_ok=True)
            filepath = os.path.join(session_proposals_dir, f"{record.proposal_id}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug(f"FileBackend: proposal {record.proposal_id[:8]} saved")
            return True
        except Exception as e:
            logger.error(f"FileBackend: save proposal failed - {e}")
            return False

    def load_proposals(self, session_id: str) -> List[PersistedProposal]:
        """加载会话的所有提案"""
        proposals = []
        try:
            session_proposals_dir = os.path.join(self._proposals_dir, session_id)
            if not os.path.exists(session_proposals_dir):
                return proposals
            for filename in os.listdir(session_proposals_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(session_proposals_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    proposals.append(PersistedProposal.from_dict(data))
        except Exception as e:
            logger.error(f"FileBackend: load proposals failed - {e}")
        return proposals


class SessionSerializer:
    """会话序列化器"""

    @staticmethod
    def serialize_session(session: Any) -> PersistedSession:
        """序列化协商会话"""
        from src.architecture.negotiation_engine import (
            NegotiationSession, NegotiationHistory
        )

        agents_snapshot = []
        for agent_id, agent in session.agents.items():
            agents_snapshot.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "strategy": agent.strategy.value if hasattr(agent.strategy, 'value') else str(agent.strategy),
                "issues": [
                    {"name": issue.name, "priority": issue.priority,
                     "possible_values": issue.possible_values}
                    for issue in agent.issues
                ],
            })

        issues_snapshot = []
        for issue in session.issues:
            issues_snapshot.append({
                "name": issue.name,
                "priority": issue.priority,
                "possible_values": issue.possible_values,
                "current_value": issue.current_value,
            })

        history_snapshot = {
            "message_count": len(session.history.messages),
            "proposal_count": len(session.history.proposals),
            "accepted_count": len(session.history.accepted_proposals),
            "proposals": [
                {
                    "proposal_id": p.proposal_id,
                    "proposer_id": p.proposer_id,
                    "issue_values": p.issue_values,
                    "utility": p.utility,
                }
                for p in session.history.proposals
            ],
        }

        consensus_data = None
        if session.consensus_proposal:
            consensus_data = {
                "proposal_id": session.consensus_proposal.proposal_id,
                "proposer_id": session.consensus_proposal.proposer_id,
                "issue_values": session.consensus_proposal.issue_values,
                "utility": session.consensus_proposal.utility,
            }

        record = PersistedSession(
            session_id=session.session_id,
            topic=session.topic,
            status=session.status.value if hasattr(session.status, 'value') else str(session.status),
            phase=session.phase.value if hasattr(session.phase, 'value') else str(session.phase),
            agents_snapshot=agents_snapshot,
            issues_snapshot=issues_snapshot,
            history_snapshot=history_snapshot,
            consensus_proposal=consensus_data,
            metadata=session.metadata,
        )
        logger.info(f"SessionSerializer: session {session.session_id[:8]} serialized")
        return record

    @staticmethod
    def serialize_proposal(session_id: str, proposal: Any, accepted: bool = False) -> PersistedProposal:
        """序列化提案"""
        record = PersistedProposal(
            session_id=session_id,
            proposal_id=proposal.proposal_id,
            proposer_id=proposal.proposer_id,
            issue_values=proposal.issue_values,
            utility=proposal.utility,
            timestamp=proposal.timestamp,
            accepted=accepted,
        )
        logger.debug(f"SessionSerializer: proposal {proposal.proposal_id[:8]} serialized")
        return record


class NegotiationPersistenceService:
    """协商持久化服务"""

    def __init__(self, backend: Optional[PersistenceBackend] = None,
                 storage_type: StorageType = StorageType.MEMORY,
                 base_dir: str = "/tmp/negotiation_persistence"):
        if backend:
            self.backend = backend
        elif storage_type == StorageType.FILE:
            self.backend = FilePersistenceBackend(base_dir)
        else:
            self.backend = MemoryPersistenceBackend()
        self.serializer = SessionSerializer()
        logger.info(f"NegotiationPersistenceService initialized with {type(self.backend).__name__}")

    def save_session(self, session: Any) -> bool:
        """保存协商会话"""
        record = self.serializer.serialize_session(session)
        result = self.backend.save_session(record)

        # 同时保存所有提案
        for proposal in session.history.proposals:
            accepted = proposal in session.history.accepted_proposals
            proposal_record = self.serializer.serialize_proposal(
                session.session_id, proposal, accepted
            )
            self.backend.save_proposal(proposal_record)

        logger.info(f"PersistenceService: session {session.session_id[:8]} saved (result={result})")
        return result

    def load_session(self, session_id: str) -> Optional[PersistedSession]:
        """加载协商会话"""
        return self.backend.load_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """删除协商会话"""
        return self.backend.delete_session(session_id)

    def list_sessions(self) -> List[PersistedSession]:
        """列出所有会话"""
        return self.backend.list_sessions()

    def load_proposals(self, session_id: str) -> List[PersistedProposal]:
        """加载会话的所有提案"""
        return self.backend.load_proposals(session_id)

    def recover_session(self, session_id: str) -> Optional[Any]:
        """恢复协商会话为可操作对象"""
        from src.architecture.negotiation_engine import (
            NegotiationSession, NegotiationAgent, NegotiationIssue,
            NegotiationProposal, NegotiationHistory, NegotiationStatus,
            NegotiationPhase, NegotiationStrategy, MessageType
        )

        record = self.backend.load_session(session_id)
        if not record:
            logger.warning(f"PersistenceService: cannot recover session {session_id[:8]}, not found")
            return None

        # 重建Agent
        agents = {}
        for agent_data in record.agents_snapshot:
            issues = []
            for issue_data in agent_data.get("issues", []):
                issues.append(NegotiationIssue(
                    name=issue_data["name"],
                    priority=issue_data.get("priority", 1.0),
                    possible_values=issue_data.get("possible_values", []),
                ))
            strategy_str = agent_data.get("strategy", "collaborative")
            try:
                strategy = NegotiationStrategy(strategy_str)
            except ValueError:
                strategy = NegotiationStrategy.COLLABORATIVE

            agent = NegotiationAgent(
                agent_id=agent_data["agent_id"],
                name=agent_data.get("name", ""),
                role=agent_data.get("role", ""),
                strategy=strategy,
                issues=issues,
            )
            agents[agent.agent_id] = agent

        # 重建议题
        issues = []
        for issue_data in record.issues_snapshot:
            issues.append(NegotiationIssue(
                name=issue_data["name"],
                priority=issue_data.get("priority", 1.0),
                possible_values=issue_data.get("possible_values", []),
                current_value=issue_data.get("current_value"),
            ))

        # 重建历史
        history = NegotiationHistory()
        for proposal_data in record.history_snapshot.get("proposals", []):
            proposal = NegotiationProposal(
                proposal_id=proposal_data.get("proposal_id", str(uuid.uuid4())),
                proposer_id=proposal_data.get("proposer_id", ""),
                issue_values=proposal_data.get("issue_values", {}),
                utility=proposal_data.get("utility", 0.0),
            )
            history.add_proposal(proposal)

        # 重建会话
        try:
            status = NegotiationStatus(record.status)
        except ValueError:
            status = NegotiationStatus.PENDING

        try:
            phase = NegotiationPhase(record.phase)
        except ValueError:
            phase = NegotiationPhase.INITIALIZATION

        session = NegotiationSession(
            session_id=record.session_id,
            topic=record.topic,
            status=status,
            phase=phase,
            history=history,
            metadata=record.metadata,
        )

        for agent_id, agent in agents.items():
            session.agents[agent_id] = agent

        for issue in issues:
            session.issues.append(issue)

        # 恢复共识提案
        if record.consensus_proposal:
            consensus = NegotiationProposal(
                proposal_id=record.consensus_proposal.get("proposal_id", ""),
                proposer_id=record.consensus_proposal.get("proposer_id", ""),
                issue_values=record.consensus_proposal.get("issue_values", {}),
                utility=record.consensus_proposal.get("utility", 0.0),
            )
            session.consensus_proposal = consensus

        logger.info(f"PersistenceService: session {session_id[:8]} recovered successfully")
        return session

    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """获取会话历史摘要"""
        record = self.backend.load_session(session_id)
        if not record:
            return {"error": "Session not found"}

        proposals = self.backend.load_proposals(session_id)

        return {
            "session_id": session_id,
            "topic": record.topic,
            "status": record.status,
            "phase": record.phase,
            "agent_count": len(record.agents_snapshot),
            "issue_count": len(record.issues_snapshot),
            "total_proposals": len(proposals),
            "accepted_proposals": sum(1 for p in proposals if p.accepted),
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def replay_session(self, session_id: str) -> List[Dict[str, Any]]:
        """回放会话提案历史"""
        proposals = self.backend.load_proposals(session_id)
        replay = []
        for p in sorted(proposals, key=lambda x: x.timestamp):
            replay.append({
                "proposal_id": p.proposal_id,
                "proposer_id": p.proposer_id,
                "issue_values": p.issue_values,
                "utility": p.utility,
                "accepted": p.accepted,
                "timestamp": p.timestamp,
            })
        logger.info(f"PersistenceService: replayed {len(replay)} proposals for session {session_id[:8]}")
        return replay


_global_persistence_service: Optional[NegotiationPersistenceService] = None


def get_persistence_service() -> NegotiationPersistenceService:
    """获取全局持久化服务"""
    global _global_persistence_service
    if _global_persistence_service is None:
        _global_persistence_service = NegotiationPersistenceService()
    return _global_persistence_service


def reset_persistence_service() -> None:
    """重置全局持久化服务"""
    global _global_persistence_service
    _global_persistence_service = None
