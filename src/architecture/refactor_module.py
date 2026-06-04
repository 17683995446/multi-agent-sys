"""
大型项目模块级重构

职责：分析模块结构，规划并执行模块级重构操作，包括提取、合并、重命名和重组

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RefactorType(str, Enum):
    """重构类型"""
    EXTRACT_MODULE = "extract_module"
    MERGE_MODULE = "merge_module"
    RENAME_MODULE = "rename_module"
    RESTRUCTURE = "restructure"


class RefactorStatus(str, Enum):
    """重构状态"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ModuleRefactorPlan:
    """模块重构计划"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    refactor_type: RefactorType = RefactorType.EXTRACT_MODULE
    source_module: str = ""
    target_module: str = ""
    changes: List[str] = field(default_factory=list)
    risk_level: str = "low"
    status: RefactorStatus = RefactorStatus.PLANNED

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"ModuleRefactorPlan created: plan_id={self.plan_id}, "
                     f"type={self.refactor_type.value}")


class ModuleRefactorer:
    """模块重构器"""

    def __init__(self):
        """初始化模块重构器"""
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}
        self._execution_log: List[Dict[str, Any]] = []
        logger.info("ModuleRefactorer initialized")

    def analyze_module(self, module_name: str, module_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析模块结构，返回模块分析结果"""
        logger.info(f"ModuleRefactorer: analyzing module={module_name}")
        try:
            info = module_info or {}
            analysis: Dict[str, Any] = {
                "module_name": module_name,
                "size": info.get("size", 0),
                "dependencies": info.get("dependencies", []),
                "exports": info.get("exports", []),
                "complexity": info.get("complexity", 0),
                "issues": info.get("issues", []),
                "refactor_suggestions": [],
            }

            # 根据模块特征生成重构建议
            if analysis["size"] > 1000:
                analysis["refactor_suggestions"].append(
                    f"模块 {module_name} 过大（{analysis['size']}行），建议拆分"
                )
            if len(analysis["dependencies"]) > 10:
                analysis["refactor_suggestions"].append(
                    f"模块 {module_name} 依赖过多（{len(analysis['dependencies'])}个），建议解耦"
                )

            self._analysis_cache[module_name] = analysis
            logger.info(f"ModuleRefactorer: analysis complete for module={module_name}, "
                        f"suggestions={len(analysis['refactor_suggestions'])}")
        except Exception as e:
            logger.error(f"ModuleRefactorer: analyze_module failed: {e}")
            analysis = {"module_name": module_name, "error": str(e)}

        return analysis

    def plan_refactor(self, refactor_type: RefactorType, source_module: str,
                      target_module: str = "", changes: Optional[List[str]] = None) -> ModuleRefactorPlan:
        """规划模块重构方案"""
        logger.info(f"ModuleRefactorer: planning refactor type={refactor_type.value}, "
                     f"source={source_module}, target={target_module}")
        try:
            plan = ModuleRefactorPlan(
                refactor_type=refactor_type,
                source_module=source_module,
                target_module=target_module,
                changes=changes or [],
            )

            # 根据重构类型设置风险等级
            risk_map = {
                RefactorType.EXTRACT_MODULE: "medium",
                RefactorType.MERGE_MODULE: "high",
                RefactorType.RENAME_MODULE: "low",
                RefactorType.RESTRUCTURE: "high",
            }
            plan.risk_level = risk_map.get(refactor_type, "medium")

            # 自动生成变更列表
            if not plan.changes:
                plan.changes = self._generate_changes(plan)

            logger.info(f"ModuleRefactorer: plan created, plan_id={plan.plan_id}, "
                        f"risk_level={plan.risk_level}, changes={len(plan.changes)}")
        except Exception as e:
            logger.error(f"ModuleRefactorer: plan_refactor failed: {e}")
            plan = ModuleRefactorPlan(source_module=source_module)

        return plan

    def execute_refactor(self, plan: ModuleRefactorPlan) -> bool:
        """执行模块重构"""
        logger.info(f"ModuleRefactorer: executing refactor plan_id={plan.plan_id}")
        try:
            if plan.status == RefactorStatus.COMPLETED:
                logger.warning(f"ModuleRefactorer: plan {plan.plan_id} already completed")
                return False

            plan.status = RefactorStatus.IN_PROGRESS
            logger.info(f"ModuleRefactorer: plan {plan.plan_id} status changed to IN_PROGRESS")

            # 模拟执行重构步骤
            for change in plan.changes:
                self._execution_log.append({
                    "plan_id": plan.plan_id,
                    "change": change,
                    "status": "executed",
                })
                logger.debug(f"ModuleRefactorer: executed change: {change}")

            plan.status = RefactorStatus.COMPLETED
            logger.info(f"ModuleRefactorer: plan {plan.plan_id} completed successfully")
        except Exception as e:
            logger.error(f"ModuleRefactorer: execute_refactor failed: {e}")
            plan.status = RefactorStatus.ROLLED_BACK
            return False

        return True

    def verify_refactor(self, plan: ModuleRefactorPlan) -> Dict[str, Any]:
        """验证重构结果"""
        logger.info(f"ModuleRefactorer: verifying refactor plan_id={plan.plan_id}")
        try:
            result: Dict[str, Any] = {
                "plan_id": plan.plan_id,
                "verified": plan.status == RefactorStatus.COMPLETED,
                "checks": [],
            }

            if plan.status != RefactorStatus.COMPLETED:
                result["checks"].append({
                    "name": "status_check",
                    "passed": False,
                    "message": f"计划状态为 {plan.status.value}，未完成",
                })
            else:
                result["checks"].append({
                    "name": "status_check",
                    "passed": True,
                    "message": "计划已完成",
                })

            # 检查变更是否已执行
            executed_changes = [
                log for log in self._execution_log
                if log["plan_id"] == plan.plan_id
            ]
            result["checks"].append({
                "name": "changes_check",
                "passed": len(executed_changes) == len(plan.changes),
                "message": f"已执行 {len(executed_changes)}/{len(plan.changes)} 项变更",
            })

            result["verified"] = all(c["passed"] for c in result["checks"])
            logger.info(f"ModuleRefactorer: verification result={result['verified']}")
        except Exception as e:
            logger.error(f"ModuleRefactorer: verify_refactor failed: {e}")
            result = {"plan_id": plan.plan_id, "verified": False, "error": str(e)}

        return result

    def rollback(self, plan: ModuleRefactorPlan) -> bool:
        """回滚重构操作"""
        logger.info(f"ModuleRefactorer: rolling back plan_id={plan.plan_id}")
        try:
            if plan.status not in (RefactorStatus.COMPLETED, RefactorStatus.IN_PROGRESS):
                logger.warning(f"ModuleRefactorer: plan {plan.plan_id} cannot be rolled back, "
                               f"status={plan.status.value}")
                return False

            # 模拟回滚操作
            plan.status = RefactorStatus.ROLLED_BACK
            self._execution_log = [
                log for log in self._execution_log
                if log["plan_id"] != plan.plan_id
            ]
            logger.info(f"ModuleRefactorer: plan {plan.plan_id} rolled back successfully")
        except Exception as e:
            logger.error(f"ModuleRefactorer: rollback failed: {e}")
            return False

        return True

    def _generate_changes(self, plan: ModuleRefactorPlan) -> List[str]:
        """根据重构类型生成变更列表"""
        logger.debug(f"ModuleRefactorer: generating changes for type={plan.refactor_type.value}")
        changes_map: Dict[RefactorType, List[str]] = {
            RefactorType.EXTRACT_MODULE: [
                f"从 {plan.source_module} 提取模块 {plan.target_module}",
                f"更新 {plan.source_module} 的导出",
                f"更新依赖 {plan.source_module} 的模块",
            ],
            RefactorType.MERGE_MODULE: [
                f"合并 {plan.source_module} 到 {plan.target_module}",
                f"更新所有引用 {plan.source_module} 的导入",
                f"删除原模块 {plan.source_module}",
            ],
            RefactorType.RENAME_MODULE: [
                f"重命名 {plan.source_module} 为 {plan.target_module}",
                f"更新所有导入引用",
            ],
            RefactorType.RESTRUCTURE: [
                f"重组 {plan.source_module} 的内部结构",
                f"更新模块公共接口",
                f"更新依赖关系",
                f"更新文档",
            ],
        }
        return changes_map.get(plan.refactor_type, [])


class ModuleRefactorService:
    """模块重构服务"""

    def __init__(self, refactorer: Optional[ModuleRefactorer] = None):
        """初始化模块重构服务"""
        self.refactorer = refactorer or ModuleRefactorer()
        self._plans: Dict[str, ModuleRefactorPlan] = {}
        logger.info("ModuleRefactorService initialized")

    def create_plan(self, refactor_type: RefactorType, source_module: str,
                    target_module: str = "", changes: Optional[List[str]] = None) -> ModuleRefactorPlan:
        """创建重构计划"""
        logger.info(f"ModuleRefactorService: creating plan type={refactor_type.value}, "
                     f"source={source_module}")
        try:
            plan = self.refactorer.plan_refactor(
                refactor_type=refactor_type,
                source_module=source_module,
                target_module=target_module,
                changes=changes,
            )
            self._plans[plan.plan_id] = plan
            logger.info(f"ModuleRefactorService: plan created, plan_id={plan.plan_id}")
        except Exception as e:
            logger.error(f"ModuleRefactorService: create_plan failed: {e}")
            plan = ModuleRefactorPlan(source_module=source_module)

        return plan

    def execute_plan(self, plan_id: str) -> bool:
        """执行重构计划"""
        logger.info(f"ModuleRefactorService: executing plan_id={plan_id}")
        if plan_id not in self._plans:
            logger.warning(f"ModuleRefactorService: plan {plan_id} not found")
            return False

        plan = self._plans[plan_id]
        result = self.refactorer.execute_refactor(plan)
        logger.info(f"ModuleRefactorService: plan {plan_id} execution result={result}")
        return result

    def get_plan(self, plan_id: str) -> Optional[ModuleRefactorPlan]:
        """获取重构计划"""
        logger.debug(f"ModuleRefactorService: getting plan_id={plan_id}")
        return self._plans.get(plan_id)

    def list_plans(self, status: Optional[RefactorStatus] = None) -> List[ModuleRefactorPlan]:
        """列出所有重构计划"""
        logger.debug(f"ModuleRefactorService: listing plans, status_filter={status}")
        plans = list(self._plans.values())
        if status is not None:
            plans = [p for p in plans if p.status == status]
        logger.debug(f"ModuleRefactorService: found {len(plans)} plans")
        return plans
