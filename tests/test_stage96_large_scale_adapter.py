"""
阶段96验收测试 - 大项目复杂重构场景适配
"""

import pytest
from src.architecture.large_scale_adapter import (
    ProjectScale,
    RefactorComplexity,
    ProjectProfile,
    LargeScaleAdapter,
    LargeScaleService,
)


class TestProjectScale:
    """测试项目规模枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ProjectScale.SMALL.value == "small"
        assert ProjectScale.MEDIUM.value == "medium"
        assert ProjectScale.LARGE.value == "large"
        assert ProjectScale.ENTERPRISE.value == "enterprise"

    def test_all_scales(self):
        """测试所有规模"""
        scales = list(ProjectScale)
        assert len(scales) == 4


class TestRefactorComplexity:
    """测试重构复杂度枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RefactorComplexity.SIMPLE.value == "simple"
        assert RefactorComplexity.MODERATE.value == "moderate"
        assert RefactorComplexity.COMPLEX.value == "complex"
        assert RefactorComplexity.EXTREME.value == "extreme"

    def test_all_complexities(self):
        """测试所有复杂度"""
        complexities = list(RefactorComplexity)
        assert len(complexities) == 4


class TestProjectProfile:
    """测试项目画像"""

    def test_default_creation(self):
        """测试默认创建"""
        profile = ProjectProfile()
        assert profile.project_id != ""
        assert profile.scale == ProjectScale.SMALL
        assert profile.file_count == 0
        assert profile.module_count == 0
        assert profile.dependency_depth == 0
        assert profile.complexity == RefactorComplexity.SIMPLE

    def test_custom_creation(self):
        """测试自定义创建"""
        profile = ProjectProfile(
            scale=ProjectScale.LARGE,
            file_count=500,
            module_count=30,
            dependency_depth=6,
            complexity=RefactorComplexity.COMPLEX,
        )
        assert profile.scale == ProjectScale.LARGE
        assert profile.file_count == 500
        assert profile.module_count == 30
        assert profile.dependency_depth == 6
        assert profile.complexity == RefactorComplexity.COMPLEX

    def test_project_id_unique(self):
        """测试项目ID唯一性"""
        p1 = ProjectProfile()
        p2 = ProjectProfile()
        assert p1.project_id != p2.project_id


class TestLargeScaleAdapter:
    """测试大项目适配器"""

    def test_initialization(self):
        """测试初始化"""
        adapter = LargeScaleAdapter()
        assert len(adapter._profiles) == 0
        assert len(adapter._plans) == 0

    def test_analyze_project_small(self):
        """测试分析小型项目"""
        adapter = LargeScaleAdapter()
        data = {"file_count": 50, "module_count": 5, "dependency_depth": 2}
        profile = adapter.analyze_project(data)
        assert profile.scale == ProjectScale.SMALL
        assert profile.complexity == RefactorComplexity.SIMPLE

    def test_analyze_project_medium(self):
        """测试分析中型项目"""
        adapter = LargeScaleAdapter()
        data = {"file_count": 300, "module_count": 15, "dependency_depth": 4}
        profile = adapter.analyze_project(data)
        assert profile.scale == ProjectScale.MEDIUM
        assert profile.complexity == RefactorComplexity.MODERATE

    def test_analyze_project_large(self):
        """测试分析大型项目"""
        adapter = LargeScaleAdapter()
        data = {"file_count": 1500, "module_count": 60, "dependency_depth": 6}
        profile = adapter.analyze_project(data)
        assert profile.scale == ProjectScale.LARGE
        assert profile.complexity == RefactorComplexity.COMPLEX

    def test_analyze_project_enterprise(self):
        """测试分析企业级项目"""
        adapter = LargeScaleAdapter()
        data = {"file_count": 6000, "module_count": 250, "dependency_depth": 10}
        profile = adapter.analyze_project(data)
        assert profile.scale == ProjectScale.ENTERPRISE
        assert profile.complexity == RefactorComplexity.EXTREME

    def test_assess_scale(self):
        """测试评估项目规模"""
        adapter = LargeScaleAdapter()
        assert adapter._assess_scale({"file_count": 50, "module_count": 3}) == ProjectScale.SMALL
        assert adapter._assess_scale({"file_count": 300, "module_count": 15}) == ProjectScale.MEDIUM
        assert adapter._assess_scale({"file_count": 1500, "module_count": 60}) == ProjectScale.LARGE
        assert adapter._assess_scale({"file_count": 6000, "module_count": 250}) == ProjectScale.ENTERPRISE

    def test_plan_refactoring_simple(self):
        """测试简单重构规划"""
        adapter = LargeScaleAdapter()
        profile = ProjectProfile(complexity=RefactorComplexity.SIMPLE)
        plan = adapter._plan_refactoring(profile)
        assert len(plan["phases"]) == 1
        assert plan["risk_level"] == "low"

    def test_plan_refactoring_extreme(self):
        """测试极端复杂重构规划"""
        adapter = LargeScaleAdapter()
        profile = ProjectProfile(complexity=RefactorComplexity.EXTREME)
        plan = adapter._plan_refactoring(profile)
        assert len(plan["phases"]) == 4
        assert plan["risk_level"] == "critical"

    def test_optimize_for_scale_enterprise(self):
        """测试企业级规模优化"""
        adapter = LargeScaleAdapter()
        profile = ProjectProfile(scale=ProjectScale.ENTERPRISE)
        plan = {"project_id": "test"}
        optimized = adapter._optimize_for_scale(profile, plan)
        assert len(optimized["optimizations"]) == 4

    def test_optimize_for_scale_small(self):
        """测试小型规模优化"""
        adapter = LargeScaleAdapter()
        profile = ProjectProfile(scale=ProjectScale.SMALL)
        plan = {"project_id": "test"}
        optimized = adapter._optimize_for_scale(profile, plan)
        assert len(optimized["optimizations"]) == 1

    def test_estimate_duration(self):
        """测试估算持续时间"""
        adapter = LargeScaleAdapter()
        simple_profile = ProjectProfile(complexity=RefactorComplexity.SIMPLE, file_count=50)
        assert adapter._estimate_duration(simple_profile) == 3.0

        extreme_profile = ProjectProfile(complexity=RefactorComplexity.EXTREME, file_count=2000)
        duration = adapter._estimate_duration(extreme_profile)
        assert duration == 120.0 * 1.5  # 文件数>1000，1.5倍

    def test_assess_risk(self):
        """测试评估风险"""
        adapter = LargeScaleAdapter()
        assert adapter._assess_risk(ProjectProfile(complexity=RefactorComplexity.SIMPLE)) == "low"
        assert adapter._assess_risk(ProjectProfile(complexity=RefactorComplexity.MODERATE)) == "medium"
        assert adapter._assess_risk(ProjectProfile(complexity=RefactorComplexity.COMPLEX)) == "high"
        assert adapter._assess_risk(ProjectProfile(complexity=RefactorComplexity.EXTREME)) == "critical"

    def test_generate_adaptation_plan(self):
        """测试生成适配计划"""
        adapter = LargeScaleAdapter()
        data = {"file_count": 1500, "module_count": 60, "dependency_depth": 6}
        plan = adapter.generate_adaptation_plan(data)
        assert "phases" in plan
        assert "optimizations" in plan
        assert "estimated_duration" in plan
        assert "risk_level" in plan

    def test_analyze_saves_profile(self):
        """测试分析后保存画像"""
        adapter = LargeScaleAdapter()
        data = {"file_count": 100, "module_count": 5, "dependency_depth": 2}
        profile = adapter.analyze_project(data)
        assert profile.project_id in adapter._profiles


class TestLargeScaleService:
    """测试大项目适配服务"""

    def test_initialization(self):
        """测试初始化"""
        service = LargeScaleService()
        assert service.adapter is not None

    def test_initialization_with_adapter(self):
        """测试使用自定义适配器初始化"""
        adapter = LargeScaleAdapter()
        service = LargeScaleService(adapter=adapter)
        assert service.adapter is adapter

    def test_adapt(self):
        """测试执行适配"""
        service = LargeScaleService()
        data = {"file_count": 1500, "module_count": 60, "dependency_depth": 6}
        plan = service.adapt(data)
        assert "phases" in plan

    def test_get_plan(self):
        """测试获取适配计划"""
        service = LargeScaleService()
        data = {"file_count": 100, "module_count": 5, "dependency_depth": 2}
        plan = service.adapt(data)
        # 获取画像ID
        profile = service.adapter._profiles.get(list(service.adapter._profiles.keys())[0])
        result = service.get_plan(profile.project_id)
        assert result is not None

    def test_get_plan_not_found(self):
        """测试获取不存在的计划"""
        service = LargeScaleService()
        result = service.get_plan("nonexistent")
        assert result is None

    def test_get_profile(self):
        """测试获取项目画像"""
        service = LargeScaleService()
        data = {"file_count": 100, "module_count": 5, "dependency_depth": 2}
        service.adapt(data)
        profile_id = list(service.adapter._profiles.keys())[0]
        profile = service.get_profile(profile_id)
        assert profile is not None
        assert profile.file_count == 100

    def test_get_profile_not_found(self):
        """测试获取不存在的画像"""
        service = LargeScaleService()
        result = service.get_profile("nonexistent")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
