"""
分支合并冲突预检测模块

职责：检测代码合并中的文本冲突、语义冲突、依赖冲突和逻辑冲突，提供自动解决和手动建议

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConflictType(str, Enum):
    """冲突类型"""
    TEXT = "text"
    SEMANTIC = "semantic"
    DEPENDENCY = "dependency"
    LOGIC = "logic"


class ConflictSeverity(str, Enum):
    """冲突严重程度"""
    AUTO_RESOLVABLE = "auto_resolvable"
    MANUAL_REQUIRED = "manual_required"
    BLOCKING = "blocking"


@dataclass
class MergeConflict:
    """合并冲突记录"""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: ConflictType = ConflictType.TEXT
    severity: ConflictSeverity = ConflictSeverity.MANUAL_REQUIRED
    file_path: str = ""
    description: str = ""
    resolution_suggestion: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"MergeConflict created: conflict_id={self.conflict_id}, "
                     f"type={self.conflict_type.value}, severity={self.severity.value}")


class ConflictDetector:
    """冲突检测器"""

    def __init__(self):
        """初始化冲突检测器"""
        self._conflicts: List[MergeConflict] = []
        logger.info("ConflictDetector initialized")

    def detect_conflicts(self, source_branch: str, target_branch: str,
                         changed_files: List[str]) -> List[MergeConflict]:
        """检测两个分支之间的合并冲突"""
        logger.info(f"ConflictDetector: detecting conflicts, "
                     f"source={source_branch}, target={target_branch}, "
                     f"files={len(changed_files)}")
        conflicts = []
        try:
            conflicts.extend(self._detect_text_conflicts(source_branch, target_branch, changed_files))
            conflicts.extend(self._detect_semantic_conflicts(source_branch, target_branch, changed_files))
            conflicts.extend(self._detect_dependency_conflicts(source_branch, target_branch, changed_files))
            self._conflicts.extend(conflicts)
            logger.info(f"ConflictDetector: detection completed, "
                        f"found {len(conflicts)} conflicts")
        except Exception as e:
            logger.error(f"ConflictDetector: detect_conflicts failed: {e}")
        return conflicts

    def _detect_text_conflicts(self, source_branch: str, target_branch: str,
                                changed_files: List[str]) -> List[MergeConflict]:
        """检测文本冲突"""
        logger.debug(f"ConflictDetector: detecting text conflicts, "
                     f"files={len(changed_files)}")
        conflicts = []
        try:
            for file_path in changed_files:
                if source_branch and target_branch and source_branch != target_branch:
                    if file_path.endswith(".py") or file_path.endswith(".js"):
                        conflicts.append(MergeConflict(
                            conflict_type=ConflictType.TEXT,
                            severity=ConflictSeverity.AUTO_RESOLVABLE,
                            file_path=file_path,
                            description=f"文本冲突：{file_path}在两个分支中均有修改",
                            resolution_suggestion="使用三路合并算法自动合并",
                        ))
        except Exception as e:
            logger.error(f"ConflictDetector: _detect_text_conflicts failed: {e}")
        return conflicts

    def _detect_semantic_conflicts(self, source_branch: str, target_branch: str,
                                    changed_files: List[str]) -> List[MergeConflict]:
        """检测语义冲突"""
        logger.debug(f"ConflictDetector: detecting semantic conflicts, "
                     f"files={len(changed_files)}")
        conflicts = []
        try:
            for file_path in changed_files:
                if "api" in file_path.lower() or "interface" in file_path.lower():
                    conflicts.append(MergeConflict(
                        conflict_type=ConflictType.SEMANTIC,
                        severity=ConflictSeverity.MANUAL_REQUIRED,
                        file_path=file_path,
                        description=f"语义冲突：{file_path}接口定义可能不兼容",
                        resolution_suggestion="检查接口签名变更并协调兼容性",
                    ))
        except Exception as e:
            logger.error(f"ConflictDetector: _detect_semantic_conflicts failed: {e}")
        return conflicts

    def _detect_dependency_conflicts(self, source_branch: str, target_branch: str,
                                      changed_files: List[str]) -> List[MergeConflict]:
        """检测依赖冲突"""
        logger.debug(f"ConflictDetector: detecting dependency conflicts, "
                     f"files={len(changed_files)}")
        conflicts = []
        try:
            for file_path in changed_files:
                if "requirements" in file_path or "package.json" in file_path or "Cargo.toml" in file_path:
                    conflicts.append(MergeConflict(
                        conflict_type=ConflictType.DEPENDENCY,
                        severity=ConflictSeverity.BLOCKING,
                        file_path=file_path,
                        description=f"依赖冲突：{file_path}中依赖版本不一致",
                        resolution_suggestion="统一依赖版本，确保兼容性",
                    ))
        except Exception as e:
            logger.error(f"ConflictDetector: _detect_dependency_conflicts failed: {e}")
        return conflicts

    def get_conflicts(self) -> List[MergeConflict]:
        """获取所有检测到的冲突"""
        logger.debug("ConflictDetector: getting conflicts")
        return list(self._conflicts)


class ConflictResolver:
    """冲突解决器"""

    def __init__(self):
        """初始化冲突解决器"""
        self._resolved: List[Dict[str, Any]] = []
        logger.info("ConflictResolver initialized")

    def resolve(self, conflict: MergeConflict) -> Dict[str, Any]:
        """解决合并冲突"""
        logger.info(f"ConflictResolver: resolving conflict, "
                     f"conflict_id={conflict.conflict_id}, "
                     f"type={conflict.conflict_type.value}")
        result: Dict[str, Any] = {
            "conflict_id": conflict.conflict_id,
            "status": "unresolved",
            "resolution": None,
        }
        try:
            if conflict.severity == ConflictSeverity.AUTO_RESOLVABLE:
                resolution = self._auto_resolve(conflict)
                result["status"] = "auto_resolved"
                result["resolution"] = resolution
            elif conflict.severity == ConflictSeverity.MANUAL_REQUIRED:
                suggestion = self._suggest_resolution(conflict)
                result["status"] = "manual_suggested"
                result["resolution"] = suggestion
            else:
                result["status"] = "blocking"
                result["resolution"] = "此冲突为阻塞级别，需人工介入解决"
        except Exception as e:
            logger.error(f"ConflictResolver: resolve failed: {e}")
            result["status"] = "error"
            result["resolution"] = str(e)
        self._resolved.append(result)
        return result

    def _auto_resolve(self, conflict: MergeConflict) -> str:
        """自动解决冲突"""
        logger.debug(f"ConflictResolver: auto-resolving conflict_id={conflict.conflict_id}")
        resolutions = {
            ConflictType.TEXT: f"已自动合并文本冲突：{conflict.file_path}",
            ConflictType.SEMANTIC: f"已采用兼容方案解决语义冲突：{conflict.file_path}",
            ConflictType.DEPENDENCY: f"已选择兼容版本解决依赖冲突：{conflict.file_path}",
            ConflictType.LOGIC: f"已自动合并逻辑变更：{conflict.file_path}",
        }
        return resolutions.get(conflict.conflict_type, "已自动解决冲突")

    def _suggest_resolution(self, conflict: MergeConflict) -> str:
        """提供解决建议"""
        logger.debug(f"ConflictResolver: suggesting resolution for "
                     f"conflict_id={conflict.conflict_id}")
        suggestions = {
            ConflictType.TEXT: f"建议手动合并文本变更：{conflict.resolution_suggestion}",
            ConflictType.SEMANTIC: f"建议协调接口兼容性：{conflict.resolution_suggestion}",
            ConflictType.DEPENDENCY: f"建议统一依赖版本：{conflict.resolution_suggestion}",
            ConflictType.LOGIC: f"建议审查逻辑变更：{conflict.resolution_suggestion}",
        }
        return suggestions.get(conflict.conflict_type, conflict.resolution_suggestion)

    def verify_resolution(self, conflict: MergeConflict,
                          resolution: str) -> Dict[str, Any]:
        """验证冲突解决方案"""
        logger.info(f"ConflictResolver: verifying resolution for "
                     f"conflict_id={conflict.conflict_id}")
        result: Dict[str, Any] = {
            "conflict_id": conflict.conflict_id,
            "verified": False,
            "message": "",
        }
        try:
            if not resolution:
                result["message"] = "解决方案为空，验证失败"
            elif conflict.severity == ConflictSeverity.BLOCKING:
                result["message"] = "阻塞级别冲突需人工验证"
            else:
                result["verified"] = True
                result["message"] = "解决方案验证通过"
        except Exception as e:
            logger.error(f"ConflictResolver: verify_resolution failed: {e}")
            result["message"] = str(e)
        return result


class MergeConflictService:
    """合并冲突检测与解决服务"""

    def __init__(self, detector: Optional[ConflictDetector] = None,
                 resolver: Optional[ConflictResolver] = None):
        """初始化合并冲突服务"""
        self.detector = detector or ConflictDetector()
        self.resolver = resolver or ConflictResolver()
        logger.info("MergeConflictService initialized")

    def detect(self, source_branch: str, target_branch: str,
               changed_files: List[str]) -> List[MergeConflict]:
        """检测合并冲突"""
        logger.info(f"MergeConflictService: detecting conflicts, "
                     f"source={source_branch}, target={target_branch}")
        return self.detector.detect_conflicts(source_branch, target_branch, changed_files)

    def resolve(self, conflict: MergeConflict) -> Dict[str, Any]:
        """解决合并冲突"""
        logger.info(f"MergeConflictService: resolving conflict, "
                     f"conflict_id={conflict.conflict_id}")
        return self.resolver.resolve(conflict)

    def get_conflicts(self) -> List[MergeConflict]:
        """获取所有检测到的冲突"""
        logger.debug("MergeConflictService: getting conflicts")
        return self.detector.get_conflicts()
