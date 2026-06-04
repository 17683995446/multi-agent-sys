"""
合同网协议任务竞标分发系统
职责：任务发布、Agent竞标、评标分发、合同管理
"""

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict


class TaskState(str, Enum):
    """任务状态"""
    PUBLISHED = "published"
    BIDDING = "bidding"
    EVALUATING = "evaluating"
    AWARDED = "awarded"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BidStatus(str, Enum):
    """竞标状态"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ContractorStatus(str, Enum):
    """承包商状态"""
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"


@dataclass
class TaskRequirement:
    """任务需求"""
    requirement_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_required: List[str] = field(default_factory=list)
    estimated_time: float = 0.0
    budget: float = 0.0
    priority: int = 1
    deadline: Optional[float] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskAnnouncement:
    """任务公告"""
    announcement_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    task_name: str = ""
    requirements: TaskRequirement = None
    state: TaskState = TaskState.PUBLISHED
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    publisher_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = TaskRequirement()


@dataclass
class Bid:
    """竞标"""
    bid_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    announcement_id: str = ""
    contractor_id: str = ""
    contractor_name: str = ""
    proposed_price: float = 0.0
    proposed_time: float = 0.0
    capability_score: float = 0.0
    experience_score: float = 0.0
    bid_message: str = ""
    status: BidStatus = BidStatus.PENDING
    submitted_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_total_score(self) -> float:
        """计算综合评分"""
        price_score = max(0, 1 - (self.proposed_price / 1000))
        time_score = max(0, 1 - (self.proposed_time / 100))
        return (
            self.capability_score * 0.3 +
            self.experience_score * 0.2 +
            price_score * 0.2 +
            time_score * 0.3
        )


@dataclass
class Contract:
    """合同"""
    contract_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    announcement_id: str = ""
    contractor_id: str = ""
    contractor_name: str = ""
    bid: Bid = None
    agreed_price: float = 0.0
    agreed_time: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class Contractor:
    """承包商/Agent"""
    contractor_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    skills: List[str] = field(default_factory=list)
    capabilities: Dict[str, float] = field(default_factory=dict)
    experience_level: float = 0.0
    current_workload: int = 0
    max_workload: int = 5
    status: ContractorStatus = ContractorStatus.AVAILABLE
    completed_tasks: int = 0
    success_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def can_accept_task(self) -> bool:
        """是否可以接受任务"""
        return (
            self.status == ContractorStatus.AVAILABLE and
            self.current_workload < self.max_workload
        )
    
    def has_skill(self, skill: str) -> bool:
        """是否具备某项技能"""
        return skill in self.skills
    
    def calculate_capability_score(self, required_skills: List[str]) -> float:
        """计算能力评分"""
        if not required_skills:
            return 1.0
        
        matched_skills = sum(1 for skill in required_skills if self.has_skill(skill))
        skill_score = matched_skills / len(required_skills)
        
        capability_score = sum(
            self.capabilities.get(skill, 0.0) 
            for skill in required_skills if skill in self.capabilities
        ) / len(required_skills) if required_skills else 0
        
        return (skill_score * 0.5 + capability_score * 0.5)


class ContractNetProtocol:
    """合同网协议核心"""
    
    def __init__(self):
        self.announcements: Dict[str, TaskAnnouncement] = {}
        self.bids: Dict[str, List[Bid]] = defaultdict(list)
        self.contracts: Dict[str, Contract] = {}
        self.contractors: Dict[str, Contractor] = {}
        self.task_publishers: Dict[str, str] = {}
        
    def register_contractor(self, name: str, skills: List[str], 
                          max_workload: int = 5) -> Contractor:
        """注册承包商"""
        contractor = Contractor(
            name=name,
            skills=skills,
            max_workload=max_workload
        )
        self.contractors[contractor.contractor_id] = contractor
        return contractor
    
    def get_contractor(self, contractor_id: str) -> Optional[Contractor]:
        """获取承包商"""
        return self.contractors.get(contractor_id)
    
    def publish_task(self, task_id: str, task_name: str, 
                    requirements: TaskRequirement,
                    publisher_id: str = "") -> TaskAnnouncement:
        """发布任务"""
        announcement = TaskAnnouncement(
            task_id=task_id,
            task_name=task_name,
            requirements=requirements,
            publisher_id=publisher_id,
            deadline=requirements.deadline
        )
        self.announcements[announcement.announcement_id] = announcement
        self.task_publishers[announcement.announcement_id] = publisher_id
        return announcement
    
    def get_announcement(self, announcement_id: str) -> Optional[TaskAnnouncement]:
        """获取任务公告"""
        return self.announcements.get(announcement_id)
    
    def submit_bid(self, announcement_id: str, contractor_id: str,
                  proposed_price: float, proposed_time: float,
                  bid_message: str = "") -> Optional[Bid]:
        """提交竞标"""
        announcement = self.announcements.get(announcement_id)
        contractor = self.contractors.get(contractor_id)
        
        if not announcement or not contractor:
            return None
        
        if not contractor.can_accept_task():
            return None
        
        capability_score = contractor.calculate_capability_score(
            announcement.requirements.skill_required
        )
        
        bid = Bid(
            announcement_id=announcement_id,
            contractor_id=contractor_id,
            contractor_name=contractor.name,
            proposed_price=proposed_price,
            proposed_time=proposed_time,
            capability_score=capability_score,
            experience_score=contractor.experience_level,
            bid_message=bid_message
        )
        
        self.bids[announcement_id].append(bid)
        return bid
    
    def get_bids(self, announcement_id: str) -> List[Bid]:
        """获取某任务的全部竞标"""
        return self.bids.get(announcement_id, [])
    
    def evaluate_bids(self, announcement_id: str, 
                     evaluation_method: str = "comprehensive") -> List[Bid]:
        """评标"""
        bids = self.get_bids(announcement_id)
        if not bids:
            return []
        
        if evaluation_method == "comprehensive":
            scored_bids = [(bid, bid.calculate_total_score()) for bid in bids]
        elif evaluation_method == "price":
            scored_bids = [
                (bid, max(0, 1 - bid.proposed_price / 1000)) 
                for bid in bids
            ]
        elif evaluation_method == "time":
            scored_bids = [
                (bid, max(0, 1 - bid.proposed_time / 100)) 
                for bid in bids
            ]
        elif evaluation_method == "capability":
            scored_bids = [(bid, bid.capability_score) for bid in bids]
        else:
            scored_bids = [(bid, bid.calculate_total_score()) for bid in bids]
        
        scored_bids.sort(key=lambda x: x[1], reverse=True)
        return [bid for bid, _ in scored_bids]
    
    def award_contract(self, announcement_id: str, contractor_id: str,
                      agreed_price: float, agreed_time: float) -> Optional[Contract]:
        """授予合同"""
        announcement = self.announcements.get(announcement_id)
        contractor = self.contractors.get(contractor_id)
        
        if not announcement or not contractor:
            return None
        
        bids = self.get_bids(announcement_id)
        winning_bid = None
        for bid in bids:
            if bid.contractor_id == contractor_id:
                bid.status = BidStatus.ACCEPTED
                winning_bid = bid
            else:
                bid.status = BidStatus.REJECTED
        
        contract = Contract(
            announcement_id=announcement_id,
            contractor_id=contractor_id,
            contractor_name=contractor.name,
            bid=winning_bid,
            agreed_price=agreed_price,
            agreed_time=agreed_time,
            start_time=time.time()
        )
        
        self.contracts[contract.contract_id] = contract
        announcement.state = TaskState.AWARDED
        
        contractor.current_workload += 1
        if contractor.current_workload >= contractor.max_workload:
            contractor.status = ContractorStatus.BUSY
        
        return contract
    
    def auto_award_best_bid(self, announcement_id: str) -> Optional[Contract]:
        """自动授予最优竞标"""
        best_bids = self.evaluate_bids(announcement_id)
        if not best_bids:
            return None
        
        best_bid = best_bids[0]
        return self.award_contract(
            announcement_id,
            best_bid.contractor_id,
            best_bid.proposed_price,
            best_bid.proposed_time
        )
    
    def complete_contract(self, contract_id: str, 
                         result: Optional[Dict[str, Any]] = None) -> bool:
        """完成任务"""
        contract = self.contracts.get(contract_id)
        if not contract:
            return False
        
        contractor = self.contractors.get(contract.contractor_id)
        if contractor:
            contractor.current_workload -= 1
            if contractor.current_workload < contractor.max_workload:
                contractor.status = ContractorStatus.AVAILABLE
            contractor.completed_tasks += 1
            if result and result.get("success"):
                contractor.success_rate = (
                    (contractor.success_rate * (contractor.completed_tasks - 1) + 1) /
                    contractor.completed_tasks
                )
            else:
                contractor.success_rate = (
                    (contractor.success_rate * (contractor.completed_tasks - 1)) /
                    contractor.completed_tasks
                )
        
        contract.end_time = time.time()
        contract.status = "completed"
        contract.result = result
        
        announcement = self.announcements.get(contract.announcement_id)
        if announcement:
            announcement.state = TaskState.COMPLETED
        
        return True
    
    def cancel_announcement(self, announcement_id: str) -> bool:
        """取消任务公告"""
        announcement = self.announcements.get(announcement_id)
        if not announcement:
            return False
        
        announcement.state = TaskState.CANCELLED
        
        for bid in self.bids.get(announcement_id, []):
            bid.status = BidStatus.WITHDRAWN
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_announcements = len(self.announcements)
        total_bids = sum(len(bids) for bids in self.bids.values())
        total_contracts = len(self.contracts)
        completed_contracts = sum(
            1 for c in self.contracts.values() 
            if c.status == "completed"
        )
        
        return {
            "total_announcements": total_announcements,
            "total_bids": total_bids,
            "total_contracts": total_contracts,
            "completed_contracts": completed_contracts,
            "total_contractors": len(self.contractors),
            "avg_bids_per_task": total_bids / total_announcements if total_announcements > 0 else 0
        }


class ContractNetService:
    """合同网服务"""
    
    def __init__(self):
        self.protocol = ContractNetProtocol()
        self.task_history: Dict[str, List[Dict]] = defaultdict(list)
    
    def register_agent_as_contractor(self, agent_id: str, name: str,
                                   skills: List[str]) -> Contractor:
        """注册Agent为承包商"""
        contractor = self.protocol.register_contractor(name, skills)
        contractor.metadata["agent_id"] = agent_id
        return contractor
    
    def publish_and_bid_flow(self, task_id: str, task_name: str,
                           requirements: TaskRequirement,
                           publisher_id: str = "") -> Tuple[Optional[TaskAnnouncement], List[Bid]]:
        """发布任务并收集竞标"""
        announcement = self.protocol.publish_task(
            task_id, task_name, requirements, publisher_id
        )
        
        capable_contractors = [
            c for c in self.protocol.contractors.values()
            if all(c.has_skill(skill) for skill in requirements.skill_required)
        ]
        
        bids = []
        for contractor in capable_contractors:
            bid = self.protocol.submit_bid(
                announcement.announcement_id,
                contractor.contractor_id,
                requirements.budget,
                requirements.estimated_time
            )
            if bid:
                bids.append(bid)
        
        announcement.state = TaskState.BIDDING
        return announcement, bids
    
    def full_auction_flow(self, task_id: str, task_name: str,
                          requirements: TaskRequirement,
                          publisher_id: str = "") -> Optional[Contract]:
        """完整拍卖流程"""
        announcement, bids = self.publish_and_bid_flow(
            task_id, task_name, requirements, publisher_id
        )
        
        if not bids:
            return None
        
        announcement.state = TaskState.EVALUATING
        
        contract = self.protocol.auto_award_best_bid(announcement.announcement_id)
        
        if contract:
            self.task_history[task_id].append({
                "type": "contract_awarded",
                "contract_id": contract.contract_id,
                "contractor": contract.contractor_name,
                "timestamp": time.time()
            })
        
        return contract
    
    def complete_task_flow(self, contract_id: str, 
                          success: bool = True,
                          message: str = "") -> bool:
        """完成任务流程"""
        result = {
            "success": success,
            "message": message,
            "timestamp": time.time()
        }
        return self.protocol.complete_contract(contract_id, result)
    
    def get_agent_performance(self, contractor_id: str) -> Optional[Dict[str, Any]]:
        """获取Agent性能"""
        contractor = self.protocol.get_contractor(contractor_id)
        if not contractor:
            return None
        
        return {
            "contractor_id": contractor_id,
            "name": contractor.name,
            "completed_tasks": contractor.completed_tasks,
            "success_rate": contractor.success_rate,
            "current_workload": contractor.current_workload,
            "status": contractor.status.value,
            "skills": contractor.skills
        }


_global_cnp_service: Optional[ContractNetService] = None


def get_cnp_service() -> ContractNetService:
    """获取全局合同网服务"""
    global _global_cnp_service
    if _global_cnp_service is None:
        _global_cnp_service = ContractNetService()
    return _global_cnp_service


def reset_cnp_service() -> None:
    """重置全局合同网服务"""
    global _global_cnp_service
    _global_cnp_service = None
