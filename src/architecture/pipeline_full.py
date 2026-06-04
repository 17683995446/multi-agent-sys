"""
完整流水线100%闭环
职责：流水线编排、阶段执行、状态管理、故障处理

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """流水线阶段"""
    REQUIREMENT = "requirement"
    ARCHITECTURE = "architecture"
    DEVELOPMENT = "development"
    REVIEW = "review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"


class PipelineStatus(str, Enum):
    """流水线状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageResult:
    """阶段结果"""
    stage: PipelineStage = PipelineStage.REQUIREMENT
    status: PipelineStatus = PipelineStatus.IDLE
    output: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0
    error: str = ""

    def __post_init__(self):
        logger.debug(f"StageResult created: stage={self.stage.value}, "
                     f"status={self.status.value}")


@dataclass
class PipelineExecution:
    """流水线执行"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stages: List[PipelineStage] = field(default_factory=list)
    current_stage: Optional[PipelineStage] = None
    status: PipelineStatus = PipelineStatus.IDLE
    results: List[StageResult] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    def __post_init__(self):
        logger.debug(f"PipelineExecution created: id={self.execution_id}, "
                     f"stages={len(self.stages)}")


class FullPipeline:
    """完整流水线"""

    def __init__(self):
        """初始化完整流水线"""
        self.stages: List[PipelineStage] = []
        self.status: PipelineStatus = PipelineStatus.IDLE
        self.results: List[StageResult] = []
        self.current_stage: Optional[PipelineStage] = None
        self._stage_handlers: Dict[PipelineStage, Callable] = {}
        self._paused_at: Optional[PipelineStage] = None
        self._start_time: float = 0.0
        self._end_time: float = 0.0
        logger.info("FullPipeline initialized")

    def add_stage(self, stage: PipelineStage) -> bool:
        """添加阶段"""
        logger.info(f"FullPipeline: adding stage={stage.value}")
        try:
            if stage in self.stages:
                logger.warning(f"FullPipeline: stage={stage.value} already exists")
                return False

            self.stages.append(stage)
            logger.info(f"FullPipeline: stage={stage.value} added, "
                        f"total_stages={len(self.stages)}")
        except Exception as e:
            logger.error(f"FullPipeline: add_stage failed: {e}")
            return False

        return True

    def remove_stage(self, stage: PipelineStage) -> bool:
        """移除阶段"""
        logger.info(f"FullPipeline: removing stage={stage.value}")
        try:
            if stage not in self.stages:
                logger.warning(f"FullPipeline: stage={stage.value} not found")
                return False

            self.stages.remove(stage)
            logger.info(f"FullPipeline: stage={stage.value} removed, "
                        f"total_stages={len(self.stages)}")
        except Exception as e:
            logger.error(f"FullPipeline: remove_stage failed: {e}")
            return False

        return True

    def run(self) -> PipelineStatus:
        """运行流水线"""
        logger.info(f"FullPipeline: running pipeline with {len(self.stages)} stages")
        try:
            if not self.stages:
                logger.warning("FullPipeline: no stages to run")
                self.status = PipelineStatus.FAILED
                return self.status

            if self.status == PipelineStatus.RUNNING:
                logger.warning("FullPipeline: already running")
                return self.status

            self.status = PipelineStatus.RUNNING
            self._start_time = time.time()
            self.results = []

            for stage in self.stages:
                self.current_stage = stage
                result = self._execute_stage(stage)
                self.results.append(result)

                if result.status == PipelineStatus.FAILED:
                    self._handle_stage_failure(stage, result.error)
                    self.status = PipelineStatus.FAILED
                    self._end_time = time.time()
                    logger.error(f"FullPipeline: failed at stage={stage.value}")
                    return self.status

                # 检查是否暂停
                if self.status == PipelineStatus.PAUSED:
                    self._paused_at = stage
                    logger.info(f"FullPipeline: paused at stage={stage.value}")
                    return self.status

            self.status = PipelineStatus.COMPLETED
            self._end_time = time.time()
            self.current_stage = None
            logger.info(f"FullPipeline: completed successfully")
        except Exception as e:
            logger.error(f"FullPipeline: run failed: {e}")
            self.status = PipelineStatus.FAILED
            self._end_time = time.time()

        return self.status

    def pause(self) -> bool:
        """暂停流水线"""
        logger.info("FullPipeline: pausing pipeline")
        try:
            if self.status != PipelineStatus.RUNNING:
                logger.warning("FullPipeline: cannot pause, not running")
                return False

            self.status = PipelineStatus.PAUSED
            logger.info("FullPipeline: pipeline paused")
        except Exception as e:
            logger.error(f"FullPipeline: pause failed: {e}")
            return False

        return True

    def resume(self) -> PipelineStatus:
        """恢复流水线"""
        logger.info("FullPipeline: resuming pipeline")
        try:
            if self.status != PipelineStatus.PAUSED:
                logger.warning("FullPipeline: cannot resume, not paused")
                return self.status

            self.status = PipelineStatus.RUNNING

            # 从暂停的阶段之后继续
            if self._paused_at is not None:
                resume_index = self.stages.index(self._paused_at) + 1
                for stage in self.stages[resume_index:]:
                    self.current_stage = stage
                    result = self._execute_stage(stage)
                    self.results.append(result)

                    if result.status == PipelineStatus.FAILED:
                        self._handle_stage_failure(stage, result.error)
                        self.status = PipelineStatus.FAILED
                        self._end_time = time.time()
                        return self.status

                    if self.status == PipelineStatus.PAUSED:
                        self._paused_at = stage
                        return self.status

            self.status = PipelineStatus.COMPLETED
            self._end_time = time.time()
            self.current_stage = None
            self._paused_at = None
            logger.info("FullPipeline: resumed and completed")
        except Exception as e:
            logger.error(f"FullPipeline: resume failed: {e}")
            self.status = PipelineStatus.FAILED
            self._end_time = time.time()

        return self.status

    def get_status(self) -> PipelineStatus:
        """获取流水线状态"""
        logger.debug(f"FullPipeline: get_status={self.status.value}")
        return self.status

    def get_results(self) -> List[StageResult]:
        """获取所有阶段结果"""
        logger.debug(f"FullPipeline: get_results, count={len(self.results)}")
        return self.results

    def _execute_stage(self, stage: PipelineStage) -> StageResult:
        """执行单个阶段"""
        logger.info(f"FullPipeline: executing stage={stage.value}")
        start_time = time.time()
        result = StageResult(stage=stage, status=PipelineStatus.RUNNING)

        try:
            # 检查是否有自定义处理器
            if stage in self._stage_handlers:
                output = self._stage_handlers[stage]()
                result.output = output if isinstance(output, dict) else {"result": output}
            else:
                # 默认执行逻辑：模拟阶段执行
                result.output = self._default_stage_execution(stage)

            result.status = PipelineStatus.COMPLETED
            result.duration = round(time.time() - start_time, 4)
            logger.info(f"FullPipeline: stage={stage.value} completed, "
                        f"duration={result.duration}")
        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.error = str(e)
            result.duration = round(time.time() - start_time, 4)
            logger.error(f"FullPipeline: stage={stage.value} failed: {e}")

        return result

    def _default_stage_execution(self, stage: PipelineStage) -> Dict[str, Any]:
        """默认阶段执行逻辑"""
        logger.debug(f"FullPipeline: default execution for stage={stage.value}")
        stage_outputs: Dict[PipelineStage, Dict[str, Any]] = {
            PipelineStage.REQUIREMENT: {
                "requirements": ["功能需求A", "功能需求B"],
                "priority": "high",
            },
            PipelineStage.ARCHITECTURE: {
                "architecture": "微服务架构",
                "components": ["服务A", "服务B"],
            },
            PipelineStage.DEVELOPMENT: {
                "modules": ["模块A", "模块B"],
                "code_coverage": 0.85,
            },
            PipelineStage.REVIEW: {
                "review_status": "approved",
                "issues": [],
            },
            PipelineStage.TESTING: {
                "total": 100,
                "passed": 98,
                "failed": 2,
            },
            PipelineStage.DOCUMENTATION: {
                "documents": ["API文档", "架构文档"],
                "coverage": 0.9,
            },
            PipelineStage.DEPLOYMENT: {
                "environment": "production",
                "version": "1.0.0",
            },
        }
        return stage_outputs.get(stage, {"result": "completed"})

    def _handle_stage_failure(self, stage: PipelineStage, error: str) -> None:
        """处理阶段失败"""
        logger.error(f"FullPipeline: handling failure at stage={stage.value}, "
                     f"error={error}")
        try:
            # 记录失败信息
            failure_info = {
                "stage": stage.value,
                "error": error,
                "timestamp": time.time(),
                "action": "logged",
            }
            logger.info(f"FullPipeline: failure handled: {failure_info}")
        except Exception as e:
            logger.error(f"FullPipeline: _handle_stage_failure failed: {e}")


class PipelineOrchestrator:
    """流水线编排器"""

    def __init__(self):
        """初始化流水线编排器"""
        self.pipelines: Dict[str, FullPipeline] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        logger.info("PipelineOrchestrator initialized")

    def create_pipeline(self, pipeline_id: str,
                        stages: Optional[List[PipelineStage]] = None) -> Optional[FullPipeline]:
        """创建流水线"""
        logger.info(f"PipelineOrchestrator: creating pipeline id={pipeline_id}, "
                    f"stages={len(stages) if stages else 0}")
        try:
            if pipeline_id in self.pipelines:
                logger.warning(f"PipelineOrchestrator: pipeline id={pipeline_id} already exists")
                return None

            pipeline = FullPipeline()
            if stages:
                for stage in stages:
                    pipeline.add_stage(stage)

            self.pipelines[pipeline_id] = pipeline
            logger.info(f"PipelineOrchestrator: pipeline id={pipeline_id} created")
        except Exception as e:
            logger.error(f"PipelineOrchestrator: create_pipeline failed: {e}")
            return None

        return pipeline

    def execute(self, pipeline_id: str) -> Optional[PipelineExecution]:
        """执行流水线"""
        logger.info(f"PipelineOrchestrator: executing pipeline id={pipeline_id}")
        if pipeline_id not in self.pipelines:
            logger.warning(f"PipelineOrchestrator: pipeline id={pipeline_id} not found")
            return None

        try:
            pipeline = self.pipelines[pipeline_id]
            execution = PipelineExecution(
                stages=list(pipeline.stages),
                status=PipelineStatus.RUNNING,
                start_time=time.time(),
            )

            # 执行流水线
            final_status = pipeline.run()

            # 更新执行记录
            execution.status = final_status
            execution.results = list(pipeline.results)
            execution.current_stage = pipeline.current_stage
            execution.end_time = time.time() if final_status in (
                PipelineStatus.COMPLETED, PipelineStatus.FAILED
            ) else 0.0

            self.executions[execution.execution_id] = execution
            logger.info(f"PipelineOrchestrator: pipeline id={pipeline_id} executed, "
                        f"status={final_status.value}")
        except Exception as e:
            logger.error(f"PipelineOrchestrator: execute failed: {e}")
            return None

        return execution

    def monitor(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """监控流水线"""
        logger.debug(f"PipelineOrchestrator: monitoring pipeline id={pipeline_id}")
        if pipeline_id not in self.pipelines:
            logger.warning(f"PipelineOrchestrator: pipeline id={pipeline_id} not found")
            return None

        try:
            pipeline = self.pipelines[pipeline_id]
            monitor_info: Dict[str, Any] = {
                "pipeline_id": pipeline_id,
                "status": pipeline.status.value,
                "total_stages": len(pipeline.stages),
                "completed_stages": len(pipeline.results),
                "current_stage": pipeline.current_stage.value if pipeline.current_stage else None,
                "results": [
                    {
                        "stage": r.stage.value,
                        "status": r.status.value,
                        "duration": r.duration,
                        "error": r.error,
                    }
                    for r in pipeline.results
                ],
            }
            logger.debug(f"PipelineOrchestrator: monitor info for id={pipeline_id}")
        except Exception as e:
            logger.error(f"PipelineOrchestrator: monitor failed: {e}")
            return None

        return monitor_info

    def get_pipeline_status(self, pipeline_id: str) -> Optional[PipelineStatus]:
        """获取流水线状态"""
        logger.debug(f"PipelineOrchestrator: getting status for pipeline id={pipeline_id}")
        if pipeline_id not in self.pipelines:
            logger.warning(f"PipelineOrchestrator: pipeline id={pipeline_id} not found")
            return None

        return self.pipelines[pipeline_id].get_status()

    def get_all_pipelines(self) -> Dict[str, Dict[str, Any]]:
        """获取所有流水线信息"""
        logger.debug("PipelineOrchestrator: getting all pipelines info")
        all_info: Dict[str, Dict[str, Any]] = {}
        try:
            for pid, pipeline in self.pipelines.items():
                all_info[pid] = {
                    "status": pipeline.status.value,
                    "stages": [s.value for s in pipeline.stages],
                    "results_count": len(pipeline.results),
                }
            logger.debug(f"PipelineOrchestrator: {len(all_info)} pipelines found")
        except Exception as e:
            logger.error(f"PipelineOrchestrator: get_all_pipelines failed: {e}")
            return {}

        return all_info
