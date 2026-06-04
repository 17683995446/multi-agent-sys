"""
阶段98验收测试 - 标准化交付物模板库
"""

import pytest
from src.architecture.delivery_template import (
    TemplateType,
    TemplateField,
    DeliveryTemplate,
    TemplateRenderer,
    TemplateLibrary,
    DeliveryTemplateService,
)


class TestTemplateType:
    """测试模板类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert TemplateType.PROJECT_PLAN.value == "project_plan"
        assert TemplateType.ARCHITECTURE_DOC.value == "architecture_doc"
        assert TemplateType.API_SPEC.value == "api_spec"
        assert TemplateType.TEST_PLAN.value == "test_plan"
        assert TemplateType.DEPLOY_GUIDE.value == "deploy_guide"

    def test_all_types(self):
        """测试所有类型"""
        types = list(TemplateType)
        assert len(types) == 5


class TestTemplateField:
    """测试模板字段"""

    def test_default_creation(self):
        """测试默认创建"""
        tf = TemplateField()
        assert tf.field_name == ""
        assert tf.field_type == "str"
        assert tf.required is True
        assert tf.default_value == ""
        assert tf.description == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        tf = TemplateField(
            field_name="project_name",
            field_type="str",
            required=True,
            default_value="未命名项目",
            description="项目名称",
        )
        assert tf.field_name == "project_name"
        assert tf.required is True
        assert tf.default_value == "未命名项目"

    def test_optional_field(self):
        """测试可选字段"""
        tf = TemplateField(
            field_name="version",
            required=False,
            default_value="1.0.0",
        )
        assert tf.required is False
        assert tf.default_value == "1.0.0"


class TestDeliveryTemplate:
    """测试交付物模板"""

    def test_default_creation(self):
        """测试默认创建"""
        template = DeliveryTemplate()
        assert template.template_id != ""
        assert template.template_type == TemplateType.PROJECT_PLAN
        assert template.name == ""
        assert template.fields == []
        assert template.content_template == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        fields = [
            TemplateField(field_name="title", required=True),
            TemplateField(field_name="author", required=False),
        ]
        template = DeliveryTemplate(
            template_type=TemplateType.API_SPEC,
            name="API规范模板",
            fields=fields,
            content_template="# {{title}}\n作者: {{author}}",
        )
        assert template.template_type == TemplateType.API_SPEC
        assert template.name == "API规范模板"
        assert len(template.fields) == 2

    def test_template_id_unique(self):
        """测试模板ID唯一性"""
        t1 = DeliveryTemplate()
        t2 = DeliveryTemplate()
        assert t1.template_id != t2.template_id


class TestTemplateRenderer:
    """测试模板渲染器"""

    def test_initialization(self):
        """测试初始化"""
        renderer = TemplateRenderer()
        assert renderer is not None

    def test_render_simple(self):
        """测试简单渲染"""
        renderer = TemplateRenderer()
        template = DeliveryTemplate(
            content_template="项目: {{project_name}}, 版本: {{version}}",
            fields=[
                TemplateField(field_name="project_name", required=True),
                TemplateField(field_name="version", required=False, default_value="1.0"),
            ],
        )
        content = renderer.render(template, {"project_name": "MyProject", "version": "2.0"})
        assert "MyProject" in content
        assert "2.0" in content

    def test_render_with_defaults(self):
        """测试使用默认值渲染"""
        renderer = TemplateRenderer()
        template = DeliveryTemplate(
            content_template="项目: {{project_name}}, 版本: {{version}}",
            fields=[
                TemplateField(field_name="project_name", required=True),
                TemplateField(field_name="version", required=False, default_value="1.0"),
            ],
        )
        content = renderer.render(template, {"project_name": "MyProject"})
        assert "MyProject" in content
        assert "1.0" in content

    def test_substitute_fields(self):
        """测试字段替换"""
        renderer = TemplateRenderer()
        content = renderer._substitute_fields(
            "Hello {{name}}!", {"name": "World"}
        )
        assert content == "Hello World!"

    def test_substitute_fields_missing(self):
        """测试缺失字段替换"""
        renderer = TemplateRenderer()
        content = renderer._substitute_fields(
            "Hello {{name}}!", {}
        )
        assert content == "Hello {{name}}!"

    def test_validate_fields_valid(self):
        """测试字段验证通过"""
        renderer = TemplateRenderer()
        template = DeliveryTemplate(
            fields=[
                TemplateField(field_name="title", required=True),
                TemplateField(field_name="desc", required=False),
            ],
        )
        result = renderer._validate_fields(template, {"title": "测试"})
        assert result["valid"] is True
        assert result["missing"] == []

    def test_validate_fields_missing_required(self):
        """测试缺失必填字段"""
        renderer = TemplateRenderer()
        template = DeliveryTemplate(
            fields=[
                TemplateField(field_name="title", required=True),
                TemplateField(field_name="author", required=True),
            ],
        )
        result = renderer._validate_fields(template, {"title": "测试"})
        assert result["valid"] is False
        assert "author" in result["missing"]

    def test_generate_document(self):
        """测试生成文档"""
        renderer = TemplateRenderer()
        template = DeliveryTemplate(
            name="测试模板",
            content_template="# {{title}}\n{{content}}",
            fields=[
                TemplateField(field_name="title", required=True),
                TemplateField(field_name="content", required=True),
            ],
        )
        doc = renderer.generate_document(template, {"title": "项目计划", "content": "详细内容"})
        assert "template_id" in doc
        assert "content" in doc
        assert "项目计划" in doc["content"]
        assert "详细内容" in doc["content"]


class TestTemplateLibrary:
    """测试模板库"""

    def test_initialization(self):
        """测试初始化"""
        library = TemplateLibrary()
        assert len(library._templates) == 0

    def test_register(self):
        """测试注册模板"""
        library = TemplateLibrary()
        template = DeliveryTemplate(name="测试模板")
        result = library.register(template)
        assert result is True
        assert len(library._templates) == 1

    def test_get(self):
        """测试获取模板"""
        library = TemplateLibrary()
        template = DeliveryTemplate(name="测试模板")
        library.register(template)
        result = library.get(template.template_id)
        assert result is not None
        assert result.name == "测试模板"

    def test_get_not_found(self):
        """测试获取不存在的模板"""
        library = TemplateLibrary()
        result = library.get("nonexistent")
        assert result is None

    def test_list_templates(self):
        """测试列出所有模板"""
        library = TemplateLibrary()
        library.register(DeliveryTemplate(name="模板1", template_type=TemplateType.PROJECT_PLAN))
        library.register(DeliveryTemplate(name="模板2", template_type=TemplateType.API_SPEC))
        templates = library.list_templates()
        assert len(templates) == 2

    def test_list_templates_by_type(self):
        """测试按类型列出模板"""
        library = TemplateLibrary()
        library.register(DeliveryTemplate(name="模板1", template_type=TemplateType.PROJECT_PLAN))
        library.register(DeliveryTemplate(name="模板2", template_type=TemplateType.API_SPEC))
        templates = library.list_templates(TemplateType.PROJECT_PLAN)
        assert len(templates) == 1
        assert templates[0].template_type == TemplateType.PROJECT_PLAN

    def test_search(self):
        """测试搜索模板"""
        library = TemplateLibrary()
        library.register(DeliveryTemplate(name="项目计划模板", content_template="项目计划内容"))
        library.register(DeliveryTemplate(name="API规范模板", content_template="API规范内容"))
        results = library.search("项目")
        assert len(results) == 1
        assert "项目" in results[0].name


class TestDeliveryTemplateService:
    """测试交付物模板服务"""

    def test_initialization(self):
        """测试初始化"""
        service = DeliveryTemplateService()
        assert service.library is not None
        assert service.renderer is not None

    def test_render(self):
        """测试渲染模板"""
        service = DeliveryTemplateService()
        template = DeliveryTemplate(
            name="测试模板",
            content_template="# {{title}}",
            fields=[TemplateField(field_name="title", required=True)],
        )
        service.library.register(template)
        doc = service.render(template.template_id, {"title": "测试标题"})
        assert doc is not None
        assert "测试标题" in doc["content"]

    def test_render_not_found(self):
        """测试渲染不存在的模板"""
        service = DeliveryTemplateService()
        result = service.render("nonexistent", {})
        assert result is None

    def test_get_template(self):
        """测试获取模板"""
        service = DeliveryTemplateService()
        template = DeliveryTemplate(name="测试模板")
        service.library.register(template)
        result = service.get_template(template.template_id)
        assert result is not None
        assert result.name == "测试模板"

    def test_list_templates(self):
        """测试列出模板"""
        service = DeliveryTemplateService()
        service.library.register(DeliveryTemplate(name="模板1"))
        service.library.register(DeliveryTemplate(name="模板2"))
        templates = service.list_templates()
        assert len(templates) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
