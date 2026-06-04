"""
分布式协商与一致性协议
职责：Raft一致性算法实现、集群节点管理、领导者选举、日志复制
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class NodeRole(str, Enum):
    """节点角色"""
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"


class NodeStatus(str, Enum):
    """节点状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    SUSPECTED = "suspected"


@dataclass
class ClusterNode:
    """集群节点"""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: NodeRole = NodeRole.FOLLOWER
    status: NodeStatus = NodeStatus.ONLINE
    address: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"ClusterNode created: id={self.node_id}, name={self.name}, role={self.role}")


@dataclass
class VoteRequest:
    """投票请求"""
    term: int = 0
    candidate_id: str = ""
    last_log_index: int = -1

    def __post_init__(self):
        logger.debug(f"VoteRequest created: term={self.term}, candidate={self.candidate_id}")


@dataclass
class VoteResponse:
    """投票响应"""
    term: int = 0
    vote_granted: bool = False
    voter_id: str = ""

    def __post_init__(self):
        logger.debug(f"VoteResponse: voter={self.voter_id}, granted={self.vote_granted}")


@dataclass
class LogEntry:
    """日志条目"""
    term: int = 0
    index: int = 0
    command: Any = None
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"LogEntry created: term={self.term}, index={self.index}")


class ConsensusLog:
    """一致性日志"""

    def __init__(self):
        self.entries: List[LogEntry] = []
        logger.info("ConsensusLog initialized")

    def append_entry(self, term: int, command: Any) -> LogEntry:
        """追加日志条目"""
        # 输入验证
        if term < 0:
            logger.warning(f"append_entry: invalid term={term}")
            raise ValueError(f"term不能为负数: {term}")

        # 业务逻辑
        try:
            index = len(self.entries)
            entry = LogEntry(term=term, index=index, command=command)
            self.entries.append(entry)
            logger.info(f"ConsensusLog: appended entry term={term}, index={index}")
        except Exception as e:
            # 异常处理
            logger.error(f"ConsensusLog: append_entry failed: {e}")
            raise

        # 返回结果
        return entry

    def get_entry(self, index: int) -> Optional[LogEntry]:
        """获取指定索引的日志条目"""
        # 输入验证
        if index < 0 or index >= len(self.entries):
            logger.debug(f"ConsensusLog: get_entry index={index} out of range")
            return None

        # 业务逻辑 + 返回结果
        return self.entries[index]

    def last_index(self) -> int:
        """获取最后日志索引"""
        if not self.entries:
            return -1
        return len(self.entries) - 1

    def last_term(self) -> int:
        """获取最后日志任期"""
        if not self.entries:
            return 0
        return self.entries[-1].term

    def get_entries_from(self, start_index: int) -> List[LogEntry]:
        """获取从指定索引开始的所有日志条目"""
        # 输入验证
        if start_index < 0 or start_index >= len(self.entries):
            return []

        # 业务逻辑 + 返回结果
        return self.entries[start_index:]

    def truncate_after(self, index: int) -> int:
        """截断指定索引之后的日志条目"""
        # 输入验证
        if index < 0:
            return 0

        # 业务逻辑
        removed = len(self.entries) - index - 1
        self.entries = self.entries[:index + 1]
        logger.info(f"ConsensusLog: truncated after index={index}, removed={removed}")

        # 返回结果
        return max(0, removed)


class RaftNode:
    """Raft节点"""

    def __init__(self, node_id: str = "", name: str = ""):
        # 输入验证
        self.node_id = node_id or str(uuid.uuid4())
        self.name = name or self.node_id[:8]

        # 业务逻辑 - 初始化状态
        self.role: NodeRole = NodeRole.FOLLOWER
        self.current_term: int = 0
        self.voted_for: Optional[str] = None
        self.log: ConsensusLog = ConsensusLog()
        self.commit_index: int = -1
        self.last_applied: int = -1
        self.votes_received: List[str] = []
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}

        logger.info(f"RaftNode initialized: id={self.node_id}, name={self.name}")

    def become_leader(self) -> None:
        """转换为领导者"""
        # 输入验证
        if self.role == NodeRole.LEADER:
            logger.debug(f"Node {self.node_id[:8]}: already leader")
            return

        # 业务逻辑
        try:
            self.role = NodeRole.LEADER
            logger.info(f"Node {self.node_id[:8]}: became LEADER at term={self.current_term}")
        except Exception as e:
            # 异常处理
            logger.error(f"Node {self.node_id[:8]}: become_leader failed: {e}")
            raise

    def become_follower(self, term: int = 0) -> None:
        """转换为跟随者"""
        # 业务逻辑
        try:
            self.role = NodeRole.FOLLOWER
            if term > self.current_term:
                self.current_term = term
                self.voted_for = None
            logger.info(f"Node {self.node_id[:8]}: became FOLLOWER, term={self.current_term}")
        except Exception as e:
            # 异常处理
            logger.error(f"Node {self.node_id[:8]}: become_follower failed: {e}")
            raise

    def become_candidate(self) -> int:
        """转换为候选人并发起选举"""
        # 业务逻辑
        try:
            self.role = NodeRole.CANDIDATE
            self.current_term += 1
            self.voted_for = self.node_id
            self.votes_received = [self.node_id]
            logger.info(f"Node {self.node_id[:8]}: became CANDIDATE, term={self.current_term}")
        except Exception as e:
            # 异常处理
            logger.error(f"Node {self.node_id[:8]}: become_candidate failed: {e}")
            raise

        # 返回结果
        return self.current_term

    def request_vote(self) -> VoteRequest:
        """创建投票请求"""
        # 业务逻辑
        request = VoteRequest(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=self.log.last_index(),
        )
        logger.info(f"Node {self.node_id[:8]}: requesting vote, term={self.current_term}")

        # 返回结果
        return request

    def handle_vote_response(self, response: VoteResponse) -> bool:
        """处理投票响应"""
        # 输入验证
        if response.term > self.current_term:
            self.become_follower(response.term)
            logger.info(f"Node {self.node_id[:8]}: discovered higher term, reverting to follower")
            return False

        # 业务逻辑
        try:
            if response.vote_granted and self.role == NodeRole.CANDIDATE:
                if response.voter_id not in self.votes_received:
                    self.votes_received.append(response.voter_id)
                logger.info(f"Node {self.node_id[:8]}: vote granted by {response.voter_id[:8]}, "
                           f"total={len(self.votes_received)}")
                return True
            elif not response.vote_granted:
                logger.debug(f"Node {self.node_id[:8]}: vote rejected by {response.voter_id[:8]}")
        except Exception as e:
            # 异常处理
            logger.error(f"Node {self.node_id[:8]}: handle_vote_response failed: {e}")

        # 返回结果
        return False

    def respond_to_vote_request(self, request: VoteRequest) -> VoteResponse:
        """响应投票请求"""
        # 输入验证
        if request.term < self.current_term:
            logger.debug(f"Node {self.node_id[:8]}: rejecting stale vote request, "
                        f"request_term={request.term} < current_term={self.current_term}")
            return VoteResponse(term=self.current_term, vote_granted=False, voter_id=self.node_id)

        # 业务逻辑
        try:
            # 如果请求任期更高，转换为跟随者
            if request.term > self.current_term:
                self.become_follower(request.term)

            # 判断是否投票
            grant = False
            if self.voted_for is None or self.voted_for == request.candidate_id:
                # 检查日志是否至少一样新
                if request.last_log_index >= self.log.last_index():
                    self.voted_for = request.candidate_id
                    grant = True
                    logger.info(f"Node {self.node_id[:8]}: granting vote to {request.candidate_id[:8]}")
                else:
                    logger.debug(f"Node {self.node_id[:8]}: candidate log not up-to-date")
            else:
                logger.debug(f"Node {self.node_id[:8]}: already voted for {self.voted_for[:8]}")
        except Exception as e:
            # 异常处理
            logger.error(f"Node {self.node_id[:8]}: respond_to_vote_request failed: {e}")
            grant = False

        # 返回结果
        return VoteResponse(term=self.current_term, vote_granted=grant, voter_id=self.node_id)

    def append_entries(self, term: int, leader_id: str,
                       prev_log_index: int, prev_log_term: int,
                       entries: List[LogEntry],
                       leader_commit: int) -> bool:
        """追加日志条目（来自领导者的心跳/复制）"""
        # 输入验证
        if term < self.current_term:
            logger.debug(f"Node {self.node_id[:8]}: rejecting stale append_entries")
            return False

        # 业务逻辑
        try:
            # 如果任期更高，转换为跟随者
            if term > self.current_term:
                self.become_follower(term)

            # 确保自己是跟随者
            if self.role == NodeRole.CANDIDATE:
                self.become_follower(term)

            # 检查前一条日志是否匹配
            if prev_log_index >= 0:
                existing = self.log.get_entry(prev_log_index)
                if existing is None or existing.term != prev_log_term:
                    logger.debug(f"Node {self.node_id[:8]}: log mismatch at index={prev_log_index}")
                    return False

            # 追加新条目
            for entry in entries:
                existing = self.log.get_entry(entry.index)
                if existing is not None and existing.term != entry.term:
                    # 冲突：截断并替换
                    self.log.truncate_after(entry.index - 1)
                    self.log.append_entry(entry.term, entry.command)
                elif existing is None:
                    self.log.append_entry(entry.term, entry.command)

            # 更新提交索引
            if leader_commit > self.commit_index:
                self.commit_index = min(leader_commit, self.log.last_index())

            logger.info(f"Node {self.node_id[:8]}: appended {len(entries)} entries, "
                       f"commit_index={self.commit_index}")
        except Exception as e:
            # 异常处理
            logger.error(f"Node {self.node_id[:8]}: append_entries failed: {e}")
            return False

        # 返回结果
        return True


class DistributedConsensusService:
    """分布式一致性服务"""

    def __init__(self):
        self.nodes: Dict[str, RaftNode] = {}
        self.cluster_nodes: Dict[str, ClusterNode] = {}
        self.leader_id: Optional[str] = None
        logger.info("DistributedConsensusService initialized")

    def create_cluster(self, node_count: int = 3) -> List[RaftNode]:
        """创建集群"""
        # 输入验证
        if node_count < 1:
            logger.warning(f"create_cluster: invalid node_count={node_count}")
            raise ValueError(f"节点数量必须大于0: {node_count}")

        # 业务逻辑
        try:
            nodes = []
            for i in range(node_count):
                node = RaftNode(name=f"node-{i}")
                self.nodes[node.node_id] = node
                cluster_node = ClusterNode(
                    node_id=node.node_id,
                    name=node.name,
                    role=NodeRole.FOLLOWER,
                    status=NodeStatus.ONLINE,
                )
                self.cluster_nodes[node.node_id] = cluster_node
                nodes.append(node)

            logger.info(f"DistributedConsensusService: created cluster with {node_count} nodes")
        except Exception as e:
            # 异常处理
            logger.error(f"DistributedConsensusService: create_cluster failed: {e}")
            raise

        # 返回结果
        return nodes

    def add_node(self, name: str = "", address: str = "") -> RaftNode:
        """添加节点"""
        # 业务逻辑
        try:
            node = RaftNode(name=name or f"node-{len(self.nodes)}")
            self.nodes[node.node_id] = node
            cluster_node = ClusterNode(
                node_id=node.node_id,
                name=node.name,
                role=NodeRole.FOLLOWER,
                status=NodeStatus.ONLINE,
                address=address,
            )
            self.cluster_nodes[node.node_id] = cluster_node
            logger.info(f"DistributedConsensusService: added node {node.name}")
        except Exception as e:
            # 异常处理
            logger.error(f"DistributedConsensusService: add_node failed: {e}")
            raise

        # 返回结果
        return node

    def remove_node(self, node_id: str) -> bool:
        """移除节点"""
        # 输入验证
        if node_id not in self.nodes:
            logger.warning(f"DistributedConsensusService: node {node_id[:8]} not found")
            return False

        # 业务逻辑
        try:
            del self.nodes[node_id]
            if node_id in self.cluster_nodes:
                del self.cluster_nodes[node_id]
            if self.leader_id == node_id:
                self.leader_id = None
            logger.info(f"DistributedConsensusService: removed node {node_id[:8]}")
        except Exception as e:
            # 异常处理
            logger.error(f"DistributedConsensusService: remove_node failed: {e}")
            return False

        # 返回结果
        return True

    def elect_leader(self) -> Optional[str]:
        """执行领导者选举"""
        # 输入验证
        if not self.nodes:
            logger.warning("DistributedConsensusService: no nodes for election")
            return None

        # 业务逻辑
        try:
            # 选择第一个节点作为候选人
            candidate_id = list(self.nodes.keys())[0]
            candidate = self.nodes[candidate_id]
            term = candidate.become_candidate()
            vote_request = candidate.request_vote()

            # 收集投票
            granted_count = 1  # 自投一票
            for nid, node in self.nodes.items():
                if nid == candidate_id:
                    continue
                response = node.respond_to_vote_request(vote_request)
                candidate.handle_vote_response(response)
                if response.vote_granted:
                    granted_count += 1

            # 判断是否获得多数票
            majority = len(self.nodes) // 2 + 1
            if granted_count >= majority:
                candidate.become_leader()
                self.leader_id = candidate_id
                # 更新集群节点角色
                for nid, cluster_node in self.cluster_nodes.items():
                    if nid == candidate_id:
                        cluster_node.role = NodeRole.LEADER
                    else:
                        cluster_node.role = NodeRole.FOLLOWER
                logger.info(f"DistributedConsensusService: leader elected={candidate_id[:8]}, "
                           f"votes={granted_count}/{len(self.nodes)}")
            else:
                candidate.become_follower(term)
                logger.info(f"DistributedConsensusService: election failed, "
                           f"votes={granted_count}/{len(self.nodes)}")
        except Exception as e:
            # 异常处理
            logger.error(f"DistributedConsensusService: elect_leader failed: {e}")
            return None

        # 返回结果
        return self.leader_id

    def replicate_entry(self, command: Any) -> bool:
        """复制日志条目到集群"""
        # 输入验证
        if not self.leader_id or self.leader_id not in self.nodes:
            logger.warning("DistributedConsensusService: no leader for replication")
            return False

        # 业务逻辑
        try:
            leader = self.nodes[self.leader_id]
            entry = leader.log.append_entry(leader.current_term, command)

            success_count = 1  # 领导者自身
            for nid, node in self.nodes.items():
                if nid == self.leader_id:
                    continue

                # 简化的日志复制
                entries_to_send = [LogEntry(
                    term=entry.term,
                    index=entry.index,
                    command=entry.command,
                )]
                prev_log_index = entry.index - 1
                prev_log_term = 0
                if prev_log_index >= 0:
                    prev_entry = leader.log.get_entry(prev_log_index)
                    if prev_entry:
                        prev_log_term = prev_entry.term

                success = node.append_entries(
                    term=leader.current_term,
                    leader_id=leader.node_id,
                    prev_log_index=prev_log_index,
                    prev_log_term=prev_log_term,
                    entries=entries_to_send,
                    leader_commit=leader.commit_index,
                )
                if success:
                    success_count += 1

            # 多数确认后提交
            majority = len(self.nodes) // 2 + 1
            if success_count >= majority:
                leader.commit_index = entry.index
                logger.info(f"DistributedConsensusService: entry committed, "
                           f"index={entry.index}, replicated={success_count}/{len(self.nodes)}")
                return True
            else:
                logger.warning(f"DistributedConsensusService: entry not committed, "
                              f"replicated={success_count}/{len(self.nodes)}")
                return False
        except Exception as e:
            # 异常处理
            logger.error(f"DistributedConsensusService: replicate_entry failed: {e}")
            return False

    def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        # 业务逻辑
        try:
            status = {
                "total_nodes": len(self.nodes),
                "leader_id": self.leader_id,
                "nodes": {},
            }
            for nid, node in self.nodes.items():
                cluster_node = self.cluster_nodes.get(nid)
                status["nodes"][nid] = {
                    "name": node.name,
                    "role": node.role.value,
                    "status": cluster_node.status.value if cluster_node else NodeStatus.ONLINE.value,
                    "term": node.current_term,
                    "commit_index": node.commit_index,
                    "log_length": len(node.log.entries),
                }
            logger.debug(f"DistributedConsensusService: cluster status retrieved")
        except Exception as e:
            # 异常处理
            logger.error(f"DistributedConsensusService: get_cluster_status failed: {e}")
            return {"total_nodes": 0, "leader_id": None, "nodes": {}}

        # 返回结果
        return status


_global_consensus_service: Optional[DistributedConsensusService] = None


def get_consensus_service() -> DistributedConsensusService:
    """获取全局一致性服务"""
    global _global_consensus_service
    if _global_consensus_service is None:
        _global_consensus_service = DistributedConsensusService()
    return _global_consensus_service


def reset_consensus_service() -> None:
    """重置全局一致性服务"""
    global _global_consensus_service
    _global_consensus_service = None
