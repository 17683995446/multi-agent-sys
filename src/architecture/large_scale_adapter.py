"""
大项目复杂重构场景适配模块

职责：分析项目规模、评估重构复杂度、规划重构方案、生成适配计划

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProjectScale(str, Enum):
    """项目规模"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class RefactorComplexity(str, Enum):
    """重构复杂度"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXTREME = "extreme"


@dataclass
class ProjectProfile:
    """项目画像"""
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scale: ProjectScale = ProjectScale.SMALL
    file_count: int = 0
    module_count: int = 0
    dependency_depth: int = 0
    complexity: RefactorComplexity = RefactorComplexity.SIMPLE

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"ProjectProfile created: project_id={self.project_id}, "
                     f"scale={self.scale.value}, "
                     f"complexity={self.complexity.value}")


class LargeScaleAdapter:
    """大项目复杂重构适配器"""

    def __init__(self):
        """初始化大项目适配器"""
        self._profiles: Dict[str, ProjectProfile] = {}
        self._plans: Dict[str, Dict[str, Any]] = {}
        logger.info("LargeScaleAdapter initialized")

    def analyze_project(self, project_data: Dict[str, Any]) -> ProjectProfile:
        """分析项目，生成项目画像"""
        logger.info(f"LargeScaleAdapter: analyzing project, "
                    f"keys={list(project_data.keys())}")
        try:
            scale = self._assess_scale(project_data)
            file_count = project_data.get("file_count", 0)
            module_count = project_data.get("module_count", 0)
            dependency_depth = project_data.get("dependency_depth", 0)

            # 根据规模和依赖深度评估复杂度
            complexity = self._evaluate_complexity(scale, dependency_depth)

            profile = ProjectProfile(
                scale=scale,
                file_count=file_count,
                module_count=module_count,
                dependency_depth=dependency_depth,
                complexity=complexity,
            )
            self._profiles[profile.project_id] = profile

            logger.info(f"LargeScaleAdapter: project analyzed, "
                        f"project_id={profile.project_id}, "
                        f"scale={scale.value}, complexity={complexity.value}")
        except Exception as e:
            logger.error(f"LargeScaleAdapter: analyze_project failed: {e}")
            profile = ProjectProfile()
        return profile

    def _assess_scale(self, project_data: Dict[str, Any]) -> ProjectScale:
        """评估项目规模"""
        logger.debug("LargeScaleAdapter: assessing project scale")
        try:
            file_count = project_data.get("file_count", 0)
            module_count = project_data.get("module_count", 0)

            # 综合文件数和模块数评估规模
            if file_count > 5000 or module_count > 200:
                scale = ProjectScale.ENTERPRISE
            elif file_count > 1000 or module_count > 50:
                scale = ProjectScale.LARGE
            elif file_count > 200 or module_count > 10:
                scale = ProjectScale.MEDIUM
            else:
                scale = ProjectScale.SMALL

            logger.debug(f"LargeScaleAdapter: assessed scale={scale.value}, "
                         f"file_count={file_count}, module_count={module_count}")
        except Exception as e:
            logger.error(f"LargeScaleAdapter: _assess_scale failed: {e}")
            scale = ProjectScale.SMALL
        return scale

    def _evaluate_complexity(self, scale: ProjectScale,
                             dependency_depth: int) -> RefactorComplexity:
        """评估重构复杂度"""
        logger.debug(f"LargeScaleAdapter: evaluating complexity, "
                     f"scale={scale.value}, depth={dependency_depth}")
        try:
            if scale == ProjectScale.ENTERPRISE and dependency_depth > 8:
                complexity = RefactorComplexity.EXTREME
            elif scale in (ProjectScale.ENTERPRISE, ProjectScale.LARGE) and dependency_depth > 5:
                complexity = RefactorComplexity.COMPLEX
            elif scale in (ProjectScale.LARGE, ProjectScale.MEDIUM) and dependency_depth > 3:
                complexity = RefactorComplexity.MODERATE
            else:
                complexity = RefactorComplexity.SIMPLE

            logger.debug(f"LargeScaleAdapter: evaluated complexity={complexity.value}")
        except Exception as e:
            logger.error(f"LargeScaleAdapter: _evaluate_complexity failed: {e}")
            complexity = RefactorComplexity.SIMPLE
        return complexity

    def _plan_refactoring(self, profile: ProjectProfile) -> Dict[str, Any]:
        """规划重构方案"""
        logger.info(f"LargeScaleAdapter: planning refactoring, "
                    f"project_id={profile.project_id}, "
                    f"scale={profile.scale.value}")
        try:
            phases: List[Dict[str, Any]] = []

            if profile.complexity == RefactorComplexity.EXTREME:
                phases = [
                    {"phase": "准备阶段", "tasks": ["建立重构基线", "创建回滚方案", "搭建测试环境"]},
                    {"phase": "拆分阶段", "tasks": ["模块边界划定", "依赖解耦", "接口抽象"]},
                    {"phase": "迁移阶段", "tasks": ["渐进式迁移", "数据迁移", "流量切换"]},
                    {"phase": "验证阶段", "tasks": ["集成测试", "性能验证", "回归测试"]},
                ]
            elif profile.complexity == RefactorComplexity.COMPLEX:
                phases = [
                    {"phase": "准备阶段", "tasks": ["建立重构基线", "创建回滚方案"]},
                    {"phase": "重构阶段", "tasks": ["模块拆分", "依赖解耦", "接口重构"]},
                    {"phase": "验证阶段", "tasks": ["集成测试", "回归测试"]},
                ]
            elif profile.complexity == RefactorComplexity.MODERATE:
                phases = [
                    {"phase": "重构阶段", "tasks": ["局部重构", "依赖优化"]},
                    {"phase": "验证阶段", "tasks": ["单元测试", "集成测试"]},
                ]
            else:
                phases = [
                    {"phase": "重构阶段", "tasks": ["代码优化", "结构调整"]},
                ]

            plan: Dict[str, Any] = {
                "project_id": profile.project_id,
                "scale": profile.scale.value,
                "complexity": profile.complexity.value,
                "phases": phases,
                "estimated_duration": self._estimate_duration(profile),
                "risk_level": self._assess_risk(profile),
                "timestamp": time.time(),
            }

            self._plans[profile.project_id] = plan
            logger.info(f"LargeScaleAdapter: refactoring plan created, "
                        f"phases={len(phases)}")
        except Exception as e:
            logger.error(f"LargeScaleAdapter: _plan_refactoring failed: {e}")
            plan = {"project_id": profile.project_id, "error": str(e)}
        return plan

    def _estimate_duration(self, profile: ProjectProfile) -> float:
        """估算重构持续时间（天）"""
        logger.debug(f"LargeScaleAdapter: estimating duration, "
                     f"complexity={profile.complexity.value}")
        try:
            duration_map = {
                RefactorComplexity.SIMPLE: 3.0,
                RefactorComplexity.MODERATE: 14.0,
                RefactorComplexity.COMPLEX: 45.0,
                RefactorComplexity.EXTREME: 120.0,
            }
            duration = duration_map.get(profile.complexity, 3.0)
            # 根据文件数量调整
            if profile.file_count > 1000:
                duration *= 1.5
            logger.debug(f"LargeScaleAdapter: estimated duration={duration} days")
        except Exception as e:
            logger.error(f"LargeScaleAdapter: _estimate_duration failed: {e}")
            duration = 3.0
        return duration

    def _assess_risk(self, profile: ProjectProfile) -> str:
        """评估重构风险等级"""
        logger.debug(f"LargeScaleAdapter: assessing risk, "
                     f"complexity={profile.complexity.value}")
        try:
            if profile.complexity == RefactorComplexity.EXTREME:
                risk = "critical"
            elif profile.complexity == RefactorComplexity.COMPLEX:
                risk = "high"
            elif profile.complexity == RefactorComplexity.MODERATE:
                risk = "medium"
            else:
                risk = "low"
            logger.debug(f"LargeScaleAdapter: risk level={risk}")
        except Exception as e:
            logger.error(f"LargeScaleAdapter: _assess_risk failed: {e}")
            risk = "low"
        return risk

    def _optimize_for_scale(self, profile: ProjectProfile,
                            plan: Dict[str, Any]) -> Dict[str, Any]:
        """针对项目规模优化重构方案"""
        logger.info(f"LargeScaleAdapter: optimizing for scale, "
                    f"scale={profile.scale.value}")
        try:
            optimized_plan = dict(plan)
            optimizations: List[str] = []

            if profile.scale == ProjectScale.ENTERPRISE:
                optimizations.extend([
                    "启用增量重构策略",
                    "建立灰度发布机制",
                    "配置自动化回滚",
                    "实施并行重构",
                ])
            elif profile.scale == ProjectScale.LARGE:
                optimizations.extend([
                    "启用增量重构策略",
                    "建立灰度发布机制",
                    "配置自动化回滚",
                ])
            elif profile.scale == ProjectScale.MEDIUM:
                optimizations.extend([
                    "启用增量重构策略",
                    "建立回滚方案",
                ])
            else:
                optimizations.append("一次性重构")

            optimized_plan["optimizations"] = optimizations
            logger.info(f"LargeScaleAdapter: optimization completed, "
                        f"optimizations={len(optimizations)}")
        except Exception as e:
            logger.error(f"LargeScaleAdapter: _optimize_for_scale failed: {e}")
            optimized_plan = dict(plan)
            optimized_plan["optimizations"] = []
        return optimized_plan

    def generate_adaptation_plan(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成适配计划"""
        logger.info("LargeScaleAdapter: generating adaptation plan")
        try:
            # 1. 分析项目
            profile = self.analyze_project(project_data)
            # 2. 规划重构
            plan = self._plan_refactoring(profile)
            # 3. 优化方案
            optimized = self._optimize_for_scale(profile, plan)

            logger.info(f"LargeScaleAdapter: adaptation plan generated, "
                        f"project_id={profile.project_id}")
        except Exception as e:
            logger.error(f"LargeScaleAdapter: generate_adaptation_plan failed: {e}")
            optimized = {"error": str(e)}
        return optimized


class LargeScaleService:
    """大项目适配服务"""

    def __init__(self, adapter: Optional[LargeScaleAdapter] = None):
        """初始化大项目适配服务"""
        self.adapter = adapter or LargeScaleAdapter()
        logger.info("LargeScaleService initialized")

    def adapt(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行项目适配"""
        logger.info("LargeScaleService: adapting project")
        return self.adapter.generate_adaptation_plan(project_data)

    def get_plan(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取适配计划"""
        logger.debug(f"LargeScaleService: getting plan, project_id={project_id}")
        return self.adapter._plans.get(project_id)

    def get_profile(self, project_id: str) -> Optional[ProjectProfile]:
        """获取项目画像"""
        logger.debug(f"LargeScaleService: getting profile, project_id={project_id}")
        return self.adapter._profiles.get(project_id)
