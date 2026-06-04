"""
自动生成重构对比报告模块

职责：对比重构前后的代码结构差异，生成详细的差异报告，包含统计信息和改进建议

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DiffType(str, Enum):
    """差异类型"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"
    RENAMED = "renamed"


@dataclass
class DiffEntry:
    """差异条目"""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    diff_type: DiffType = DiffType.MODIFIED
    file_path: str = ""
    before: str = ""
    after: str = ""
    description: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"DiffEntry created: entry_id={self.entry_id}, "
                     f"type={self.diff_type.value}, file={self.file_path}")


@dataclass
class RefactorDiffReport:
    """重构差异报告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    summary: str = ""
    entries: List[DiffEntry] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"RefactorDiffReport created: report_id={self.report_id}, "
                     f"entries={len(self.entries)}")


class RefactorDiffGenerator:
    """重构差异生成器"""

    def __init__(self):
        """初始化重构差异生成器"""
        self._reports: List[RefactorDiffReport] = []
        logger.info("RefactorDiffGenerator initialized")

    def generate_diff(self, before_structure: Dict[str, Any],
                      after_structure: Dict[str, Any]) -> List[DiffEntry]:
        """生成重构差异"""
        logger.info("RefactorDiffGenerator: generating diff")
        try:
            entries: List[DiffEntry] = []
            entries.extend(self._compare_structures(before_structure, after_structure))
            entries.extend(self._compare_code(before_structure, after_structure))

            logger.info(f"RefactorDiffGenerator: generated {len(entries)} diff entries")
        except Exception as e:
            logger.error(f"RefactorDiffGenerator: generate_diff failed: {e}")
            entries = []
        return entries

    def _compare_structures(self, before: Dict[str, Any],
                            after: Dict[str, Any]) -> List[DiffEntry]:
        """对比结构差异"""
        logger.debug("RefactorDiffGenerator: comparing structures")
        entries: List[DiffEntry] = []
        try:
            before_files = set(before.get("files", {}).keys()) if isinstance(before.get("files"), dict) else set()
            after_files = set(after.get("files", {}).keys()) if isinstance(after.get("files"), dict) else set()

            added = after_files - before_files
            removed = before_files - after_files

            for file_path in added:
                entries.append(DiffEntry(
                    diff_type=DiffType.ADDED,
                    file_path=file_path,
                    after=after.get("files", {}).get(file_path, ""),
                    description=f"新增文件: {file_path}",
                ))

            for file_path in removed:
                entries.append(DiffEntry(
                    diff_type=DiffType.REMOVED,
                    file_path=file_path,
                    before=before.get("files", {}).get(file_path, ""),
                    description=f"删除文件: {file_path}",
                ))

            common = before_files & after_files
            for file_path in common:
                before_content = before.get("files", {}).get(file_path, "")
                after_content = after.get("files", {}).get(file_path, "")
                if before_content != after_content:
                    entries.append(DiffEntry(
                        diff_type=DiffType.MODIFIED,
                        file_path=file_path,
                        before=before_content,
                        after=after_content,
                        description=f"修改文件: {file_path}",
                    ))

            before_modules = set(before.get("modules", []))
            after_modules = set(after.get("modules", []))
            new_modules = after_modules - before_modules
            removed_modules = before_modules - after_modules

            for module in new_modules:
                entries.append(DiffEntry(
                    diff_type=DiffType.ADDED,
                    file_path=module,
                    description=f"新增模块: {module}",
                ))

            for module in removed_modules:
                entries.append(DiffEntry(
                    diff_type=DiffType.REMOVED,
                    file_path=module,
                    description=f"删除模块: {module}",
                ))

            logger.debug(f"RefactorDiffGenerator: structure comparison found "
                        f"{len(entries)} differences")
        except Exception as e:
            logger.error(f"RefactorDiffGenerator: _compare_structures failed: {e}")
        return entries

    def _compare_code(self, before: Dict[str, Any],
                      after: Dict[str, Any]) -> List[DiffEntry]:
        """对比代码差异"""
        logger.debug("RefactorDiffGenerator: comparing code")
        entries: List[DiffEntry] = []
        try:
            before_classes = set(before.get("classes", []))
            after_classes = set(after.get("classes", []))

            added_classes = after_classes - before_classes
            removed_classes = before_classes - after_classes

            for cls in added_classes:
                entries.append(DiffEntry(
                    diff_type=DiffType.ADDED,
                    file_path=cls,
                    description=f"新增类: {cls}",
                ))

            for cls in removed_classes:
                entries.append(DiffEntry(
                    diff_type=DiffType.REMOVED,
                    file_path=cls,
                    description=f"删除类: {cls}",
                ))

            before_functions = set(before.get("functions", []))
            after_functions = set(after.get("functions", []))

            added_funcs = after_functions - before_functions
            removed_funcs = before_functions - after_functions

            for func in added_funcs:
                entries.append(DiffEntry(
                    diff_type=DiffType.ADDED,
                    file_path=func,
                    description=f"新增函数: {func}",
                ))

            for func in removed_funcs:
                entries.append(DiffEntry(
                    diff_type=DiffType.REMOVED,
                    file_path=func,
                    description=f"删除函数: {func}",
                ))

            moved = before.get("moved", [])
            for move in moved:
                entries.append(DiffEntry(
                    diff_type=DiffType.MOVED,
                    file_path=move.get("path", ""),
                    before=move.get("from", ""),
                    after=move.get("to", ""),
                    description=f"移动: {move.get('from', '')} -> {move.get('to', '')}",
                ))

            renamed = before.get("renamed", [])
            for rename in renamed:
                entries.append(DiffEntry(
                    diff_type=DiffType.RENAMED,
                    file_path=rename.get("path", ""),
                    before=rename.get("old_name", ""),
                    after=rename.get("new_name", ""),
                    description=f"重命名: {rename.get('old_name', '')} -> {rename.get('new_name', '')}",
                ))

            logger.debug(f"RefactorDiffGenerator: code comparison found "
                        f"{len(entries)} differences")
        except Exception as e:
            logger.error(f"RefactorDiffGenerator: _compare_code failed: {e}")
        return entries

    def _calculate_statistics(self, entries: List[DiffEntry]) -> Dict[str, Any]:
        """计算统计信息"""
        logger.debug("RefactorDiffGenerator: calculating statistics")
        try:
            by_type: Dict[str, int] = {}
            for entry in entries:
                by_type[entry.diff_type.value] = by_type.get(entry.diff_type.value, 0) + 1

            stats: Dict[str, Any] = {
                "total_changes": len(entries),
                "by_type": by_type,
                "added_count": by_type.get(DiffType.ADDED.value, 0),
                "removed_count": by_type.get(DiffType.REMOVED.value, 0),
                "modified_count": by_type.get(DiffType.MODIFIED.value, 0),
                "moved_count": by_type.get(DiffType.MOVED.value, 0),
                "renamed_count": by_type.get(DiffType.RENAMED.value, 0),
            }
            logger.debug(f"RefactorDiffGenerator: statistics={stats}")
        except Exception as e:
            logger.error(f"RefactorDiffGenerator: _calculate_statistics failed: {e}")
            stats = {}
        return stats

    def generate_report(self, before_structure: Dict[str, Any],
                        after_structure: Dict[str, Any]) -> RefactorDiffReport:
        """生成重构差异报告"""
        logger.info("RefactorDiffGenerator: generating report")
        try:
            entries = self.generate_diff(before_structure, after_structure)
            statistics = self._calculate_statistics(entries)

            recommendations: List[str] = []
            if statistics.get("removed_count", 0) > statistics.get("added_count", 0):
                recommendations.append("删除多于新增，建议确认功能完整性")
            if statistics.get("modified_count", 0) > 10:
                recommendations.append("修改文件较多，建议分批验证")
            if statistics.get("moved_count", 0) > 0:
                recommendations.append("存在文件移动，建议检查引用更新")
            if statistics.get("renamed_count", 0) > 0:
                recommendations.append("存在重命名操作，建议检查所有引用")

            summary = (f"共检测到 {len(entries)} 处变更: "
                       f"新增 {statistics.get('added_count', 0)}, "
                       f"删除 {statistics.get('removed_count', 0)}, "
                       f"修改 {statistics.get('modified_count', 0)}, "
                       f"移动 {statistics.get('moved_count', 0)}, "
                       f"重命名 {statistics.get('renamed_count', 0)}")

            report = RefactorDiffReport(
                summary=summary,
                entries=entries,
                statistics=statistics,
                recommendations=recommendations,
            )
            self._reports.append(report)
            logger.info(f"RefactorDiffGenerator: report generated, "
                        f"total_changes={len(entries)}")
        except Exception as e:
            logger.error(f"RefactorDiffGenerator: generate_report failed: {e}")
            report = RefactorDiffReport(summary=f"生成报告失败: {e}")
        return report


class RefactorDiffService:
    """重构差异服务"""

    def __init__(self, generator: Optional[RefactorDiffGenerator] = None):
        """初始化重构差异服务"""
        self.generator = generator or RefactorDiffGenerator()
        logger.info("RefactorDiffService initialized")

    def generate(self, before_structure: Dict[str, Any],
                 after_structure: Dict[str, Any]) -> RefactorDiffReport:
        """执行重构差异分析"""
        logger.info("RefactorDiffService: generating diff report")
        return self.generator.generate_report(before_structure, after_structure)

    def get_report(self, index: int = -1) -> Optional[RefactorDiffReport]:
        """获取差异报告"""
        logger.debug(f"RefactorDiffService: getting report, index={index}")
        if not self.generator._reports:
            return None
        try:
            return self.generator._reports[index]
        except IndexError:
            return None

    def get_statistics(self, index: int = -1) -> Dict[str, Any]:
        """获取统计信息"""
        logger.debug(f"RefactorDiffService: getting statistics, index={index}")
        report = self.get_report(index)
        if report is None:
            return {}
        return report.statistics
