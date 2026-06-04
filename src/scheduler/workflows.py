"""
多Agent软件工程系统 - LangGraph工作流实现

使用LangGraph实现完整的工程流程编排
"""

from typing import Annotated, Literal
from operator import add
from datetime import datetime
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from .langgraph_core import (
    WorkflowState, TaskStateEnum,
    initialize_task_decomposition,
    generate_architecture_design,
    code_development,
    code_review,
    code_testing,
    finalize_task
)


def create_engineering_workflow() -> StateGraph:
    """
    创建工程流程工作流
    第一性原理：单向依赖DAG
    """
    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("initialize", initialize_task_decomposition)
    workflow.add_node("design", generate_architecture_design)
    workflow.add_node("develop", code_development)
    workflow.add_node("review", code_review)
    workflow.add_node("test", code_testing)
    workflow.add_node("finalize", finalize_task)

    # 添加边（单向依赖）
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "design")
    workflow.add_edge("design", "develop")
    workflow.add_edge("develop", "review")
    workflow.add_edge("review", "test")
    workflow.add_edge("test", "finalize")
    workflow.add_edge("finalize", END)

    # 编译工作流
    return workflow


def create_review_feedback_workflow() -> StateGraph:
    """
    创建带评审反馈的工作流（包含循环分支）
    """
    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("initialize", initialize_task_decomposition)
    workflow.add_node("design", generate_architecture_design)
    workflow.add_node("develop", code_development)
    workflow.add_node("review", code_review)

    # 添加条件边
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "design")
    workflow.add_edge("design", "develop")
    workflow.add_edge("develop", "review")

    # 评审后的条件路由
    def route_review_result(state: WorkflowState) -> Literal["test", "develop", END]:
        if state['current_status'] == TaskStateEnum.REVIEWED and state['review']:
            if state['review']['status'] == "passed":
                return "test"
            else:
                return "develop"
        return END

    workflow.add_conditional_edges(
        "review",
        route_review_result,
        {
            "develop": "develop",
            "test": "test",
            END: END
        }
    )

    workflow.add_node("test", code_testing)
    workflow.add_node("finalize", finalize_task)
    workflow.add_edge("test", "finalize")
    workflow.add_edge("finalize", END)

    return workflow


def execute_workflow_simple(task_id: str, task_title: str) -> dict:
    """
    执行简单的工作流
    """
    workflow = create_engineering_workflow()
    app = workflow.compile()

    initial_state: WorkflowState = {
        "task_id": task_id,
        "task_title": task_title,
        "task_description": "A task to execute",
        "priority": 1,
        "current_status": TaskStateEnum.PENDING,
        "requirements": {},
        "architecture": None,
        "code": None,
        "review": None,
        "test_results": None,
        "logs": []
    }

    result = app.invoke(initial_state)
    return result


def get_workflow_stream(task_id: str, task_title: str):
    """
    获取工作流执行流（用于可视化）
    """
    workflow = create_engineering_workflow()
    app = workflow.compile()
    return app.stream(
        {
            "task_id": task_id,
            "task_title": task_title,
            "task_description": "Stream test",
            "priority": 1,
            "current_status": TaskStateEnum.PENDING,
            "requirements": {},
            "architecture": None,
            "code": None,
            "review": None,
            "test_results": None,
            "logs": []
        },
        stream_mode="updates"
    )
