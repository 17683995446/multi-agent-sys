from typing import Dict, List, Optional, Any
from .metagpt_core import (
    BaseRole, RoleType, Task, TaskStatus, Message,
    WorkflowTemplate, RoleRegistry, create_default_registry
)


class WorkflowEngine:
    """工作流引擎，负责执行任务协作"""
    
    def __init__(self, registry: Optional[RoleRegistry] = None):
        self.registry = registry or create_default_registry()
        self.tasks: Dict[str, Task] = {}
        self.task_outputs: Dict[str, Any] = {}
    
    def load_workflow(self, template: WorkflowTemplate) -> None:
        """加载工作流模板"""
        for task in template.tasks:
            self.tasks[task.id] = task
    
    def get_ready_tasks(self) -> List[Task]:
        """获取准备好的任务（依赖已完成）"""
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                deps_completed = all(
                    self.tasks.get(dep_id, Task(id=dep_id, title="", description="", role=RoleType.ENGINEER, status=TaskStatus.COMPLETED)).status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                if deps_completed:
                    ready.append(task)
        return ready
    
    def execute_task(self, task_id: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """执行单个任务"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        role = self.registry.get(task.role)
        if not role:
            raise ValueError(f"Role {task.role} not found")
        
        task.status = TaskStatus.IN_PROGRESS
        
        # 简单执行：根据角色类型选择默认动作
        action_map = {
            RoleType.PRODUCT_MANAGER: "define_prd",
            RoleType.ARCHITECT: "design_architecture",
            RoleType.ENGINEER: "write_code",
            RoleType.TESTER: "execute_tests"
        }
        
        action_name = action_map.get(task.role, "")
        if not action_name:
            raise ValueError(f"No default action for role {task.role}")
        
        output = role.execute_action(action_name, context or {})
        task.output = str(output)
        task.status = TaskStatus.COMPLETED
        self.task_outputs[task_id] = output
        
        return output
    
    def run_workflow(self, entry_point: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """运行整个工作流"""
        # 从入口点开始执行所有准备好的任务
        while True:
            ready_tasks = self.get_ready_tasks()
            if not ready_tasks:
                break
            
            for task in ready_tasks:
                self.execute_task(task.id, context)
        
        return self.task_outputs


def create_standard_development_workflow() -> WorkflowTemplate:
    """创建标准开发工作流模板"""
    tasks = [
        Task(
            id="task-1",
            title="Define PRD",
            description="Define product requirements",
            role=RoleType.PRODUCT_MANAGER,
            dependencies=[]
        ),
        Task(
            id="task-2",
            title="Design Architecture",
            description="Design system architecture",
            role=RoleType.ARCHITECT,
            dependencies=["task-1"]
        ),
        Task(
            id="task-3",
            title="Write Code",
            description="Implement features",
            role=RoleType.ENGINEER,
            dependencies=["task-2"]
        ),
        Task(
            id="task-4",
            title="Test",
            description="Test the system",
            role=RoleType.TESTER,
            dependencies=["task-3"]
        )
    ]
    
    return WorkflowTemplate(
        name="Standard Development Workflow",
        description="Standard software development process",
        tasks=tasks,
        entry_point="task-1"
    )
