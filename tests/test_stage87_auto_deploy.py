"""
阶段87验收测试 - 全自动部署流水线
"""

import pytest
from src.architecture.auto_deploy import (
    DeployEnvironment,
    DeployStatus,
    DeployConfig,
    DeployResult,
    AutoDeployer,
    AutoDeployService,
)


class TestDeployEnvironment:
    """测试部署环境枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert DeployEnvironment.DEV.value == "dev"
        assert DeployEnvironment.STAGING.value == "staging"
        assert DeployEnvironment.PRODUCTION.value == "production"

    def test_all_environments(self):
        """测试所有环境"""
        envs = list(DeployEnvironment)
        assert len(envs) == 3


class TestDeployStatus:
    """测试部署状态枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert DeployStatus.PENDING.value == "pending"
        assert DeployStatus.PREPARING.value == "preparing"
        assert DeployStatus.DEPLOYING.value == "deploying"
        assert DeployStatus.VERIFYING.value == "verifying"
        assert DeployStatus.COMPLETED.value == "completed"
        assert DeployStatus.ROLLED_BACK.value == "rolled_back"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(DeployStatus)
        assert len(statuses) == 6


class TestDeployConfig:
    """测试部署配置"""

    def test_default_creation(self):
        """测试默认创建"""
        config = DeployConfig()
        assert config.config_id != ""
        assert config.environment == DeployEnvironment.DEV
        assert config.version == "1.0.0"
        assert config.artifacts == []
        assert config.health_check_url == ""
        assert config.rollback_version == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        config = DeployConfig(
            environment=DeployEnvironment.PRODUCTION,
            version="2.5.0",
            artifacts=["app.jar", "config.yaml"],
            health_check_url="http://api/health",
            rollback_version="2.4.0",
        )
        assert config.environment == DeployEnvironment.PRODUCTION
        assert config.version == "2.5.0"
        assert len(config.artifacts) == 2
        assert config.health_check_url == "http://api/health"
        assert config.rollback_version == "2.4.0"

    def test_config_id_unique(self):
        """测试配置ID唯一性"""
        c1 = DeployConfig()
        c2 = DeployConfig()
        assert c1.config_id != c2.config_id


class TestDeployResult:
    """测试部署结果"""

    def test_default_creation(self):
        """测试默认创建"""
        result = DeployResult()
        assert result.deploy_id != ""
        assert result.environment == DeployEnvironment.DEV
        assert result.status == DeployStatus.PENDING
        assert result.version == "1.0.0"
        assert result.start_time == 0.0
        assert result.end_time == 0.0
        assert result.health_status == "unknown"

    def test_custom_creation(self):
        """测试自定义创建"""
        result = DeployResult(
            environment=DeployEnvironment.STAGING,
            status=DeployStatus.COMPLETED,
            version="3.0.0",
            health_status="healthy",
        )
        assert result.environment == DeployEnvironment.STAGING
        assert result.status == DeployStatus.COMPLETED
        assert result.version == "3.0.0"
        assert result.health_status == "healthy"


class TestAutoDeployer:
    """测试自动部署器"""

    def test_initialization(self):
        """测试初始化"""
        deployer = AutoDeployer()
        assert len(deployer._results) == 0
        assert len(deployer._history) == 0

    def test_deploy_success(self):
        """测试成功部署"""
        deployer = AutoDeployer()
        config = DeployConfig(
            environment=DeployEnvironment.DEV,
            version="1.0.0",
            artifacts=["app.jar"],
            health_check_url="http://localhost/health",
        )
        result = deployer.deploy(config)
        assert result.status == DeployStatus.COMPLETED
        assert result.health_status == "healthy"
        assert result.start_time > 0
        assert result.end_time > 0

    def test_deploy_no_health_check(self):
        """测试无健康检查的部署"""
        deployer = AutoDeployer()
        config = DeployConfig(
            environment=DeployEnvironment.STAGING,
            version="1.1.0",
            artifacts=["app.jar"],
        )
        result = deployer.deploy(config)
        assert result.status == DeployStatus.COMPLETED
        assert result.health_status == "unknown"

    def test_deploy_no_artifacts(self):
        """测试无制品的部署"""
        deployer = AutoDeployer()
        config = DeployConfig(
            environment=DeployEnvironment.DEV,
            version="1.0.0",
        )
        result = deployer.deploy(config)
        assert result.status == DeployStatus.COMPLETED

    def test_deploy_production(self):
        """测试生产环境部署"""
        deployer = AutoDeployer()
        config = DeployConfig(
            environment=DeployEnvironment.PRODUCTION,
            version="2.0.0",
            artifacts=["app.jar", "config.yaml"],
            health_check_url="http://prod/health",
            rollback_version="1.9.0",
        )
        result = deployer.deploy(config)
        assert result.status == DeployStatus.COMPLETED
        assert result.environment == DeployEnvironment.PRODUCTION

    def test_rollback(self):
        """测试回滚"""
        deployer = AutoDeployer()
        config = DeployConfig(
            environment=DeployEnvironment.PRODUCTION,
            version="2.0.0",
            rollback_version="1.9.0",
        )
        deploy_result = deployer.deploy(config)
        rollback_result = deployer._rollback(deploy_result.deploy_id, config)
        assert rollback_result.status == DeployStatus.ROLLED_BACK
        assert rollback_result.health_status == "rolled_back"

    def test_rollback_not_found(self):
        """测试回滚不存在的部署"""
        deployer = AutoDeployer()
        config = DeployConfig(rollback_version="1.0.0")
        result = deployer._rollback("nonexistent", config)
        assert result.status == DeployStatus.ROLLED_BACK

    def test_generate_report(self):
        """测试生成报告"""
        deployer = AutoDeployer()
        config = DeployConfig(
            environment=DeployEnvironment.DEV,
            version="1.0.0",
            health_check_url="http://localhost/health",
        )
        result = deployer.deploy(config)
        report = deployer.generate_report(result.deploy_id)
        assert "deploy_id" in report
        assert "environment" in report
        assert "status" in report
        assert "version" in report
        assert "health_status" in report
        assert "duration" in report

    def test_generate_report_not_found(self):
        """测试生成不存在的部署报告"""
        deployer = AutoDeployer()
        report = deployer.generate_report("nonexistent")
        assert "message" in report

    def test_deploy_saves_result(self):
        """测试部署后保存结果"""
        deployer = AutoDeployer()
        config = DeployConfig(version="1.0.0")
        result = deployer.deploy(config)
        assert result.deploy_id in deployer._results

    def test_deploy_adds_to_history(self):
        """测试部署后添加到历史"""
        deployer = AutoDeployer()
        config = DeployConfig(version="1.0.0")
        deployer.deploy(config)
        assert len(deployer._history) == 1


class TestAutoDeployService:
    """测试全自动部署服务"""

    def test_initialization(self):
        """测试初始化"""
        service = AutoDeployService()
        assert service.deployer is not None

    def test_initialization_with_deployer(self):
        """测试使用自定义部署器初始化"""
        deployer = AutoDeployer()
        service = AutoDeployService(deployer=deployer)
        assert service.deployer is deployer

    def test_deploy(self):
        """测试执行部署"""
        service = AutoDeployService()
        config = DeployConfig(
            environment=DeployEnvironment.STAGING,
            version="1.0.0",
            health_check_url="http://staging/health",
        )
        result = service.deploy(config)
        assert result.status == DeployStatus.COMPLETED

    def test_get_status(self):
        """测试获取部署状态"""
        service = AutoDeployService()
        config = DeployConfig(version="1.0.0")
        deploy_result = service.deploy(config)
        status = service.get_status(deploy_result.deploy_id)
        assert status == DeployStatus.COMPLETED

    def test_get_status_not_found(self):
        """测试获取不存在的部署状态"""
        service = AutoDeployService()
        status = service.get_status("nonexistent")
        assert status is None

    def test_rollback(self):
        """测试回滚"""
        service = AutoDeployService()
        config = DeployConfig(
            version="2.0.0",
            rollback_version="1.0.0",
        )
        deploy_result = service.deploy(config)
        rollback_result = service.rollback(deploy_result.deploy_id, config)
        assert rollback_result.status == DeployStatus.ROLLED_BACK

    def test_get_history(self):
        """测试获取部署历史"""
        service = AutoDeployService()
        config1 = DeployConfig(version="1.0.0")
        config2 = DeployConfig(version="2.0.0")
        service.deploy(config1)
        service.deploy(config2)
        history = service.get_history()
        assert len(history) >= 2

    def test_get_history_empty(self):
        """测试空部署历史"""
        service = AutoDeployService()
        history = service.get_history()
        assert history == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
