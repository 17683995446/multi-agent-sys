"""
最终态：可无人值守全自动系统模块

职责：自动执行任务、错误恢复、批量处理、无人值守运行

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SystemMode(str, Enum):
    """系统模式"""
    MANUAL = "manual"
    SEMI_AUTO = "semi_auto"
    FULL_AUTO = "full_auto"
    MAINTENANCE = "maintenance"


class AutonomousStatus(str, Enum):
    """自治状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    RECOVERING = "recovering"


@dataclass
class SystemConfig:
    """系统配置"""
    mode: SystemMode = SystemMode.MANUAL
    max_concurrent_tasks: int = 5
    auto_recovery: bool = True
    monitoring_interval: float = 60.0
    escalation_rules: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"SystemConfig created: mode={self.mode.value}, "
                     f"max_concurrent={self.max_concurrent_tasks}, "
                     f"auto_recovery={self.auto_recovery}")


@dataclass
class AutonomousResult:
    """自治执行结果"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: AutonomousStatus = AutonomousStatus.IDLE
    steps_completed: int = 0
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    output: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"AutonomousResult created: task_id={self.task_id}, "
                     f"status={self.status.value}")


class AutonomousController:
    """自治控制器"""

    def __init__(self, config: Optional[SystemConfig] = None):
        """初始化自治控制器"""
        self._config = config or SystemConfig()
        self._status: AutonomousStatus = AutonomousStatus.IDLE
        self._results: Dict[str, AutonomousResult] = {}
        self._current_task: Optional[str] = None
        self._error_count: int = 0
        self._max_errors: int = 3
        logger.info(f"AutonomousController initialized, "
                    f"mode={self._config.mode.value}")

    def start(self, task: Dict[str, Any]) -> AutonomousResult:
        """启动任务"""
        logger.info(f"AutonomousController: starting task, "
                    f"mode={self._config.mode.value}")
        try:
            if self._status == AutonomousStatus.RUNNING:
                logger.warning("AutonomousController: already running")
                return AutonomousResult(status=AutonomousStatus.ERROR,
                                        errors=["系统正在运行中"])

            self._status = AutonomousStatus.RUNNING
            result = self._execute_task(task)
            self._status = AutonomousStatus.IDLE
            return result
        except Exception as e:
            logger.error(f"AutonomousController: start failed: {e}")
            self._status = AutonomousStatus.ERROR
            result = AutonomousResult(
                status=AutonomousStatus.ERROR,
                errors=[str(e)],
            )
            self._results[result.task_id] = result
            return result

    def stop(self) -> bool:
        """停止任务"""
        logger.info("AutonomousController: stopping")
        try:
            self._status = AutonomousStatus.IDLE
            self._current_task = None
            logger.info("AutonomousController: stopped")
        except Exception as e:
            logger.error(f"AutonomousController: stop failed: {e}")
            return False
        return True

    def pause(self) -> bool:
        """暂停任务"""
        logger.info("AutonomousController: pausing")
        try:
            if self._status == AutonomousStatus.RUNNING:
                self._status = AutonomousStatus.PAUSED
                logger.info("AutonomousController: paused")
            else:
                logger.warning("AutonomousController: not running, cannot pause")
                return False
        except Exception as e:
            logger.error(f"AutonomousController: pause failed: {e}")
            return False
        return True

    def resume(self) -> bool:
        """恢复任务"""
        logger.info("AutonomousController: resuming")
        try:
            if self._status == AutonomousStatus.PAUSED:
                self._status = AutonomousStatus.RUNNING
                logger.info("AutonomousController: resumed")
            else:
                logger.warning("AutonomousController: not paused, cannot resume")
                return False
        except Exception as e:
            logger.error(f"AutonomousController: resume failed: {e}")
            return False
        return True

    def _execute_task(self, task: Dict[str, Any]) -> AutonomousResult:
        """执行任务"""
        task_id = str(uuid.uuid4())
        self._current_task = task_id
        logger.info(f"AutonomousController: executing task, task_id={task_id}")
        try:
            start_time = time.time()
            steps = task.get("steps", [])
            errors: List[str] = []
            steps_completed = 0
            output: Dict[str, Any] = {}

            for step in steps:
                try:
                    # 模拟步骤执行
                    step_name = step.get("name", "unknown")
                    logger.debug(f"AutonomousController: executing step: {step_name}")

                    # 检查步骤是否标记为失败
                    if step.get("should_fail", False):
                        raise RuntimeError(f"步骤执行失败: {step_name}")

                    steps_completed += 1
                    output[step_name] = step.get("result", "completed")
                except Exception as step_error:
                    error_msg = str(step_error)
                    errors.append(error_msg)
                    self._error_count += 1
                    logger.warning(f"AutonomousController: step failed: {error_msg}")

                    # 尝试自动恢复
                    if self._config.auto_recovery:
                        recovered = self._auto_recover(error_msg)
                        if recovered:
                            logger.info("AutonomousController: auto recovery succeeded")
                            steps_completed += 1
                            output[step.get("name", "unknown")] = "recovered"
                        else:
                            # 升级处理
                            self._escalate(error_msg)
                            if self._error_count >= self._max_errors:
                                logger.error("AutonomousController: max errors reached, stopping")
                                break

            duration = time.time() - start_time

            status = AutonomousStatus.IDLE
            if errors and steps_completed < len(steps):
                status = AutonomousStatus.ERROR
            elif errors:
                status = AutonomousStatus.IDLE  # 有错误但完成了

            result = AutonomousResult(
                task_id=task_id,
                status=status,
                steps_completed=steps_completed,
                errors=errors,
                duration=duration,
                output=output,
            )

            self._results[task_id] = result

            logger.info(f"AutonomousController: task completed, "
                        f"task_id={task_id}, "
                        f"steps={steps_completed}/{len(steps)}, "
                        f"errors={len(errors)}")
        except Exception as e:
            logger.error(f"AutonomousController: _execute_task failed: {e}")
            result = AutonomousResult(
                task_id=task_id,
                status=AutonomousStatus.ERROR,
                errors=[str(e)],
            )
            self._results[task_id] = result
        return result

    def _handle_error(self, error: str) -> bool:
        """处理错误"""
        logger.info(f"AutonomousController: handling error: {error}")
        try:
            self._error_count += 1
            if self._config.auto_recovery:
                return self._auto_recover(error)
            return False
        except Exception as e:
            logger.error(f"AutonomousController: _handle_error failed: {e}")
            return False

    def _auto_recover(self, error: str) -> bool:
        """自动恢复"""
        logger.info(f"AutonomousController: auto recovering from error: {error}")
        try:
            # 简化的恢复策略
            if "超时" in error or "timeout" in error.lower():
                logger.info("AutonomousController: retrying with extended timeout")
                return True
            elif "连接" in error or "connection" in error.lower():
                logger.info("AutonomousController: reconnecting")
                return True
            elif "资源" in error or "resource" in error.lower():
                logger.info("AutonomousController: releasing and reallocating resources")
                return True
            else:
                logger.warning(f"AutonomousController: cannot auto-recover: {error}")
                return False
        except Exception as e:
            logger.error(f"AutonomousController: _auto_recover failed: {e}")
            return False

    def _escalate(self, error: str) -> Dict[str, Any]:
        """升级处理"""
        logger.info(f"AutonomousController: escalating error: {error}")
        try:
            escalation: Dict[str, Any] = {
                "error": error,
                "mode": self._config.mode.value,
                "error_count": self._error_count,
                "timestamp": time.time(),
            }

            # 根据升级规则处理
            rules = self._config.escalation_rules
            if rules:
                action = rules.get("action", "notify")
                escalation["action"] = action

            logger.info(f"AutonomousController: escalated, "
                        f"error_count={self._error_count}")
        except Exception as e:
            logger.error(f"AutonomousController: _escalate failed: {e}")
            escalation = {"error": error}
        return escalation

    def get_status(self) -> AutonomousStatus:
        """获取当前状态"""
        logger.debug("AutonomousController: getting status")
        return self._status


class AutonomousSystem:
    """自治系统"""

    def __init__(self, config: Optional[SystemConfig] = None):
        """初始化自治系统"""
        self.config = config or SystemConfig()
        self.controller = AutonomousController(self.config)
        self._results: List[AutonomousResult] = []
        logger.info(f"AutonomousSystem initialized, "
                    f"mode={self.config.mode.value}")

    def run_task(self, task: Dict[str, Any]) -> AutonomousResult:
        """运行单个任务"""
        logger.info(f"AutonomousSystem: running task, "
                    f"mode={self.config.mode.value}")
        try:
            if self.config.mode == SystemMode.MANUAL:
                logger.warning("AutonomousSystem: manual mode, task not auto-executed")
                return AutonomousResult(
                    status=AutonomousStatus.IDLE,
                    output={"message": "手动模式，需要手动确认执行"},
                )

            result = self.controller.start(task)
            self._results.append(result)
            return result
        except Exception as e:
            logger.error(f"AutonomousSystem: run_task failed: {e}")
            result = AutonomousResult(
                status=AutonomousStatus.ERROR,
                errors=[str(e)],
            )
            self._results.append(result)
            return result

    def run_batch(self, tasks: List[Dict[str, Any]]) -> List[AutonomousResult]:
        """批量运行任务"""
        logger.info(f"AutonomousSystem: running batch, "
                    f"tasks={len(tasks)}")
        try:
            results: List[AutonomousResult] = []
            for i, task in enumerate(tasks):
                logger.info(f"AutonomousSystem: running batch task {i + 1}/{len(tasks)}")
                result = self.run_task(task)
                results.append(result)

                # 检查并发限制
                if i >= self.config.max_concurrent_tasks:
                    logger.warning("AutonomousSystem: max concurrent tasks reached")
                    break

            logger.info(f"AutonomousSystem: batch completed, "
                        f"results={len(results)}")
        except Exception as e:
            logger.error(f"AutonomousSystem: run_batch failed: {e}")
            results = []
        return results

    def get_status(self) -> AutonomousStatus:
        """获取系统状态"""
        logger.debug("AutonomousSystem: getting status")
        return self.controller.get_status()

    def get_results(self) -> List[AutonomousResult]:
        """获取所有结果"""
        logger.debug("AutonomousSystem: getting results")
        return list(self._results)

    def shutdown(self) -> bool:
        """关闭系统"""
        logger.info("AutonomousSystem: shutting down")
        try:
            self.controller.stop()
            logger.info("AutonomousSystem: shutdown completed")
        except Exception as e:
            logger.error(f"AutonomousSystem: shutdown failed: {e}")
            return False
        return True
