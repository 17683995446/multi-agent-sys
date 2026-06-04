"""
文档Agent模块
职责：文档生成、归档能力、同步更新

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class DocType(str, Enum):
    """文档类型"""
    README = "readme"
    API = "api"
    GUIDE = "guide"
    CHANGELOG = "changelog"
    README_CODE = "readme_code"
    GUIDE_CODE = "guide_code"


class DocFormat(str, Enum):
    """文档格式"""
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"


class ArchiveType(str, Enum):
    """归档类型"""
    FILE = "file"
    VERSION = "version"


class SyncStatus(str, Enum):
    """同步状态"""
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    OUTDATED = "outdated"


@dataclass
class DocumentSection:
    """文档章节"""
    section_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    level: int = 1
    children: List["DocumentSection"] = field(default_factory=list)


@dataclass
class Document:
    """文档"""
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    doc_type: DocType = DocType.README
    format: DocFormat = DocFormat.MARKDOWN
    sections: List[DocumentSection] = field(default_factory=list)
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ArchiveEntry:
    """归档条目"""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    archive_type: ArchiveType = ArchiveType.FILE
    document: Document = None
    version: str = "1.0.0"
    file_path: str = ""
    checksum: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SyncRecord:
    """同步记录"""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    target: str = ""
    status: SyncStatus = SyncStatus.SYNCED
    auto_sync: bool = False
    last_sync_at: Optional[datetime] = None
    sync_result: str = ""


@dataclass
class DocConfig:
    """文档Agent配置"""
    name: str
    enable_template_generation: bool = True
    enable_intelligent_generation: bool = True
    enable_version_archive: bool = True
    enable_auto_sync: bool = True
    default_format: DocFormat = DocFormat.MARKDOWN


class DocTemplateGenerator:
    """文档模板生成器"""
    
    def __init__(self):
        self.templates = {
            DocType.README: self._generate_readme_template,
            DocType.API: self._generate_api_template,
            DocType.GUIDE: self._generate_guide_template,
            DocType.CHANGELOG: self._generate_changelog_template,
        }
    
    def generate_from_template(self, doc_type: DocType, **kwargs) -> Document:
        """从模板生成文档"""
        title = kwargs.get("title", f"New {doc_type.value} Document")
        
        doc = Document(
            title=title,
            doc_type=doc_type,
            format=DocFormat.MARKDOWN
        )
        
        if doc_type in self.templates:
            sections = self.templates[doc_type](**kwargs)
            doc.sections = sections
        
        doc.content = self._sections_to_markdown(doc.sections)
        
        return doc
    
    def _generate_readme_template(self, **kwargs) -> List[DocumentSection]:
        """生成README模板"""
        sections = [
            DocumentSection(title="# 项目名称", content="", level=1),
            DocumentSection(title="## 简介", content="项目简介内容", level=2),
            DocumentSection(title="## 安装", content="安装说明", level=2),
            DocumentSection(title="## 使用", content="使用说明", level=2),
            DocumentSection(title="## 贡献", content="贡献指南", level=2),
            DocumentSection(title="## 许可证", content="MIT License", level=2),
        ]
        return sections
    
    def _generate_api_template(self, **kwargs) -> List[DocumentSection]:
        """生成API文档模板"""
        sections = [
            DocumentSection(title="# API 文档", content="", level=1),
            DocumentSection(title="## 概述", content="API概述", level=2),
            DocumentSection(title="## 认证", content="认证说明", level=2),
            DocumentSection(title="## 端点", content="端点列表", level=2),
            DocumentSection(title="## 错误码", content="错误码说明", level=2),
        ]
        return sections
    
    def _generate_guide_template(self, **kwargs) -> List[DocumentSection]:
        """生成指南模板"""
        sections = [
            DocumentSection(title="# 使用指南", content="", level=1),
            DocumentSection(title="## 快速开始", content="快速开始指南", level=2),
            DocumentSection(title="## 进阶教程", content="进阶教程", level=2),
            DocumentSection(title="## 最佳实践", content="最佳实践", level=2),
            DocumentSection(title="## 常见问题", content="FAQ", level=2),
        ]
        return sections
    
    def _generate_changelog_template(self, **kwargs) -> List[DocumentSection]:
        """生成变更日志模板"""
        version = kwargs.get("version", "1.0.0")
        sections = [
            DocumentSection(title=f"# 变更日志 v{version}", content="", level=1),
            DocumentSection(title="## 最新版本", content="", level=2),
            DocumentSection(title="### 新增", content="- 新功能", level=3),
            DocumentSection(title="### 修改", content="- 功能改进", level=3),
            DocumentSection(title="### 修复", content="- Bug修复", level=3),
        ]
        return sections
    
    def _sections_to_markdown(self, sections: List[DocumentSection]) -> str:
        """将章节转换为Markdown"""
        lines = []
        for section in sections:
            lines.append(section.title)
            if section.content:
                lines.append(section.content)
            lines.append("")
            if section.children:
                lines.append(self._sections_to_markdown(section.children))
        return "\n".join(lines)


class IntelligentDocGenerator:
    """智能文档生成器"""
    
    def __init__(self):
        pass
    
    def generate_from_code(self, code: str, doc_type: DocType = DocType.README) -> Document:
        """从代码智能生成文档"""
        doc = Document(
            title="Auto-generated Documentation",
            doc_type=doc_type
        )
        
        sections = []
        
        if doc_type == DocType.README_CODE:
            sections = self._analyze_for_readme(code)
        elif doc_type == DocType.GUIDE_CODE:
            sections = self._analyze_for_guide(code)
        
        doc.sections = sections
        doc.content = self._sections_to_markdown(sections)
        doc.metadata["auto_generated"] = True
        doc.metadata["code_hash"] = self._calculate_hash(code)
        
        return doc
    
    def _analyze_for_readme(self, code: str) -> List[DocumentSection]:
        """分析代码生成README"""
        sections = [
            DocumentSection(title="# 项目文档", content="", level=1),
            DocumentSection(title="## 项目简介", content=self._extract_description(code), level=2),
            DocumentSection(title="## 功能特性", content=self._extract_features(code), level=2),
            DocumentSection(title="## 使用方法", content=self._extract_usage(code), level=2),
        ]
        return sections
    
    def _analyze_for_guide(self, code: str) -> List[DocumentSection]:
        """分析代码生成指南"""
        sections = [
            DocumentSection(title="# 使用指南", content="", level=1),
            DocumentSection(title="## 安装指南", content=self._extract_installation(code), level=2),
            DocumentSection(title="## 配置说明", content=self._extract_configuration(code), level=2),
            DocumentSection(title="## 示例代码", content=self._extract_examples(code), level=2),
        ]
        return sections
    
    def _extract_description(self, code: str) -> str:
        """提取描述"""
        docstring_match = code.find('"""')
        if docstring_match != -1:
            end = code.find('"""', docstring_match + 3)
            if end != -1:
                return code[docstring_match + 3:end].strip()
        return "Auto-generated from source code"
    
    def _extract_features(self, code: str) -> str:
        """提取功能特性"""
        features = []
        if "def " in code:
            features.append("- 函数定义")
        if "class " in code:
            features.append("- 类定义")
        if "import " in code:
            features.append("- 模块导入")
        return "\n".join(features) if features else "- 代码分析完成"
    
    def _extract_usage(self, code: str) -> str:
        """提取使用方法"""
        functions = []
        for line in code.split("\n"):
            if line.strip().startswith("def "):
                func_name = line.split("def ")[1].split("(")[0].strip()
                functions.append(f"- {func_name}()")
        return "\n".join(functions[:5]) if functions else "- 参考示例代码"
    
    def _extract_installation(self, code: str) -> str:
        """提取安装说明"""
        imports = []
        for line in code.split("\n"):
            if line.strip().startswith("import "):
                imports.append(line.strip())
        return "\n".join(imports[:5]) if imports else "- 安装依赖"
    
    def _extract_configuration(self, code: str) -> str:
        """提取配置说明"""
        return "配置参数基于代码中的默认值"
    
    def _extract_examples(self, code: str) -> str:
        """提取示例代码"""
        return "```python\n" + "\n".join(code.split("\n")[:10]) + "\n```"
    
    def _sections_to_markdown(self, sections: List[DocumentSection]) -> str:
        """将章节转换为Markdown"""
        lines = []
        for section in sections:
            lines.append(section.title)
            if section.content:
                lines.append(section.content)
            lines.append("")
        return "\n".join(lines)
    
    def _calculate_hash(self, code: str) -> str:
        """计算代码哈希"""
        return hashlib.md5(code.encode()).hexdigest()


class DocArchiver:
    """文档归档器"""
    
    def __init__(self):
        self.archives: List[ArchiveEntry] = []
    
    def archive_document(self, document: Document, 
                       archive_type: ArchiveType = ArchiveType.FILE) -> ArchiveEntry:
        """归档文档"""
        entry = ArchiveEntry(
            archive_type=archive_type,
            document=document,
            version=document.metadata.get("version", "1.0.0"),
            file_path=f"docs/{document.doc_id}.md",
            checksum=self._calculate_checksum(document.content)
        )
        
        self.archives.append(entry)
        
        return entry
    
    def archive_file(self, file_path: str, content: str) -> ArchiveEntry:
        """归档文件"""
        doc = Document(
            title=file_path,
            doc_type=DocType.README,
            content=content
        )
        
        entry = ArchiveEntry(
            archive_type=ArchiveType.FILE,
            document=doc,
            file_path=file_path,
            checksum=self._calculate_checksum(content)
        )
        
        self.archives.append(entry)
        
        return entry
    
    def get_archive_history(self, doc_id: str) -> List[ArchiveEntry]:
        """获取归档历史"""
        return [
            entry for entry in self.archives
            if entry.document and entry.document.doc_id == doc_id
        ]
    
    def _calculate_checksum(self, content: str) -> str:
        """计算校验和"""
        return hashlib.sha256(content.encode()).hexdigest()


class DocSynchronizer:
    """文档同步器"""
    
    def __init__(self):
        self.sync_records: List[SyncRecord] = []
    
    def add_sync_pair(self, source: str, target: str, 
                     auto_sync: bool = False) -> SyncRecord:
        """添加同步对"""
        record = SyncRecord(
            source=source,
            target=target,
            auto_sync=auto_sync,
            status=SyncStatus.PENDING
        )
        
        self.sync_records.append(record)
        
        return record
    
    def sync_manual(self, source: str, target: str) -> SyncRecord:
        """手动同步"""
        record = SyncRecord(
            source=source,
            target=target,
            auto_sync=False,
            status=SyncStatus.SYNCED,
            last_sync_at=datetime.now(),
            sync_result="Manual sync completed"
        )
        
        self.sync_records.append(record)
        
        return record
    
    def sync_auto(self, doc_id: str) -> SyncRecord:
        """自动同步"""
        record = SyncRecord(
            source=f"source_{doc_id}",
            target=f"target_{doc_id}",
            auto_sync=True,
            status=SyncStatus.SYNCED,
            last_sync_at=datetime.now(),
            sync_result="Auto sync completed"
        )
        
        self.sync_records.append(record)
        
        return record
    
    def get_sync_status(self, doc_id: str) -> SyncStatus:
        """获取同步状态"""
        records = [
            r for r in self.sync_records
            if doc_id in r.source or doc_id in r.target
        ]
        
        if not records:
            return SyncStatus.OUTDATED
        
        latest = max(records, key=lambda r: r.last_sync_at or datetime.min)
        
        return latest.status


class DocAgent:
    """文档Agent"""
    
    def __init__(self, config: DocConfig):
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.template_generator = DocTemplateGenerator()
        self.intelligent_generator = IntelligentDocGenerator()
        self.archiver = DocArchiver()
        self.synchronizer = DocSynchronizer()
        self.documents: List[Document] = []
    
    def generate_document(self, doc_type: DocType, 
                         use_intelligent: bool = False, **kwargs) -> Document:
        """生成文档"""
        if use_intelligent and self.config.enable_intelligent_generation:
            code = kwargs.get("code", "")
            doc = self.intelligent_generator.generate_from_code(code, doc_type)
        elif self.config.enable_template_generation:
            doc = self.template_generator.generate_from_template(doc_type, **kwargs)
        else:
            doc = Document(title=kwargs.get("title", "New Document"), doc_type=doc_type)
        
        self.documents.append(doc)
        
        return doc
    
    def archive_document(self, doc_id: str, 
                       archive_type: ArchiveType = ArchiveType.VERSION) -> ArchiveEntry:
        """归档文档"""
        doc = next((d for d in self.documents if d.doc_id == doc_id), None)
        
        if not doc:
            doc = Document(title="Unknown", doc_id=doc_id)
        
        return self.archiver.archive_document(doc, archive_type)
    
    def sync_document(self, doc_id: str, 
                    auto_sync: bool = None) -> SyncRecord:
        """同步文档"""
        if auto_sync is None:
            auto_sync = self.config.enable_auto_sync
        
        if auto_sync:
            return self.synchronizer.sync_auto(doc_id)
        else:
            return self.synchronizer.sync_manual(
                f"source/{doc_id}",
                f"target/{doc_id}"
            )
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return next((d for d in self.documents if d.doc_id == doc_id), None)
    
    def list_documents(self) -> List[Document]:
        """列出所有文档"""
        return self.documents


_global_doc_agent: Optional[DocAgent] = None


def get_doc_agent(config: Optional[DocConfig] = None) -> DocAgent:
    """获取全局文档Agent"""
    global _global_doc_agent
    if _global_doc_agent is None:
        if config is None:
            config = DocConfig(name="DocAgent")
        _global_doc_agent = DocAgent(config)
    return _global_doc_agent


def reset_doc_agent() -> None:
    """重置文档Agent"""
    global _global_doc_agent
    _global_doc_agent = None
