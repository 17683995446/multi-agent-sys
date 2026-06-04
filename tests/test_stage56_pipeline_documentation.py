"""
阶段56验收测试：测试通过→文档归档链路
"""

import pytest
from src.architecture.pipeline_documentation import (
    DocType,
    DocStatus,
    DocumentRecord,
    DocGenerator,
    DocArchiver,
    DocumentationPipeline,
)


class TestDocType:
    """测试文档类型枚举"""

    def test_type_values(self):
        """测试文档类型枚举值"""
        assert DocType.API.value == "api"
        assert DocType.README.value == "readme"
        assert DocType.CHANGELOG.value == "changelog"
        assert DocType.ARCHITECTURE.value == "architecture"
        assert DocType.TEST_REPORT.value == "test_report"

    def test_all_types(self):
        """测试所有类型"""
        types = list(DocType)
        assert len(types) == 5


class TestDocStatus:
    """测试文档状态枚举"""

    def test_status_values(self):
        """测试文档状态枚举值"""
        assert DocStatus.PENDING.value == "pending"
        assert DocStatus.GENERATING.value == "generating"
        assert DocStatus.COMPLETED.value == "completed"
        assert DocStatus.ARCHIVED.value == "archived"

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = list(DocStatus)
        assert len(statuses) == 4


class TestDocumentRecord:
    """测试文档记录"""

    def test_default_creation(self):
        """测试默认创建"""
        record = DocumentRecord()
        assert record.doc_id != ""
        assert record.doc_type == DocType.API
        assert record.title == ""
        assert record.content == ""
        assert record.status == DocStatus.PENDING
        assert record.created_at > 0
        assert record.metadata == {}

    def test_custom_creation(self):
        """测试自定义创建"""
        record = DocumentRecord(
            doc_type=DocType.README,
            title="项目说明",
            content="# Hello",
            status=DocStatus.COMPLETED,
            metadata={"version": "1.0"},
        )
        assert record.doc_type == DocType.README
        assert record.title == "项目说明"
        assert record.content == "# Hello"
        assert record.status == DocStatus.COMPLETED
        assert record.metadata["version"] == "1.0"

    def test_doc_id_unique(self):
        """测试文档ID唯一性"""
        r1 = DocumentRecord()
        r2 = DocumentRecord()
        assert r1.doc_id != r2.doc_id


class TestDocGenerator:
    """测试文档生成器"""

    def test_initialization(self):
        """测试初始化"""
        gen = DocGenerator()
        assert len(gen.templates) == 5

    def test_generate_api_doc(self):
        """测试生成API文档"""
        gen = DocGenerator()
        record = gen.generate(DocType.API, title="用户接口")
        assert record.status == DocStatus.COMPLETED
        assert "API文档" in record.content
        assert "用户接口" in record.content

    def test_generate_readme(self):
        """测试生成README文档"""
        gen = DocGenerator()
        record = gen.generate(DocType.README, title="项目说明",
                              metadata={"description": "这是一个测试项目"})
        assert record.status == DocStatus.COMPLETED
        assert "项目说明" in record.content
        assert "这是一个测试项目" in record.content

    def test_generate_changelog(self):
        """测试生成变更日志"""
        gen = DocGenerator()
        record = gen.generate(DocType.CHANGELOG, title="v2.0变更",
                              metadata={"changes": ["新增功能A", "修复Bug B"]})
        assert record.status == DocStatus.COMPLETED
        assert "v2.0变更" in record.content
        assert "新增功能A" in record.content
        assert "修复Bug B" in record.content

    def test_generate_test_report(self):
        """测试生成测试报告"""
        gen = DocGenerator()
        record = gen.generate(DocType.TEST_REPORT, title="回归测试报告",
                              metadata={"test_results": {"total": 10, "passed": 8, "failed": 2}})
        assert record.status == DocStatus.COMPLETED
        assert "回归测试报告" in record.content
        assert "10" in record.content
        assert "8" in record.content
        assert "2" in record.content

    def test_generate_architecture_doc(self):
        """测试生成架构文档（走默认分支）"""
        gen = DocGenerator()
        record = gen.generate(DocType.ARCHITECTURE, title="系统架构")
        assert record.status == DocStatus.COMPLETED
        assert "系统架构" in record.content

    def test_generate_with_empty_metadata(self):
        """测试无元数据生成"""
        gen = DocGenerator()
        record = gen.generate(DocType.API, title="空元数据API")
        assert record.status == DocStatus.COMPLETED
        assert record.content != ""

    def test_generate_preserves_metadata(self):
        """测试生成时保留元数据"""
        gen = DocGenerator()
        meta = {"endpoints": ["/api/v1/users", "/api/v1/posts"]}
        record = gen.generate(DocType.API, title="带端点API", metadata=meta)
        assert record.metadata == meta
        assert "/api/v1/users" in record.content


class TestDocArchiver:
    """测试文档归档器"""

    def test_initialization(self):
        """测试初始化"""
        archiver = DocArchiver()
        assert len(archiver._archive) == 0

    def test_archive_completed_doc(self):
        """测试归档已完成的文档"""
        archiver = DocArchiver()
        record = DocumentRecord(
            title="测试文档",
            status=DocStatus.COMPLETED,
            content="内容",
        )
        result = archiver.archive(record)
        assert result.status == DocStatus.ARCHIVED
        assert result.doc_id in archiver._archive

    def test_archive_non_completed_doc(self):
        """测试归档未完成的文档（应不归档）"""
        archiver = DocArchiver()
        record = DocumentRecord(
            title="未完成文档",
            status=DocStatus.PENDING,
        )
        result = archiver.archive(record)
        assert result.status == DocStatus.PENDING
        assert result.doc_id not in archiver._archive

    def test_retrieve_existing(self):
        """测试检索存在的文档"""
        archiver = DocArchiver()
        record = DocumentRecord(title="检索测试", status=DocStatus.COMPLETED)
        archiver.archive(record)
        retrieved = archiver.retrieve(record.doc_id)
        assert retrieved is not None
        assert retrieved.doc_id == record.doc_id

    def test_retrieve_nonexistent(self):
        """测试检索不存在的文档"""
        archiver = DocArchiver()
        result = archiver.retrieve("nonexistent")
        assert result is None

    def test_list_docs_all(self):
        """测试列出所有文档"""
        archiver = DocArchiver()
        r1 = DocumentRecord(title="文档1", doc_type=DocType.API, status=DocStatus.COMPLETED)
        r2 = DocumentRecord(title="文档2", doc_type=DocType.README, status=DocStatus.COMPLETED)
        archiver.archive(r1)
        archiver.archive(r2)
        docs = archiver.list_docs()
        assert len(docs) == 2

    def test_list_docs_by_type(self):
        """测试按类型列出文档"""
        archiver = DocArchiver()
        r1 = DocumentRecord(title="API文档", doc_type=DocType.API, status=DocStatus.COMPLETED)
        r2 = DocumentRecord(title="README", doc_type=DocType.README, status=DocStatus.COMPLETED)
        r3 = DocumentRecord(title="API文档2", doc_type=DocType.API, status=DocStatus.COMPLETED)
        archiver.archive(r1)
        archiver.archive(r2)
        archiver.archive(r3)
        api_docs = archiver.list_docs(DocType.API)
        assert len(api_docs) == 2

    def test_search_by_title(self):
        """测试按标题搜索"""
        archiver = DocArchiver()
        r1 = DocumentRecord(title="用户API文档", status=DocStatus.COMPLETED, content="内容A")
        r2 = DocumentRecord(title="订单API文档", status=DocStatus.COMPLETED, content="内容B")
        r3 = DocumentRecord(title="架构说明", status=DocStatus.COMPLETED, content="内容C")
        archiver.archive(r1)
        archiver.archive(r2)
        archiver.archive(r3)
        results = archiver.search("API")
        assert len(results) == 2

    def test_search_by_content(self):
        """测试按内容搜索"""
        archiver = DocArchiver()
        r1 = DocumentRecord(title="文档A", status=DocStatus.COMPLETED, content="包含关键词的文档")
        r2 = DocumentRecord(title="文档B", status=DocStatus.COMPLETED, content="没有匹配")
        archiver.archive(r1)
        archiver.archive(r2)
        results = archiver.search("关键词")
        assert len(results) == 1

    def test_search_no_results(self):
        """测试搜索无结果"""
        archiver = DocArchiver()
        results = archiver.search("不存在的关键词")
        assert len(results) == 0


class TestDocumentationPipeline:
    """测试文档归档流水线"""

    def test_initialization(self):
        """测试初始化"""
        pipeline = DocumentationPipeline()
        assert pipeline.generator is not None
        assert pipeline.archiver is not None
        assert len(pipeline.records) == 0

    def test_process_api_doc(self):
        """测试处理API文档"""
        pipeline = DocumentationPipeline()
        record = pipeline.process(DocType.API, title="用户接口文档")
        assert record.status == DocStatus.ARCHIVED
        assert record.doc_id in pipeline.records

    def test_process_readme(self):
        """测试处理README文档"""
        pipeline = DocumentationPipeline()
        record = pipeline.process(DocType.README, title="项目README",
                                  metadata={"description": "项目描述"})
        assert record.status == DocStatus.ARCHIVED
        assert "项目描述" in record.content

    def test_process_changelog(self):
        """测试处理变更日志"""
        pipeline = DocumentationPipeline()
        record = pipeline.process(DocType.CHANGELOG, title="v1.0变更日志",
                                  metadata={"changes": ["初始化项目"]})
        assert record.status == DocStatus.ARCHIVED

    def test_process_test_report(self):
        """测试处理测试报告"""
        pipeline = DocumentationPipeline()
        record = pipeline.process(DocType.TEST_REPORT, title="测试报告",
                                  metadata={"test_results": {"total": 5, "passed": 5, "failed": 0}})
        assert record.status == DocStatus.ARCHIVED

    def test_get_document_from_archive(self):
        """测试从归档获取文档"""
        pipeline = DocumentationPipeline()
        record = pipeline.process(DocType.API, title="获取测试")
        retrieved = pipeline.get_document(record.doc_id)
        assert retrieved is not None
        assert retrieved.doc_id == record.doc_id

    def test_get_document_nonexistent(self):
        """测试获取不存在的文档"""
        pipeline = DocumentationPipeline()
        result = pipeline.get_document("nonexistent")
        assert result is None

    def test_get_status(self):
        """测试获取文档状态"""
        pipeline = DocumentationPipeline()
        record = pipeline.process(DocType.API, title="状态测试")
        status = pipeline.get_status(record.doc_id)
        assert status == DocStatus.ARCHIVED

    def test_get_status_nonexistent(self):
        """测试获取不存在文档的状态"""
        pipeline = DocumentationPipeline()
        status = pipeline.get_status("nonexistent")
        assert status is None

    def test_full_pipeline_workflow(self):
        """测试完整流水线工作流"""
        pipeline = DocumentationPipeline()

        # 1. 生成API文档
        api_doc = pipeline.process(DocType.API, title="用户API",
                                   metadata={"endpoints": ["/users", "/posts"]})
        assert api_doc.status == DocStatus.ARCHIVED

        # 2. 生成测试报告
        test_report = pipeline.process(DocType.TEST_REPORT, title="测试报告",
                                       metadata={"test_results": {"total": 10, "passed": 9, "failed": 1}})
        assert test_report.status == DocStatus.ARCHIVED

        # 3. 搜索文档
        results = pipeline.archiver.search("API")
        assert len(results) >= 1

        # 4. 列出所有文档
        all_docs = pipeline.archiver.list_docs()
        assert len(all_docs) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
