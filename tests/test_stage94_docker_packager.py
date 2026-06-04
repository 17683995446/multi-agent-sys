"""
阶段94验收测试 - Docker容器化打包
"""

import pytest
from src.architecture.docker_packager import (
    ContainerStatus,
    DockerConfig,
    ContainerInstance,
    DockerPackager,
    DockerPackageService,
)


class TestContainerStatus:
    """测试容器状态枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert ContainerStatus.BUILDING.value == "building"
        assert ContainerStatus.READY.value == "ready"
        assert ContainerStatus.RUNNING.value == "running"
        assert ContainerStatus.STOPPED.value == "stopped"
        assert ContainerStatus.ERROR.value == "error"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(ContainerStatus)
        assert len(statuses) == 5


class TestDockerConfig:
    """测试Docker配置"""

    def test_default_creation(self):
        """测试默认创建"""
        config = DockerConfig()
        assert config.image_name == "app"
        assert config.tag == "latest"
        assert config.base_image == "python:3.11-slim"
        assert config.ports == [8000]
        assert config.env_vars == {}
        assert config.volumes == []
        assert "test" in config.health_check

    def test_custom_creation(self):
        """测试自定义创建"""
        config = DockerConfig(
            image_name="myapp",
            tag="v1.0",
            base_image="node:18-alpine",
            ports=[3000, 8080],
            env_vars={"NODE_ENV": "production"},
            volumes=["/data:/app/data"],
            health_check={"test": ["CMD", "curl", "-f", "http://localhost:3000"]},
        )
        assert config.image_name == "myapp"
        assert config.tag == "v1.0"
        assert config.base_image == "node:18-alpine"
        assert len(config.ports) == 2
        assert config.env_vars["NODE_ENV"] == "production"
        assert len(config.volumes) == 1


class TestContainerInstance:
    """测试容器实例"""

    def test_default_creation(self):
        """测试默认创建"""
        container = ContainerInstance()
        assert container.container_id != ""
        assert container.status == ContainerStatus.BUILDING
        assert container.created_at > 0
        assert container.ip_address == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        config = DockerConfig(image_name="test")
        container = ContainerInstance(
            config=config,
            status=ContainerStatus.RUNNING,
            ip_address="172.17.0.5",
        )
        assert container.config.image_name == "test"
        assert container.status == ContainerStatus.RUNNING
        assert container.ip_address == "172.17.0.5"

    def test_container_id_unique(self):
        """测试容器ID唯一性"""
        c1 = ContainerInstance()
        c2 = ContainerInstance()
        assert c1.container_id != c2.container_id


class TestDockerPackager:
    """测试Docker容器化打包器"""

    def test_initialization(self):
        """测试初始化"""
        packager = DockerPackager()
        assert len(packager._images) == 0
        assert len(packager._containers) == 0

    def test_build_image(self):
        """测试构建镜像"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        image_key = packager.build_image(config)
        assert image_key == "myapp:v1.0"
        assert image_key in packager._images

    def test_build_image_invalid_config(self):
        """测试构建镜像无效配置"""
        packager = DockerPackager()
        config = DockerConfig(image_name="", tag="")
        image_key = packager.build_image(config)
        assert image_key == ""

    def test_generate_dockerfile(self):
        """测试生成Dockerfile"""
        packager = DockerPackager()
        config = DockerConfig(
            image_name="myapp",
            env_vars={"APP_ENV": "prod"},
            ports=[8000, 9000],
        )
        dockerfile = packager._generate_dockerfile(config)
        assert "FROM python:3.11-slim" in dockerfile
        assert "EXPOSE 8000" in dockerfile
        assert "EXPOSE 9000" in dockerfile
        assert "ENV APP_ENV=prod" in dockerfile

    def test_validate_config_valid(self):
        """测试验证有效配置"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        assert packager._validate_config(config) is True

    def test_validate_config_empty_name(self):
        """测试验证空镜像名"""
        packager = DockerPackager()
        config = DockerConfig(image_name="", tag="v1.0")
        assert packager._validate_config(config) is False

    def test_validate_config_empty_tag(self):
        """测试验证空标签"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="")
        assert packager._validate_config(config) is False

    def test_validate_config_empty_base(self):
        """测试验证空基础镜像"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0", base_image="")
        assert packager._validate_config(config) is False

    def test_create_container(self):
        """测试创建容器"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        image_key = packager.build_image(config)
        container = packager.create_container(image_key)
        assert container is not None
        assert container.status == ContainerStatus.READY
        assert container.container_id in packager._containers

    def test_create_container_with_config(self):
        """测试使用自定义配置创建容器"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        container = packager.create_container("nonexistent", config=config)
        assert container is not None

    def test_create_container_not_found(self):
        """测试创建容器镜像不存在"""
        packager = DockerPackager()
        container = packager.create_container("nonexistent:v1.0")
        assert container is None

    def test_start_container(self):
        """测试启动容器"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        image_key = packager.build_image(config)
        container = packager.create_container(image_key)
        result = packager.start(container.container_id)
        assert result is True
        assert container.status == ContainerStatus.RUNNING

    def test_start_container_not_found(self):
        """测试启动不存在的容器"""
        packager = DockerPackager()
        result = packager.start("nonexistent")
        assert result is False

    def test_start_running_container(self):
        """测试启动已运行的容器"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        image_key = packager.build_image(config)
        container = packager.create_container(image_key)
        packager.start(container.container_id)
        result = packager.start(container.container_id)
        assert result is False

    def test_stop_container(self):
        """测试停止容器"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        image_key = packager.build_image(config)
        container = packager.create_container(image_key)
        packager.start(container.container_id)
        result = packager.stop(container.container_id)
        assert result is True
        assert container.status == ContainerStatus.STOPPED

    def test_stop_not_running_container(self):
        """测试停止未运行的容器"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        image_key = packager.build_image(config)
        container = packager.create_container(image_key)
        result = packager.stop(container.container_id)
        assert result is False

    def test_remove_container(self):
        """测试移除容器"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        image_key = packager.build_image(config)
        container = packager.create_container(image_key)
        result = packager.remove(container.container_id)
        assert result is True
        assert container.container_id not in packager._containers

    def test_remove_not_found(self):
        """测试移除不存在的容器"""
        packager = DockerPackager()
        result = packager.remove("nonexistent")
        assert result is False

    def test_restart_container(self):
        """测试重启容器（停止后再启动）"""
        packager = DockerPackager()
        config = DockerConfig(image_name="myapp", tag="v1.0")
        image_key = packager.build_image(config)
        container = packager.create_container(image_key)
        packager.start(container.container_id)
        packager.stop(container.container_id)
        result = packager.start(container.container_id)
        assert result is True
        assert container.status == ContainerStatus.RUNNING


class TestDockerPackageService:
    """测试Docker容器化打包服务"""

    def test_initialization(self):
        """测试初始化"""
        service = DockerPackageService()
        assert service.packager is not None

    def test_initialization_with_packager(self):
        """测试使用自定义打包器初始化"""
        packager = DockerPackager()
        service = DockerPackageService(packager=packager)
        assert service.packager is packager

    def test_build(self):
        """测试构建镜像"""
        service = DockerPackageService()
        config = DockerConfig(image_name="svcapp", tag="v2.0")
        image_key = service.build(config)
        assert image_key == "svcapp:v2.0"

    def test_deploy(self):
        """测试部署容器"""
        service = DockerPackageService()
        config = DockerConfig(image_name="svcapp", tag="v2.0")
        image_key = service.build(config)
        container = service.deploy(image_key)
        assert container is not None
        assert container.status == ContainerStatus.RUNNING

    def test_get_status(self):
        """测试获取容器状态"""
        service = DockerPackageService()
        config = DockerConfig(image_name="svcapp", tag="v2.0")
        image_key = service.build(config)
        container = service.deploy(image_key)
        status = service.get_status(container.container_id)
        assert status == ContainerStatus.RUNNING

    def test_get_status_not_found(self):
        """测试获取不存在容器的状态"""
        service = DockerPackageService()
        status = service.get_status("nonexistent")
        assert status is None

    def test_get_containers(self):
        """测试获取所有容器"""
        service = DockerPackageService()
        config1 = DockerConfig(image_name="app1", tag="v1")
        config2 = DockerConfig(image_name="app2", tag="v1")
        service.build(config1)
        service.build(config2)
        service.deploy("app1:v1")
        service.deploy("app2:v1")
        containers = service.get_containers()
        assert len(containers) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
