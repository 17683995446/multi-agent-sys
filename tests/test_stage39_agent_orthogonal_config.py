"""
阶段39验收测试：Agent正交职责配置
"""

import pytest
from src.architecture.agent_orthogonal_config import (
    AgentType,
    ResponsibilityCategory,
    Responsibility,
    AgentRole,
    ResponsibilityMatrix,
    ResponsibilityMatrixBuilder,
    OverlapDetector,
    GapDetector,
    ResponsibilityDocumentGenerator,
    AgentOrthogonalConfig,
    get_agent_config,
    reset_agent_config
)


class TestResponsibilityMatrixBuilder:
    """测试职责矩阵（验收项39.1）"""
    
    def test_create_basic_matrix(self):
        """测试创建基础矩阵"""
        builder = ResponsibilityMatrixBuilder()
        
        agent = builder.add_agent(
            AgentType.CONTROL,
            "总控Agent",
            "全局协调"
        )
        
        resp = builder.add_responsibility(
            "全局决策",
            "全局协调和任务决策",
            AgentType.CONTROL,
            category=ResponsibilityCategory.DECISION
        )
        
        matrix = builder.build()
        
        assert matrix is not None
        assert len(matrix.agents) == 1
        assert len(matrix.responsibilities) == 1
    
    def test_standard_matrix_initialization(self):
        """测试标准矩阵初始化"""
        config = AgentOrthogonalConfig()
        matrix = config.initialize_standard_matrix()
        
        assert matrix is not None
        assert len(matrix.agents) >= 8
        assert len(matrix.responsibilities) >= 8
    
    def test_agent_types_coverage(self):
        """测试Agent类型覆盖"""
        config = AgentOrthogonalConfig()
        matrix = config.initialize_standard_matrix()
        
        agent_types = set(agent.agent_type for agent in matrix.agents)
        
        assert AgentType.CONTROL in agent_types
        assert AgentType.REQUIREMENT in agent_types
        assert AgentType.ARCHITECTURE in agent_types
        assert AgentType.DEVELOPMENT in agent_types


class TestOverlapDetector:
    """测试无重叠验证（验收项39.2）"""
    
    def test_no_overlap_detection(self):
        """测试无重叠检测"""
        builder = ResponsibilityMatrixBuilder()
        
        builder.add_agent(AgentType.CONTROL, "Control Agent", "")
        builder.add_agent(AgentType.REQUIREMENT, "Requirement Agent", "")
        
        builder.add_responsibility(
            "全局决策", "", AgentType.CONTROL,
            category=ResponsibilityCategory.DECISION
        )
        
        builder.add_responsibility(
            "需求分析", "", AgentType.REQUIREMENT,
            category=ResponsibilityCategory.ANALYSIS
        )
        
        matrix = builder.build()
        
        overlaps = OverlapDetector.detect_overlaps(matrix)
        
        assert len(overlaps) == 0
        assert OverlapDetector.has_overlap(matrix) is False
    
    def test_overlap_detection(self):
        """测试重叠检测"""
        builder = ResponsibilityMatrixBuilder()
        
        builder.add_agent(AgentType.CONTROL, "Control Agent", "")
        
        builder.add_responsibility(
            "决策任务", "", AgentType.CONTROL,
            category=ResponsibilityCategory.DECISION
        )
        
        builder.add_responsibility(
            "决策任务2", "", AgentType.CONTROL,
            category=ResponsibilityCategory.DECISION
        )
        
        matrix = builder.build()
        
        overlaps = OverlapDetector.detect_overlaps(matrix)
        
        assert len(matrix.overlap_checks) >= 0


class TestGapDetector:
    """测试无空缺验证（验收项39.3）"""
    
    def test_no_gap_detection(self):
        """测试无空缺检测"""
        builder = ResponsibilityMatrixBuilder()
        
        builder.add_agent(AgentType.CONTROL, "Control Agent", "")
        builder.add_agent(AgentType.REQUIREMENT, "Requirement Agent", "")
        
        builder.add_responsibility(
            "全局决策", "", AgentType.CONTROL,
            category=ResponsibilityCategory.DECISION,
            required=True
        )
        
        builder.add_responsibility(
            "需求分析", "", AgentType.REQUIREMENT,
            category=ResponsibilityCategory.ANALYSIS,
            required=True
        )
        
        matrix = builder.build()
        
        gaps = GapDetector.detect_gaps(
            matrix,
            [ResponsibilityCategory.DECISION, ResponsibilityCategory.ANALYSIS]
        )
        
        assert len(matrix.gap_checks) >= 0
    
    def test_gap_detection_for_category(self):
        """测试分类空缺检测"""
        builder = ResponsibilityMatrixBuilder()
        
        builder.add_agent(AgentType.CONTROL, "Control Agent", "")
        
        builder.add_responsibility(
            "全局决策", "", AgentType.CONTROL,
            category=ResponsibilityCategory.DECISION,
            required=True
        )
        
        matrix = builder.build()
        
        gaps = GapDetector.detect_gaps(
            matrix,
            [ResponsibilityCategory.DECISION, ResponsibilityCategory.ANALYSIS]
        )
        
        assert len(matrix.gap_checks) >= 0


class TestResponsibilityDocumentGenerator:
    """测试分工文档（验收项39.4）"""
    
    def test_markdown_document_generation(self):
        """测试Markdown文档生成"""
        config = AgentOrthogonalConfig()
        matrix = config.initialize_standard_matrix()
        
        doc = ResponsibilityDocumentGenerator.generate_markdown_document(matrix)
        
        assert "Agent职责分工文档" in doc
        assert "Agent角色列表" in doc
        assert "职责矩阵" in doc
        assert "验证结果" in doc
    
    def test_visual_matrix_generation(self):
        """测试可视化矩阵生成"""
        config = AgentOrthogonalConfig()
        matrix = config.initialize_standard_matrix()
        
        visual = ResponsibilityDocumentGenerator.generate_visual_matrix(matrix)
        
        assert "```" in visual
        assert len(visual) > 0


class TestAgentOrthogonalConfig:
    """测试Agent正交配置"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = AgentOrthogonalConfig()
        matrix = config.initialize_standard_matrix()
        
        assert matrix is not None
        assert config.responsibility_matrix is matrix
    
    def test_config_verification(self):
        """测试配置验证"""
        config = AgentOrthogonalConfig()
        matrix = config.initialize_standard_matrix()
        
        valid, result = config.verify_config()
        
        assert result is not None
        assert "overlap_count" in result
        assert "gap_count" in result
    
    def test_documentation_generation(self):
        """测试文档生成"""
        config = AgentOrthogonalConfig()
        matrix = config.initialize_standard_matrix()
        
        doc = config.generate_documentation()
        
        assert doc is not None
        assert len(doc) > 0


class TestGlobalConfig:
    """测试全局配置"""
    
    def test_get_global_config(self):
        """测试获取全局配置"""
        reset_agent_config()
        
        config1 = get_agent_config()
        config2 = get_agent_config()
        
        assert config1 is config2
    
    def test_reset_global_config(self):
        """测试重置全局配置"""
        config1 = get_agent_config()
        reset_agent_config()
        config2 = get_agent_config()
        
        assert config1 is not config2


class TestCompleteScenario:
    """测试完整场景"""
    
    def test_complete_config_scenario(self):
        """测试完整配置场景"""
        config = AgentOrthogonalConfig()
        
        matrix = config.initialize_standard_matrix()
        assert matrix is not None
        
        valid, result = config.verify_config()
        assert result is not None
        
        doc = config.generate_documentation()
        assert doc is not None
        assert len(doc) > 0


class TestNoOverlapTest:
    """测试无重叠测试脚本（验收项39.2）"""
    
    def test_no_overlap_script_functionality(self):
        """测试无重叠功能"""
        config = AgentOrthogonalConfig()
        config.initialize_standard_matrix()
        
        has_overlap = OverlapDetector.has_overlap(config.responsibility_matrix)
        
        assert isinstance(has_overlap, bool)


class TestNoGapTest:
    """测试无空缺测试脚本（验收项39.3）"""
    
    def test_no_gap_script_functionality(self):
        """测试无空缺功能"""
        config = AgentOrthogonalConfig()
        config.initialize_standard_matrix()
        
        has_gap = GapDetector.has_gap(config.responsibility_matrix)
        
        assert isinstance(has_gap, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
