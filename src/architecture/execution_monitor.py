"""
执行监控器
职责：执行状态跟踪、执行记录管理、执行统计、性能摘要
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """执行状态"""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionRecord:
    """执行记录"""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    agent_id: str = ""
    status: ExecutionStatus = ExecutionStatus.QUEUED
    start_time: float = 0.0
    end_time: float = 0.0
    result: Any = None
    error: str = ""

    def __post_init__(self):
        logger.debug(f"ExecutionRecord created: id={self.record_id}, task={self.task_id}, status={self.status}")


class ExecutionMonitor:
    """执行监控器"""

    def __init__(self):
        self.records: Dict[str, ExecutionRecord] = {}
        self.active_executions: Dict[str, ExecutionRecord] = {}
        logger.info("ExecutionMonitor initialized")

    def start_execution(self, task_id: str = "", agent_id: str = "") -> ExecutionRecord:
        """开始执行，创建执行记录"""
        try:
            record = ExecutionRecord(
                task_id=task_id,
                agent_id=agent_id,
                status=ExecutionStatus.RUNNING,
                start_time=time.time(),
            )
            self.records[record.record_id] = record
            self.active_executions[record.record_id] = record
            logger.info(f"ExecutionMonitor: started execution id={record.record_id}, "
                       f"task={task_id}, agent={agent_id}")
        except Exception as e:
            logger.error(f"ExecutionMonitor: start_execution failed: {e}")
            raise

        return record

    def end_execution(self, record_id: str, status: ExecutionStatus = ExecutionStatus.SUCCESS,
                      result: Any = None, error: str = "") -> Optional[ExecutionRecord]:
        """结束执行，更新执行记录"""
        if record_id not in self.records:
            logger.warning(f"ExecutionMonitor: record_id={record_id} not found")
            return None

        try:
            record = self.records[record_id]
            record.status = status
            record.end_time = time.time()
            record.result = result
            record.error = error

            if record_id in self.active_executions:
                del self.active_executions[record_id]

            logger.info(f"ExecutionMonitor: ended execution id={record_id}, "
                       f"status={status.value}, duration={record.end_time - record.start_time:.4f}s")
        except Exception as e:
            logger.error(f"ExecutionMonitor: end_execution failed: {e}")
            return None

        return record

    def get_status(self, record_id: str) -> Optional[ExecutionStatus]:
        """获取执行状态"""
        if record_id not in self.records:
            logger.debug(f"ExecutionMonitor: get_status record_id={record_id} not found")
            return None

        status = self.records[record_id].status
        logger.debug(f"ExecutionMonitor: get_status id={record_id}, status={status.value}")
        return status

    def get_active_count(self) -> int:
        """获取活跃执行数量"""
        count = len(self.active_executions)
        logger.debug(f"ExecutionMonitor: active_count={count}")
        return count

    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        try:
            stats: Dict[str, Any] = {
                "total": len(self.records),
                "active": len(self.active_executions),
                "by_status": {},
            }
            for status in ExecutionStatus:
                count = sum(1 for r in self.records.values() if r.status == status)
                stats["by_status"][status.value] = count

            # 计算已完成执行的平均耗时
            completed = [r for r in self.records.values()
                        if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.FAILED)
                        and r.end_time > 0 and r.start_time > 0]
            if completed:
                avg_duration = sum(r.end_time - r.start_time for r in completed) / len(completed)
                stats["avg_duration"] = avg_duration
            else:
                stats["avg_duration"] = 0.0

            logger.info(f"ExecutionMonitor: statistics total={stats['total']}, "
                       f"active={stats['active']}")
        except Exception as e:
            logger.error(f"ExecutionMonitor: get_statistics failed: {e}")
            return {"total": 0, "active": 0, "by_status": {}, "avg_duration": 0.0}

        return stats


class ExecutionMonitorService:
    """执行监控服务"""

    def __init__(self):
        self.monitor = ExecutionMonitor()
        logger.info("ExecutionMonitorService initialized")

    def track_execution(self, task_id: str = "", agent_id: str = "",
                       status: ExecutionStatus = ExecutionStatus.SUCCESS,
                       result: Any = None, error: str = "") -> Optional[ExecutionRecord]:
        """跟踪执行，自动创建并结束执行记录"""
        try:
            record = self.monitor.start_execution(task_id=task_id, agent_id=agent_id)
            ended = self.monitor.end_execution(
                record.record_id, status=status, result=result, error=error
            )
            logger.info(f"ExecutionMonitorService: tracked execution task={task_id}, "
                       f"status={status.value}")
        except Exception as e:
            logger.error(f"ExecutionMonitorService: track_execution failed: {e}")
            return None

        return ended

    def get_execution_log(self, task_id: str = "") -> List[ExecutionRecord]:
        """获取执行日志"""
        try:
            if task_id:
                records = [r for r in self.monitor.records.values() if r.task_id == task_id]
            else:
                records = list(self.monitor.records.values())

            records.sort(key=lambda r: r.start_time)
            logger.debug(f"ExecutionMonitorService: execution log, "
                        f"count={len(records)}, task_filter={task_id or 'none'}")
        except Exception as e:
            logger.error(f"ExecutionMonitorService: get_execution_log failed: {e}")
            return []

        return records

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        try:
            stats = self.monitor.get_statistics()
            summary = {
                "statistics": stats,
                "active_count": self.monitor.get_active_count(),
            }
            logger.info(f"ExecutionMonitorService: performance summary, "
                       f"total={stats['total']}")
        except Exception as e:
            logger.error(f"ExecutionMonitorService: get_performance_summary failed: {e}")
            return {"statistics": {}, "active_count": 0}

        return summary
