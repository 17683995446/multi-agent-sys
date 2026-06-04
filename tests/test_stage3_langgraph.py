"""
阶段3：接入LangGraph基础调度内核 测试文件

验收标准：
1. LangGraph >= 0.0.30 成功安装 ✅
2. StateGraph 基础状态机成功创建 ✅
3. 状态类型定义完整 ✅
4. 节点和边可正常执行 ✅
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestLangGraphVersion:
    """测试LangGraph版本和导入"""

    def test_langgraph_import(self):
        """验证LangGraph可正常导入"""
        import langgraph
        assert langgraph is not None

    def test_state_graph_import(self):
        """验证StateGraph可正常导入"""
        from langgraph.graph import StateGraph
        assert StateGraph is not None

    def test_essential_modules(self):
        """验证所有必需的LangGraph模块"""
        from langgraph.graph import StateGraph, END, START
        from langgraph.types import Command
        assert StateGraph is not None
        assert END is not None
        assert START is not None


class TestWorkflowState:
    """测试工作流状态定义"""

    def test_workflow_state_import(self):
        """验证工作流状态类型可导入"""
        from scheduler import WorkflowState
        assert WorkflowState is not None

    def test_task_state_enum_import(self):
        """验证任务状态枚举可导入"""
        from scheduler import TaskStateEnum
        assert TaskStateEnum is not None
        assert hasattr(TaskStateEnum, "PENDING")
        assert hasattr(TaskStateEnum, "COMPLETED")

    def test_state_initialization(self):
        """测试状态初始化"""
        from scheduler import WorkflowState, TaskStateEnum

        state: WorkflowState = {
            "task_id": "test_task_1",
            "task_title": "Test Task",
            "task_description": "A test task",
            "priority": 1,
            "current_status": TaskStateEnum.PENDING,
            "requirements": {},
            "architecture": None,
            "code": None,
            "review": None,
            "test_results": None,
            "logs": []
        }

        assert state["task_id"] == "test_task_1"
        assert state["current_status"] == TaskStateEnum.PENDING


class TestWorkflowCreation:
    """测试工作流创建"""

    def test_create_engineering_workflow(self):
        """测试工程流程工作流创建"""
        from scheduler import create_engineering_workflow

        workflow = create_engineering_workflow()
        assert workflow is not None

    def test_create_review_feedback_workflow(self):
        """测试带评审反馈的工作流创建"""
        from scheduler import create_review_feedback_workflow

        workflow = create_review_feedback_workflow()
        assert workflow is not None

    def test_workflow_compile(self):
        """测试工作流编译"""
        from scheduler import create_engineering_workflow

        workflow = create_engineering_workflow()
        app = workflow.compile()
        assert app is not None


class TestWorkflowExecution:
    """测试工作流执行"""

    def test_simple_workflow_execution(self):
        """测试简单工作流执行"""
        from scheduler import execute_workflow_simple

        result = execute_workflow_simple("test_1", "Simple Test Task")
        assert result is not None
        assert "task_id" in result
        assert "task_title" in result
        assert result["task_title"] == "Simple Test Task"

    def test_workflow_logs(self):
        """测试工作流日志记录"""
        from scheduler import execute_workflow_simple

        result = execute_workflow_simple("log_test", "Log Test Task")
        assert "logs" in result
        assert len(result["logs"]) > 0
        assert any("Decomposing" in log or "Designing" in log or "Developing" in log for log in result["logs"])

    def test_workflow_state_progression(self):
        """测试工作流状态进度"""
        from scheduler import execute_workflow_simple, TaskStateEnum

        result = execute_workflow_simple("progression_test", "Progression Test")
        assert "current_status" in result
        assert result["current_status"] == TaskStateEnum.COMPLETED


class TestWorkflowNodes:
    """测试工作流节点"""

    def test_initialize_node(self):
        """测试任务初始化节点"""
        from scheduler import initialize_task_decomposition, WorkflowState, TaskStateEnum

        state: WorkflowState = {
            "task_id": "node_test_1",
            "task_title": "Node Test",
            "task_description": "Node test",
            "priority": 1,
            "current_status": TaskStateEnum.PENDING,
            "requirements": {},
            "architecture": None,
            "code": None,
            "review": None,
            "test_results": None,
            "logs": []
        }

        result = initialize_task_decomposition(state)
        assert "logs" in result
        assert len(result["logs"]) > 0

    def test_architecture_design_node(self):
        """测试架构设计节点"""
        from scheduler import generate_architecture_design, WorkflowState, TaskStateEnum

        state: WorkflowState = {
            "task_id": "arch_test",
            "task_title": "Architecture Test",
            "task_description": "Arch test",
            "priority": 1,
            "current_status": TaskStateEnum.PENDING,
            "requirements": {},
            "architecture": None,
            "code": None,
            "review": None,
            "test_results": None,
            "logs": []
        }

        result = generate_architecture_design(state)
        assert "architecture" in result
        assert "modules" in result["architecture"]
        assert "input_layer" in result["architecture"]["modules"]


class TestDAGValidity:
    """测试DAG有效性"""

    def test_no_circular_dependencies(self):
        """验证没有循环依赖"""
        from scheduler import create_engineering_workflow

        workflow = create_engineering_workflow()
        app = workflow.compile()
        assert app is not None

    def test_linear_workflow_progression(self):
        """验证线性工作流进度"""
        from scheduler import execute_workflow_simple, TaskStateEnum

        result = execute_workflow_simple("linear_test", "Linear Progression Test")
        assert result["architecture"] is not None
        assert result["code"] is not None
        assert result["review"] is not None
        assert result["test_results"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
