"""
架构争议协商分支
职责：争议管理、协商调解、方案评估、推荐决策

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DisputeType(str, Enum):
    """争议类型"""
    ARCHITECTURE = "architecture"
    TECHNOLOGY = "technology"
    PRIORITY = "priority"
    RESOURCE = "resource"
    DESIGN = "design"


class DisputeStatus(str, Enum):
    """争议状态"""
    RAISED = "raised"
    NEGOTIATING = "negotiating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    ABANDONED = "abandoned"


@dataclass
class DisputeRecord:
    """争议记录"""
    dispute_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dispute_type: DisputeType = DisputeType.ARCHITECTURE
    description: str = ""
    parties: List[str] = field(default_factory=list)
    status: DisputeStatus = DisputeStatus.RAISED
    resolution: str = ""
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"DisputeRecord created: id={self.dispute_id}, "
                     f"type={self.dispute_type.value}, status={self.status.value}")


class DisputeNegotiator:
    """争议协商器"""

    def __init__(self):
        """初始化争议协商器"""
        self.disputes: Dict[str, DisputeRecord] = {}
        logger.info("DisputeNegotiator initialized")

    def raise_dispute(self, dispute_type: DisputeType, description: str,
                      parties: Optional[List[str]] = None) -> DisputeRecord:
        """发起争议"""
        logger.info(f"DisputeNegotiator: raising dispute type={dispute_type.value}, "
                    f"description={description[:30]}")
        try:
            record = DisputeRecord(
                dispute_type=dispute_type,
                description=description,
                parties=parties or [],
                status=DisputeStatus.RAISED,
            )
            self.disputes[record.dispute_id] = record
            logger.info(f"DisputeNegotiator: dispute raised id={record.dispute_id}")
        except Exception as e:
            logger.error(f"DisputeNegotiator: raise_dispute failed: {e}")
            raise
        return record

    def negotiate(self, dispute_id: str) -> Optional[DisputeRecord]:
        """开始协商"""
        logger.info(f"DisputeNegotiator: negotiating dispute_id={dispute_id}")
        if dispute_id not in self.disputes:
            logger.warning(f"DisputeNegotiator: dispute_id={dispute_id} not found")
            return None

        try:
            record = self.disputes[dispute_id]
            if record.status not in (DisputeStatus.RAISED, DisputeStatus.NEGOTIATING):
                logger.warning(f"DisputeNegotiator: dispute_id={dispute_id} "
                               f"status={record.status.value} cannot negotiate")
                return record

            record.status = DisputeStatus.NEGOTIATING
            logger.info(f"DisputeNegotiator: dispute_id={dispute_id} now negotiating")
        except Exception as e:
            logger.error(f"DisputeNegotiator: negotiate failed: {e}")
            return None

        return record

    def resolve(self, dispute_id: str, resolution: str) -> Optional[DisputeRecord]:
        """解决争议"""
        logger.info(f"DisputeNegotiator: resolving dispute_id={dispute_id}")
        if dispute_id not in self.disputes:
            logger.warning(f"DisputeNegotiator: dispute_id={dispute_id} not found")
            return None

        try:
            record = self.disputes[dispute_id]
            if record.status in (DisputeStatus.RESOLVED, DisputeStatus.ABANDONED):
                logger.warning(f"DisputeNegotiator: dispute_id={dispute_id} "
                               f"status={record.status.value} cannot resolve")
                return record

            record.status = DisputeStatus.RESOLVED
            record.resolution = resolution
            logger.info(f"DisputeNegotiator: dispute_id={dispute_id} resolved")
        except Exception as e:
            logger.error(f"DisputeNegotiator: resolve failed: {e}")
            return None

        return record

    def escalate(self, dispute_id: str) -> Optional[DisputeRecord]:
        """升级争议"""
        logger.info(f"DisputeNegotiator: escalating dispute_id={dispute_id}")
        if dispute_id not in self.disputes:
            logger.warning(f"DisputeNegotiator: dispute_id={dispute_id} not found")
            return None

        try:
            record = self.disputes[dispute_id]
            if record.status in (DisputeStatus.RESOLVED, DisputeStatus.ABANDONED):
                logger.warning(f"DisputeNegotiator: dispute_id={dispute_id} "
                               f"status={record.status.value} cannot escalate")
                return record

            record.status = DisputeStatus.ESCALATED
            logger.info(f"DisputeNegotiator: dispute_id={dispute_id} escalated")
        except Exception as e:
            logger.error(f"DisputeNegotiator: escalate failed: {e}")
            return None

        return record

    def get_dispute(self, dispute_id: str) -> Optional[DisputeRecord]:
        """获取争议记录"""
        logger.debug(f"DisputeNegotiator: getting dispute_id={dispute_id}")
        record = self.disputes.get(dispute_id)
        if record is None:
            logger.warning(f"DisputeNegotiator: dispute_id={dispute_id} not found")
        return record


class ArchitectureMediator:
    """架构调解器"""

    def __init__(self):
        """初始化架构调解器"""
        self.compromise_proposals: Dict[str, Dict[str, Any]] = {}
        self.evaluations: Dict[str, Dict[str, Any]] = {}
        self.recommendations: Dict[str, str] = {}
        logger.info("ArchitectureMediator initialized")

    def mediate(self, dispute: DisputeRecord) -> Optional[Dict[str, Any]]:
        """调解争议"""
        logger.info(f"ArchitectureMediator: mediating dispute_id={dispute.dispute_id}, "
                    f"type={dispute.dispute_type.value}")
        try:
            mediation_result: Dict[str, Any] = {
                "dispute_id": dispute.dispute_id,
                "dispute_type": dispute.dispute_type.value,
                "parties": dispute.parties,
                "action": "mediate",
                "suggestions": [],
            }

            if dispute.dispute_type == DisputeType.ARCHITECTURE:
                mediation_result["suggestions"] = [
                    "采用分层架构折中方案",
                    "引入适配器模式解耦",
                    "使用微服务边界划分",
                ]
            elif dispute.dispute_type == DisputeType.TECHNOLOGY:
                mediation_result["suggestions"] = [
                    "进行技术原型验证",
                    "评估团队技术栈熟悉度",
                    "考虑长期维护成本",
                ]
            elif dispute.dispute_type == DisputeType.PRIORITY:
                mediation_result["suggestions"] = [
                    "基于业务价值排序",
                    "使用MoSCoW优先级法",
                    "引入利益相关方投票",
                ]
            elif dispute.dispute_type == DisputeType.RESOURCE:
                mediation_result["suggestions"] = [
                    "重新评估资源分配",
                    "考虑外部资源引入",
                    "优化现有资源利用率",
                ]
            elif dispute.dispute_type == DisputeType.DESIGN:
                mediation_result["suggestions"] = [
                    "采用设计模式折中",
                    "进行用户体验测试",
                    "参考行业最佳实践",
                ]

            self.compromise_proposals[dispute.dispute_id] = mediation_result
            logger.info(f"ArchitectureMediator: mediation done for "
                        f"dispute_id={dispute.dispute_id}")
        except Exception as e:
            logger.error(f"ArchitectureMediator: mediate failed: {e}")
            return None

        return mediation_result

    def propose_compromise(self, dispute_id: str,
                          options: List[str]) -> Optional[Dict[str, Any]]:
        """提出折中方案"""
        logger.info(f"ArchitectureMediator: proposing compromise for "
                    f"dispute_id={dispute_id}, options={len(options)}")
        try:
            compromise: Dict[str, Any] = {
                "dispute_id": dispute_id,
                "action": "compromise",
                "options": options,
                "compromise": "",
            }

            if options:
                compromise["compromise"] = f"综合方案: {', '.join(options[:2])}"
            else:
                compromise["compromise"] = "无可用方案"

            self.compromise_proposals[dispute_id] = compromise
            logger.info(f"ArchitectureMediator: compromise proposed for "
                        f"dispute_id={dispute_id}")
        except Exception as e:
            logger.error(f"ArchitectureMediator: propose_compromise failed: {e}")
            return None

        return compromise

    def evaluate_options(self, dispute_id: str,
                        options: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """评估选项"""
        logger.info(f"ArchitectureMediator: evaluating options for "
                    f"dispute_id={dispute_id}, count={len(options)}")
        try:
            evaluation: Dict[str, Any] = {
                "dispute_id": dispute_id,
                "action": "evaluate",
                "scores": {},
                "best_option": "",
            }

            for i, option in enumerate(options):
                score = 0.0
                if isinstance(option, dict):
                    score += option.get("feasibility", 0) * 0.3
                    score += option.get("impact", 0) * 0.4
                    score += option.get("cost_efficiency", 0) * 0.3
                evaluation["scores"][f"option_{i}"] = round(score, 2)

            if evaluation["scores"]:
                best = max(evaluation["scores"], key=lambda k: evaluation["scores"][k])
                evaluation["best_option"] = best

            self.evaluations[dispute_id] = evaluation
            logger.info(f"ArchitectureMediator: evaluation done for "
                        f"dispute_id={dispute_id}, best={evaluation['best_option']}")
        except Exception as e:
            logger.error(f"ArchitectureMediator: evaluate_options failed: {e}")
            return None

        return evaluation

    def recommend_solution(self, dispute_id: str,
                           evaluation: Optional[Dict[str, Any]] = None) -> str:
        """推荐解决方案"""
        logger.info(f"ArchitectureMediator: recommending solution for "
                    f"dispute_id={dispute_id}")
        try:
            if evaluation and evaluation.get("best_option"):
                recommendation = evaluation["best_option"]
            elif dispute_id in self.evaluations:
                recommendation = self.evaluations[dispute_id].get("best_option", "协商解决")
            elif dispute_id in self.compromise_proposals:
                proposal = self.compromise_proposals[dispute_id]
                recommendation = proposal.get("compromise", "协商解决")
            else:
                recommendation = "协商解决"

            self.recommendations[dispute_id] = recommendation
            logger.info(f"ArchitectureMediator: recommendation={recommendation} "
                        f"for dispute_id={dispute_id}")
        except Exception as e:
            logger.error(f"ArchitectureMediator: recommend_solution failed: {e}")
            return "协商解决"

        return recommendation


class DisputePipeline:
    """争议流水线"""

    def __init__(self):
        """初始化争议流水线"""
        self.negotiator = DisputeNegotiator()
        self.mediator = ArchitectureMediator()
        self.history: List[Dict[str, Any]] = []
        logger.info("DisputePipeline initialized")

    def process_dispute(self, dispute_type: DisputeType, description: str,
                        parties: Optional[List[str]] = None) -> Optional[DisputeRecord]:
        """处理争议：发起→协商→调解→解决"""
        logger.info(f"DisputePipeline: processing dispute type={dispute_type.value}")
        try:
            # 1. 发起争议
            record = self.negotiator.raise_dispute(dispute_type, description, parties)
            if record is None:
                logger.error("DisputePipeline: failed to raise dispute")
                return None

            # 2. 开始协商
            record = self.negotiator.negotiate(record.dispute_id)
            if record is None:
                logger.error("DisputePipeline: failed to negotiate")
                return record

            # 3. 调解
            mediation = self.mediator.mediate(record)
            if mediation is None:
                logger.warning("DisputePipeline: mediation failed, escalating")
                self.negotiator.escalate(record.dispute_id)
            else:
                # 4. 推荐解决方案
                recommendation = self.mediator.recommend_solution(record.dispute_id)
                # 5. 解决争议
                record = self.negotiator.resolve(record.dispute_id, recommendation)

            # 记录历史
            self.history.append({
                "dispute_id": record.dispute_id if record else "",
                "dispute_type": dispute_type.value,
                "action": "process",
                "timestamp": time.time(),
            })

            logger.info(f"DisputePipeline: dispute processed, "
                        f"status={record.status.value if record else 'N/A'}")
        except Exception as e:
            logger.error(f"DisputePipeline: process_dispute failed: {e}")
            return None

        return record

    def get_resolution(self, dispute_id: str) -> Optional[str]:
        """获取争议解决方案"""
        logger.debug(f"DisputePipeline: getting resolution for dispute_id={dispute_id}")
        record = self.negotiator.get_dispute(dispute_id)
        if record is None:
            logger.warning(f"DisputePipeline: no dispute for dispute_id={dispute_id}")
            return None

        if record.status == DisputeStatus.RESOLVED:
            logger.debug(f"DisputePipeline: resolution={record.resolution}")
            return record.resolution

        logger.debug(f"DisputePipeline: dispute not resolved, "
                     f"status={record.status.value}")
        return None

    def get_dispute_history(self, dispute_type: Optional[DisputeType] = None) -> List[Dict[str, Any]]:
        """获取争议历史"""
        logger.debug(f"DisputePipeline: getting dispute history, "
                     f"filter_type={dispute_type}")
        if dispute_type is None:
            logger.debug(f"DisputePipeline: returning {len(self.history)} history records")
            return self.history

        filtered = [h for h in self.history if h.get("dispute_type") == dispute_type.value]
        logger.debug(f"DisputePipeline: returning {len(filtered)} filtered history records")
        return filtered
