"""
HTD层级任务拆解算法
职责：层级任务分解、分解结果验证、性能优化
"""

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SubTask:
    """子任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    level: int = 0
    parent_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    estimated_time: float = 0.0
    actual_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List["SubTask"] = field(default_factory=list)
    
    def add_child(self, child: "SubTask") -> None:
        """添加子任务"""
        child.parent_id = self.task_id
        child.level = self.level + 1
        self.children.append(child)
    
    def is_leaf(self) -> bool:
        """是否是叶子节点"""
        return len(self.children) == 0
    
    def get_all_children(self) -> List["SubTask"]:
        """获取所有子任务（递归）"""
        all_children = []
        for child in self.children:
            all_children.append(child)
            all_children.extend(child.get_all_children())
        return all_children
    
    def get_leaf_tasks(self) -> List["SubTask"]:
        """获取所有叶子任务"""
        if self.is_leaf():
            return [self]
        leaves = []
        for child in self.children:
            leaves.extend(child.get_leaf_tasks())
        return leaves


@dataclass
class TaskDecomposition:
    """任务分解结果"""
    decomposition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    root_task: Optional[SubTask] = None
    total_levels: int = 0
    total_tasks: int = 0
    leaf_tasks_count: int = 0
    decomposition_time: float = 0.0
    validation_result: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HTDDecomposer:
    """HTD层级任务拆解器"""
    
    def __init__(self, max_levels: int = 5, min_task_size: float = 0.5):
        """
        初始化HTD拆解器
        
        Args:
            max_levels: 最大分解层级
            min_task_size: 最小任务估算时间（小时）
        """
        self.max_levels = max_levels
        self.min_task_size = min_task_size
        self.decomposition_rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict[str, Any]:
        """初始化分解规则"""
        return {
            "level_1": {
                "name": "阶段层",
                "description": "将大任务分解为主要阶段",
                "min_size": 8.0,
                "max_size": 40.0
            },
            "level_2": {
                "name": "模块层",
                "description": "将阶段分解为功能模块",
                "min_size": 4.0,
                "max_size": 8.0
            },
            "level_3": {
                "name": "功能层",
                "description": "将模块分解为具体功能",
                "min_size": 2.0,
                "max_size": 4.0
            },
            "level_4": {
                "name": "任务层",
                "description": "将功能分解为可执行任务",
                "min_size": 0.5,
                "max_size": 2.0
            },
            "level_5": {
                "name": "原子层",
                "description": "将任务分解为原子操作",
                "min_size": 0.1,
                "max_size": 0.5
            }
        }
    
    def decompose(self, task_name: str, task_description: str, 
                  estimated_time: float, 
                  custom_rules: Optional[Dict[str, Any]] = None) -> TaskDecomposition:
        """
        执行HTD层级分解
        
        Args:
            task_name: 任务名称
            task_description: 任务描述
            estimated_time: 预估时间（小时）
            custom_rules: 自定义分解规则
            
        Returns:
            任务分解结果
        """
        start_time = time.time()
        
        # 合并规则
        rules = self.decomposition_rules.copy()
        if custom_rules:
            rules.update(custom_rules)
        
        # 创建根任务
        root_task = SubTask(
            name=task_name,
            description=task_description,
            level=0,
            estimated_time=estimated_time,
            priority=TaskPriority.HIGH
        )
        
        # 执行递归分解
        self._decompose_recursive(root_task, 0, rules)
        
        # 统计信息
        all_tasks = [root_task] + root_task.get_all_children()
        leaf_tasks = root_task.get_leaf_tasks()
        max_level = max(task.level for task in all_tasks) if all_tasks else 0
        
        decomposition = TaskDecomposition(
            root_task=root_task,
            total_levels=max_level + 1,
            total_tasks=len(all_tasks),
            leaf_tasks_count=len(leaf_tasks),
            decomposition_time=time.time() - start_time,
            metadata={
                "max_levels_used": self.max_levels,
                "min_task_size": self.min_task_size,
                "rules_applied": rules
            }
        )
        
        # 验证分解结果
        decomposition.validation_result = self.validate(decomposition)
        
        return decomposition
    
    def _decompose_recursive(self, task: SubTask, current_level: int, 
                            rules: Dict[str, Any]) -> None:
        """
        递归分解任务
        
        Args:
            task: 当前任务
            current_level: 当前层级
            rules: 分解规则
        """
        # 检查是否达到最大层级
        if current_level >= self.max_levels:
            return
        
        # 检查任务大小是否需要分解
        if task.estimated_time <= self.min_task_size:
            return
        
        # 获取当前层级的规则
        level_key = f"level_{current_level + 1}"
        if level_key not in rules:
            return
        
        rule = rules[level_key]
        target_size = (rule["min_size"] + rule["max_size"]) / 2
        
        # 根据任务类型进行分解
        subtasks = self._generate_subtasks(task, current_level, rule)
        
        # 分配估算时间
        if subtasks and task.estimated_time > 0:
            time_per_task = task.estimated_time / len(subtasks)
            for subtask in subtasks:
                subtask.estimated_time = time_per_task
        
        # 添加子任务
        for subtask in subtasks:
            task.add_child(subtask)
            self._decompose_recursive(subtask, current_level + 1, rules)
    
    def _generate_subtasks(self, parent_task: SubTask, 
                          current_level: int, 
                          rule: Dict[str, Any]) -> List[SubTask]:
        """
        生成子任务
        
        Args:
            parent_task: 父任务
            current_level: 当前层级
            rule: 分解规则
            
        Returns:
            子任务列表
        """
        subtasks = []
        
        # 根据任务描述中的关键词进行智能分解
        keywords = self._extract_keywords(parent_task.description)
        
        if "设计" in keywords or "架构" in keywords:
            subtasks = self._decompose_design_task(parent_task, current_level)
        elif "开发" in keywords or "实现" in keywords or "编码" in keywords:
            subtasks = self._decompose_development_task(parent_task, current_level)
        elif "测试" in keywords or "验证" in keywords:
            subtasks = self._decompose_test_task(parent_task, current_level)
        elif "文档" in keywords:
            subtasks = self._decompose_document_task(parent_task, current_level)
        else:
            subtasks = self._decompose_generic_task(parent_task, current_level)
        
        return subtasks
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词"""
        keywords = {"设计", "架构", "开发", "实现", "编码", "测试", "验证", "文档"}
        found = set()
        for keyword in keywords:
            if keyword in text:
                found.add(keyword)
        return found
    
    def _decompose_design_task(self, parent_task: SubTask, 
                              current_level: int) -> List[SubTask]:
        """分解设计任务"""
        subtasks = [
            SubTask(
                name=f"{parent_task.name} - 需求分析",
                description="分析设计需求和约束条件",
                priority=TaskPriority.HIGH
            ),
            SubTask(
                name=f"{parent_task.name} - 方案设计",
                description="设计多个备选方案",
                priority=TaskPriority.HIGH
            ),
            SubTask(
                name=f"{parent_task.name} - 方案评审",
                description="评审并选择最优方案",
                priority=TaskPriority.MEDIUM
            ),
            SubTask(
                name=f"{parent_task.name} - 详细设计",
                description="完成详细设计文档",
                priority=TaskPriority.HIGH
            )
        ]
        return subtasks
    
    def _decompose_development_task(self, parent_task: SubTask, 
                                   current_level: int) -> List[SubTask]:
        """分解开发任务"""
        subtasks = [
            SubTask(
                name=f"{parent_task.name} - 环境准备",
                description="准备开发环境和依赖",
                priority=TaskPriority.MEDIUM
            ),
            SubTask(
                name=f"{parent_task.name} - 代码实现",
                description="编写核心代码",
                priority=TaskPriority.HIGH
            ),
            SubTask(
                name=f"{parent_task.name} - 单元测试",
                description="编写和运行单元测试",
                priority=TaskPriority.HIGH
            ),
            SubTask(
                name=f"{parent_task.name} - 代码审查",
                description="进行代码审查",
                priority=TaskPriority.MEDIUM
            )
        ]
        return subtasks
    
    def _decompose_test_task(self, parent_task: SubTask, 
                            current_level: int) -> List[SubTask]:
        """分解测试任务"""
        subtasks = [
            SubTask(
                name=f"{parent_task.name} - 测试计划",
                description="制定测试计划",
                priority=TaskPriority.MEDIUM
            ),
            SubTask(
                name=f"{parent_task.name} - 用例设计",
                description="设计测试用例",
                priority=TaskPriority.HIGH
            ),
            SubTask(
                name=f"{parent_task.name} - 测试执行",
                description="执行测试并记录结果",
                priority=TaskPriority.HIGH
            ),
            SubTask(
                name=f"{parent_task.name} - 缺陷修复",
                description="修复发现的缺陷",
                priority=TaskPriority.HIGH
            )
        ]
        return subtasks
    
    def _decompose_document_task(self, parent_task: SubTask, 
                                current_level: int) -> List[SubTask]:
        """分解文档任务"""
        subtasks = [
            SubTask(
                name=f"{parent_task.name} - 大纲设计",
                description="设计文档大纲",
                priority=TaskPriority.MEDIUM
            ),
            SubTask(
                name=f"{parent_task.name} - 内容编写",
                description="编写文档内容",
                priority=TaskPriority.HIGH
            ),
            SubTask(
                name=f"{parent_task.name} - 审核修订",
                description="审核和修订文档",
                priority=TaskPriority.MEDIUM
            ),
            SubTask(
                name=f"{parent_task.name} - 发布归档",
                description="发布并归档文档",
                priority=TaskPriority.LOW
            )
        ]
        return subtasks
    
    def _decompose_generic_task(self, parent_task: SubTask, 
                               current_level: int) -> List[SubTask]:
        """分解通用任务"""
        # 默认分解为3-4个子任务
        num_subtasks = min(4, max(2, int(parent_task.estimated_time / 2)))
        subtasks = []
        
        for i in range(num_subtasks):
            subtask = SubTask(
                name=f"{parent_task.name} - 子任务 {i + 1}",
                description=f"执行{parent_task.name}的第{i + 1}部分",
                priority=parent_task.priority
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def validate(self, decomposition: TaskDecomposition) -> Dict[str, Any]:
        """
        验证分解结果
        
        Args:
            decomposition: 任务分解结果
            
        Returns:
            验证结果
        """
        if not decomposition.root_task:
            return {
                "valid": False,
                "errors": ["No root task found"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # 检查原子性
        leaf_tasks = decomposition.root_task.get_leaf_tasks()
        for task in leaf_tasks:
            if task.estimated_time > self.min_task_size * 2:
                warnings.append(f"Task '{task.name}' might need further decomposition")
        
        # 检查完整性
        total_leaf_time = sum(task.estimated_time for task in leaf_tasks)
        root_time = decomposition.root_task.estimated_time
        if root_time > 0 and abs(total_leaf_time - root_time) > root_time * 0.1:
            warnings.append(f"Time mismatch: root={root_time}, leaves={total_leaf_time}")
        
        # 检查层级数
        if decomposition.total_levels > self.max_levels:
            warnings.append(f"Exceeded max levels: {decomposition.total_levels} > {self.max_levels}")
        
        # 检查是否有空任务
        empty_tasks = [t for t in leaf_tasks if not t.name.strip()]
        if empty_tasks:
            errors.append(f"Found {len(empty_tasks)} empty tasks")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "atom_check": "passed" if not warnings else "needs_review",
            "integrity_check": "passed" if not warnings else "needs_review"
        }
    
    def get_flat_task_list(self, decomposition: TaskDecomposition) -> List[SubTask]:
        """
        获取扁平化的任务列表
        
        Args:
            decomposition: 任务分解结果
            
        Returns:
            扁平化的任务列表
        """
        if not decomposition.root_task:
            return []
        
        all_tasks = [decomposition.root_task]
        all_tasks.extend(decomposition.root_task.get_all_children())
        return all_tasks
    
    def get_task_dependency_graph(self, decomposition: TaskDecomposition) -> Dict[str, List[str]]:
        """
        获取任务依赖图
        
        Args:
            decomposition: 任务分解结果
            
        Returns:
            依赖图 {task_id: [dependent_task_ids]}
        """
        if not decomposition.root_task:
            return {}
        
        all_tasks = self.get_flat_task_list(decomposition)
        graph = {task.task_id: [] for task in all_tasks}
        
        # 子任务依赖父任务完成
        for task in all_tasks:
            if task.parent_id:
                graph[task.parent_id].append(task.task_id)
        
        return graph


class HTDDecompositionService:
    """HTD分解服务"""
    
    def __init__(self):
        self.decomposer = HTDDecomposer()
        self.decompositions: Dict[str, TaskDecomposition] = {}
    
    def decompose_task(self, task_name: str, task_description: str, 
                      estimated_time: float,
                      max_levels: int = 5) -> TaskDecomposition:
        """
        分解任务
        
        Args:
            task_name: 任务名称
            task_description: 任务描述
            estimated_time: 预估时间
            max_levels: 最大层级
            
        Returns:
            分解结果
        """
        decomposer = HTDDecomposer(max_levels=max_levels)
        decomposition = decomposer.decompose(
            task_name, task_description, estimated_time
        )
        self.decompositions[decomposition.decomposition_id] = decomposition
        return decomposition
    
    def get_decomposition(self, decomposition_id: str) -> Optional[TaskDecomposition]:
        """获取分解结果"""
        return self.decompositions.get(decomposition_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.decompositions:
            return {"total_decompositions": 0}
        
        times = [d.decomposition_time for d in self.decompositions.values()]
        return {
            "total_decompositions": len(self.decompositions),
            "avg_time": sum(times) / len(times),
            "max_time": max(times),
            "min_time": min(times)
        }


_global_htd_service: Optional[HTDDecompositionService] = None


def get_htd_service() -> HTDDecompositionService:
    """获取全局HTD服务"""
    global _global_htd_service
    if _global_htd_service is None:
        _global_htd_service = HTDDecompositionService()
    return _global_htd_service


def reset_htd_service() -> None:
    """重置全局HTD服务"""
    global _global_htd_service
    _global_htd_service = None
