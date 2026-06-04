"""
阶段32验收测试：需求拆解Agent初始化

验收标准：
1. ✓ Agent类定义（完整配置）
2. ✓ HTD分解能力（自动分解）
3. ✓ 影响范围分析（语义分析）
4. ✓ 输出格式（标准Schema）
"""

import pytest
import json
from src.architecture.requirement_agent import (
    RequirementType,
    RequirementStatus,
    ImpactLevel,
    RequirementNode,
    ImpactAnalysis,
    RequirementConfig,
    DecompositionResult,
    HierarchicalDecomposer,
    ImpactAnalyzer,
    SchemaOutputGenerator,
    RequirementAgent,
    get_requirement_agent,
    reset_requirement_agent
)


class TestRequirementConfig:
    """测试Agent类定义"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = RequirementConfig(name="RequirementAgent")
        
        assert config.name == "RequirementAgent"
        assert config.max_depth == 5
        assert config.auto_decompose is True
        assert config.enable_impact_analysis is True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = RequirementConfig(
            name="CustomReqAgent",
            max_depth=3,
            auto_decompose=False,
            enable_impact_analysis=False
        )
        
        assert config.name == "CustomReqAgent"
        assert config.max_depth == 3
        assert config.auto_decompose is False


class TestHierarchicalDecomposer:
    """测试HTD分解能力"""
    
    def test_simple_decompose(self):
        """测试简单分解"""
        decomposer = HierarchicalDecomposer()
        
        result = decomposer.decompose(
            "The system must display user information. It should load user data and save preferences.",
            max_depth=2
        )
        
        assert result.root_requirement is not None
        assert result.total_requirements >= 1
        assert result.decomposition_levels >= 1
    
    def test_extract_sub_requirements(self):
        """测试提取子需求"""
        decomposer = HierarchicalDecomposer()
        
        text = "The system must display user information. It should load data from the database. It shall validate user input."
        
        sub_reqs = decomposer._extract_sub_requirements(text)
        
        assert len(sub_reqs) >= 2
    
    def test_depth_calculation(self):
        """测试深度计算"""
        decomposer = HierarchicalDecomposer()
        
        result = decomposer.decompose("Main requirement with multiple sub-tasks", max_depth=3)
        
        assert result.decomposition_levels >= 1


class TestImpactAnalyzer:
    """测试影响范围分析"""
    
    def test_semantic_analysis(self):
        """测试语义分析"""
        analyzer = ImpactAnalyzer()
        
        requirement = RequirementNode(
            title="Database Integration",
            description="This feature will save data to the database and query user information from tables."
        )
        
        analysis = analyzer.analyze(requirement)
        
        assert analysis is not None
        assert len(analysis.impacted_modules) >= 1
    
    def test_assess_risk(self):
        """测试风险评估"""
        analyzer = ImpactAnalyzer()
        
        risk_low = analyzer._assess_risk(["api"])
        risk_high = analyzer._assess_risk(["api", "database", "ui"])
        
        assert risk_low == ImpactLevel.LOW
        assert risk_high == ImpactLevel.HIGH
    
    def test_assess_complexity(self):
        """测试复杂度评估"""
        analyzer = ImpactAnalyzer()
        
        req_simple = RequirementNode(title="Simple", description="Simple")
        req_complex = RequirementNode(title="Complex", description="This is a very complex requirement that goes into lots of details about what needs to be done and how it affects various parts of the system in multiple ways.")
        
        comp_simple = analyzer._assess_complexity(req_simple)
        comp_complex = analyzer._assess_complexity(req_complex)
        
        assert comp_simple == ImpactLevel.LOW


class TestSchemaOutputGenerator:
    """测试输出格式"""
    
    def test_structured_text(self):
        """测试结构化文本输出"""
        generator = SchemaOutputGenerator("1.0.0")
        
        root = RequirementNode(title="Main Requirement", description="The main requirement")
        
        result = DecompositionResult(
            root_requirement=root,
            all_nodes={root.node_id: root},
            total_requirements=1,
            decomposition_levels=1
        )
        
        text_output = generator.generate_structured_text(result)
        
        assert "REQUIREMENT DECOMPOSITION" in text_output
        assert "Main Requirement" in text_output
    
    def test_json_schema(self):
        """测试标准JSON Schema"""
        generator = SchemaOutputGenerator("1.0.0")
        
        root = RequirementNode(title="Test Requirement", description="Test")
        
        result = DecompositionResult(
            root_requirement=root,
            all_nodes={root.node_id: root},
            total_requirements=1,
            decomposition_levels=1
        )
        
        json_schema = generator.generate_json_schema(result)
        
        assert "schema_version" in json_schema
        assert "summary" in json_schema
        assert "requirements" in json_schema
        assert json_schema["summary"]["total_requirements"] == 1
    
    def test_json_with_impact(self):
        """测试带影响分析的JSON"""
        generator = SchemaOutputGenerator("1.0.0")
        
        root = RequirementNode(title="Test Requirement", description="Test")
        
        result = DecompositionResult(
            root_requirement=root,
            all_nodes={root.node_id: root},
            total_requirements=1,
            decomposition_levels=1
        )
        
        impact = ImpactAnalysis(requirement_id=root.node_id)
        
        json_schema = generator.generate_json_schema(result, impact)
        
        assert "impact_analysis" in json_schema


class TestRequirementAgent:
    """测试需求Agent"""
    
    def test_process_requirement(self):
        """测试处理需求"""
        config = RequirementConfig(name="TestAgent", max_depth=2)
        agent = RequirementAgent(config)
        
        result = agent.process_requirement(
            "The system must display user information and save user settings. It should load data quickly."
        )
        
        assert "decomposition" in result
        assert "structured_text" in result
        assert "json_schema" in result
        assert result["decomposition"].total_requirements >= 1
    
    def test_get_requirement_by_id(self):
        """测试通过ID获取需求"""
        config = RequirementConfig(name="TestAgent")
        agent = RequirementAgent(config)
        
        process_result = agent.process_requirement("Simple requirement")
        
        root_id = process_result["decomposition"].root_requirement.node_id
        retrieved = agent.get_requirement_by_id(root_id)
        
        assert retrieved is not None
        assert retrieved.node_id == root_id


class TestGlobalAgent:
    """测试全局Agent"""
    
    def test_get_global_agent(self):
        """测试获取全局Agent"""
        reset_requirement_agent()
        
        agent1 = get_requirement_agent()
        agent2 = get_requirement_agent()
        
        assert agent1 is agent2
    
    def test_reset_global_agent(self):
        """测试重置全局Agent"""
        agent1 = get_requirement_agent()
        reset_requirement_agent()
        agent2 = get_requirement_agent()
        
        assert agent1 is not agent2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
