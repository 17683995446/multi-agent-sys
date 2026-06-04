"""
阶段48验收测试：分布式协商与一致性协议
"""

import pytest
import time

from src.architecture.distributed_consensus import (
    NodeRole, NodeStatus,
    ClusterNode, VoteRequest, VoteResponse, LogEntry,
    ConsensusLog, RaftNode, DistributedConsensusService,
    get_consensus_service, reset_consensus_service
)


class TestNodeRole:
    """测试节点角色枚举"""

    def test_role_values(self):
        """测试角色枚举值"""
        assert NodeRole.LEADER.value == "leader"
        assert NodeRole.FOLLOWER.value == "follower"
        assert NodeRole.CANDIDATE.value == "candidate"

    def test_role_from_string(self):
        """测试从字符串创建角色"""
        assert NodeRole("leader") == NodeRole.LEADER
        assert NodeRole("follower") == NodeRole.FOLLOWER
        assert NodeRole("candidate") == NodeRole.CANDIDATE


class TestNodeStatus:
    """测试节点状态枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        assert NodeStatus.ONLINE.value == "online"
        assert NodeStatus.OFFLINE.value == "offline"
        assert NodeStatus.SUSPECTED.value == "suspected"


class TestClusterNode:
    """测试集群节点"""

    def test_default_creation(self):
        """测试默认创建"""
        node = ClusterNode()
        assert node.node_id != ""
        assert node.name == ""
        assert node.role == NodeRole.FOLLOWER
        assert node.status == NodeStatus.ONLINE
        assert node.address == ""
        assert node.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        node = ClusterNode(
            node_id="n1",
            name="node-1",
            role=NodeRole.LEADER,
            status=NodeStatus.ONLINE,
            address="127.0.0.1:8080",
            metadata={"region": "us-east"},
        )
        assert node.node_id == "n1"
        assert node.name == "node-1"
        assert node.role == NodeRole.LEADER
        assert node.address == "127.0.0.1:8080"
        assert node.metadata["region"] == "us-east"


class TestVoteRequest:
    """测试投票请求"""

    def test_default_creation(self):
        """测试默认创建"""
        req = VoteRequest()
        assert req.term == 0
        assert req.candidate_id == ""
        assert req.last_log_index == -1

    def test_custom_creation(self):
        """测试自定义创建"""
        req = VoteRequest(term=3, candidate_id="c1", last_log_index=5)
        assert req.term == 3
        assert req.candidate_id == "c1"
        assert req.last_log_index == 5


class TestVoteResponse:
    """测试投票响应"""

    def test_default_creation(self):
        """测试默认创建"""
        resp = VoteResponse()
        assert resp.term == 0
        assert resp.vote_granted == False
        assert resp.voter_id == ""

    def test_granted_response(self):
        """测试同意投票响应"""
        resp = VoteResponse(term=2, vote_granted=True, voter_id="v1")
        assert resp.vote_granted == True
        assert resp.voter_id == "v1"


class TestLogEntry:
    """测试日志条目"""

    def test_default_creation(self):
        """测试默认创建"""
        entry = LogEntry()
        assert entry.term == 0
        assert entry.index == 0
        assert entry.command is None
        assert entry.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        entry = LogEntry(term=1, index=3, command="SET x=1")
        assert entry.term == 1
        assert entry.index == 3
        assert entry.command == "SET x=1"


class TestConsensusLog:
    """测试一致性日志"""

    def test_initial_state(self):
        """测试初始状态"""
        log = ConsensusLog()
        assert len(log.entries) == 0
        assert log.last_index() == -1
        assert log.last_term() == 0

    def test_append_entry(self):
        """测试追加日志条目"""
        log = ConsensusLog()
        entry = log.append_entry(term=1, command="cmd1")
        assert entry.term == 1
        assert entry.index == 0
        assert entry.command == "cmd1"
        assert log.last_index() == 0
        assert log.last_term() == 1

    def test_append_multiple_entries(self):
        """测试追加多个日志条目"""
        log = ConsensusLog()
        log.append_entry(term=1, command="cmd1")
        log.append_entry(term=1, command="cmd2")
        log.append_entry(term=2, command="cmd3")

        assert log.last_index() == 2
        assert log.last_term() == 2
        assert len(log.entries) == 3

    def test_get_entry(self):
        """测试获取日志条目"""
        log = ConsensusLog()
        log.append_entry(term=1, command="cmd1")
        log.append_entry(term=2, command="cmd2")

        entry = log.get_entry(0)
        assert entry is not None
        assert entry.command == "cmd1"

        entry = log.get_entry(1)
        assert entry is not None
        assert entry.command == "cmd2"

    def test_get_entry_out_of_range(self):
        """测试获取越界索引"""
        log = ConsensusLog()
        assert log.get_entry(-1) is None
        assert log.get_entry(0) is None
        assert log.get_entry(100) is None

    def test_append_invalid_term(self):
        """测试追加无效任期"""
        log = ConsensusLog()
        with pytest.raises(ValueError):
            log.append_entry(term=-1, command="cmd")

    def test_get_entries_from(self):
        """测试从指定索引获取日志"""
        log = ConsensusLog()
        log.append_entry(term=1, command="cmd0")
        log.append_entry(term=1, command="cmd1")
        log.append_entry(term=2, command="cmd2")

        entries = log.get_entries_from(1)
        assert len(entries) == 2
        assert entries[0].command == "cmd1"
        assert entries[1].command == "cmd2"

    def test_get_entries_from_invalid(self):
        """测试从无效索引获取日志"""
        log = ConsensusLog()
        log.append_entry(term=1, command="cmd0")
        assert log.get_entries_from(-1) == []
        assert log.get_entries_from(10) == []

    def test_truncate_after(self):
        """测试截断日志"""
        log = ConsensusLog()
        log.append_entry(term=1, command="cmd0")
        log.append_entry(term=1, command="cmd1")
        log.append_entry(term=2, command="cmd2")

        removed = log.truncate_after(0)
        assert removed == 2
        assert len(log.entries) == 1
        assert log.last_index() == 0


class TestRaftNode:
    """测试Raft节点"""

    def test_initial_state(self):
        """测试初始状态"""
        node = RaftNode(node_id="n1", name="test-node")
        assert node.node_id == "n1"
        assert node.name == "test-node"
        assert node.role == NodeRole.FOLLOWER
        assert node.current_term == 0
        assert node.voted_for is None
        assert node.commit_index == -1
        assert node.last_applied == -1

    def test_become_leader(self):
        """测试成为领导者"""
        node = RaftNode(node_id="n1")
        node.become_leader()
        assert node.role == NodeRole.LEADER

    def test_become_leader_idempotent(self):
        """测试重复成为领导者"""
        node = RaftNode(node_id="n1")
        node.become_leader()
        node.become_leader()  # 不应报错
        assert node.role == NodeRole.LEADER

    def test_become_follower(self):
        """测试成为跟随者"""
        node = RaftNode(node_id="n1")
        node.become_leader()
        node.become_follower(term=5)
        assert node.role == NodeRole.FOLLOWER
        assert node.current_term == 5
        assert node.voted_for is None

    def test_become_candidate(self):
        """测试成为候选人"""
        node = RaftNode(node_id="n1")
        term = node.become_candidate()
        assert node.role == NodeRole.CANDIDATE
        assert node.current_term == 1
        assert node.voted_for == "n1"
        assert "n1" in node.votes_received
        assert term == 1

    def test_request_vote(self):
        """测试创建投票请求"""
        node = RaftNode(node_id="n1")
        node.become_candidate()
        request = node.request_vote()
        assert request.candidate_id == "n1"
        assert request.term == 1
        assert request.last_log_index == -1

    def test_handle_vote_response_granted(self):
        """测试处理投票同意响应"""
        node = RaftNode(node_id="n1")
        node.become_candidate()
        response = VoteResponse(term=1, vote_granted=True, voter_id="n2")
        result = node.handle_vote_response(response)
        assert result == True
        assert "n2" in node.votes_received

    def test_handle_vote_response_rejected(self):
        """测试处理投票拒绝响应"""
        node = RaftNode(node_id="n1")
        node.become_candidate()
        response = VoteResponse(term=1, vote_granted=False, voter_id="n2")
        result = node.handle_vote_response(response)
        assert result == False

    def test_handle_vote_response_higher_term(self):
        """测试处理更高任期的投票响应"""
        node = RaftNode(node_id="n1")
        node.become_candidate()
        response = VoteResponse(term=10, vote_granted=False, voter_id="n2")
        node.handle_vote_response(response)
        assert node.role == NodeRole.FOLLOWER
        assert node.current_term == 10

    def test_respond_to_vote_request_grant(self):
        """测试同意投票请求"""
        node = RaftNode(node_id="n1")
        request = VoteRequest(term=1, candidate_id="n2", last_log_index=-1)
        response = node.respond_to_vote_request(request)
        assert response.vote_granted == True
        assert node.voted_for == "n2"

    def test_respond_to_vote_request_stale_term(self):
        """测试拒绝过期任期的投票请求"""
        node = RaftNode(node_id="n1")
        node.current_term = 5
        request = VoteRequest(term=3, candidate_id="n2", last_log_index=-1)
        response = node.respond_to_vote_request(request)
        assert response.vote_granted == False

    def test_respond_to_vote_request_already_voted(self):
        """测试已投票后拒绝其他候选人"""
        node = RaftNode(node_id="n1")
        node.voted_for = "n2"
        request = VoteRequest(term=0, candidate_id="n3", last_log_index=-1)
        response = node.respond_to_vote_request(request)
        assert response.vote_granted == False

    def test_append_entries_from_leader(self):
        """测试接受领导者的日志追加"""
        node = RaftNode(node_id="n1")
        entries = [LogEntry(term=1, index=0, command="cmd1")]
        result = node.append_entries(
            term=1, leader_id="leader",
            prev_log_index=-1, prev_log_term=0,
            entries=entries, leader_commit=-1,
        )
        assert result == True
        assert len(node.log.entries) == 1

    def test_append_entries_stale_term(self):
        """测试拒绝过期任期的日志追加"""
        node = RaftNode(node_id="n1")
        node.current_term = 5
        entries = [LogEntry(term=1, index=0, command="cmd1")]
        result = node.append_entries(
            term=3, leader_id="leader",
            prev_log_index=-1, prev_log_term=0,
            entries=entries, leader_commit=-1,
        )
        assert result == False

    def test_append_entries_log_mismatch(self):
        """测试日志不匹配时拒绝追加"""
        node = RaftNode(node_id="n1")
        node.log.append_entry(term=1, command="old")
        entries = [LogEntry(term=2, index=1, command="new")]
        result = node.append_entries(
            term=2, leader_id="leader",
            prev_log_index=0, prev_log_term=99,  # 不匹配
            entries=entries, leader_commit=-1,
        )
        assert result == False

    def test_append_entries_updates_commit(self):
        """测试日志追加更新提交索引"""
        node = RaftNode(node_id="n1")
        entries = [LogEntry(term=1, index=0, command="cmd1")]
        node.append_entries(
            term=1, leader_id="leader",
            prev_log_index=-1, prev_log_term=0,
            entries=entries, leader_commit=0,
        )
        assert node.commit_index == 0


class TestDistributedConsensusService:
    """测试分布式一致性服务"""

    def setup_method(self):
        reset_consensus_service()

    def test_initial_state(self):
        """测试初始状态"""
        service = DistributedConsensusService()
        assert len(service.nodes) == 0
        assert service.leader_id is None

    def test_create_cluster(self):
        """测试创建集群"""
        service = DistributedConsensusService()
        nodes = service.create_cluster(node_count=3)
        assert len(nodes) == 3
        assert len(service.nodes) == 3
        assert len(service.cluster_nodes) == 3

    def test_create_cluster_invalid(self):
        """测试创建无效集群"""
        service = DistributedConsensusService()
        with pytest.raises(ValueError):
            service.create_cluster(node_count=0)

    def test_add_node(self):
        """测试添加节点"""
        service = DistributedConsensusService()
        node = service.add_node(name="extra-node", address="127.0.0.1:9090")
        assert node.name == "extra-node"
        assert len(service.nodes) == 1
        cluster_node = service.cluster_nodes[node.node_id]
        assert cluster_node.address == "127.0.0.1:9090"

    def test_remove_node(self):
        """测试移除节点"""
        service = DistributedConsensusService()
        nodes = service.create_cluster(node_count=3)
        node_id = nodes[0].node_id
        result = service.remove_node(node_id)
        assert result == True
        assert len(service.nodes) == 2

    def test_remove_nonexistent_node(self):
        """测试移除不存在的节点"""
        service = DistributedConsensusService()
        result = service.remove_node("nonexistent")
        assert result == False

    def test_elect_leader(self):
        """测试领导者选举"""
        service = DistributedConsensusService()
        service.create_cluster(node_count=3)
        leader_id = service.elect_leader()
        assert leader_id is not None
        assert service.nodes[leader_id].role == NodeRole.LEADER

    def test_elect_leader_no_nodes(self):
        """测试无节点时选举"""
        service = DistributedConsensusService()
        leader_id = service.elect_leader()
        assert leader_id is None

    def test_elect_leader_updates_cluster_nodes(self):
        """测试选举后更新集群节点角色"""
        service = DistributedConsensusService()
        service.create_cluster(node_count=3)
        leader_id = service.elect_leader()
        assert leader_id is not None
        for nid, cn in service.cluster_nodes.items():
            if nid == leader_id:
                assert cn.role == NodeRole.LEADER
            else:
                assert cn.role == NodeRole.FOLLOWER

    def test_replicate_entry(self):
        """测试日志复制"""
        service = DistributedConsensusService()
        service.create_cluster(node_count=3)
        service.elect_leader()
        result = service.replicate_entry("SET x=1")
        assert result == True

    def test_replicate_entry_no_leader(self):
        """测试无领导者时复制"""
        service = DistributedConsensusService()
        service.create_cluster(node_count=3)
        result = service.replicate_entry("SET x=1")
        assert result == False

    def test_get_cluster_status(self):
        """测试获取集群状态"""
        service = DistributedConsensusService()
        service.create_cluster(node_count=3)
        service.elect_leader()
        status = service.get_cluster_status()
        assert status["total_nodes"] == 3
        assert status["leader_id"] is not None
        assert len(status["nodes"]) == 3

    def test_get_cluster_status_empty(self):
        """测试空集群状态"""
        service = DistributedConsensusService()
        status = service.get_cluster_status()
        assert status["total_nodes"] == 0
        assert status["leader_id"] is None

    def test_remove_leader_resets_leader_id(self):
        """测试移除领导者后重置leader_id"""
        service = DistributedConsensusService()
        service.create_cluster(node_count=3)
        leader_id = service.elect_leader()
        assert leader_id is not None
        service.remove_node(leader_id)
        assert service.leader_id is None

    def test_global_service(self):
        """测试全局服务"""
        service1 = get_consensus_service()
        service2 = get_consensus_service()
        assert service1 is service2
        reset_consensus_service()
        service3 = get_consensus_service()
        assert service3 is not service1
