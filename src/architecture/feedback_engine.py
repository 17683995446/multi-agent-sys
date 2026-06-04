"""
反馈循环引擎
职责：反馈收集、趋势分析、调整生成、反馈循环管理
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """反馈类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    SUGGESTION = "suggestion"


class FeedbackSeverity(str, Enum):
    """反馈严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Feedback:
    """反馈"""
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    target: str = ""
    feedback_type: FeedbackType = FeedbackType.NEUTRAL
    severity: FeedbackSeverity = FeedbackSeverity.INFO
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"Feedback created: id={self.feedback_id}, type={self.feedback_type}, "
                    f"severity={self.severity}")


@dataclass
class FeedbackLoop:
    """反馈循环"""
    loop_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    feedbacks: List[Feedback] = field(default_factory=list)
    adjustments: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        logger.debug(f"FeedbackLoop created: id={self.loop_id}, name={self.name}")


class FeedbackAnalyzer:
    """反馈分析器"""

    def __init__(self):
        self.feedbacks: List[Feedback] = []
        logger.info("FeedbackAnalyzer initialized")

    def add_feedback(self, feedback: Feedback) -> None:
        """添加反馈"""
        try:
            self.feedbacks.append(feedback)
            logger.info(f"FeedbackAnalyzer: added feedback id={feedback.feedback_id}, "
                       f"type={feedback.feedback_type.value}")
        except Exception as e:
            logger.error(f"FeedbackAnalyzer: add_feedback failed: {e}")
            raise

    def analyze_trends(self) -> Dict[str, Any]:
        """分析反馈趋势"""
        try:
            if not self.feedbacks:
                logger.debug("FeedbackAnalyzer: no feedbacks to analyze")
                return {"trend": "no_data", "counts": {}, "severity_counts": {}}

            # 按类型统计
            type_counts: Dict[str, int] = {}
            for ft in FeedbackType:
                type_counts[ft.value] = sum(1 for f in self.feedbacks if f.feedback_type == ft)

            # 按严重程度统计
            severity_counts: Dict[str, int] = {}
            for fs in FeedbackSeverity:
                severity_counts[fs.value] = sum(1 for f in self.feedbacks if f.severity == fs)

            # 判断趋势
            positive_ratio = type_counts.get(FeedbackType.POSITIVE.value, 0) / len(self.feedbacks)
            negative_ratio = type_counts.get(FeedbackType.NEGATIVE.value, 0) / len(self.feedbacks)

            if positive_ratio > 0.6:
                trend = "improving"
            elif negative_ratio > 0.6:
                trend = "declining"
            else:
                trend = "stable"

            result = {
                "trend": trend,
                "counts": type_counts,
                "severity_counts": severity_counts,
                "total": len(self.feedbacks),
            }
            logger.info(f"FeedbackAnalyzer: trend={trend}, total={len(self.feedbacks)}")
        except Exception as e:
            logger.error(f"FeedbackAnalyzer: analyze_trends failed: {e}")
            return {"trend": "error", "counts": {}, "severity_counts": {}}

        return result

    def get_summary(self) -> Dict[str, Any]:
        """获取反馈摘要"""
        try:
            summary = {
                "total_feedbacks": len(self.feedbacks),
                "by_type": {},
                "by_severity": {},
            }
            for ft in FeedbackType:
                count = sum(1 for f in self.feedbacks if f.feedback_type == ft)
                summary["by_type"][ft.value] = count
            for fs in FeedbackSeverity:
                count = sum(1 for f in self.feedbacks if f.severity == fs)
                summary["by_severity"][fs.value] = count

            logger.debug(f"FeedbackAnalyzer: summary total={len(self.feedbacks)}")
        except Exception as e:
            logger.error(f"FeedbackAnalyzer: get_summary failed: {e}")
            return {"total_feedbacks": 0, "by_type": {}, "by_severity": {}}

        return summary


class FeedbackEngine:
    """反馈循环引擎"""

    def __init__(self):
        self.loops: Dict[str, FeedbackLoop] = {}
        logger.info("FeedbackEngine initialized")

    def create_loop(self, name: str = "") -> FeedbackLoop:
        """创建反馈循环"""
        try:
            loop = FeedbackLoop(name=name)
            self.loops[loop.loop_id] = loop
            logger.info(f"FeedbackEngine: created loop id={loop.loop_id}, name={name}")
        except Exception as e:
            logger.error(f"FeedbackEngine: create_loop failed: {e}")
            raise

        return loop

    def add_feedback(self, loop_id: str, feedback: Feedback) -> bool:
        """向循环添加反馈"""
        if loop_id not in self.loops:
            logger.warning(f"FeedbackEngine: loop_id={loop_id} not found")
            return False

        try:
            self.loops[loop_id].feedbacks.append(feedback)
            logger.info(f"FeedbackEngine: added feedback to loop={loop_id}, "
                       f"feedback_id={feedback.feedback_id}")
        except Exception as e:
            logger.error(f"FeedbackEngine: add_feedback failed: {e}")
            return False

        return True

    def process_loop(self, loop_id: str) -> Optional[Dict[str, Any]]:
        """处理反馈循环，生成分析结果"""
        if loop_id not in self.loops:
            logger.warning(f"FeedbackEngine: loop_id={loop_id} not found")
            return None

        try:
            loop = self.loops[loop_id]
            analyzer = FeedbackAnalyzer()
            for fb in loop.feedbacks:
                analyzer.add_feedback(fb)

            trends = analyzer.analyze_trends()
            adjustments = self.generate_adjustments(loop)
            loop.adjustments.extend(adjustments)

            result = {
                "loop_id": loop_id,
                "trends": trends,
                "adjustments": adjustments,
                "feedback_count": len(loop.feedbacks),
            }
            logger.info(f"FeedbackEngine: processed loop={loop_id}, "
                       f"trend={trends.get('trend', 'N/A')}, "
                       f"adjustments={len(adjustments)}")
        except Exception as e:
            logger.error(f"FeedbackEngine: process_loop failed: {e}")
            return None

        return result

    def generate_adjustments(self, loop: FeedbackLoop) -> List[Dict[str, Any]]:
        """根据反馈生成调整建议"""
        try:
            adjustments: List[Dict[str, Any]] = []

            if not loop.feedbacks:
                logger.debug(f"FeedbackEngine: no feedbacks in loop={loop.loop_id}")
                return adjustments

            # 统计负面反馈
            negative_count = sum(1 for f in loop.feedbacks if f.feedback_type == FeedbackType.NEGATIVE)
            critical_count = sum(1 for f in loop.feedbacks if f.severity == FeedbackSeverity.CRITICAL)

            if critical_count > 0:
                adjustments.append({
                    "type": "critical_fix",
                    "priority": "high",
                    "message": f"发现{critical_count}个严重问题，需要立即修复",
                })

            if negative_count > len(loop.feedbacks) * 0.5:
                adjustments.append({
                    "type": "performance_improvement",
                    "priority": "medium",
                    "message": f"负面反馈占比过高({negative_count}/{len(loop.feedbacks)})，需要改进",
                })

            # 统计建议
            suggestions = [f for f in loop.feedbacks if f.feedback_type == FeedbackType.SUGGESTION]
            if suggestions:
                adjustments.append({
                    "type": "suggestion_review",
                    "priority": "low",
                    "message": f"收到{suggestions.size() if hasattr(suggestions, 'size') else len(suggestions)}条建议，建议审查",
                })

            logger.info(f"FeedbackEngine: generated {len(adjustments)} adjustments "
                       f"for loop={loop.loop_id}")
        except Exception as e:
            logger.error(f"FeedbackEngine: generate_adjustments failed: {e}")
            return []

        return adjustments
