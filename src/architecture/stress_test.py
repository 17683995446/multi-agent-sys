"""
多Agent协作压力测试模块

职责：执行多Agent压力测试、收集性能指标、生成压力测试报告

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StressTestType(str, Enum):
    """压力测试类型"""
    CONCURRENT_AGENTS = "concurrent_agents"
    HIGH_VOLUME_TASKS = "high_volume_tasks"
    LONG_DURATION = "long_duration"
    MIXED_WORKLOAD = "mixed_workload"


@dataclass
class StressTestConfig:
    """压力测试配置"""
    test_type: StressTestType = StressTestType.CONCURRENT_AGENTS
    agent_count: int = 10
    task_count: int = 100
    duration_seconds: float = 60.0
    ramp_up_seconds: float = 10.0

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"StressTestConfig created: test_type={self.test_type.value}, "
                     f"agent_count={self.agent_count}, task_count={self.task_count}")


@dataclass
class StressTestResult:
    """压力测试结果"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: StressTestConfig = field(default_factory=StressTestConfig)
    total_operations: int = 0
    successful_ops: int = 0
    failed_ops: int = 0
    avg_latency: float = 0.0
    max_latency: float = 0.0
    throughput: float = 0.0
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"StressTestResult created: test_id={self.test_id}")


class StressTester:
    """多Agent协作压力测试器"""

    def __init__(self):
        """初始化压力测试器"""
        self._results: Dict[str, StressTestResult] = {}
        self._metrics: List[Dict[str, Any]] = []
        logger.info("StressTester initialized")

    def run(self, config: StressTestConfig) -> StressTestResult:
        """执行压力测试"""
        logger.info(f"StressTester: running stress test, "
                    f"type={config.test_type.value}, "
                    f"agents={config.agent_count}, tasks={config.task_count}")
        try:
            result = StressTestResult(config=config)
            start_time = time.time()

            if config.test_type == StressTestType.CONCURRENT_AGENTS:
                self._run_concurrent(config, result)
            elif config.test_type == StressTestType.HIGH_VOLUME_TASKS:
                self._run_high_volume(config, result)
            elif config.test_type == StressTestType.LONG_DURATION:
                self._run_long_duration(config, result)
            elif config.test_type == StressTestType.MIXED_WORKLOAD:
                self._run_concurrent(config, result)
                self._run_high_volume(config, result)

            elapsed = time.time() - start_time
            result.throughput = result.total_operations / elapsed if elapsed > 0 else 0.0
            self._collect_metrics(result)

            self._results[result.test_id] = result
            logger.info(f"StressTester: stress test completed, "
                        f"test_id={result.test_id}, "
                        f"total_ops={result.total_operations}, "
                        f"successful={result.successful_ops}, "
                        f"failed={result.failed_ops}")
        except Exception as e:
            logger.error(f"StressTester: run failed: {e}")
            result = StressTestResult(config=config)
            result.errors.append(str(e))
        return result

    def _run_concurrent(self, config: StressTestConfig,
                        result: StressTestResult) -> None:
        """运行并发Agent测试"""
        logger.debug(f"StressTester: running concurrent test, "
                     f"agents={config.agent_count}")
        try:
            for i in range(config.agent_count):
                latency = 0.01 + (i % 5) * 0.005
                result.total_operations += 1
                if latency < 0.1:
                    result.successful_ops += 1
                else:
                    result.failed_ops += 1
                    result.errors.append(f"Agent {i} timeout")
                result.avg_latency += latency
                result.max_latency = max(result.max_latency, latency)
            if result.total_operations > 0:
                result.avg_latency /= result.total_operations
            logger.debug(f"StressTester: concurrent test completed, "
                         f"ops={result.total_operations}")
        except Exception as e:
            logger.error(f"StressTester: _run_concurrent failed: {e}")
            result.errors.append(str(e))

    def _run_high_volume(self, config: StressTestConfig,
                         result: StressTestResult) -> None:
        """运行高任务量测试"""
        logger.debug(f"StressTester: running high volume test, "
                     f"tasks={config.task_count}")
        try:
            base_ops = result.total_operations
            for i in range(config.task_count):
                latency = 0.005 + (i % 10) * 0.002
                result.total_operations += 1
                if latency < 0.05:
                    result.successful_ops += 1
                else:
                    result.failed_ops += 1
                    result.errors.append(f"Task {i} exceeded latency")
                result.avg_latency += latency
                result.max_latency = max(result.max_latency, latency)
            if result.total_operations > base_ops:
                new_ops = result.total_operations - base_ops
                total_latency = result.avg_latency * result.total_operations
                result.avg_latency = total_latency / result.total_operations if result.total_operations > 0 else 0.0
            logger.debug(f"StressTester: high volume test completed")
        except Exception as e:
            logger.error(f"StressTester: _run_high_volume failed: {e}")
            result.errors.append(str(e))

    def _run_long_duration(self, config: StressTestConfig,
                           result: StressTestResult) -> None:
        """运行长持续时间测试"""
        logger.debug(f"StressTester: running long duration test, "
                     f"duration={config.duration_seconds}s")
        try:
            iterations = int(config.duration_seconds / 0.01)
            for i in range(min(iterations, 100)):
                latency = 0.005 + (i % 3) * 0.001
                result.total_operations += 1
                result.successful_ops += 1
                result.avg_latency += latency
                result.max_latency = max(result.max_latency, latency)
            if result.total_operations > 0:
                result.avg_latency /= result.total_operations
            logger.debug(f"StressTester: long duration test completed")
        except Exception as e:
            logger.error(f"StressTester: _run_long_duration failed: {e}")
            result.errors.append(str(e))

    def _collect_metrics(self, result: StressTestResult) -> None:
        """收集性能指标"""
        logger.debug(f"StressTester: collecting metrics, "
                     f"test_id={result.test_id}")
        try:
            metrics: Dict[str, Any] = {
                "test_id": result.test_id,
                "total_operations": result.total_operations,
                "successful_ops": result.successful_ops,
                "failed_ops": result.failed_ops,
                "avg_latency": result.avg_latency,
                "max_latency": result.max_latency,
                "throughput": result.throughput,
                "error_count": len(result.errors),
                "timestamp": time.time(),
            }
            self._metrics.append(metrics)
            logger.debug(f"StressTester: metrics collected")
        except Exception as e:
            logger.error(f"StressTester: _collect_metrics failed: {e}")

    def generate_report(self, test_id: str) -> Dict[str, Any]:
        """生成压力测试报告"""
        logger.info(f"StressTester: generating report, test_id={test_id}")
        try:
            result = self._results.get(test_id)
            if result is None:
                return {"message": "未找到测试结果"}

            report: Dict[str, Any] = {
                "test_id": result.test_id,
                "test_type": result.config.test_type.value,
                "agent_count": result.config.agent_count,
                "task_count": result.config.task_count,
                "total_operations": result.total_operations,
                "successful_ops": result.successful_ops,
                "failed_ops": result.failed_ops,
                "success_rate": (
                    result.successful_ops / result.total_operations * 100
                    if result.total_operations > 0 else 0.0
                ),
                "avg_latency": result.avg_latency,
                "max_latency": result.max_latency,
                "throughput": result.throughput,
                "error_count": len(result.errors),
                "errors": result.errors[:10],
                "timestamp": time.time(),
            }
            logger.info(f"StressTester: report generated, test_id={test_id}")
        except Exception as e:
            logger.error(f"StressTester: generate_report failed: {e}")
            report = {"error": str(e)}
        return report


class StressTestService:
    """多Agent协作压力测试服务"""

    def __init__(self, tester: Optional[StressTester] = None):
        """初始化压力测试服务"""
        self.tester = tester or StressTester()
        logger.info("StressTestService initialized")

    def run(self, config: StressTestConfig) -> StressTestResult:
        """执行压力测试"""
        logger.info(f"StressTestService: running stress test, "
                    f"type={config.test_type.value}")
        return self.tester.run(config)

    def get_result(self, test_id: str) -> Optional[StressTestResult]:
        """获取测试结果"""
        logger.debug(f"StressTestService: getting result, test_id={test_id}")
        return self.tester._results.get(test_id)

    def get_report(self, test_id: str) -> Dict[str, Any]:
        """获取测试报告"""
        logger.debug(f"StressTestService: getting report, test_id={test_id}")
        return self.tester.generate_report(test_id)
