"""
批量工程任务压测适配模块

职责：生成负载、执行压测、收集指标、推荐扩缩容

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LoadProfile(str, Enum):
    """负载配置"""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    EXTREME = "extreme"


@dataclass
class LoadConfig:
    """负载配置"""
    profile: LoadProfile = LoadProfile.MODERATE
    concurrent_tasks: int = 10
    total_tasks: int = 100
    task_complexity: float = 1.0
    think_time_ms: int = 100

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"LoadConfig created: profile={self.profile.value}, "
                     f"concurrent={self.concurrent_tasks}, total={self.total_tasks}")


@dataclass
class LoadMetrics:
    """负载指标"""
    total_tasks: int = 0
    completed: int = 0
    failed: int = 0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"LoadMetrics created: total={self.total_tasks}, "
                     f"completed={self.completed}")


class LoadGenerator:
    """负载生成器"""

    def __init__(self):
        """初始化负载生成器"""
        self._metrics_history: List[LoadMetrics] = []
        self._response_times: List[float] = []
        logger.info("LoadGenerator initialized")

    def generate_load(self, config: LoadConfig) -> LoadMetrics:
        """生成负载"""
        logger.info(f"LoadGenerator: generating load, "
                    f"profile={config.profile.value}, "
                    f"total_tasks={config.total_tasks}")
        try:
            start_time = time.time()
            response_times: List[float] = []
            completed = 0
            failed = 0

            for i in range(config.total_tasks):
                task = self._create_task(i, config)
                success, response_time = self._execute_task(task, config)
                response_times.append(response_time)
                self._response_times.append(response_time)

                if success:
                    completed += 1
                else:
                    failed += 1

            elapsed = time.time() - start_time
            metrics = self.collect_metrics(
                config.total_tasks, completed, failed,
                response_times, elapsed
            )
            self._metrics_history.append(metrics)

            logger.info(f"LoadGenerator: load generated, "
                        f"completed={completed}, failed={failed}, "
                        f"throughput={metrics.throughput:.2f}")
            return metrics
        except Exception as e:
            logger.error(f"LoadGenerator: generate_load failed: {e}")
            return LoadMetrics(total_tasks=config.total_tasks)

    def _create_task(self, task_index: int,
                     config: LoadConfig) -> Dict[str, Any]:
        """创建任务"""
        logger.debug(f"LoadGenerator: creating task {task_index}")
        try:
            task: Dict[str, Any] = {
                "task_id": f"task_{task_index}",
                "index": task_index,
                "complexity": config.task_complexity,
                "profile": config.profile.value,
            }
            return task
        except Exception as e:
            logger.error(f"LoadGenerator: _create_task failed: {e}")
            return {"task_id": f"task_{task_index}", "index": task_index}

    def _execute_task(self, task: Dict[str, Any],
                      config: LoadConfig) -> tuple:
        """执行任务"""
        logger.debug(f"LoadGenerator: executing task, "
                     f"task_id={task.get('task_id', 'unknown')}")
        try:
            response_time = self._measure_response(task, config)
            # 根据负载配置决定成功率
            if config.profile == LoadProfile.EXTREME:
                success = response_time < 2.0
            elif config.profile == LoadProfile.HEAVY:
                success = response_time < 1.0
            else:
                success = response_time < 0.5
            return success, response_time
        except Exception as e:
            logger.error(f"LoadGenerator: _execute_task failed: {e}")
            return False, 0.0

    def _measure_response(self, task: Dict[str, Any],
                          config: LoadConfig) -> float:
        """测量响应时间"""
        logger.debug(f"LoadGenerator: measuring response, "
                     f"task_id={task.get('task_id', 'unknown')}")
        try:
            complexity = task.get("complexity", 1.0)
            # 模拟响应时间
            base_time = 0.01
            if config.profile == LoadProfile.LIGHT:
                response_time = base_time * complexity * 0.5
            elif config.profile == LoadProfile.MODERATE:
                response_time = base_time * complexity * 1.0
            elif config.profile == LoadProfile.HEAVY:
                response_time = base_time * complexity * 2.0
            else:  # EXTREME
                response_time = base_time * complexity * 5.0

            # 添加一些随机性
            task_index = task.get("index", 0)
            response_time += (task_index % 10) * 0.005
            return response_time
        except Exception as e:
            logger.error(f"LoadGenerator: _measure_response failed: {e}")
            return 1.0

    def collect_metrics(self, total: int, completed: int, failed: int,
                        response_times: List[float],
                        elapsed: float) -> LoadMetrics:
        """收集指标"""
        logger.debug(f"LoadGenerator: collecting metrics, "
                     f"total={total}, completed={completed}")
        try:
            sorted_times = sorted(response_times) if response_times else [0.0]
            avg_time = sum(sorted_times) / len(sorted_times) if sorted_times else 0.0
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
            p99_time = sorted_times[min(p99_index, len(sorted_times) - 1)]
            throughput = total / elapsed if elapsed > 0 else 0.0
            error_rate = (failed / total * 100) if total > 0 else 0.0

            metrics = LoadMetrics(
                total_tasks=total,
                completed=completed,
                failed=failed,
                avg_response_time=avg_time,
                p95_response_time=p95_time,
                p99_response_time=p99_time,
                throughput=throughput,
                error_rate=error_rate,
            )
            logger.debug(f"LoadGenerator: metrics collected, "
                         f"avg={avg_time:.4f}, p95={p95_time:.4f}")
            return metrics
        except Exception as e:
            logger.error(f"LoadGenerator: collect_metrics failed: {e}")
            return LoadMetrics(total_tasks=total)


class LoadAdapterService:
    """批量工程任务压测适配服务"""

    def __init__(self, generator: Optional[LoadGenerator] = None):
        """初始化负载适配服务"""
        self.generator = generator or LoadGenerator()
        logger.info("LoadAdapterService initialized")

    def run_load_test(self, config: LoadConfig) -> LoadMetrics:
        """运行负载测试"""
        logger.info(f"LoadAdapterService: running load test, "
                    f"profile={config.profile.value}")
        return self.generator.generate_load(config)

    def get_metrics(self) -> List[LoadMetrics]:
        """获取指标历史"""
        logger.debug("LoadAdapterService: getting metrics history")
        return list(self.generator._metrics_history)

    def get_report(self) -> Dict[str, Any]:
        """获取测试报告"""
        logger.debug("LoadAdapterService: getting report")
        try:
            history = self.generator._metrics_history
            if not history:
                return {"message": "暂无负载测试数据"}

            latest = history[-1]
            report: Dict[str, Any] = {
                "total_tasks": latest.total_tasks,
                "completed": latest.completed,
                "failed": latest.failed,
                "avg_response_time": latest.avg_response_time,
                "p95_response_time": latest.p95_response_time,
                "p99_response_time": latest.p99_response_time,
                "throughput": latest.throughput,
                "error_rate": latest.error_rate,
                "history_count": len(history),
                "timestamp": time.time(),
            }
            return report
        except Exception as e:
            logger.error(f"LoadAdapterService: get_report failed: {e}")
            return {"error": str(e)}

    def suggest_scaling(self, metrics: LoadMetrics) -> Dict[str, Any]:
        """推荐扩缩容"""
        logger.info(f"LoadAdapterService: suggesting scaling, "
                    f"error_rate={metrics.error_rate}")
        try:
            suggestion: Dict[str, Any] = {
                "current_metrics": {
                    "throughput": metrics.throughput,
                    "error_rate": metrics.error_rate,
                    "avg_response_time": metrics.avg_response_time,
                    "p95_response_time": metrics.p95_response_time,
                },
            }

            if metrics.error_rate > 10.0:
                suggestion["action"] = "scale_up"
                suggestion["reason"] = "错误率过高，建议增加资源"
                suggestion["recommended_instances"] = 3
            elif metrics.error_rate > 5.0:
                suggestion["action"] = "scale_up"
                suggestion["reason"] = "错误率偏高，建议适当增加资源"
                suggestion["recommended_instances"] = 2
            elif metrics.avg_response_time > 1.0:
                suggestion["action"] = "scale_up"
                suggestion["reason"] = "平均响应时间过长，建议增加资源"
                suggestion["recommended_instances"] = 2
            elif metrics.error_rate < 1.0 and metrics.avg_response_time < 0.1:
                suggestion["action"] = "scale_down"
                suggestion["reason"] = "系统负载较低，可适当减少资源"
                suggestion["recommended_instances"] = 1
            else:
                suggestion["action"] = "maintain"
                suggestion["reason"] = "系统运行正常，保持当前资源"
                suggestion["recommended_instances"] = 1

            logger.info(f"LoadAdapterService: scaling suggestion, "
                        f"action={suggestion['action']}")
            return suggestion
        except Exception as e:
            logger.error(f"LoadAdapterService: suggest_scaling failed: {e}")
            return {"error": str(e)}
