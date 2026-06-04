"""
阶段52验收测试：架构分析→方案输出链路
"""

import pytest

from src.architecture.pipeline_architecture import (
    AnalysisType, AnalysisStatus,
    ArchitectureAnalysis, ArchitectureSolution,
    ArchitectureAnalyzer, SolutionGenerator, ArchitecturePipeline,
)


class TestAnalysisType:
    """测试分析类型枚举"""

    def test_type_values(self):
        """测试分析类型枚举值"""
        assert AnalysisType.STRUCTURAL.value == "structural"
        assert AnalysisType.DEPENDENCY.value == "dependency"
        assert AnalysisType.PERFORMANCE.value == "performance"
        assert AnalysisType.SECURITY.value == "security"

    def test_all_types(self):
        """测试所有分析类型"""
        types = list(AnalysisType)
        assert len(types) == 4


class TestAnalysisStatus:
    """测试分析状态枚举"""

    def test_status_values(self):
        """测试状态枚举值"""
        assert AnalysisStatus.PENDING.value == "pending"
        assert AnalysisStatus.ANALYZING.value == "analyzing"
        assert AnalysisStatus.COMPLETED.value == "completed"
        assert AnalysisStatus.FAILED.value == "failed"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(AnalysisStatus)
        assert len(statuses) == 4


class TestArchitectureAnalysis:
    """测试架构分析结果"""

    def test_default_creation(self):
        """测试默认创建"""
        analysis = ArchitectureAnalysis()
        assert analysis.analysis_id != ""
        assert analysis.analysis_type == AnalysisType.STRUCTURAL
        assert analysis.target == ""
        assert analysis.findings == []
        assert analysis.recommendations == []
        assert analysis.status == AnalysisStatus.PENDING
        assert analysis.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        analysis = ArchitectureAnalysis(
            analysis_type=AnalysisType.DEPENDENCY,
            target="用户模块",
            findings=[{"category": "dependency"}],
            recommendations=["解耦依赖"],
            status=AnalysisStatus.COMPLETED,
        )
        assert analysis.analysis_type == AnalysisType.DEPENDENCY
        assert analysis.target == "用户模块"
        assert len(analysis.findings) == 1
        assert len(analysis.recommendations) == 1

    def test_unique_ids(self):
        """测试唯一ID"""
        a1 = ArchitectureAnalysis()
        a2 = ArchitectureAnalysis()
        assert a1.analysis_id != a2.analysis_id


class TestArchitectureSolution:
    """测试架构方案"""

    def test_default_creation(self):
        """测试默认创建"""
        solution = ArchitectureSolution()
        assert solution.solution_id != ""
        assert solution.analysis_id == ""
        assert solution.approach == ""
        assert solution.components == []
        assert solution.risk_assessment == {}
        assert solution.confidence == 0.0

    def test_custom_creation(self):
        """测试自定义创建"""
        solution = ArchitectureSolution(
            analysis_id="a-123",
            approach="重构架构",
            components=[{"name": "comp1"}],
            risk_assessment={"risk_level": "low"},
            confidence=0.85,
        )
        assert solution.analysis_id == "a-123"
        assert solution.approach == "重构架构"
        assert len(solution.components) == 1
        assert solution.confidence == 0.85


class TestArchitectureAnalyzer:
    """测试架构分析器"""

    def test_initial_state(self):
        """测试初始状态"""
        analyzer = ArchitectureAnalyzer()
        assert len(analyzer._analyses) == 0

    def test_analyze_structural(self):
        """测试结构分析"""
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze("系统模块架构", AnalysisType.STRUCTURAL)
        assert analysis.status == AnalysisStatus.COMPLETED
        assert len(analysis.findings) > 0
        assert analysis.target == "系统模块架构"

    def test_analyze_dependency(self):
        """测试依赖分析"""
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze("模块依赖关系", AnalysisType.DEPENDENCY)
        assert analysis.status == AnalysisStatus.COMPLETED
        assert len(analysis.findings) > 0

    def test_analyze_performance(self):
        """测试性能分析"""
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze("系统性能优化", AnalysisType.PERFORMANCE)
        assert analysis.status == AnalysisStatus.COMPLETED
        assert len(analysis.findings) > 0

    def test_analyze_security(self):
        """测试安全分析"""
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze("系统安全审计", AnalysisType.SECURITY)
        assert analysis.status == AnalysisStatus.COMPLETED
        assert len(analysis.findings) > 0

    def test_analyze_empty_target(self):
        """测试空目标分析"""
        analyzer = ArchitectureAnalyzer()
        with pytest.raises(ValueError):
            analyzer.analyze("")

    def test_analyze_with_modularity(self):
        """测试模块化检测"""
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze("模块化架构设计", AnalysisType.STRUCTURAL)
        categories = [f.get("category") for f in analysis.findings]
        assert "modularity" in categories

    def test_analyze_with_circular_dependency(self):
        """测试循环依赖检测"""
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze("循环依赖检测", AnalysisType.DEPENDENCY)
        categories = [f.get("category") for f in analysis.findings]
        assert "circular_dependency" in categories

    def test_analyze_recommendations(self):
        """测试建议生成"""
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze("系统架构", AnalysisType.STRUCTURAL)
        assert len(analysis.recommendations) > 0

    def test_analyze_stored(self):
        """测试分析结果存储"""
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze("测试目标", AnalysisType.STRUCTURAL)
        assert analysis.analysis_id in analyzer._analyses


class TestSolutionGenerator:
    """测试方案生成器"""

    def test_initial_state(self):
        """测试初始状态"""
        generator = SolutionGenerator()
        assert len(generator._solutions) == 0

    def test_generate_solution(self):
        """测试生成方案"""
        generator = SolutionGenerator()
        analysis = ArchitectureAnalysis(
            analysis_type=AnalysisType.STRUCTURAL,
            target="测试目标",
            findings=[{"category": "structure", "description": "测试发现", "severity": "info"}],
            status=AnalysisStatus.COMPLETED,
        )
        solution = generator.generate_solution(analysis)
        assert solution.analysis_id == analysis.analysis_id
        assert solution.approach != ""
        assert len(solution.components) > 0
        assert solution.confidence > 0

    def test_generate_solution_invalid_analysis(self):
        """测试无效分析生成方案"""
        generator = SolutionGenerator()
        with pytest.raises(ValueError):
            generator.generate_solution(ArchitectureAnalysis(analysis_id=""))

    def test_generate_solution_with_warnings(self):
        """测试含警告的方案生成"""
        generator = SolutionGenerator()
        analysis = ArchitectureAnalysis(
            analysis_type=AnalysisType.DEPENDENCY,
            target="耦合依赖",
            findings=[
                {"category": "coupling", "description": "高耦合", "severity": "warning"},
                {"category": "dependency", "description": "依赖分析", "severity": "info"},
            ],
            status=AnalysisStatus.COMPLETED,
        )
        solution = generator.generate_solution(analysis)
        assert solution.risk_assessment["risk_level"] in ("medium", "high")
        assert solution.risk_assessment["warning_count"] == 1

    def test_generate_solution_approach_by_type(self):
        """测试不同分析类型的方案方向"""
        generator = SolutionGenerator()

        for atype in AnalysisType:
            analysis = ArchitectureAnalysis(
                analysis_type=atype,
                target="测试",
                findings=[],
                status=AnalysisStatus.COMPLETED,
            )
            solution = generator.generate_solution(analysis)
            assert solution.approach != ""

    def test_generate_solution_stored(self):
        """测试方案存储"""
        generator = SolutionGenerator()
        analysis = ArchitectureAnalysis(
            analysis_type=AnalysisType.STRUCTURAL,
            target="测试",
            findings=[],
            status=AnalysisStatus.COMPLETED,
        )
        solution = generator.generate_solution(analysis)
        assert solution.solution_id in generator._solutions


class TestArchitecturePipeline:
    """测试架构分析→方案输出链路"""

    def test_initial_state(self):
        """测试初始状态"""
        pipeline = ArchitecturePipeline()
        assert len(pipeline._analyses) == 0
        assert len(pipeline._solutions) == 0

    def test_process_structural(self):
        """测试结构分析处理"""
        pipeline = ArchitecturePipeline()
        solution = pipeline.process("系统架构分析", AnalysisType.STRUCTURAL)
        assert solution.approach != ""
        assert solution.confidence > 0

    def test_process_dependency(self):
        """测试依赖分析处理"""
        pipeline = ArchitecturePipeline()
        solution = pipeline.process("依赖关系分析", AnalysisType.DEPENDENCY)
        assert solution.approach != ""

    def test_process_performance(self):
        """测试性能分析处理"""
        pipeline = ArchitecturePipeline()
        solution = pipeline.process("性能瓶颈分析", AnalysisType.PERFORMANCE)
        assert solution.approach != ""

    def test_process_security(self):
        """测试安全分析处理"""
        pipeline = ArchitecturePipeline()
        solution = pipeline.process("安全漏洞分析", AnalysisType.SECURITY)
        assert solution.approach != ""

    def test_process_empty_target(self):
        """测试空目标处理"""
        pipeline = ArchitecturePipeline()
        result = pipeline.process("")
        assert result.metadata.get("error") is not None

    def test_get_analysis(self):
        """测试获取分析结果"""
        pipeline = ArchitecturePipeline()
        solution = pipeline.process("测试目标", AnalysisType.STRUCTURAL)
        analysis = pipeline.get_analysis(solution.analysis_id)
        assert analysis is not None
        assert analysis.target == "测试目标"

    def test_get_analysis_not_found(self):
        """测试获取不存在的分析"""
        pipeline = ArchitecturePipeline()
        assert pipeline.get_analysis("nonexistent") is None

    def test_get_analysis_empty_id(self):
        """测试空ID获取分析"""
        pipeline = ArchitecturePipeline()
        assert pipeline.get_analysis("") is None

    def test_get_solution(self):
        """测试获取方案"""
        pipeline = ArchitecturePipeline()
        solution = pipeline.process("测试目标", AnalysisType.STRUCTURAL)
        fetched = pipeline.get_solution(solution.solution_id)
        assert fetched is not None
        assert fetched.solution_id == solution.solution_id

    def test_get_solution_not_found(self):
        """测试获取不存在的方案"""
        pipeline = ArchitecturePipeline()
        assert pipeline.get_solution("nonexistent") is None

    def test_full_pipeline_workflow(self):
        """测试完整链路工作流"""
        pipeline = ArchitecturePipeline()

        # 1. 执行多种分析
        s1 = pipeline.process("模块化架构设计", AnalysisType.STRUCTURAL)
        s2 = pipeline.process("循环依赖检测", AnalysisType.DEPENDENCY)
        s3 = pipeline.process("性能瓶颈分析", AnalysisType.PERFORMANCE)

        # 2. 验证分析结果
        a1 = pipeline.get_analysis(s1.analysis_id)
        assert a1 is not None
        assert a1.status == AnalysisStatus.COMPLETED

        # 3. 验证方案
        assert s1.confidence > 0
        assert s2.confidence > 0
        assert s3.confidence > 0

        # 4. 验证存储
        assert len(pipeline._analyses) == 3
        assert len(pipeline._solutions) == 3
