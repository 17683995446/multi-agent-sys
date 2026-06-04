"""
测试通过→文档归档链路
职责：文档生成、文档归档、文档检索

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DocType(str, Enum):
    """文档类型"""
    API = "api"
    README = "readme"
    CHANGELOG = "changelog"
    ARCHITECTURE = "architecture"
    TEST_REPORT = "test_report"


class DocStatus(str, Enum):
    """文档状态"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class DocumentRecord:
    """文档记录"""
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_type: DocType = DocType.API
    title: str = ""
    content: str = ""
    status: DocStatus = DocStatus.PENDING
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug(f"DocumentRecord created: id={self.doc_id}, title={self.title}, "
                     f"type={self.doc_type.value}")


class DocGenerator:
    """文档生成器"""

    def __init__(self):
        """初始化文档生成器"""
        self.templates: Dict[DocType, str] = {
            DocType.API: "# API文档\n\n## 接口列表\n\n",
            DocType.README: "# 项目说明\n\n## 简介\n\n",
            DocType.CHANGELOG: "# 变更日志\n\n## 版本记录\n\n",
            DocType.ARCHITECTURE: "# 架构文档\n\n## 系统架构\n\n",
            DocType.TEST_REPORT: "# 测试报告\n\n## 测试结果\n\n",
        }
        logger.info("DocGenerator initialized")

    def generate(self, doc_type: DocType, title: str = "",
                 metadata: Optional[Dict[str, Any]] = None) -> DocumentRecord:
        """生成文档"""
        logger.info(f"DocGenerator: generating doc type={doc_type.value}, title={title}")
        try:
            record = DocumentRecord(
                doc_type=doc_type,
                title=title,
                status=DocStatus.GENERATING,
                metadata=metadata or {},
            )

            if doc_type == DocType.API:
                record.content = self._generate_api_doc(record)
            elif doc_type == DocType.README:
                record.content = self._generate_readme(record)
            elif doc_type == DocType.CHANGELOG:
                record.content = self._generate_changelog(record)
            elif doc_type == DocType.TEST_REPORT:
                record.content = self._generate_test_report(record)
            else:
                record.content = self._generate_api_doc(record)

            record.status = DocStatus.COMPLETED
            logger.info(f"DocGenerator: doc generated id={record.doc_id}, "
                        f"type={doc_type.value}, status={record.status.value}")
        except Exception as e:
            logger.error(f"DocGenerator: generate failed: {e}")
            record.status = DocStatus.PENDING
            record.content = ""

        return record

    def _generate_api_doc(self, record: DocumentRecord) -> str:
        """生成API文档"""
        logger.debug(f"DocGenerator: generating API doc id={record.doc_id}")
        template = self.templates.get(DocType.API, "")
        title = record.title or "API文档"
        content = f"{template}### {title}\n\n"
        if record.metadata.get("endpoints"):
            for ep in record.metadata["endpoints"]:
                content += f"- {ep}\n"
            content += "\n"
        content += f"生成时间: {datetime.fromtimestamp(record.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
        return content

    def _generate_readme(self, record: DocumentRecord) -> str:
        """生成README文档"""
        logger.debug(f"DocGenerator: generating README doc id={record.doc_id}")
        template = self.templates.get(DocType.README, "")
        title = record.title or "项目说明"
        content = f"{template}### {title}\n\n"
        if record.metadata.get("description"):
            content += f"{record.metadata['description']}\n\n"
        content += f"生成时间: {datetime.fromtimestamp(record.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
        return content

    def _generate_changelog(self, record: DocumentRecord) -> str:
        """生成变更日志文档"""
        logger.debug(f"DocGenerator: generating changelog doc id={record.doc_id}")
        template = self.templates.get(DocType.CHANGELOG, "")
        title = record.title or "变更日志"
        content = f"{template}### {title}\n\n"
        if record.metadata.get("changes"):
            for change in record.metadata["changes"]:
                content += f"- {change}\n"
            content += "\n"
        content += f"生成时间: {datetime.fromtimestamp(record.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
        return content

    def _generate_test_report(self, record: DocumentRecord) -> str:
        """生成测试报告文档"""
        logger.debug(f"DocGenerator: generating test report doc id={record.doc_id}")
        template = self.templates.get(DocType.TEST_REPORT, "")
        title = record.title or "测试报告"
        content = f"{template}### {title}\n\n"
        if record.metadata.get("test_results"):
            total = record.metadata["test_results"].get("total", 0)
            passed = record.metadata["test_results"].get("passed", 0)
            failed = record.metadata["test_results"].get("failed", 0)
            content += f"- 总计: {total}\n- 通过: {passed}\n- 失败: {failed}\n\n"
        content += f"生成时间: {datetime.fromtimestamp(record.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
        return content


class DocArchiver:
    """文档归档器"""

    def __init__(self):
        """初始化文档归档器"""
        self._archive: Dict[str, DocumentRecord] = {}
        logger.info("DocArchiver initialized")

    def archive(self, record: DocumentRecord) -> DocumentRecord:
        """归档文档"""
        logger.info(f"DocArchiver: archiving doc id={record.doc_id}, "
                    f"title={record.title}")
        try:
            if record.status != DocStatus.COMPLETED:
                logger.warning(f"DocArchiver: doc id={record.doc_id} "
                               f"status={record.status.value}, not completed")
                return record

            record.status = DocStatus.ARCHIVED
            self._archive[record.doc_id] = record
            logger.info(f"DocArchiver: doc id={record.doc_id} archived")
        except Exception as e:
            logger.error(f"DocArchiver: archive failed: {e}")

        return record

    def retrieve(self, doc_id: str) -> Optional[DocumentRecord]:
        """检索文档"""
        logger.debug(f"DocArchiver: retrieving doc id={doc_id}")
        record = self._archive.get(doc_id)
        if record is None:
            logger.warning(f"DocArchiver: doc id={doc_id} not found")
        return record

    def list_docs(self, doc_type: Optional[DocType] = None) -> List[DocumentRecord]:
        """列出文档"""
        logger.debug(f"DocArchiver: listing docs, type={doc_type}")
        docs = list(self._archive.values())
        if doc_type is not None:
            docs = [d for d in docs if d.doc_type == doc_type]
        logger.debug(f"DocArchiver: found {len(docs)} docs")
        return docs

    def search(self, keyword: str) -> List[DocumentRecord]:
        """搜索文档"""
        logger.debug(f"DocArchiver: searching keyword={keyword}")
        results = []
        keyword_lower = keyword.lower()
        for doc in self._archive.values():
            if (keyword_lower in doc.title.lower() or
                    keyword_lower in doc.content.lower()):
                results.append(doc)
        logger.debug(f"DocArchiver: search found {len(results)} docs")
        return results


class DocumentationPipeline:
    """文档归档流水线"""

    def __init__(self):
        """初始化文档归档流水线"""
        self.generator = DocGenerator()
        self.archiver = DocArchiver()
        self.records: Dict[str, DocumentRecord] = {}
        logger.info("DocumentationPipeline initialized")

    def process(self, doc_type: DocType, title: str = "",
                metadata: Optional[Dict[str, Any]] = None) -> DocumentRecord:
        """处理文档流程：生成并归档"""
        logger.info(f"DocumentationPipeline: processing doc type={doc_type.value}, "
                    f"title={title}")
        try:
            record = self.generator.generate(doc_type, title=title, metadata=metadata)
            if record.status == DocStatus.COMPLETED:
                record = self.archiver.archive(record)
            self.records[record.doc_id] = record
            logger.info(f"DocumentationPipeline: doc processed id={record.doc_id}, "
                        f"status={record.status.value}")
        except Exception as e:
            logger.error(f"DocumentationPipeline: process failed: {e}")
            raise

        return record

    def get_document(self, doc_id: str) -> Optional[DocumentRecord]:
        """获取文档"""
        logger.debug(f"DocumentationPipeline: getting document id={doc_id}")
        record = self.archiver.retrieve(doc_id)
        if record is None:
            record = self.records.get(doc_id)
        if record is None:
            logger.warning(f"DocumentationPipeline: doc id={doc_id} not found")
        return record

    def get_status(self, doc_id: str) -> Optional[DocStatus]:
        """获取文档状态"""
        logger.debug(f"DocumentationPipeline: getting status for doc id={doc_id}")
        record = self.records.get(doc_id)
        if record is None:
            logger.warning(f"DocumentationPipeline: no status for doc id={doc_id}")
            return None
        return record.status
