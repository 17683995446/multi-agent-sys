"""
阶段53验收测试：任务分发→开发执行链路
"""

import pytest

from src.architecture.pipeline_development import (
    TaskType, TaskStatus,
    DevelopmentTask,
    TaskDistributor, TaskExecutor, DevelopmentPipeline,
)


class TestTaskType:
    """测试任务类型枚举"""

    def test_type_values(self):
        """测试任务类型枚举值"""
        assert TaskType.DESIGN.value == "design"
        assert TaskType.CODING.value == "coding"
        assert TaskType.TESTING.value == "testing"
        assert TaskType.REVIEW.value == "review"
        assert TaskType.DOCUMENTATION.value == "documentation"

    def test_all_types(self):
        """测试所有任务类型"""
        types = list(TaskType)
        assert len(types) == 5


class TestTaskStatus:
    """测试任务状态枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        assert TaskStatus.CREATED.value == "created"
        assert TaskStatus.ASSIGNED.value == "assigned"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(TaskStatus)
        assert len(statuses) == 5


class TestDevelopmentTask:
    """测试开发任务"""

    def test_default_creation(self):
        """测试默认创建"""
        task = DevelopmentTask()
        assert task.task_id != ""
        assert task.task_type == TaskType.CODING
        assert task.description == ""
        assert task.assignee == ""
        assert task.status == TaskStatus.CREATED
        assert task.dependencies == []
        assert task.result == {}
        assert task.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        task = DevelopmentTask(
            task_type=TaskType.DESIGN,
            description="设计用户模块",
            assignee="design_agent",
            status=TaskStatus.ASSIGNED,
            dependencies=["dep-1"],
            result={"design_doc": "方案A"},
        )
        assert task.task_type == TaskType.DESIGN
        assert task.description == "设计用户模块"
        assert task.assignee == "design_agent"
        assert task.status == TaskStatus.ASSIGNED
        assert len(task.dependencies) == 1

    def test_unique_ids(self):
        """测试唯一ID"""
        t1 = DevelopmentTask()
        t2 = DevelopmentTask()
        assert t1.task_id != t2.task_id


class TestTaskDistributor:
    """测试任务分发器"""

    def test_initial_state(self):
        """测试初始状态"""
        distributor = TaskDistributor()
        assert len(distributor._tasks) == 0
        assert len(distributor._assignments) == 0

    def test_distribute_design_task(self):
        """测试分发设计任务"""
        distributor = TaskDistributor()
        task = DevelopmentTask(task_type=TaskType.DESIGN, description="设计模块")
        result = distributor.distribute(task)
        assert result.assignee == "design_agent"
        assert result.status == TaskStatus.ASSIGNED

    def test_distribute_coding_task(self):
        """测试分发编码任务"""
        distributor = TaskDistributor()
        task = DevelopmentTask(task_type=TaskType.CODING, description="编码实现")
        result = distributor.distribute(task)
        assert result.assignee == "coding_agent"
        assert result.status == TaskStatus.ASSIGNED

    def test_distribute_testing_task(self):
        """测试分发测试任务"""
        distributor = TaskDistributor()
        task = DevelopmentTask(task_type=TaskType.TESTING, description="单元测试")
        result = distributor.distribute(task)
        assert result.assignee == "testing_agent"

    def test_distribute_review_task(self):
        """测试分发评审任务"""
        distributor = TaskDistributor()
        task = DevelopmentTask(task_type=TaskType.REVIEW, description="代码评审")
        result = distributor.distribute(task)
        assert result.assignee == "review_agent"

    def test_distribute_documentation_task(self):
        """测试分发文档任务"""
        distributor = TaskDistributor()
        task = DevelopmentTask(task_type=TaskType.DOCUMENTATION, description="编写文档")
        result = distributor.distribute(task)
        assert result.assignee == "doc_agent"

    def test_distribute_invalid_task(self):
        """测试分发无效任务"""
        distributor = TaskDistributor()
        with pytest.raises(ValueError):
            distributor.distribute(DevelopmentTask(task_id=""))

    def test_distribute_with_unmet_dependencies(self):
        """测试依赖未满足时分发"""
        distributor = TaskDistributor()
        task = DevelopmentTask(
            task_type=TaskType.CODING,
            description="编码实现",
            dependencies=["nonexistent-dep"],
        )
        result = distributor.distribute(task)
        assert result.metadata.get("dependency_status") == "unmet"

    def test_distribute_with_met_dependencies(self):
        """测试依赖已满足时分发"""
        distributor = TaskDistributor()
        # 先完成一个任务
        dep_task = DevelopmentTask(task_type=TaskType.DESIGN, description="设计")
        dep_task.status = TaskStatus.COMPLETED
        distributor._tasks[dep_task.task_id] = dep_task

        # 分发依赖该任务的任务
        task = DevelopmentTask(
            task_type=TaskType.CODING,
            description="编码",
            dependencies=[dep_task.task_id],
        )
        result = distributor.distribute(task)
        assert result.status == TaskStatus.ASSIGNED

    def test_match_agent(self):
        """测试Agent匹配"""
        distributor = TaskDistributor()
        for ttype in TaskType:
            task = DevelopmentTask(task_type=ttype, description="测试")
            agent = distributor._match_agent(task)
            assert agent is not None

    def test_check_dependencies_no_deps(self):
        """测试无依赖检查"""
        distributor = TaskDistributor()
        task = DevelopmentTask(description="测试")
        assert distributor._check_dependencies(task) is True


class TestTaskExecutor:
    """测试任务执行器"""

    def test_initial_state(self):
        """测试初始状态"""
        executor = TaskExecutor()
        assert len(executor._execution_log) == 0

    def test_execute_design(self):
        """测试执行设计任务"""
        executor = TaskExecutor()
        task = DevelopmentTask(task_type=TaskType.DESIGN, description="设计用户模块")
        result = executor.execute(task)
        assert result.status == TaskStatus.COMPLETED
        assert "design_doc" in result.result
        assert "components" in result.result

    def test_execute_coding(self):
        """测试执行编码任务"""
        executor = TaskExecutor()
        task = DevelopmentTask(task_type=TaskType.CODING, description="实现登录功能")
        result = executor.execute(task)
        assert result.status == TaskStatus.COMPLETED
        assert "code_files" in result.result
        assert "lines_of_code" in result.result

    def test_execute_testing(self):
        """测试执行测试任务"""
        executor = TaskExecutor()
        task = DevelopmentTask(task_type=TaskType.TESTING, description="单元测试")
        result = executor.execute(task)
        assert result.status == TaskStatus.COMPLETED
        assert "test_cases" in result.result
        assert "coverage" in result.result

    def test_execute_review(self):
        """测试执行评审任务"""
        executor = TaskExecutor()
        task = DevelopmentTask(task_type=TaskType.REVIEW, description="代码评审")
        result = executor.execute(task)
        assert result.status == TaskStatus.COMPLETED
        assert "review_status" in result.result

    def test_execute_documentation(self):
        """测试执行文档任务"""
        executor = TaskExecutor()
        task = DevelopmentTask(task_type=TaskType.DOCUMENTATION, description="编写文档")
        result = executor.execute(task)
        assert result.status == TaskStatus.COMPLETED
        assert "doc_files" in result.result

    def test_execute_invalid_task(self):
        """测试执行无效任务"""
        executor = TaskExecutor()
        with pytest.raises(ValueError):
            executor.execute(DevelopmentTask(task_id=""))

    def test_execute_logs(self):
        """测试执行日志"""
        executor = TaskExecutor()
        task = DevelopmentTask(task_type=TaskType.CODING, description="测试")
        executor.execute(task)
        assert task.task_id in executor._execution_log
        assert executor._execution_log[task.task_id]["status"] == "success"


class TestDevelopmentPipeline:
    """测试任务分发→开发执行链路"""

    def test_initial_state(self):
        """测试初始状态"""
        pipeline = DevelopmentPipeline()
        assert len(pipeline._tasks) == 0

    def test_process_coding_task(self):
        """测试处理编码任务"""
        pipeline = DevelopmentPipeline()
        task = pipeline.process_task("实现用户登录功能", TaskType.CODING)
        assert task.status == TaskStatus.COMPLETED
        assert task.assignee == "coding_agent"
        assert "code_files" in task.result

    def test_process_design_task(self):
        """测试处理设计任务"""
        pipeline = DevelopmentPipeline()
        task = pipeline.process_task("设计数据库架构", TaskType.DESIGN)
        assert task.status == TaskStatus.COMPLETED
        assert task.assignee == "design_agent"

    def test_process_testing_task(self):
        """测试处理测试任务"""
        pipeline = DevelopmentPipeline()
        task = pipeline.process_task("编写单元测试", TaskType.TESTING)
        assert task.status == TaskStatus.COMPLETED

    def test_process_review_task(self):
        """测试处理评审任务"""
        pipeline = DevelopmentPipeline()
        task = pipeline.process_task("代码评审", TaskType.REVIEW)
        assert task.status == TaskStatus.COMPLETED

    def test_process_documentation_task(self):
        """测试处理文档任务"""
        pipeline = DevelopmentPipeline()
        task = pipeline.process_task("编写API文档", TaskType.DOCUMENTATION)
        assert task.status == TaskStatus.COMPLETED

    def test_process_empty_description(self):
        """测试空描述处理"""
        pipeline = DevelopmentPipeline()
        with pytest.raises(ValueError):
            pipeline.process_task("")

    def test_get_task_status(self):
        """测试获取任务状态"""
        pipeline = DevelopmentPipeline()
        task = pipeline.process_task("测试任务", TaskType.CODING)
        status = pipeline.get_task_status(task.task_id)
        assert status is not None
        assert status["status"] == TaskStatus.COMPLETED.value
        assert status["assignee"] == "coding_agent"

    def test_get_task_status_not_found(self):
        """测试获取不存在任务的状态"""
        pipeline = DevelopmentPipeline()
        status = pipeline.get_task_status("nonexistent")
        assert status is None

    def test_get_task_status_empty_id(self):
        """测试空ID获取状态"""
        pipeline = DevelopmentPipeline()
        status = pipeline.get_task_status("")
        assert status is None

    def test_get_pipeline_status(self):
        """测试获取链路整体状态"""
        pipeline = DevelopmentPipeline()
        pipeline.process_task("任务1", TaskType.CODING)
        pipeline.process_task("任务2", TaskType.DESIGN)
        pipeline.process_task("任务3", TaskType.TESTING)

        status = pipeline.get_pipeline_status()
        assert status["total_tasks"] == 3
        assert status["status_counts"]["completed"] == 3
        assert status["type_counts"]["coding"] == 1
        assert status["type_counts"]["design"] == 1
        assert status["type_counts"]["testing"] == 1

    def test_get_pipeline_status_empty(self):
        """测试空链路状态"""
        pipeline = DevelopmentPipeline()
        status = pipeline.get_pipeline_status()
        assert status["total_tasks"] == 0

    def test_full_pipeline_workflow(self):
        """测试完整链路工作流"""
        pipeline = DevelopmentPipeline()

        # 1. 设计
        design_task = pipeline.process_task("系统架构设计", TaskType.DESIGN)
        assert design_task.status == TaskStatus.COMPLETED

        # 2. 编码
        coding_task = pipeline.process_task("核心模块编码", TaskType.CODING)
        assert coding_task.status == TaskStatus.COMPLETED

        # 3. 测试
        testing_task = pipeline.process_task("集成测试", TaskType.TESTING)
        assert testing_task.status == TaskStatus.COMPLETED

        # 4. 评审
        review_task = pipeline.process_task("代码评审", TaskType.REVIEW)
        assert review_task.status == TaskStatus.COMPLETED

        # 5. 文档
        doc_task = pipeline.process_task("编写文档", TaskType.DOCUMENTATION)
        assert doc_task.status == TaskStatus.COMPLETED

        # 6. 验证整体状态
        status = pipeline.get_pipeline_status()
        assert status["total_tasks"] == 5
        assert status["status_counts"]["completed"] == 5
