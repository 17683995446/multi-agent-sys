"""
原子化代码规范校验模块

职责：变量级、方法级、类级、模块级四级代码规范校验

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CheckLevel(str, Enum):
    """校验级别"""
    VARIABLE = "variable"
    METHOD = "method"
    CLASS = "class"
    MODULE = "module"


class CheckResult(str, Enum):
    """校验结果"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class CheckItem:
    """校验项"""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    level: CheckLevel = CheckLevel.VARIABLE
    rule: str = ""
    result: CheckResult = CheckResult.PASS
    message: str = ""
    location: str = ""
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        logger.debug(f"CheckItem created: id={self.item_id}, "
                     f"level={self.level.value}, rule={self.rule}")


class CodeChecker:
    """代码规范校验器"""

    def __init__(self):
        """初始化代码规范校验器"""
        self.items: List[CheckItem] = []
        self.rules: Dict[CheckLevel, List[str]] = {
            CheckLevel.VARIABLE: ["命名规范", "类型注解", "常量定义"],
            CheckLevel.METHOD: ["参数数量", "返回值", "复杂度"],
            CheckLevel.CLASS: ["命名规范", "继承深度", "方法数量"],
            CheckLevel.MODULE: ["导入规范", "文档字符串", "行数限制"],
        }
        logger.info("CodeChecker initialized")

    def check_variable(self, name: str, location: str = "") -> List[CheckItem]:
        """校验变量规范"""
        logger.info(f"CodeChecker: checking variable '{name}' at {location}")
        items = []
        try:
            # 命名规范检查
            if name.upper() == name and "_" in name:
                # 常量命名合规
                items.append(CheckItem(
                    level=CheckLevel.VARIABLE,
                    rule="命名规范",
                    result=CheckResult.PASS,
                    message=f"常量命名合规: {name}",
                    location=location,
                ))
            elif name.isupper():
                items.append(CheckItem(
                    level=CheckLevel.VARIABLE,
                    rule="命名规范",
                    result=CheckResult.PASS,
                    message=f"常量命名合规: {name}",
                    location=location,
                ))
            elif "_" in name or name.islower():
                items.append(CheckItem(
                    level=CheckLevel.VARIABLE,
                    rule="命名规范",
                    result=CheckResult.PASS,
                    message=f"变量命名合规: {name}",
                    location=location,
                ))
            elif name[0].isupper():
                items.append(CheckItem(
                    level=CheckLevel.VARIABLE,
                    rule="命名规范",
                    result=CheckResult.WARNING,
                    message=f"变量命名不符合snake_case: {name}",
                    location=location,
                ))
            else:
                items.append(CheckItem(
                    level=CheckLevel.VARIABLE,
                    rule="命名规范",
                    result=CheckResult.WARNING,
                    message=f"变量命名不规范: {name}",
                    location=location,
                ))

            # 类型注解检查
            items.append(CheckItem(
                level=CheckLevel.VARIABLE,
                rule="类型注解",
                result=CheckResult.WARNING,
                message=f"变量缺少类型注解: {name}",
                location=location,
            ))

            self.items.extend(items)
            logger.info(f"CodeChecker: variable check completed, "
                        f"{len(items)} items")
        except Exception as e:
            logger.error(f"CodeChecker: check_variable failed: {e}")
        return items

    def check_method(self, name: str, params: int = 0,
                     location: str = "") -> List[CheckItem]:
        """校验方法规范"""
        logger.info(f"CodeChecker: checking method '{name}' with "
                    f"{params} params at {location}")
        items = []
        try:
            # 参数数量检查
            if params > 7:
                items.append(CheckItem(
                    level=CheckLevel.METHOD,
                    rule="参数数量",
                    result=CheckResult.FAIL,
                    message=f"方法参数过多({params}): {name}",
                    location=location,
                ))
            elif params > 5:
                items.append(CheckItem(
                    level=CheckLevel.METHOD,
                    rule="参数数量",
                    result=CheckResult.WARNING,
                    message=f"方法参数较多({params}): {name}",
                    location=location,
                ))
            else:
                items.append(CheckItem(
                    level=CheckLevel.METHOD,
                    rule="参数数量",
                    result=CheckResult.PASS,
                    message=f"方法参数数量合规({params}): {name}",
                    location=location,
                ))

            # 返回值检查
            if name.startswith("__") and name.endswith("__"):
                items.append(CheckItem(
                    level=CheckLevel.METHOD,
                    rule="返回值",
                    result=CheckResult.PASS,
                    message=f"魔术方法: {name}",
                    location=location,
                ))
            else:
                items.append(CheckItem(
                    level=CheckLevel.METHOD,
                    rule="返回值",
                    result=CheckResult.WARNING,
                    message=f"方法缺少返回值注解: {name}",
                    location=location,
                ))

            self.items.extend(items)
            logger.info(f"CodeChecker: method check completed, "
                        f"{len(items)} items")
        except Exception as e:
            logger.error(f"CodeChecker: check_method failed: {e}")
        return items

    def check_class(self, name: str, method_count: int = 0,
                    base_count: int = 0, location: str = "") -> List[CheckItem]:
        """校验类规范"""
        logger.info(f"CodeChecker: checking class '{name}' with "
                    f"{method_count} methods at {location}")
        items = []
        try:
            # 类命名规范
            if name[0].isupper():
                items.append(CheckItem(
                    level=CheckLevel.CLASS,
                    rule="命名规范",
                    result=CheckResult.PASS,
                    message=f"类命名合规(PascalCase): {name}",
                    location=location,
                ))
            else:
                items.append(CheckItem(
                    level=CheckLevel.CLASS,
                    rule="命名规范",
                    result=CheckResult.FAIL,
                    message=f"类命名不符合PascalCase: {name}",
                    location=location,
                ))

            # 继承深度检查
            if base_count > 3:
                items.append(CheckItem(
                    level=CheckLevel.CLASS,
                    rule="继承深度",
                    result=CheckResult.FAIL,
                    message=f"继承层次过深({base_count}): {name}",
                    location=location,
                ))
            elif base_count > 1:
                items.append(CheckItem(
                    level=CheckLevel.CLASS,
                    rule="继承深度",
                    result=CheckResult.WARNING,
                    message=f"继承层次较深({base_count}): {name}",
                    location=location,
                ))
            else:
                items.append(CheckItem(
                    level=CheckLevel.CLASS,
                    rule="继承深度",
                    result=CheckResult.PASS,
                    message=f"继承深度合规({base_count}): {name}",
                    location=location,
                ))

            # 方法数量检查
            if method_count > 20:
                items.append(CheckItem(
                    level=CheckLevel.CLASS,
                    rule="方法数量",
                    result=CheckResult.FAIL,
                    message=f"类方法过多({method_count}): {name}",
                    location=location,
                ))
            elif method_count > 10:
                items.append(CheckItem(
                    level=CheckLevel.CLASS,
                    rule="方法数量",
                    result=CheckResult.WARNING,
                    message=f"类方法较多({method_count}): {name}",
                    location=location,
                ))
            else:
                items.append(CheckItem(
                    level=CheckLevel.CLASS,
                    rule="方法数量",
                    result=CheckResult.PASS,
                    message=f"类方法数量合规({method_count}): {name}",
                    location=location,
                ))

            self.items.extend(items)
            logger.info(f"CodeChecker: class check completed, "
                        f"{len(items)} items")
        except Exception as e:
            logger.error(f"CodeChecker: check_class failed: {e}")
        return items

    def check_module(self, name: str, line_count: int = 0,
                     import_count: int = 0, location: str = "") -> List[CheckItem]:
        """校验模块规范"""
        logger.info(f"CodeChecker: checking module '{name}' at {location}")
        items = []
        try:
            # 导入规范检查
            if import_count > 20:
                items.append(CheckItem(
                    level=CheckLevel.MODULE,
                    rule="导入规范",
                    result=CheckResult.FAIL,
                    message=f"模块导入过多({import_count}): {name}",
                    location=location,
                ))
            elif import_count > 10:
                items.append(CheckItem(
                    level=CheckLevel.MODULE,
                    rule="导入规范",
                    result=CheckResult.WARNING,
                    message=f"模块导入较多({import_count}): {name}",
                    location=location,
                ))
            else:
                items.append(CheckItem(
                    level=CheckLevel.MODULE,
                    rule="导入规范",
                    result=CheckResult.PASS,
                    message=f"模块导入数量合规({import_count}): {name}",
                    location=location,
                ))

            # 行数限制检查
            if line_count > 500:
                items.append(CheckItem(
                    level=CheckLevel.MODULE,
                    rule="行数限制",
                    result=CheckResult.FAIL,
                    message=f"模块行数过多({line_count}): {name}",
                    location=location,
                ))
            elif line_count > 300:
                items.append(CheckItem(
                    level=CheckLevel.MODULE,
                    rule="行数限制",
                    result=CheckResult.WARNING,
                    message=f"模块行数较多({line_count}): {name}",
                    location=location,
                ))
            else:
                items.append(CheckItem(
                    level=CheckLevel.MODULE,
                    rule="行数限制",
                    result=CheckResult.PASS,
                    message=f"模块行数合规({line_count}): {name}",
                    location=location,
                ))

            self.items.extend(items)
            logger.info(f"CodeChecker: module check completed, "
                        f"{len(items)} items")
        except Exception as e:
            logger.error(f"CodeChecker: check_module failed: {e}")
        return items

    def run_all_checks(self, code_data: Dict[str, Any]) -> List[CheckItem]:
        """运行所有级别的校验"""
        logger.info("CodeChecker: running all checks")
        all_items = []
        try:
            # 变量级校验
            variables = code_data.get("variables", [])
            for var in variables:
                items = self.check_variable(
                    name=var.get("name", ""),
                    location=var.get("location", ""),
                )
                all_items.extend(items)

            # 方法级校验
            methods = code_data.get("methods", [])
            for method in methods:
                items = self.check_method(
                    name=method.get("name", ""),
                    params=method.get("params", 0),
                    location=method.get("location", ""),
                )
                all_items.extend(items)

            # 类级校验
            classes = code_data.get("classes", [])
            for cls in classes:
                items = self.check_class(
                    name=cls.get("name", ""),
                    method_count=cls.get("method_count", 0),
                    base_count=cls.get("base_count", 0),
                    location=cls.get("location", ""),
                )
                all_items.extend(items)

            # 模块级校验
            modules = code_data.get("modules", [])
            for mod in modules:
                items = self.check_module(
                    name=mod.get("name", ""),
                    line_count=mod.get("line_count", 0),
                    import_count=mod.get("import_count", 0),
                    location=mod.get("location", ""),
                )
                all_items.extend(items)

            logger.info(f"CodeChecker: all checks completed, "
                        f"{len(all_items)} items total")
        except Exception as e:
            logger.error(f"CodeChecker: run_all_checks failed: {e}")
        return all_items

    def generate_report(self) -> Dict[str, Any]:
        """生成校验报告"""
        logger.info("CodeChecker: generating report")
        try:
            total = len(self.items)
            pass_count = sum(
                1 for i in self.items if i.result == CheckResult.PASS
            )
            warning_count = sum(
                1 for i in self.items if i.result == CheckResult.WARNING
            )
            fail_count = sum(
                1 for i in self.items if i.result == CheckResult.FAIL
            )

            score = 100.0
            if total > 0:
                score = max(
                    0.0,
                    100.0 - warning_count * 5 - fail_count * 15,
                )

            report = {
                "total_items": total,
                "pass_count": pass_count,
                "warning_count": warning_count,
                "fail_count": fail_count,
                "score": score,
                "items": [
                    {
                        "item_id": i.item_id,
                        "level": i.level.value,
                        "rule": i.rule,
                        "result": i.result.value,
                        "message": i.message,
                        "location": i.location,
                    }
                    for i in self.items
                ],
            }
            logger.info(f"CodeChecker: report generated, "
                        f"score={score:.1f}")
        except Exception as e:
            logger.error(f"CodeChecker: generate_report failed: {e}")
            report = {"total_items": 0, "pass_count": 0,
                      "warning_count": 0, "fail_count": 0,
                      "score": 0.0, "items": []}
        return report


class CodeCheckService:
    """代码规范校验服务"""

    def __init__(self):
        """初始化代码规范校验服务"""
        self.checker = CodeChecker()
        logger.info("CodeCheckService initialized")

    def check(self, code_data: Dict[str, Any]) -> List[CheckItem]:
        """执行代码规范校验"""
        logger.info("CodeCheckService: checking code")
        try:
            items = self.checker.run_all_checks(code_data)
            logger.info(f"CodeCheckService: check completed, "
                        f"{len(items)} items")
        except Exception as e:
            logger.error(f"CodeCheckService: check failed: {e}")
            items = []
        return items

    def get_report(self) -> Dict[str, Any]:
        """获取校验报告"""
        logger.debug("CodeCheckService: getting report")
        return self.checker.generate_report()

    def get_violations(self,
                       level: Optional[CheckLevel] = None,
                       result: Optional[CheckResult] = None
                       ) -> List[CheckItem]:
        """获取违规项列表"""
        logger.debug("CodeCheckService: getting violations")
        violations = [
            i for i in self.checker.items
            if i.result != CheckResult.PASS
        ]
        if level is not None:
            violations = [v for v in violations if v.level == level]
        if result is not None:
            violations = [v for v in violations if v.result == result]
        return violations
