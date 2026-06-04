"""
标准化交付物模板库模块

职责：管理交付物模板、渲染模板、生成标准化文档

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TemplateType(str, Enum):
    """模板类型"""
    PROJECT_PLAN = "project_plan"
    ARCHITECTURE_DOC = "architecture_doc"
    API_SPEC = "api_spec"
    TEST_PLAN = "test_plan"
    DEPLOY_GUIDE = "deploy_guide"


@dataclass
class TemplateField:
    """模板字段"""
    field_name: str = ""
    field_type: str = "str"
    required: bool = True
    default_value: str = ""
    description: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"TemplateField created: field_name={self.field_name}, "
                     f"type={self.field_type}, required={self.required}")


@dataclass
class DeliveryTemplate:
    """交付物模板"""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    template_type: TemplateType = TemplateType.PROJECT_PLAN
    name: str = ""
    fields: List[TemplateField] = field(default_factory=list)
    content_template: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"DeliveryTemplate created: template_id={self.template_id}, "
                     f"type={self.template_type.value}, name={self.name}")


class TemplateRenderer:
    """模板渲染器"""

    def __init__(self):
        """初始化模板渲染器"""
        logger.info("TemplateRenderer initialized")

    def render(self, template: DeliveryTemplate,
               field_values: Dict[str, Any]) -> str:
        """渲染模板"""
        logger.info(f"TemplateRenderer: rendering template, "
                    f"template_id={template.template_id}, "
                    f"name={template.name}")
        try:
            # 1. 验证字段
            validation = self._validate_fields(template, field_values)
            if not validation["valid"]:
                logger.warning(f"TemplateRenderer: validation failed, "
                               f"missing={validation.get('missing', [])}")
                # 用默认值填充缺失的必填字段
                for missing_field in validation.get("missing", []):
                    for tf in template.fields:
                        if tf.field_name == missing_field and tf.default_value:
                            field_values[missing_field] = tf.default_value

            # 用默认值填充缺失的可选字段
            for tf in template.fields:
                if tf.field_name not in field_values and tf.default_value:
                    field_values[tf.field_name] = tf.default_value

            # 2. 替换字段
            content = self._substitute_fields(template.content_template, field_values)

            logger.info(f"TemplateRenderer: render completed, "
                        f"content_length={len(content)}")
        except Exception as e:
            logger.error(f"TemplateRenderer: render failed: {e}")
            content = template.content_template
        return content

    def _substitute_fields(self, content_template: str,
                           field_values: Dict[str, Any]) -> str:
        """替换模板字段"""
        logger.debug(f"TemplateRenderer: substituting fields, "
                     f"fields={list(field_values.keys())}")
        try:
            content = content_template
            for key, value in field_values.items():
                placeholder = f"{{{{{key}}}}}"
                content = content.replace(placeholder, str(value))

            logger.debug(f"TemplateRenderer: substitution completed")
        except Exception as e:
            logger.error(f"TemplateRenderer: _substitute_fields failed: {e}")
            content = content_template
        return content

    def _validate_fields(self, template: DeliveryTemplate,
                         field_values: Dict[str, Any]) -> Dict[str, Any]:
        """验证字段"""
        logger.debug(f"TemplateRenderer: validating fields, "
                     f"template_id={template.template_id}")
        try:
            missing: List[str] = []
            for tf in template.fields:
                if tf.required and tf.field_name not in field_values:
                    if not tf.default_value:
                        missing.append(tf.field_name)

            valid = len(missing) == 0
            result: Dict[str, Any] = {
                "valid": valid,
                "missing": missing,
            }
            logger.debug(f"TemplateRenderer: validation result, "
                         f"valid={valid}, missing={missing}")
        except Exception as e:
            logger.error(f"TemplateRenderer: _validate_fields failed: {e}")
            result = {"valid": False, "missing": []}
        return result

    def generate_document(self, template: DeliveryTemplate,
                          field_values: Dict[str, Any]) -> Dict[str, Any]:
        """生成文档"""
        logger.info(f"TemplateRenderer: generating document, "
                    f"template_id={template.template_id}")
        try:
            content = self.render(template, field_values)
            validation = self._validate_fields(template, field_values)

            document: Dict[str, Any] = {
                "template_id": template.template_id,
                "template_type": template.template_type.value,
                "template_name": template.name,
                "content": content,
                "validation": validation,
                "field_values": field_values,
                "timestamp": time.time(),
            }
            logger.info(f"TemplateRenderer: document generated, "
                        f"content_length={len(content)}")
        except Exception as e:
            logger.error(f"TemplateRenderer: generate_document failed: {e}")
            document = {"error": str(e)}
        return document


class TemplateLibrary:
    """模板库"""

    def __init__(self):
        """初始化模板库"""
        self._templates: Dict[str, DeliveryTemplate] = {}
        logger.info("TemplateLibrary initialized")

    def register(self, template: DeliveryTemplate) -> bool:
        """注册模板"""
        logger.info(f"TemplateLibrary: registering template, "
                    f"template_id={template.template_id}, "
                    f"name={template.name}")
        try:
            self._templates[template.template_id] = template
            logger.info(f"TemplateLibrary: template registered, "
                        f"total={len(self._templates)}")
        except Exception as e:
            logger.error(f"TemplateLibrary: register failed: {e}")
            return False
        return True

    def get(self, template_id: str) -> Optional[DeliveryTemplate]:
        """获取模板"""
        logger.debug(f"TemplateLibrary: getting template, "
                     f"template_id={template_id}")
        return self._templates.get(template_id)

    def list_templates(self,
                       template_type: Optional[TemplateType] = None) -> List[DeliveryTemplate]:
        """列出模板"""
        logger.debug(f"TemplateLibrary: listing templates, "
                     f"type={template_type}")
        try:
            if template_type is not None:
                templates = [t for t in self._templates.values()
                             if t.template_type == template_type]
            else:
                templates = list(self._templates.values())
            logger.debug(f"TemplateLibrary: found {len(templates)} templates")
        except Exception as e:
            logger.error(f"TemplateLibrary: list_templates failed: {e}")
            templates = []
        return templates

    def search(self, keyword: str) -> List[DeliveryTemplate]:
        """搜索模板"""
        logger.debug(f"TemplateLibrary: searching, keyword={keyword}")
        try:
            results: List[DeliveryTemplate] = []
            keyword_lower = keyword.lower()
            for template in self._templates.values():
                if (keyword_lower in template.name.lower() or
                        keyword_lower in template.content_template.lower()):
                    results.append(template)
            logger.debug(f"TemplateLibrary: search found {len(results)} templates")
        except Exception as e:
            logger.error(f"TemplateLibrary: search failed: {e}")
            results = []
        return results


class DeliveryTemplateService:
    """交付物模板服务"""

    def __init__(self, library: Optional[TemplateLibrary] = None,
                 renderer: Optional[TemplateRenderer] = None):
        """初始化交付物模板服务"""
        self.library = library or TemplateLibrary()
        self.renderer = renderer or TemplateRenderer()
        logger.info("DeliveryTemplateService initialized")

    def render(self, template_id: str,
               field_values: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """渲染模板"""
        logger.info(f"DeliveryTemplateService: rendering, "
                    f"template_id={template_id}")
        template = self.library.get(template_id)
        if template is None:
            logger.warning(f"DeliveryTemplateService: template not found, "
                           f"template_id={template_id}")
            return None
        return self.renderer.generate_document(template, field_values)

    def get_template(self, template_id: str) -> Optional[DeliveryTemplate]:
        """获取模板"""
        logger.debug(f"DeliveryTemplateService: getting template, "
                     f"template_id={template_id}")
        return self.library.get(template_id)

    def list_templates(self,
                       template_type: Optional[TemplateType] = None) -> List[DeliveryTemplate]:
        """列出模板"""
        logger.debug(f"DeliveryTemplateService: listing templates, "
                     f"type={template_type}")
        return self.library.list_templates(template_type)
