"""
阶段38验收测试：文档Agent初始化
"""

import pytest
from src.architecture.doc_agent import (
    DocType,
    DocFormat,
    ArchiveType,
    SyncStatus,
    DocumentSection,
    Document,
    ArchiveEntry,
    SyncRecord,
    DocConfig,
    DocTemplateGenerator,
    IntelligentDocGenerator,
    DocArchiver,
    DocSynchronizer,
    DocAgent,
    get_doc_agent,
    reset_doc_agent
)


class TestDocConfig:
    """测试Agent类定义（验收项38.1）"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = DocConfig(name="DocAgent")
        
        assert config.name == "DocAgent"
        assert config.enable_template_generation is True
        assert config.enable_intelligent_generation is True
        assert config.enable_version_archive is True
        assert config.enable_auto_sync is True
        assert config.default_format == DocFormat.MARKDOWN
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = DocConfig(
            name="CustomDocAgent",
            enable_intelligent_generation=False,
            enable_auto_sync=False
        )
        
        assert config.name == "CustomDocAgent"
        assert config.enable_intelligent_generation is False
        assert config.enable_auto_sync is False


class TestDocTemplateGenerator:
    """测试文档模板生成器（验收项38.2 - 模板生成）"""
    
    def test_generate_readme_template(self):
        """测试README模板生成"""
        generator = DocTemplateGenerator()
        
        doc = generator.generate_from_template(DocType.README, title="Test README")
        
        assert doc is not None
        assert doc.title == "Test README"
        assert doc.doc_type == DocType.README
        assert len(doc.sections) > 0
    
    def test_generate_api_template(self):
        """测试API文档模板生成"""
        generator = DocTemplateGenerator()
        
        doc = generator.generate_from_template(DocType.API, title="API Documentation")
        
        assert doc is not None
        assert doc.doc_type == DocType.API
        assert len(doc.sections) > 0
    
    def test_generate_guide_template(self):
        """测试指南模板生成"""
        generator = DocTemplateGenerator()
        
        doc = generator.generate_from_template(DocType.GUIDE, title="User Guide")
        
        assert doc is not None
        assert doc.doc_type == DocType.GUIDE
        assert len(doc.sections) > 0
    
    def test_generate_changelog_template(self):
        """测试变更日志模板生成"""
        generator = DocTemplateGenerator()
        
        doc = generator.generate_from_template(
            DocType.CHANGELOG, 
            title="Changelog",
            version="1.0.0"
        )
        
        assert doc is not None
        assert doc.doc_type == DocType.CHANGELOG
        assert len(doc.sections) > 0


class TestIntelligentDocGenerator:
    """测试智能文档生成器（验收项38.2 - 智能生成）"""
    
    def test_generate_from_code(self):
        """测试从代码生成文档"""
        generator = IntelligentDocGenerator()
        
        code = '''
"""Sample module for testing."""
def function_one():
    pass

def function_two():
    pass
'''
        
        doc = generator.generate_from_code(code, DocType.README_CODE)
        
        assert doc is not None
        assert doc.metadata.get("auto_generated") is True
        assert "code_hash" in doc.metadata
    
    def test_generate_readme_from_code(self):
        """测试从代码生成README"""
        generator = IntelligentDocGenerator()
        
        code = '''
"""This is a sample module.
It provides sample functionality.
"""
def test_func():
    pass
'''
        
        doc = generator.generate_from_code(code, DocType.README_CODE)
        
        assert doc is not None
        assert len(doc.sections) > 0
    
    def test_generate_guide_from_code(self):
        """测试从代码生成指南"""
        generator = IntelligentDocGenerator()
        
        code = '''
import os
import sys

def main():
    pass
'''
        
        doc = generator.generate_from_code(code, DocType.GUIDE_CODE)
        
        assert doc is not None
        assert len(doc.sections) > 0


class TestDocArchiver:
    """测试文档归档器（验收项38.3 - 版本归档）"""
    
    def test_archive_document(self):
        """测试文档归档"""
        archiver = DocArchiver()
        
        doc = Document(title="Test Document")
        entry = archiver.archive_document(doc, ArchiveType.VERSION)
        
        assert entry is not None
        assert entry.archive_type == ArchiveType.VERSION
        assert entry.checksum != ""
    
    def test_archive_file(self):
        """测试文件归档"""
        archiver = DocArchiver()
        
        content = "Sample file content"
        entry = archiver.archive_file("test.txt", content)
        
        assert entry is not None
        assert entry.archive_type == ArchiveType.FILE
        assert entry.file_path == "test.txt"
        assert entry.checksum != ""
    
    def test_get_archive_history(self):
        """测试获取归档历史"""
        archiver = DocArchiver()
        
        doc = Document(title="Test Document", doc_id="test_id_123")
        archiver.archive_document(doc, ArchiveType.VERSION)
        archiver.archive_document(doc, ArchiveType.VERSION)
        
        history = archiver.get_archive_history("test_id_123")
        
        assert len(history) >= 2


class TestDocSynchronizer:
    """测试文档同步器（验收项38.4 - 自动同步）"""
    
    def test_add_sync_pair(self):
        """测试添加同步对"""
        synchronizer = DocSynchronizer()
        
        record = synchronizer.add_sync_pair(
            "source/doc.md",
            "target/doc.md",
            auto_sync=True
        )
        
        assert record is not None
        assert record.auto_sync is True
        assert record.status == SyncStatus.PENDING
    
    def test_sync_manual(self):
        """测试手动同步"""
        synchronizer = DocSynchronizer()
        
        record = synchronizer.sync_manual("source/doc.md", "target/doc.md")
        
        assert record is not None
        assert record.auto_sync is False
        assert record.status == SyncStatus.SYNCED
        assert record.last_sync_at is not None
    
    def test_sync_auto(self):
        """测试自动同步"""
        synchronizer = DocSynchronizer()
        
        record = synchronizer.sync_auto("doc_id_123")
        
        assert record is not None
        assert record.auto_sync is True
        assert record.status == SyncStatus.SYNCED
        assert record.last_sync_at is not None
    
    def test_get_sync_status(self):
        """测试获取同步状态"""
        synchronizer = DocSynchronizer()
        
        synchronizer.sync_auto("doc_id_456")
        
        status = synchronizer.get_sync_status("doc_id_456")
        
        assert status in [SyncStatus.SYNCED, SyncStatus.OUTDATED]


class TestDocAgent:
    """测试文档Agent"""
    
    def test_generate_document_template(self):
        """测试使用模板生成文档"""
        config = DocConfig(name="TestAgent")
        agent = DocAgent(config)
        
        doc = agent.generate_document(DocType.README, title="Test Document")
        
        assert doc is not None
        assert len(agent.documents) == 1
    
    def test_generate_document_intelligent(self):
        """测试智能生成文档"""
        config = DocConfig(name="TestAgent", enable_intelligent_generation=True)
        agent = DocAgent(config)
        
        code = '''
"""Sample module."""
def sample_function():
    pass
'''
        
        doc = agent.generate_document(
            DocType.README_CODE,
            use_intelligent=True,
            code=code
        )
        
        assert doc is not None
        assert doc.metadata.get("auto_generated") is True
    
    def test_archive_document(self):
        """测试归档文档"""
        config = DocConfig(name="TestAgent")
        agent = DocAgent(config)
        
        doc = agent.generate_document(DocType.README, title="Archive Test")
        
        entry = agent.archive_document(doc.doc_id, ArchiveType.VERSION)
        
        assert entry is not None
        assert entry.archive_type == ArchiveType.VERSION
    
    def test_sync_document_auto(self):
        """测试自动同步文档"""
        config = DocConfig(name="TestAgent", enable_auto_sync=True)
        agent = DocAgent(config)
        
        doc = agent.generate_document(DocType.README, title="Sync Test")
        
        record = agent.sync_document(doc.doc_id, auto_sync=True)
        
        assert record is not None
        assert record.auto_sync is True
    
    def test_sync_document_manual(self):
        """测试手动同步文档"""
        config = DocConfig(name="TestAgent", enable_auto_sync=False)
        agent = DocAgent(config)
        
        doc = agent.generate_document(DocType.README, title="Sync Test")
        
        record = agent.sync_document(doc.doc_id, auto_sync=False)
        
        assert record is not None
        assert record.auto_sync is False
    
    def test_get_document(self):
        """测试获取文档"""
        config = DocConfig(name="TestAgent")
        agent = DocAgent(config)
        
        doc = agent.generate_document(DocType.README, title="Get Test")
        
        retrieved = agent.get_document(doc.doc_id)
        
        assert retrieved is not None
        assert retrieved.doc_id == doc.doc_id
    
    def test_list_documents(self):
        """测试列出文档"""
        config = DocConfig(name="TestAgent")
        agent = DocAgent(config)
        
        agent.generate_document(DocType.README, title="Doc 1")
        agent.generate_document(DocType.API, title="Doc 2")
        
        docs = agent.list_documents()
        
        assert len(docs) >= 2


class TestGlobalAgent:
    """测试全局Agent"""
    
    def test_get_global_agent(self):
        """测试获取全局Agent"""
        reset_doc_agent()
        
        agent1 = get_doc_agent()
        agent2 = get_doc_agent()
        
        assert agent1 is agent2
    
    def test_reset_global_agent(self):
        """测试重置全局Agent"""
        agent1 = get_doc_agent()
        reset_doc_agent()
        agent2 = get_doc_agent()
        
        assert agent1 is not agent2


class TestCompleteScenario:
    """测试完整场景"""
    
    def test_complete_doc_scenario(self):
        """测试完整文档场景"""
        config = DocConfig(
            name="CompleteDocAgent",
            enable_template_generation=True,
            enable_intelligent_generation=True,
            enable_version_archive=True,
            enable_auto_sync=True
        )
        agent = DocAgent(config)
        
        doc1 = agent.generate_document(DocType.README, title="Project README")
        assert doc1 is not None
        
        code = '''
"""Sample project module."""
def main():
    pass
'''
        doc2 = agent.generate_document(
            DocType.README_CODE,
            use_intelligent=True,
            code=code
        )
        assert doc2.metadata.get("auto_generated") is True
        
        entry = agent.archive_document(doc1.doc_id, ArchiveType.VERSION)
        assert entry is not None
        
        record = agent.sync_document(doc1.doc_id, auto_sync=True)
        assert record.auto_sync is True
        
        docs = agent.list_documents()
        assert len(docs) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
