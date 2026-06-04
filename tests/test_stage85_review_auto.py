"""
阶段85验收测试 - 自动生成评审报告/整改建议
"""

import pytest
from src.architecture.review_auto import (
    ReviewCategory,
    RecommendationPriority,
    ReviewFinding,
    AutoReviewer,
    AutoReviewService,
)


class TestReviewCategory:
    """测试评审类别枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ReviewCategory.ARCHITECTURE.value == "architecture"
        assert ReviewCategory.CODE_QUALITY.value == "code_quality"
        assert ReviewCategory.SECURITY.value == "security"
        assert ReviewCategory.PERFORMANCE.value == "performance"
        assert ReviewCategory.MAINTAINABILITY.value == "maintainability"

    def test_all_categories(self):
        """测试所有评审类别"""
        categories = list(ReviewCategory)
        assert len(categories) == 5


class TestRecommendationPriority:
    """测试建议优先级枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert RecommendationPriority.LOW.value == "low"
        assert RecommendationPriority.MEDIUM.value == "medium"
        assert RecommendationPriority.HIGH.value == "high"
        assert RecommendationPriority.CRITICAL.value == "critical"

    def test_all_priorities(self):
        """测试所有优先级"""
        priorities = list(RecommendationPriority)
        assert len(priorities) == 4


class TestReviewFinding:
    """测试评审发现"""

    def test_default_creation(self):
        """测试默认创建"""
        finding = ReviewFinding()
        assert finding.finding_id != ""
        assert finding.category == ReviewCategory.CODE_QUALITY
        assert finding.severity == RecommendationPriority.MEDIUM
        assert finding.description == ""
        assert finding.location == ""
        assert finding.recommendation == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        finding = ReviewFinding(
            category=ReviewCategory.SECURITY,
            severity=RecommendationPriority.CRITICAL,
            description="SQL注入风险",
            location="数据访问层",
            recommendation="使用参数化查询",
        )
        assert finding.category == ReviewCategory.SECURITY
        assert finding.severity == RecommendationPriority.CRITICAL
        assert finding.description == "SQL注入风险"
        assert finding.location == "数据访问层"
        assert finding.recommendation == "使用参数化查询"

    def test_unique_ids(self):
        """测试唯一ID"""
        f1 = ReviewFinding()
        f2 = ReviewFinding()
        assert f1.finding_id != f2.finding_id


class TestAutoReviewer:
    """测试自动评审器"""

    def _make_healthy_project(self):
        """构造健康项目数据"""
        return {
            "coupling_score": 3,
            "layer_count": 3,
            "circular_dependencies": 0,
            "avg_complexity": 8,
            "duplication_rate": 3.0,
            "naming_score": 85.0,
            "vulnerability_count": 0,
            "auth_coverage": 95.0,
            "sql_injection_risk": False,
            "avg_response_time": 200,
            "memory_usage": 45.0,
            "n_plus_one_queries": 0,
            "doc_coverage": 70.0,
            "test_coverage": 85.0,
            "todo_count": 5,
        }

    def test_initialization(self):
        """测试初始化"""
        reviewer = AutoReviewer()
        assert reviewer._findings == []

    def test_review_healthy_project(self):
        """测试评审健康项目"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        findings = reviewer.review(data)
        assert len(findings) == 0

    def test_review_architecture_high_coupling(self):
        """测试评审高耦合架构"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["coupling_score"] = 20
        findings = reviewer._review_architecture(data)
        assert len(findings) > 0
        assert findings[0].category == ReviewCategory.ARCHITECTURE
        assert findings[0].severity == RecommendationPriority.CRITICAL

    def test_review_architecture_medium_coupling(self):
        """测试评审中等耦合架构"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["coupling_score"] = 10
        findings = reviewer._review_architecture(data)
        assert len(findings) > 0
        assert findings[0].severity == RecommendationPriority.HIGH

    def test_review_architecture_too_many_layers(self):
        """测试评审过多层次"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["layer_count"] = 8
        findings = reviewer._review_architecture(data)
        layer_findings = [f for f in findings if "层次过多" in f.description]
        assert len(layer_findings) == 1

    def test_review_architecture_circular_deps(self):
        """测试评审循环依赖"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["circular_dependencies"] = 3
        findings = reviewer._review_architecture(data)
        circular_findings = [f for f in findings if "循环依赖" in f.description]
        assert len(circular_findings) == 1

    def test_review_code_quality_high_complexity(self):
        """测试评审高复杂度代码"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["avg_complexity"] = 30
        findings = reviewer._review_code_quality(data)
        assert len(findings) > 0
        assert findings[0].severity == RecommendationPriority.CRITICAL

    def test_review_code_quality_duplication(self):
        """测试评审代码重复"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["duplication_rate"] = 25.0
        findings = reviewer._review_code_quality(data)
        dup_findings = [f for f in findings if "重复" in f.description]
        assert len(dup_findings) == 1

    def test_review_security_critical_vulns(self):
        """测试评审严重安全漏洞"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["vulnerability_count"] = 15
        findings = reviewer._review_security(data)
        assert len(findings) > 0
        assert findings[0].severity == RecommendationPriority.CRITICAL

    def test_review_security_sql_injection(self):
        """测试评审SQL注入风险"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["sql_injection_risk"] = True
        findings = reviewer._review_security(data)
        sql_findings = [f for f in findings if "SQL注入" in f.description]
        assert len(sql_findings) == 1
        assert sql_findings[0].severity == RecommendationPriority.CRITICAL

    def test_review_security_low_auth_coverage(self):
        """测试评审低认证覆盖率"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["auth_coverage"] = 40.0
        findings = reviewer._review_security(data)
        auth_findings = [f for f in findings if "认证" in f.description]
        assert len(auth_findings) == 1

    def test_review_performance_slow_response(self):
        """测试评审慢响应"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["avg_response_time"] = 3000
        findings = reviewer._review_performance(data)
        assert len(findings) > 0
        assert findings[0].severity == RecommendationPriority.CRITICAL

    def test_review_performance_high_memory(self):
        """测试评审高内存使用"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["memory_usage"] = 90.0
        findings = reviewer._review_performance(data)
        mem_findings = [f for f in findings if "内存" in f.description]
        assert len(mem_findings) == 1

    def test_review_performance_n_plus_one(self):
        """测试评审N+1查询"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["n_plus_one_queries"] = 5
        findings = reviewer._review_performance(data)
        nplus_findings = [f for f in findings if "N+1" in f.description]
        assert len(nplus_findings) == 1

    def test_review_maintainability_low_doc(self):
        """测试评审低文档覆盖"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["doc_coverage"] = 15.0
        findings = reviewer._review_maintainability(data)
        doc_findings = [f for f in findings if "文档" in f.description]
        assert len(doc_findings) == 1

    def test_review_maintainability_low_test_coverage(self):
        """测试评审低测试覆盖"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["test_coverage"] = 20.0
        findings = reviewer._review_maintainability(data)
        test_findings = [f for f in findings if "测试覆盖率" in f.description]
        assert len(test_findings) == 1

    def test_review_maintainability_many_todos(self):
        """测试评审大量TODO"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["todo_count"] = 30
        findings = reviewer._review_maintainability(data)
        todo_findings = [f for f in findings if "TODO" in f.description]
        assert len(todo_findings) == 1

    def test_generate_report(self):
        """测试生成评审报告"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["coupling_score"] = 20
        data["vulnerability_count"] = 15
        reviewer.review(data)
        report = reviewer.generate_report()
        assert "overall_severity" in report
        assert "total_findings" in report
        assert "by_category" in report
        assert "by_severity" in report
        assert "findings" in report

    def test_generate_recommendations(self):
        """测试生成整改建议"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["coupling_score"] = 20
        data["vulnerability_count"] = 5
        reviewer.review(data)
        recommendations = reviewer.generate_recommendations()
        assert len(recommendations) > 0
        assert "recommendation" in recommendations[0]
        assert "severity" in recommendations[0]

    def test_generate_recommendations_sorted_by_severity(self):
        """测试建议按严重程度排序"""
        reviewer = AutoReviewer()
        data = self._make_healthy_project()
        data["coupling_score"] = 20  # CRITICAL
        data["avg_complexity"] = 18  # HIGH
        data["duplication_rate"] = 12.0  # MEDIUM
        reviewer.review(data)
        recommendations = reviewer.generate_recommendations()
        if len(recommendations) >= 2:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            for i in range(len(recommendations) - 1):
                assert severity_order.get(recommendations[i]["severity"], 4) <= \
                       severity_order.get(recommendations[i + 1]["severity"], 4)


class TestAutoReviewService:
    """测试自动评审服务"""

    def test_initialization(self):
        """测试初始化"""
        service = AutoReviewService()
        assert service.reviewer is not None

    def test_initialization_with_reviewer(self):
        """测试使用自定义评审器初始化"""
        reviewer = AutoReviewer()
        service = AutoReviewService(reviewer=reviewer)
        assert service.reviewer is reviewer

    def test_review(self):
        """测试执行评审"""
        service = AutoReviewService()
        data = {
            "coupling_score": 20,
            "layer_count": 3,
            "circular_dependencies": 0,
            "avg_complexity": 8,
            "duplication_rate": 3.0,
            "naming_score": 85.0,
            "vulnerability_count": 0,
            "auth_coverage": 95.0,
            "sql_injection_risk": False,
            "avg_response_time": 200,
            "memory_usage": 45.0,
            "n_plus_one_queries": 0,
            "doc_coverage": 70.0,
            "test_coverage": 85.0,
            "todo_count": 5,
        }
        findings = service.review(data)
        assert isinstance(findings, list)

    def test_get_report(self):
        """测试获取评审报告"""
        service = AutoReviewService()
        data = {
            "coupling_score": 20,
            "layer_count": 3,
            "circular_dependencies": 0,
            "avg_complexity": 8,
            "duplication_rate": 3.0,
            "naming_score": 85.0,
            "vulnerability_count": 0,
            "auth_coverage": 95.0,
            "sql_injection_risk": False,
            "avg_response_time": 200,
            "memory_usage": 45.0,
            "n_plus_one_queries": 0,
            "doc_coverage": 70.0,
            "test_coverage": 85.0,
            "todo_count": 5,
        }
        service.review(data)
        report = service.get_report()
        assert "overall_severity" in report
        assert "total_findings" in report

    def test_get_recommendations(self):
        """测试获取整改建议"""
        service = AutoReviewService()
        data = {
            "coupling_score": 20,
            "layer_count": 3,
            "circular_dependencies": 0,
            "avg_complexity": 8,
            "duplication_rate": 3.0,
            "naming_score": 85.0,
            "vulnerability_count": 0,
            "auth_coverage": 95.0,
            "sql_injection_risk": False,
            "avg_response_time": 200,
            "memory_usage": 45.0,
            "n_plus_one_queries": 0,
            "doc_coverage": 70.0,
            "test_coverage": 85.0,
            "todo_count": 5,
        }
        service.review(data)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
