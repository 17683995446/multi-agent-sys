"""
阶段59验收测试：架构争议协商分支
"""

import pytest
from src.architecture.pipeline_dispute import (
    DisputeType,
    DisputeStatus,
    DisputeRecord,
    DisputeNegotiator,
    ArchitectureMediator,
    DisputePipeline,
)


class TestDisputeType:
    """测试争议类型枚举"""

    def test_type_values(self):
        """测试争议类型枚举值"""
        assert DisputeType.ARCHITECTURE.value == "architecture"
        assert DisputeType.TECHNOLOGY.value == "technology"
        assert DisputeType.PRIORITY.value == "priority"
        assert DisputeType.RESOURCE.value == "resource"
        assert DisputeType.DESIGN.value == "design"

    def test_all_types(self):
        """测试所有类型"""
        types = list(DisputeType)
        assert len(types) == 5


class TestDisputeStatus:
    """测试争议状态枚举"""

    def test_status_values(self):
        """测试争议状态枚举值"""
        assert DisputeStatus.RAISED.value == "raised"
        assert DisputeStatus.NEGOTIATING.value == "negotiating"
        assert DisputeStatus.RESOLVED.value == "resolved"
        assert DisputeStatus.ESCALATED.value == "escalated"
        assert DisputeStatus.ABANDONED.value == "abandoned"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(DisputeStatus)
        assert len(statuses) == 5


class TestDisputeRecord:
    """测试争议记录"""

    def test_default_creation(self):
        """测试默认创建"""
        record = DisputeRecord()
        assert record.dispute_id != ""
        assert record.dispute_type == DisputeType.ARCHITECTURE
        assert record.description == ""
        assert record.parties == []
        assert record.status == DisputeStatus.RAISED
        assert record.resolution == ""
        assert record.timestamp > 0

    def test_custom_creation(self):
        """测试自定义创建"""
        record = DisputeRecord(
            dispute_type=DisputeType.TECHNOLOGY,
            description="技术选型争议",
            parties=["团队A", "团队B"],
            status=DisputeStatus.NEGOTIATING,
            resolution="已解决",
        )
        assert record.dispute_type == DisputeType.TECHNOLOGY
        assert record.description == "技术选型争议"
        assert record.parties == ["团队A", "团队B"]
        assert record.status == DisputeStatus.NEGOTIATING
        assert record.resolution == "已解决"

    def test_dispute_id_unique(self):
        """测试争议ID唯一性"""
        r1 = DisputeRecord()
        r2 = DisputeRecord()
        assert r1.dispute_id != r2.dispute_id


class TestDisputeNegotiator:
    """测试争议协商器"""

    def test_initialization(self):
        """测试初始化"""
        negotiator = DisputeNegotiator()
        assert len(negotiator.disputes) == 0

    def test_raise_dispute(self):
        """测试发起争议"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.ARCHITECTURE,
            description="微服务与单体架构争议",
            parties=["团队A", "团队B"],
        )
        assert record.dispute_id in negotiator.disputes
        assert record.dispute_type == DisputeType.ARCHITECTURE
        assert record.status == DisputeStatus.RAISED
        assert record.parties == ["团队A", "团队B"]

    def test_raise_dispute_no_parties(self):
        """测试发起争议无参与方"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.RESOURCE,
            description="资源分配争议",
        )
        assert record.parties == []

    def test_negotiate(self):
        """测试开始协商"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.TECHNOLOGY,
            description="技术栈争议",
        )
        result = negotiator.negotiate(record.dispute_id)
        assert result is not None
        assert result.status == DisputeStatus.NEGOTIATING

    def test_negotiate_nonexistent(self):
        """测试协商不存在的争议"""
        negotiator = DisputeNegotiator()
        result = negotiator.negotiate("nonexistent")
        assert result is None

    def test_resolve(self):
        """测试解决争议"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.PRIORITY,
            description="优先级争议",
        )
        negotiator.negotiate(record.dispute_id)
        result = negotiator.resolve(record.dispute_id, "采用MoSCoW方法")
        assert result is not None
        assert result.status == DisputeStatus.RESOLVED
        assert result.resolution == "采用MoSCoW方法"

    def test_resolve_nonexistent(self):
        """测试解决不存在的争议"""
        negotiator = DisputeNegotiator()
        result = negotiator.resolve("nonexistent", "方案")
        assert result is None

    def test_resolve_already_resolved(self):
        """测试解决已解决的争议"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.DESIGN,
            description="设计争议",
        )
        negotiator.negotiate(record.dispute_id)
        negotiator.resolve(record.dispute_id, "方案A")
        result = negotiator.resolve(record.dispute_id, "方案B")
        assert result is not None
        assert result.status == DisputeStatus.RESOLVED
        assert result.resolution == "方案A"

    def test_escalate(self):
        """测试升级争议"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.ARCHITECTURE,
            description="架构争议",
        )
        result = negotiator.escalate(record.dispute_id)
        assert result is not None
        assert result.status == DisputeStatus.ESCALATED

    def test_escalate_nonexistent(self):
        """测试升级不存在的争议"""
        negotiator = DisputeNegotiator()
        result = negotiator.escalate("nonexistent")
        assert result is None

    def test_escalate_resolved_dispute(self):
        """测试升级已解决的争议"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.TECHNOLOGY,
            description="技术争议",
        )
        negotiator.negotiate(record.dispute_id)
        negotiator.resolve(record.dispute_id, "方案")
        result = negotiator.escalate(record.dispute_id)
        assert result is not None
        assert result.status == DisputeStatus.RESOLVED

    def test_get_dispute(self):
        """测试获取争议记录"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.RESOURCE,
            description="资源争议",
        )
        result = negotiator.get_dispute(record.dispute_id)
        assert result is not None
        assert result.dispute_id == record.dispute_id

    def test_get_dispute_nonexistent(self):
        """测试获取不存在的争议记录"""
        negotiator = DisputeNegotiator()
        result = negotiator.get_dispute("nonexistent")
        assert result is None

    def test_negotiate_from_negotiating(self):
        """测试从协商状态继续协商"""
        negotiator = DisputeNegotiator()
        record = negotiator.raise_dispute(
            dispute_type=DisputeType.DESIGN,
            description="设计争议",
        )
        negotiator.negotiate(record.dispute_id)
        result = negotiator.negotiate(record.dispute_id)
        assert result is not None
        assert result.status == DisputeStatus.NEGOTIATING


class TestArchitectureMediator:
    """测试架构调解器"""

    def test_initialization(self):
        """测试初始化"""
        mediator = ArchitectureMediator()
        assert len(mediator.compromise_proposals) == 0
        assert len(mediator.evaluations) == 0
        assert len(mediator.recommendations) == 0

    def test_mediate_architecture(self):
        """测试调解架构争议"""
        mediator = ArchitectureMediator()
        dispute = DisputeRecord(
            dispute_type=DisputeType.ARCHITECTURE,
            description="架构争议",
            parties=["团队A", "团队B"],
        )
        result = mediator.mediate(dispute)
        assert result is not None
        assert result["dispute_id"] == dispute.dispute_id
        assert len(result["suggestions"]) > 0

    def test_mediate_technology(self):
        """测试调解技术争议"""
        mediator = ArchitectureMediator()
        dispute = DisputeRecord(
            dispute_type=DisputeType.TECHNOLOGY,
            description="技术争议",
        )
        result = mediator.mediate(dispute)
        assert result is not None
        assert len(result["suggestions"]) > 0

    def test_mediate_priority(self):
        """测试调解优先级争议"""
        mediator = ArchitectureMediator()
        dispute = DisputeRecord(
            dispute_type=DisputeType.PRIORITY,
            description="优先级争议",
        )
        result = mediator.mediate(dispute)
        assert result is not None
        assert len(result["suggestions"]) > 0

    def test_mediate_resource(self):
        """测试调解资源争议"""
        mediator = ArchitectureMediator()
        dispute = DisputeRecord(
            dispute_type=DisputeType.RESOURCE,
            description="资源争议",
        )
        result = mediator.mediate(dispute)
        assert result is not None
        assert len(result["suggestions"]) > 0

    def test_mediate_design(self):
        """测试调解设计争议"""
        mediator = ArchitectureMediator()
        dispute = DisputeRecord(
            dispute_type=DisputeType.DESIGN,
            description="设计争议",
        )
        result = mediator.mediate(dispute)
        assert result is not None
        assert len(result["suggestions"]) > 0

    def test_propose_compromise(self):
        """测试提出折中方案"""
        mediator = ArchitectureMediator()
        result = mediator.propose_compromise(
            dispute_id="test-id",
            options=["方案A", "方案B", "方案C"],
        )
        assert result is not None
        assert result["compromise"] != ""
        assert "方案A" in result["compromise"]

    def test_propose_compromise_empty_options(self):
        """测试提出折中方案空选项"""
        mediator = ArchitectureMediator()
        result = mediator.propose_compromise(
            dispute_id="test-id",
            options=[],
        )
        assert result is not None
        assert result["compromise"] == "无可用方案"

    def test_evaluate_options(self):
        """测试评估选项"""
        mediator = ArchitectureMediator()
        options = [
            {"feasibility": 0.8, "impact": 0.9, "cost_efficiency": 0.7},
            {"feasibility": 0.6, "impact": 0.5, "cost_efficiency": 0.9},
        ]
        result = mediator.evaluate_options("test-id", options)
        assert result is not None
        assert "scores" in result
        assert result["best_option"] == "option_0"

    def test_evaluate_options_empty(self):
        """测试评估空选项"""
        mediator = ArchitectureMediator()
        result = mediator.evaluate_options("test-id", [])
        assert result is not None
        assert result["best_option"] == ""

    def test_recommend_solution_with_evaluation(self):
        """测试根据评估推荐解决方案"""
        mediator = ArchitectureMediator()
        evaluation = {"best_option": "option_1"}
        result = mediator.recommend_solution("test-id", evaluation)
        assert result == "option_1"

    def test_recommend_solution_without_evaluation(self):
        """测试无评估时推荐解决方案"""
        mediator = ArchitectureMediator()
        result = mediator.recommend_solution("test-id")
        assert result == "协商解决"

    def test_recommend_solution_with_prior_evaluation(self):
        """测试有先前评估时推荐解决方案"""
        mediator = ArchitectureMediator()
        mediator.evaluate_options("test-id", [
            {"feasibility": 0.9, "impact": 0.8, "cost_efficiency": 0.7},
        ])
        result = mediator.recommend_solution("test-id")
        assert result == "option_0"


class TestDisputePipeline:
    """测试争议流水线"""

    def test_initialization(self):
        """测试初始化"""
        pipeline = DisputePipeline()
        assert pipeline.negotiator is not None
        assert pipeline.mediator is not None
        assert len(pipeline.history) == 0

    def test_process_dispute_architecture(self):
        """测试处理架构争议"""
        pipeline = DisputePipeline()
        record = pipeline.process_dispute(
            dispute_type=DisputeType.ARCHITECTURE,
            description="微服务与单体架构争议",
            parties=["团队A", "团队B"],
        )
        assert record is not None
        assert record.status == DisputeStatus.RESOLVED
        assert record.resolution != ""

    def test_process_dispute_technology(self):
        """测试处理技术争议"""
        pipeline = DisputePipeline()
        record = pipeline.process_dispute(
            dispute_type=DisputeType.TECHNOLOGY,
            description="React vs Vue选型",
        )
        assert record is not None
        assert record.status == DisputeStatus.RESOLVED

    def test_process_dispute_priority(self):
        """测试处理优先级争议"""
        pipeline = DisputePipeline()
        record = pipeline.process_dispute(
            dispute_type=DisputeType.PRIORITY,
            description="功能优先级争议",
        )
        assert record is not None
        assert record.status == DisputeStatus.RESOLVED

    def test_process_dispute_resource(self):
        """测试处理资源争议"""
        pipeline = DisputePipeline()
        record = pipeline.process_dispute(
            dispute_type=DisputeType.RESOURCE,
            description="服务器资源分配争议",
        )
        assert record is not None
        assert record.status == DisputeStatus.RESOLVED

    def test_process_dispute_design(self):
        """测试处理设计争议"""
        pipeline = DisputePipeline()
        record = pipeline.process_dispute(
            dispute_type=DisputeType.DESIGN,
            description="UI设计方案争议",
        )
        assert record is not None
        assert record.status == DisputeStatus.RESOLVED

    def test_get_resolution(self):
        """测试获取解决方案"""
        pipeline = DisputePipeline()
        record = pipeline.process_dispute(
            dispute_type=DisputeType.ARCHITECTURE,
            description="架构争议",
        )
        resolution = pipeline.get_resolution(record.dispute_id)
        assert resolution is not None
        assert resolution != ""

    def test_get_resolution_nonexistent(self):
        """测试获取不存在的争议解决方案"""
        pipeline = DisputePipeline()
        resolution = pipeline.get_resolution("nonexistent")
        assert resolution is None

    def test_get_resolution_unresolved(self):
        """测试获取未解决争议的解决方案"""
        pipeline = DisputePipeline()
        record = pipeline.negotiator.raise_dispute(
            dispute_type=DisputeType.DESIGN,
            description="设计争议",
        )
        resolution = pipeline.get_resolution(record.dispute_id)
        assert resolution is None

    def test_get_dispute_history(self):
        """测试获取争议历史"""
        pipeline = DisputePipeline()
        pipeline.process_dispute(
            dispute_type=DisputeType.ARCHITECTURE,
            description="架构争议",
        )
        pipeline.process_dispute(
            dispute_type=DisputeType.TECHNOLOGY,
            description="技术争议",
        )
        history = pipeline.get_dispute_history()
        assert len(history) == 2

    def test_get_dispute_history_filtered(self):
        """测试按类型获取争议历史"""
        pipeline = DisputePipeline()
        pipeline.process_dispute(
            dispute_type=DisputeType.ARCHITECTURE,
            description="架构争议",
        )
        pipeline.process_dispute(
            dispute_type=DisputeType.TECHNOLOGY,
            description="技术争议",
        )
        history = pipeline.get_dispute_history(dispute_type=DisputeType.ARCHITECTURE)
        assert len(history) == 1
        assert history[0]["dispute_type"] == "architecture"

    def test_get_dispute_history_empty(self):
        """测试空争议历史"""
        pipeline = DisputePipeline()
        history = pipeline.get_dispute_history()
        assert len(history) == 0

    def test_full_dispute_workflow(self):
        """测试完整争议工作流"""
        pipeline = DisputePipeline()

        # 1. 处理争议
        record = pipeline.process_dispute(
            dispute_type=DisputeType.TECHNOLOGY,
            description="数据库选型争议",
            parties=["后端团队", "DBA团队"],
        )

        # 2. 验证解决
        assert record.status == DisputeStatus.RESOLVED

        # 3. 获取解决方案
        resolution = pipeline.get_resolution(record.dispute_id)
        assert resolution is not None

        # 4. 查看历史
        history = pipeline.get_dispute_history()
        assert len(history) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
