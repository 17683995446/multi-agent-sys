"""
阶段60验收测试：完整流水线100%闭环
"""

import pytest
from src.architecture.pipeline_full import (
    PipelineStage,
    PipelineStatus,
    StageResult,
    PipelineExecution,
    FullPipeline,
    PipelineOrchestrator,
)


class TestPipelineStage:
    """测试流水线阶段枚举"""

    def test_stage_values(self):
        """测试流水线阶段枚举值"""
        assert PipelineStage.REQUIREMENT.value == "requirement"
        assert PipelineStage.ARCHITECTURE.value == "architecture"
        assert PipelineStage.DEVELOPMENT.value == "development"
        assert PipelineStage.REVIEW.value == "review"
        assert PipelineStage.TESTING.value == "testing"
        assert PipelineStage.DOCUMENTATION.value == "documentation"
        assert PipelineStage.DEPLOYMENT.value == "deployment"

    def test_all_stages(self):
        """测试所有阶段"""
        stages = list(PipelineStage)
        assert len(stages) == 7


class TestPipelineStatus:
    """测试流水线状态枚举"""

    def test_status_values(self):
        """测试流水线状态枚举值"""
        assert PipelineStatus.IDLE.value == "idle"
        assert PipelineStatus.RUNNING.value == "running"
        assert PipelineStatus.PAUSED.value == "paused"
        assert PipelineStatus.COMPLETED.value == "completed"
        assert PipelineStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(PipelineStatus)
        assert len(statuses) == 5


class TestStageResult:
    """测试阶段结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = StageResult()
        assert result.stage == PipelineStage.REQUIREMENT
        assert result.status == PipelineStatus.IDLE
        assert result.output == {}
        assert result.duration == 0.0
        assert result.error == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        result = StageResult(
            stage=PipelineStage.DEVELOPMENT,
            status=PipelineStatus.COMPLETED,
            output={"modules": ["模块A"]},
            duration=1.5,
            error="",
        )
        assert result.stage == PipelineStage.DEVELOPMENT
        assert result.status == PipelineStatus.COMPLETED
        assert result.output == {"modules": ["模块A"]}
        assert result.duration == 1.5

    def test_failed_result(self):
        """测试失败结果"""
        result = StageResult(
            stage=PipelineStage.TESTING,
            status=PipelineStatus.FAILED,
            error="测试超时",
        )
        assert result.status == PipelineStatus.FAILED
        assert result.error == "测试超时"


class TestPipelineExecution:
    """测试流水线执行"""

    def test_default_creation(self):
        """测试默认创建"""
        execution = PipelineExecution()
        assert execution.execution_id != ""
        assert execution.stages == []
        assert execution.current_stage is None
        assert execution.status == PipelineStatus.IDLE
        assert execution.results == []
        assert execution.start_time == 0.0
        assert execution.end_time == 0.0

    def test_custom_creation(self):
        """测试自定义创建"""
        stages = [PipelineStage.REQUIREMENT, PipelineStage.ARCHITECTURE]
        execution = PipelineExecution(
            stages=stages,
            status=PipelineStatus.RUNNING,
            start_time=1000.0,
        )
        assert len(execution.stages) == 2
        assert execution.status == PipelineStatus.RUNNING
        assert execution.start_time == 1000.0

    def test_execution_id_unique(self):
        """测试执行ID唯一性"""
        e1 = PipelineExecution()
        e2 = PipelineExecution()
        assert e1.execution_id != e2.execution_id


class TestFullPipeline:
    """测试完整流水线"""

    def test_initialization(self):
        """测试初始化"""
        pipeline = FullPipeline()
        assert pipeline.status == PipelineStatus.IDLE
        assert len(pipeline.stages) == 0
        assert len(pipeline.results) == 0
        assert pipeline.current_stage is None

    def test_add_stage(self):
        """测试添加阶段"""
        pipeline = FullPipeline()
        result = pipeline.add_stage(PipelineStage.REQUIREMENT)
        assert result is True
        assert PipelineStage.REQUIREMENT in pipeline.stages

    def test_add_stage_duplicate(self):
        """测试添加重复阶段"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        result = pipeline.add_stage(PipelineStage.REQUIREMENT)
        assert result is False

    def test_add_multiple_stages(self):
        """测试添加多个阶段"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        pipeline.add_stage(PipelineStage.ARCHITECTURE)
        pipeline.add_stage(PipelineStage.DEVELOPMENT)
        assert len(pipeline.stages) == 3

    def test_remove_stage(self):
        """测试移除阶段"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        result = pipeline.remove_stage(PipelineStage.REQUIREMENT)
        assert result is True
        assert PipelineStage.REQUIREMENT not in pipeline.stages

    def test_remove_stage_not_found(self):
        """测试移除不存在的阶段"""
        pipeline = FullPipeline()
        result = pipeline.remove_stage(PipelineStage.DEPLOYMENT)
        assert result is False

    def test_run_empty_pipeline(self):
        """测试运行空流水线"""
        pipeline = FullPipeline()
        status = pipeline.run()
        assert status == PipelineStatus.FAILED

    def test_run_single_stage(self):
        """测试运行单阶段流水线"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        status = pipeline.run()
        assert status == PipelineStatus.COMPLETED
        assert len(pipeline.results) == 1

    def test_run_full_pipeline(self):
        """测试运行完整流水线"""
        pipeline = FullPipeline()
        for stage in PipelineStage:
            pipeline.add_stage(stage)
        status = pipeline.run()
        assert status == PipelineStatus.COMPLETED
        assert len(pipeline.results) == 7

    def test_run_partial_pipeline(self):
        """测试运行部分阶段流水线"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        pipeline.add_stage(PipelineStage.ARCHITECTURE)
        pipeline.add_stage(PipelineStage.DEVELOPMENT)
        status = pipeline.run()
        assert status == PipelineStatus.COMPLETED
        assert len(pipeline.results) == 3

    def test_get_status(self):
        """测试获取状态"""
        pipeline = FullPipeline()
        assert pipeline.get_status() == PipelineStatus.IDLE

    def test_get_status_after_run(self):
        """测试运行后获取状态"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        pipeline.run()
        assert pipeline.get_status() == PipelineStatus.COMPLETED

    def test_get_results(self):
        """测试获取结果"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        pipeline.add_stage(PipelineStage.ARCHITECTURE)
        pipeline.run()
        results = pipeline.get_results()
        assert len(results) == 2
        assert results[0].stage == PipelineStage.REQUIREMENT
        assert results[1].stage == PipelineStage.ARCHITECTURE

    def test_get_results_empty(self):
        """测试获取空结果"""
        pipeline = FullPipeline()
        results = pipeline.get_results()
        assert results == []

    def test_pause(self):
        """测试暂停流水线"""
        pipeline = FullPipeline()
        # 需要在运行中才能暂停，这里直接测试暂停逻辑
        pipeline.status = PipelineStatus.RUNNING
        result = pipeline.pause()
        assert result is True
        assert pipeline.status == PipelineStatus.PAUSED

    def test_pause_not_running(self):
        """测试非运行状态暂停"""
        pipeline = FullPipeline()
        result = pipeline.pause()
        assert result is False

    def test_resume(self):
        """测试恢复流水线"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        pipeline.add_stage(PipelineStage.ARCHITECTURE)
        pipeline.status = PipelineStatus.PAUSED
        pipeline._paused_at = PipelineStage.REQUIREMENT
        # 手动添加已完成的阶段结果
        pipeline.results = [
            StageResult(stage=PipelineStage.REQUIREMENT, status=PipelineStatus.COMPLETED)
        ]
        status = pipeline.resume()
        assert status == PipelineStatus.COMPLETED

    def test_resume_not_paused(self):
        """测试非暂停状态恢复"""
        pipeline = FullPipeline()
        status = pipeline.resume()
        assert status == PipelineStatus.IDLE

    def test_stage_result_output(self):
        """测试阶段结果输出"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        pipeline.run()
        results = pipeline.get_results()
        assert len(results) == 1
        assert "requirements" in results[0].output

    def test_architecture_stage_output(self):
        """测试架构阶段输出"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.ARCHITECTURE)
        pipeline.run()
        results = pipeline.get_results()
        assert "architecture" in results[0].output

    def test_development_stage_output(self):
        """测试开发阶段输出"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.DEVELOPMENT)
        pipeline.run()
        results = pipeline.get_results()
        assert "modules" in results[0].output

    def test_review_stage_output(self):
        """测试评审阶段输出"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REVIEW)
        pipeline.run()
        results = pipeline.get_results()
        assert "review_status" in results[0].output

    def test_testing_stage_output(self):
        """测试测试阶段输出"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.TESTING)
        pipeline.run()
        results = pipeline.get_results()
        assert "total" in results[0].output

    def test_documentation_stage_output(self):
        """测试文档阶段输出"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.DOCUMENTATION)
        pipeline.run()
        results = pipeline.get_results()
        assert "documents" in results[0].output

    def test_deployment_stage_output(self):
        """测试部署阶段输出"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.DEPLOYMENT)
        pipeline.run()
        results = pipeline.get_results()
        assert "environment" in results[0].output

    def test_run_already_running(self):
        """测试运行已在运行的流水线"""
        pipeline = FullPipeline()
        pipeline.add_stage(PipelineStage.REQUIREMENT)
        pipeline.status = PipelineStatus.RUNNING
        status = pipeline.run()
        assert status == PipelineStatus.RUNNING


class TestPipelineOrchestrator:
    """测试流水线编排器"""

    def test_initialization(self):
        """测试初始化"""
        orchestrator = PipelineOrchestrator()
        assert len(orchestrator.pipelines) == 0
        assert len(orchestrator.executions) == 0

    def test_create_pipeline(self):
        """测试创建流水线"""
        orchestrator = PipelineOrchestrator()
        pipeline = orchestrator.create_pipeline("pipeline-1")
        assert pipeline is not None
        assert "pipeline-1" in orchestrator.pipelines

    def test_create_pipeline_with_stages(self):
        """测试创建带阶段的流水线"""
        orchestrator = PipelineOrchestrator()
        stages = [PipelineStage.REQUIREMENT, PipelineStage.ARCHITECTURE]
        pipeline = orchestrator.create_pipeline("pipeline-2", stages=stages)
        assert pipeline is not None
        assert len(pipeline.stages) == 2

    def test_create_pipeline_duplicate(self):
        """测试创建重复流水线"""
        orchestrator = PipelineOrchestrator()
        orchestrator.create_pipeline("pipeline-1")
        pipeline = orchestrator.create_pipeline("pipeline-1")
        assert pipeline is None

    def test_execute(self):
        """测试执行流水线"""
        orchestrator = PipelineOrchestrator()
        stages = [PipelineStage.REQUIREMENT, PipelineStage.ARCHITECTURE]
        orchestrator.create_pipeline("pipeline-1", stages=stages)
        execution = orchestrator.execute("pipeline-1")
        assert execution is not None
        assert execution.status == PipelineStatus.COMPLETED

    def test_execute_nonexistent(self):
        """测试执行不存在的流水线"""
        orchestrator = PipelineOrchestrator()
        execution = orchestrator.execute("nonexistent")
        assert execution is None

    def test_execute_full_lifecycle(self):
        """测试执行完整生命周期"""
        orchestrator = PipelineOrchestrator()
        stages = list(PipelineStage)
        orchestrator.create_pipeline("full-lifecycle", stages=stages)
        execution = orchestrator.execute("full-lifecycle")
        assert execution is not None
        assert execution.status == PipelineStatus.COMPLETED
        assert len(execution.results) == 7

    def test_monitor(self):
        """测试监控流水线"""
        orchestrator = PipelineOrchestrator()
        stages = [PipelineStage.REQUIREMENT, PipelineStage.ARCHITECTURE]
        orchestrator.create_pipeline("pipeline-1", stages=stages)
        orchestrator.execute("pipeline-1")
        info = orchestrator.monitor("pipeline-1")
        assert info is not None
        assert info["status"] == "completed"
        assert info["total_stages"] == 2

    def test_monitor_nonexistent(self):
        """测试监控不存在的流水线"""
        orchestrator = PipelineOrchestrator()
        info = orchestrator.monitor("nonexistent")
        assert info is None

    def test_get_pipeline_status(self):
        """测试获取流水线状态"""
        orchestrator = PipelineOrchestrator()
        orchestrator.create_pipeline("pipeline-1")
        status = orchestrator.get_pipeline_status("pipeline-1")
        assert status == PipelineStatus.IDLE

    def test_get_pipeline_status_after_run(self):
        """测试运行后获取流水线状态"""
        orchestrator = PipelineOrchestrator()
        stages = [PipelineStage.REQUIREMENT]
        orchestrator.create_pipeline("pipeline-1", stages=stages)
        orchestrator.execute("pipeline-1")
        status = orchestrator.get_pipeline_status("pipeline-1")
        assert status == PipelineStatus.COMPLETED

    def test_get_pipeline_status_nonexistent(self):
        """测试获取不存在流水线的状态"""
        orchestrator = PipelineOrchestrator()
        status = orchestrator.get_pipeline_status("nonexistent")
        assert status is None

    def test_get_all_pipelines(self):
        """测试获取所有流水线"""
        orchestrator = PipelineOrchestrator()
        orchestrator.create_pipeline("pipeline-1")
        orchestrator.create_pipeline("pipeline-2")
        all_pipelines = orchestrator.get_all_pipelines()
        assert len(all_pipelines) == 2
        assert "pipeline-1" in all_pipelines
        assert "pipeline-2" in all_pipelines

    def test_get_all_pipelines_empty(self):
        """测试获取空流水线列表"""
        orchestrator = PipelineOrchestrator()
        all_pipelines = orchestrator.get_all_pipelines()
        assert len(all_pipelines) == 0

    def test_execution_record_stored(self):
        """测试执行记录存储"""
        orchestrator = PipelineOrchestrator()
        stages = [PipelineStage.REQUIREMENT]
        orchestrator.create_pipeline("pipeline-1", stages=stages)
        execution = orchestrator.execute("pipeline-1")
        assert execution is not None
        assert execution.execution_id in orchestrator.executions

    def test_multiple_executions(self):
        """测试多次执行"""
        orchestrator = PipelineOrchestrator()
        stages = [PipelineStage.REQUIREMENT]
        orchestrator.create_pipeline("pipeline-1", stages=stages)
        e1 = orchestrator.execute("pipeline-1")
        e2 = orchestrator.execute("pipeline-1")
        assert e1 is not None
        assert e2 is not None
        assert e1.execution_id != e2.execution_id

    def test_full_orchestration_workflow(self):
        """测试完整编排工作流"""
        orchestrator = PipelineOrchestrator()

        # 1. 创建流水线
        stages = [
            PipelineStage.REQUIREMENT,
            PipelineStage.ARCHITECTURE,
            PipelineStage.DEVELOPMENT,
        ]
        pipeline = orchestrator.create_pipeline("workflow", stages=stages)
        assert pipeline is not None

        # 2. 执行流水线
        execution = orchestrator.execute("workflow")
        assert execution is not None
        assert execution.status == PipelineStatus.COMPLETED

        # 3. 监控流水线
        info = orchestrator.monitor("workflow")
        assert info is not None
        assert info["status"] == "completed"

        # 4. 获取状态
        status = orchestrator.get_pipeline_status("workflow")
        assert status == PipelineStatus.COMPLETED

        # 5. 获取所有流水线
        all_pipelines = orchestrator.get_all_pipelines()
        assert "workflow" in all_pipelines


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
