"""
Docker容器化打包模块

职责：构建Docker镜像、管理容器实例、容器生命周期管理

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContainerStatus(str, Enum):
    """容器状态"""
    BUILDING = "building"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class DockerConfig:
    """Docker配置"""
    image_name: str = "app"
    tag: str = "latest"
    base_image: str = "python:3.11-slim"
    ports: List[int] = field(default_factory=lambda: [8000])
    env_vars: Dict[str, str] = field(default_factory=dict)
    volumes: List[str] = field(default_factory=list)
    health_check: Dict[str, Any] = field(default_factory=lambda: {
        "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
    })

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"DockerConfig created: image={self.image_name}:{self.tag}, "
                     f"base={self.base_image}")


@dataclass
class ContainerInstance:
    """容器实例"""
    container_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    config: DockerConfig = field(default_factory=DockerConfig)
    status: ContainerStatus = ContainerStatus.BUILDING
    created_at: float = field(default_factory=time.time)
    ip_address: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"ContainerInstance created: container_id={self.container_id}, "
                     f"status={self.status.value}")


class DockerPackager:
    """Docker容器化打包器"""

    def __init__(self):
        """初始化Docker打包器"""
        self._images: Dict[str, DockerConfig] = {}
        self._containers: Dict[str, ContainerInstance] = {}
        logger.info("DockerPackager initialized")

    def build_image(self, config: DockerConfig) -> str:
        """构建Docker镜像"""
        logger.info(f"DockerPackager: building image, "
                    f"image={config.image_name}:{config.tag}")
        try:
            # 验证配置
            valid = self._validate_config(config)
            if not valid:
                logger.error(f"DockerPackager: invalid config for {config.image_name}")
                return ""

            # 生成Dockerfile
            dockerfile = self._generate_dockerfile(config)
            image_key = f"{config.image_name}:{config.tag}"
            self._images[image_key] = config
            logger.info(f"DockerPackager: image built, image_key={image_key}")
            return image_key
        except Exception as e:
            logger.error(f"DockerPackager: build_image failed: {e}")
            return ""

    def _generate_dockerfile(self, config: DockerConfig) -> str:
        """生成Dockerfile"""
        logger.debug(f"DockerPackager: generating Dockerfile, "
                     f"image={config.image_name}")
        try:
            lines = [
                f"FROM {config.base_image}",
                "WORKDIR /app",
                "COPY . .",
                "RUN pip install --no-cache-dir -r requirements.txt",
            ]
            for port in config.ports:
                lines.append(f"EXPOSE {port}")
            for key, value in config.env_vars.items():
                lines.append(f"ENV {key}={value}")
            lines.append('CMD ["python", "-m", "app"]')
            dockerfile = "\n".join(lines)
            logger.debug(f"DockerPackager: Dockerfile generated, "
                         f"lines={len(lines)}")
            return dockerfile
        except Exception as e:
            logger.error(f"DockerPackager: _generate_dockerfile failed: {e}")
            return ""

    def _validate_config(self, config: DockerConfig) -> bool:
        """验证Docker配置"""
        logger.debug(f"DockerPackager: validating config, "
                     f"image={config.image_name}")
        try:
            if not config.image_name:
                logger.debug("DockerPackager: empty image name")
                return False
            if not config.tag:
                logger.debug("DockerPackager: empty tag")
                return False
            if not config.base_image:
                logger.debug("DockerPackager: empty base image")
                return False
            return True
        except Exception as e:
            logger.error(f"DockerPackager: _validate_config failed: {e}")
            return False

    def create_container(self, image_key: str,
                         config: Optional[DockerConfig] = None) -> Optional[ContainerInstance]:
        """创建容器实例"""
        logger.info(f"DockerPackager: creating container, image_key={image_key}")
        try:
            if image_key not in self._images and config is None:
                logger.warning(f"DockerPackager: image not found, image_key={image_key}")
                return None

            container_config = config or self._images.get(image_key, DockerConfig())
            container = ContainerInstance(
                config=container_config,
                status=ContainerStatus.READY,
                ip_address=f"172.17.0.{len(self._containers) + 2}",
            )
            self._containers[container.container_id] = container
            logger.info(f"DockerPackager: container created, "
                        f"container_id={container.container_id}")
            return container
        except Exception as e:
            logger.error(f"DockerPackager: create_container failed: {e}")
            return None

    def start(self, container_id: str) -> bool:
        """启动容器"""
        logger.info(f"DockerPackager: starting container, container_id={container_id}")
        try:
            container = self._containers.get(container_id)
            if container is None:
                logger.warning(f"DockerPackager: container not found, "
                               f"container_id={container_id}")
                return False
            if container.status not in (ContainerStatus.READY, ContainerStatus.STOPPED):
                logger.warning(f"DockerPackager: cannot start container, "
                               f"status={container.status.value}")
                return False
            container.status = ContainerStatus.RUNNING
            logger.info(f"DockerPackager: container started, "
                        f"container_id={container_id}")
            return True
        except Exception as e:
            logger.error(f"DockerPackager: start failed: {e}")
            return False

    def stop(self, container_id: str) -> bool:
        """停止容器"""
        logger.info(f"DockerPackager: stopping container, container_id={container_id}")
        try:
            container = self._containers.get(container_id)
            if container is None:
                logger.warning(f"DockerPackager: container not found, "
                               f"container_id={container_id}")
                return False
            if container.status != ContainerStatus.RUNNING:
                logger.warning(f"DockerPackager: cannot stop container, "
                               f"status={container.status.value}")
                return False
            container.status = ContainerStatus.STOPPED
            logger.info(f"DockerPackager: container stopped, "
                        f"container_id={container_id}")
            return True
        except Exception as e:
            logger.error(f"DockerPackager: stop failed: {e}")
            return False

    def remove(self, container_id: str) -> bool:
        """移除容器"""
        logger.info(f"DockerPackager: removing container, container_id={container_id}")
        try:
            if container_id not in self._containers:
                logger.warning(f"DockerPackager: container not found, "
                               f"container_id={container_id}")
                return False
            del self._containers[container_id]
            logger.info(f"DockerPackager: container removed, "
                        f"container_id={container_id}")
            return True
        except Exception as e:
            logger.error(f"DockerPackager: remove failed: {e}")
            return False


class DockerPackageService:
    """Docker容器化打包服务"""

    def __init__(self, packager: Optional[DockerPackager] = None):
        """初始化Docker打包服务"""
        self.packager = packager or DockerPackager()
        logger.info("DockerPackageService initialized")

    def build(self, config: DockerConfig) -> str:
        """构建镜像"""
        logger.info(f"DockerPackageService: building image, "
                    f"image={config.image_name}:{config.tag}")
        return self.packager.build_image(config)

    def deploy(self, image_key: str,
               config: Optional[DockerConfig] = None) -> Optional[ContainerInstance]:
        """部署容器"""
        logger.info(f"DockerPackageService: deploying, image_key={image_key}")
        try:
            container = self.packager.create_container(image_key, config)
            if container is None:
                return None
            started = self.packager.start(container.container_id)
            if not started:
                container.status = ContainerStatus.ERROR
            return container
        except Exception as e:
            logger.error(f"DockerPackageService: deploy failed: {e}")
            return None

    def get_status(self, container_id: str) -> Optional[ContainerStatus]:
        """获取容器状态"""
        logger.debug(f"DockerPackageService: getting status, "
                     f"container_id={container_id}")
        container = self.packager._containers.get(container_id)
        if container is None:
            return None
        return container.status

    def get_containers(self) -> List[ContainerInstance]:
        """获取所有容器"""
        logger.debug("DockerPackageService: getting all containers")
        return list(self.packager._containers.values())
