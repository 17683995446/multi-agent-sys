"""
单机稳定运行版本冻结模块

职责：版本冻结、稳定性验证、发布管理、热修复

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReleaseStatus(str, Enum):
    """发布状态"""
    DEVELOPMENT = "development"
    CANDIDATE = "candidate"
    FROZEN = "frozen"
    RELEASED = "released"
    HOTFIX = "hotfix"


@dataclass
class ReleaseNote:
    """发布说明"""
    release_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: str = "0.0.0"
    status: ReleaseStatus = ReleaseStatus.DEVELOPMENT
    features: List[str] = field(default_factory=list)
    bug_fixes: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"ReleaseNote created: release_id={self.release_id}, "
                     f"version={self.version}, status={self.status.value}")


class VersionFreezer:
    """版本冻结器"""

    def __init__(self):
        """初始化版本冻结器"""
        self._releases: Dict[str, ReleaseNote] = {}
        self._checksums: Dict[str, str] = {}
        logger.info("VersionFreezer initialized")

    def freeze_version(self, version: str,
                       features: Optional[List[str]] = None,
                       bug_fixes: Optional[List[str]] = None,
                       breaking_changes: Optional[List[str]] = None,
                       dependencies: Optional[Dict[str, str]] = None) -> ReleaseNote:
        """冻结版本"""
        logger.info(f"VersionFreezer: freezing version={version}")
        try:
            note = ReleaseNote(
                version=version,
                status=ReleaseStatus.CANDIDATE,
                features=features or [],
                bug_fixes=bug_fixes or [],
                breaking_changes=breaking_changes or [],
                dependencies=dependencies or {},
            )

            # 验证稳定性
            stable = self._verify_stability(note)
            if not stable:
                logger.warning(f"VersionFreezer: stability check failed for {version}")
                note.status = ReleaseStatus.DEVELOPMENT
                self._releases[note.release_id] = note
                return note

            # 运行冒烟测试
            smoke_passed = self._run_smoke_tests(note)
            if not smoke_passed:
                logger.warning(f"VersionFreezer: smoke test failed for {version}")
                note.status = ReleaseStatus.DEVELOPMENT
                self._releases[note.release_id] = note
                return note

            # 生成校验和
            checksum = self._generate_checksum(note)
            self._checksums[note.release_id] = checksum

            note.status = ReleaseStatus.FROZEN
            self._releases[note.release_id] = note
            logger.info(f"VersionFreezer: version frozen, "
                        f"version={version}, release_id={note.release_id}")
        except Exception as e:
            logger.error(f"VersionFreezer: freeze_version failed: {e}")
            note = ReleaseNote(version=version, status=ReleaseStatus.DEVELOPMENT)
            self._releases[note.release_id] = note
        return note

    def _verify_stability(self, note: ReleaseNote) -> bool:
        """验证稳定性"""
        logger.debug(f"VersionFreezer: verifying stability, version={note.version}")
        try:
            # 检查是否有未解决的破坏性变更
            if note.breaking_changes and len(note.breaking_changes) > 3:
                logger.debug("VersionFreezer: too many breaking changes")
                return False
            # 检查版本号格式
            parts = note.version.split(".")
            if len(parts) < 2:
                logger.debug("VersionFreezer: invalid version format")
                return False
            return True
        except Exception as e:
            logger.error(f"VersionFreezer: _verify_stability failed: {e}")
            return False

    def _run_smoke_tests(self, note: ReleaseNote) -> bool:
        """运行冒烟测试"""
        logger.debug(f"VersionFreezer: running smoke tests, version={note.version}")
        try:
            # 模拟冒烟测试
            if note.version.startswith("0.0"):
                return False
            return True
        except Exception as e:
            logger.error(f"VersionFreezer: _run_smoke_tests failed: {e}")
            return False

    def _generate_checksum(self, note: ReleaseNote) -> str:
        """生成校验和"""
        logger.debug(f"VersionFreezer: generating checksum, version={note.version}")
        try:
            content = f"{note.version}:{note.features}:{note.bug_fixes}"
            checksum = hashlib.md5(content.encode()).hexdigest()
            logger.debug(f"VersionFreezer: checksum={checksum}")
            return checksum
        except Exception as e:
            logger.error(f"VersionFreezer: _generate_checksum failed: {e}")
            return ""

    def create_release_note(self, release_id: str) -> Dict[str, Any]:
        """创建发布说明"""
        logger.info(f"VersionFreezer: creating release note, release_id={release_id}")
        try:
            note = self._releases.get(release_id)
            if note is None:
                return {"message": "未找到发布记录"}

            release_note: Dict[str, Any] = {
                "release_id": note.release_id,
                "version": note.version,
                "status": note.status.value,
                "features": note.features,
                "bug_fixes": note.bug_fixes,
                "breaking_changes": note.breaking_changes,
                "dependencies": note.dependencies,
                "checksum": self._checksums.get(release_id, ""),
                "timestamp": note.timestamp,
            }
            logger.info(f"VersionFreezer: release note created, version={note.version}")
        except Exception as e:
            logger.error(f"VersionFreezer: create_release_note failed: {e}")
            release_note = {"error": str(e)}
        return release_note


class StableReleaseManager:
    """稳定发布管理器"""

    def __init__(self, freezer: Optional[VersionFreezer] = None):
        """初始化稳定发布管理器"""
        self.freezer = freezer or VersionFreezer()
        logger.info("StableReleaseManager initialized")

    def create_release(self, version: str,
                       features: Optional[List[str]] = None,
                       bug_fixes: Optional[List[str]] = None,
                       breaking_changes: Optional[List[str]] = None,
                       dependencies: Optional[Dict[str, str]] = None) -> ReleaseNote:
        """创建发布"""
        logger.info(f"StableReleaseManager: creating release, version={version}")
        return self.freezer.freeze_version(
            version, features, bug_fixes, breaking_changes, dependencies
        )

    def promote(self, release_id: str) -> Optional[ReleaseNote]:
        """提升发布状态"""
        logger.info(f"StableReleaseManager: promoting release, release_id={release_id}")
        try:
            note = self.freezer._releases.get(release_id)
            if note is None:
                logger.warning(f"StableReleaseManager: release not found, "
                               f"release_id={release_id}")
                return None

            if note.status == ReleaseStatus.FROZEN:
                note.status = ReleaseStatus.RELEASED
                logger.info(f"StableReleaseManager: release promoted to RELEASED, "
                            f"version={note.version}")
            elif note.status == ReleaseStatus.CANDIDATE:
                note.status = ReleaseStatus.FROZEN
                logger.info(f"StableReleaseManager: release promoted to FROZEN, "
                            f"version={note.version}")
            else:
                logger.warning(f"StableReleaseManager: cannot promote from "
                               f"status={note.status.value}")
            return note
        except Exception as e:
            logger.error(f"StableReleaseManager: promote failed: {e}")
            return None

    def get_release(self, release_id: str) -> Optional[ReleaseNote]:
        """获取发布"""
        logger.debug(f"StableReleaseManager: getting release, release_id={release_id}")
        return self.freezer._releases.get(release_id)

    def list_releases(self, status: Optional[ReleaseStatus] = None) -> List[ReleaseNote]:
        """列出发布"""
        logger.debug(f"StableReleaseManager: listing releases, status={status}")
        releases = list(self.freezer._releases.values())
        if status is not None:
            releases = [r for r in releases if r.status == status]
        return releases

    def create_hotfix(self, version: str,
                      bug_fixes: Optional[List[str]] = None) -> ReleaseNote:
        """创建热修复"""
        logger.info(f"StableReleaseManager: creating hotfix, version={version}")
        try:
            note = ReleaseNote(
                version=version,
                status=ReleaseStatus.HOTFIX,
                bug_fixes=bug_fixes or [],
            )
            self.freezer._releases[note.release_id] = note
            logger.info(f"StableReleaseManager: hotfix created, "
                        f"version={version}, release_id={note.release_id}")
        except Exception as e:
            logger.error(f"StableReleaseManager: create_hotfix failed: {e}")
            note = ReleaseNote(version=version)
        return note


class StableReleaseService:
    """单机稳定运行版本冻结服务"""

    def __init__(self, manager: Optional[StableReleaseManager] = None):
        """初始化稳定发布服务"""
        self.manager = manager or StableReleaseManager()
        logger.info("StableReleaseService initialized")

    def freeze(self, version: str,
               features: Optional[List[str]] = None,
               bug_fixes: Optional[List[str]] = None,
               breaking_changes: Optional[List[str]] = None,
               dependencies: Optional[Dict[str, str]] = None) -> ReleaseNote:
        """冻结版本"""
        logger.info(f"StableReleaseService: freezing version={version}")
        return self.manager.create_release(
            version, features, bug_fixes, breaking_changes, dependencies
        )

    def release(self, release_id: str) -> Optional[ReleaseNote]:
        """发布版本"""
        logger.info(f"StableReleaseService: releasing, release_id={release_id}")
        return self.manager.promote(release_id)

    def get_release(self, release_id: str) -> Optional[ReleaseNote]:
        """获取发布信息"""
        logger.debug(f"StableReleaseService: getting release, release_id={release_id}")
        return self.manager.get_release(release_id)

    def get_notes(self, release_id: str) -> Dict[str, Any]:
        """获取发布说明"""
        logger.debug(f"StableReleaseService: getting notes, release_id={release_id}")
        return self.manager.freezer.create_release_note(release_id)
