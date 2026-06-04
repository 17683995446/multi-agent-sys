"""
全自动拆解为原子任务清单模块

职责：将复杂需求自动拆解为可执行的原子任务清单，支持多种拆解策略，估算复杂度和优先级

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DecompositionStrategy(str, Enum):
    """拆解策略"""
    BY_FEATURE = "by_feature"
    BY_MODULE = "by_module"
    BY_LAYER = "by_layer"
    BY_RESPONSIBILITY = "by_responsibility"


class AtomTaskType(str, Enum):
    """原子任务类型"""
    DESIGN = "design"
    CODE = "code"
    TEST = "test"
    REVIEW = "review"
    DOC = "doc"


@dataclass
class AtomTask:
    """原子任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: AtomTaskType = AtomTaskType.CODE
    name: str = ""
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    estimated_complexity: float = 1.0
    priority: int = 0

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"AtomTask created: task_id={self.task_id}, "
                     f"type={self.task_type.value}, name={self.name}")


class AutoDecomposer:
    """自动拆解器"""

    def __init__(self):
        """初始化自动拆解器"""
        self._tasks: List[AtomTask] = []
        self._strategy: Optional[DecompositionStrategy] = None
        logger.info("AutoDecomposer initialized")

    def decompose(self, requirements: Dict[str, Any],
                  strategy: DecompositionStrategy = DecompositionStrategy.BY_FEATURE) -> List[AtomTask]:
        """拆解需求为原子任务清单"""
        logger.info(f"AutoDecomposer: decomposing requirements, "
                    f"strategy={strategy.value}, keys={list(requirements.keys())}")
        try:
            self._strategy = strategy
            analysis = self._analyze_requirements(requirements)

            if strategy == DecompositionStrategy.BY_FEATURE:
                tasks = self._split_by_feature(requirements, analysis)
            elif strategy == DecompositionStrategy.BY_MODULE:
                tasks = self._split_by_module(requirements, analysis)
            elif strategy == DecompositionStrategy.BY_LAYER:
                tasks = self._split_by_layer(requirements, analysis)
            elif strategy == DecompositionStrategy.BY_RESPONSIBILITY:
                tasks = self._split_by_responsibility(requirements, analysis)
            else:
                tasks = self._split_by_feature(requirements, analysis)

            for task in tasks:
                task.estimated_complexity = self._estimate_complexity(task, analysis)
                task.priority = self._calculate_priority(task, analysis)

            self._tasks = tasks
            logger.info(f"AutoDecomposer: decomposed into {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"AutoDecomposer: decompose failed: {e}")
            tasks = []
        return tasks

    def _analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析需求，提取关键信息"""
        logger.debug("AutoDecomposer: analyzing requirements")
        try:
            analysis: Dict[str, Any] = {
                "feature_count": len(requirements.get("features", [])),
                "module_count": len(requirements.get("modules", [])),
                "layer_count": len(requirements.get("layers", [])),
                "complexity": requirements.get("complexity", "medium"),
                "has_api": requirements.get("has_api", False),
                "has_ui": requirements.get("has_ui", False),
                "has_db": requirements.get("has_db", False),
            }
            logger.debug(f"AutoDecomposer: analysis result={analysis}")
        except Exception as e:
            logger.error(f"AutoDecomposer: _analyze_requirements failed: {e}")
            analysis = {"feature_count": 0, "module_count": 0, "layer_count": 0,
                        "complexity": "medium"}
        return analysis

    def _split_by_feature(self, requirements: Dict[str, Any],
                          analysis: Dict[str, Any]) -> List[AtomTask]:
        """按功能拆解"""
        logger.debug("AutoDecomposer: splitting by feature")
        tasks: List[AtomTask] = []
        try:
            features = requirements.get("features", [])
            if not features:
                features = ["default_feature"]

            for i, feature in enumerate(features):
                feature_name = feature if isinstance(feature, str) else feature.get("name", f"feature_{i}")
                design_task = AtomTask(
                    task_type=AtomTaskType.DESIGN,
                    name=f"设计_{feature_name}",
                    description=f"设计功能 {feature_name} 的架构和接口",
                    priority=len(features) - i,
                )
                code_task = AtomTask(
                    task_type=AtomTaskType.CODE,
                    name=f"编码_{feature_name}",
                    description=f"实现功能 {feature_name} 的核心逻辑",
                    dependencies=[design_task.task_id],
                    priority=len(features) - i,
                )
                test_task = AtomTask(
                    task_type=AtomTaskType.TEST,
                    name=f"测试_{feature_name}",
                    description=f"为功能 {feature_name} 编写单元测试",
                    dependencies=[code_task.task_id],
                    priority=len(features) - i,
                )
                tasks.extend([design_task, code_task, test_task])
            logger.info(f"AutoDecomposer: split by feature into {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"AutoDecomposer: _split_by_feature failed: {e}")
        return tasks

    def _split_by_module(self, requirements: Dict[str, Any],
                         analysis: Dict[str, Any]) -> List[AtomTask]:
        """按模块拆解"""
        logger.debug("AutoDecomposer: splitting by module")
        tasks: List[AtomTask] = []
        try:
            modules = requirements.get("modules", [])
            if not modules:
                modules = ["default_module"]

            for i, module in enumerate(modules):
                module_name = module if isinstance(module, str) else module.get("name", f"module_{i}")
                code_task = AtomTask(
                    task_type=AtomTaskType.CODE,
                    name=f"实现_{module_name}",
                    description=f"实现模块 {module_name} 的完整功能",
                    priority=len(modules) - i,
                )
                test_task = AtomTask(
                    task_type=AtomTaskType.TEST,
                    name=f"测试_{module_name}",
                    description=f"为模块 {module_name} 编写测试",
                    dependencies=[code_task.task_id],
                    priority=len(modules) - i,
                )
                review_task = AtomTask(
                    task_type=AtomTaskType.REVIEW,
                    name=f"评审_{module_name}",
                    description=f"评审模块 {module_name} 的代码质量",
                    dependencies=[test_task.task_id],
                    priority=len(modules) - i,
                )
                tasks.extend([code_task, test_task, review_task])
            logger.info(f"AutoDecomposer: split by module into {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"AutoDecomposer: _split_by_module failed: {e}")
        return tasks

    def _split_by_layer(self, requirements: Dict[str, Any],
                        analysis: Dict[str, Any]) -> List[AtomTask]:
        """按层次拆解"""
        logger.debug("AutoDecomposer: splitting by layer")
        tasks: List[AtomTask] = []
        try:
            layers = requirements.get("layers", [])
            if not layers:
                layers = ["presentation", "business", "data"]

            prev_task_id: Optional[str] = None
            for i, layer in enumerate(layers):
                layer_name = layer if isinstance(layer, str) else layer.get("name", f"layer_{i}")
                deps = [prev_task_id] if prev_task_id else []
                design_task = AtomTask(
                    task_type=AtomTaskType.DESIGN,
                    name=f"设计_{layer_name}层",
                    description=f"设计 {layer_name} 层的接口和交互",
                    dependencies=deps,
                    priority=len(layers) - i,
                )
                code_task = AtomTask(
                    task_type=AtomTaskType.CODE,
                    name=f"实现_{layer_name}层",
                    description=f"实现 {layer_name} 层的核心逻辑",
                    dependencies=[design_task.task_id],
                    priority=len(layers) - i,
                )
                prev_task_id = code_task.task_id
                tasks.extend([design_task, code_task])
            logger.info(f"AutoDecomposer: split by layer into {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"AutoDecomposer: _split_by_layer failed: {e}")
        return tasks

    def _split_by_responsibility(self, requirements: Dict[str, Any],
                                 analysis: Dict[str, Any]) -> List[AtomTask]:
        """按职责拆解"""
        logger.debug("AutoDecomposer: splitting by responsibility")
        tasks: List[AtomTask] = []
        try:
            responsibilities = requirements.get("responsibilities", [])
            if not responsibilities:
                responsibilities = ["core_logic", "data_handling", "interface"]

            for i, resp in enumerate(responsibilities):
                resp_name = resp if isinstance(resp, str) else resp.get("name", f"resp_{i}")
                design_task = AtomTask(
                    task_type=AtomTaskType.DESIGN,
                    name=f"设计_{resp_name}",
                    description=f"设计职责 {resp_name} 的方案",
                    priority=len(responsibilities) - i,
                )
                code_task = AtomTask(
                    task_type=AtomTaskType.CODE,
                    name=f"编码_{resp_name}",
                    description=f"实现职责 {resp_name} 的代码",
                    dependencies=[design_task.task_id],
                    priority=len(responsibilities) - i,
                )
                test_task = AtomTask(
                    task_type=AtomTaskType.TEST,
                    name=f"测试_{resp_name}",
                    description=f"验证职责 {resp_name} 的正确性",
                    dependencies=[code_task.task_id],
                    priority=len(responsibilities) - i,
                )
                doc_task = AtomTask(
                    task_type=AtomTaskType.DOC,
                    name=f"文档_{resp_name}",
                    description=f"编写职责 {resp_name} 的文档",
                    dependencies=[test_task.task_id],
                    priority=len(responsibilities) - i,
                )
                tasks.extend([design_task, code_task, test_task, doc_task])
            logger.info(f"AutoDecomposer: split by responsibility into {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"AutoDecomposer: _split_by_responsibility failed: {e}")
        return tasks

    def _estimate_complexity(self, task: AtomTask,
                             analysis: Dict[str, Any]) -> float:
        """估算任务复杂度"""
        logger.debug(f"AutoDecomposer: estimating complexity for task={task.task_id}")
        try:
            base_complexity = {
                AtomTaskType.DESIGN: 2.0,
                AtomTaskType.CODE: 5.0,
                AtomTaskType.TEST: 3.0,
                AtomTaskType.REVIEW: 2.0,
                AtomTaskType.DOC: 1.5,
            }
            complexity = base_complexity.get(task.task_type, 3.0)

            if analysis.get("complexity") == "high":
                complexity *= 1.5
            elif analysis.get("complexity") == "low":
                complexity *= 0.7

            if analysis.get("has_api"):
                complexity *= 1.1
            if analysis.get("has_ui"):
                complexity *= 1.2
            if analysis.get("has_db"):
                complexity *= 1.15

            return round(complexity, 2)
        except Exception as e:
            logger.error(f"AutoDecomposer: _estimate_complexity failed: {e}")
            return 3.0

    def _calculate_priority(self, task: AtomTask,
                            analysis: Dict[str, Any]) -> int:
        """计算任务优先级"""
        logger.debug(f"AutoDecomposer: calculating priority for task={task.task_id}")
        try:
            priority = task.priority
            if task.task_type == AtomTaskType.DESIGN:
                priority += 10
            elif task.task_type == AtomTaskType.CODE:
                priority += 5
            elif task.task_type == AtomTaskType.TEST:
                priority += 3
            elif task.task_type == AtomTaskType.REVIEW:
                priority += 2
            elif task.task_type == AtomTaskType.DOC:
                priority += 1
            return max(0, priority)
        except Exception as e:
            logger.error(f"AutoDecomposer: _calculate_priority failed: {e}")
            return 0

    def generate_task_list(self) -> Dict[str, Any]:
        """生成任务清单报告"""
        logger.info("AutoDecomposer: generating task list")
        try:
            by_type: Dict[str, int] = {}
            total_complexity = 0.0
            for task in self._tasks:
                by_type[task.task_type.value] = by_type.get(task.task_type.value, 0) + 1
                total_complexity += task.estimated_complexity

            task_list: Dict[str, Any] = {
                "total_tasks": len(self._tasks),
                "by_type": by_type,
                "total_complexity": round(total_complexity, 2),
                "avg_complexity": round(total_complexity / len(self._tasks), 2) if self._tasks else 0.0,
                "strategy": self._strategy.value if self._strategy else "unknown",
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "type": t.task_type.value,
                        "name": t.name,
                        "description": t.description,
                        "dependencies": t.dependencies,
                        "complexity": t.estimated_complexity,
                        "priority": t.priority,
                    }
                    for t in self._tasks
                ],
            }
            logger.info(f"AutoDecomposer: task list generated, "
                        f"total={len(self._tasks)}")
        except Exception as e:
            logger.error(f"AutoDecomposer: generate_task_list failed: {e}")
            task_list = {"error": str(e)}
        return task_list


class AutoDecomposeService:
    """自动拆解服务"""

    def __init__(self, decomposer: Optional[AutoDecomposer] = None):
        """初始化自动拆解服务"""
        self.decomposer = decomposer or AutoDecomposer()
        logger.info("AutoDecomposeService initialized")

    def decompose(self, requirements: Dict[str, Any],
                  strategy: DecompositionStrategy = DecompositionStrategy.BY_FEATURE) -> List[AtomTask]:
        """执行需求拆解"""
        logger.info("AutoDecomposeService: decomposing requirements")
        return self.decomposer.decompose(requirements, strategy)

    def get_task_list(self) -> Dict[str, Any]:
        """获取任务清单"""
        logger.debug("AutoDecomposeService: getting task list")
        return self.decomposer.generate_task_list()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        logger.debug("AutoDecomposeService: getting statistics")
        task_list = self.decomposer.generate_task_list()
        if "error" in task_list:
            return task_list
        return {
            "total_tasks": task_list.get("total_tasks", 0),
            "by_type": task_list.get("by_type", {}),
            "total_complexity": task_list.get("total_complexity", 0.0),
            "avg_complexity": task_list.get("avg_complexity", 0.0),
        }
