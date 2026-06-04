from __future__ import annotations

import ast
import inspect
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, Future

from src.core import get_logger

logger = get_logger("constraint_manager")


class ConstraintSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConstraintType(Enum):
    STRUCTURAL = "structural"
    DEPENDENCY = "dependency"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CUSTOM = "custom"


class ViolationAction(Enum):
    LOG = "log"
    WARN = "warn"
    BLOCK = "block"
    ROLLBACK = "rollback"


@dataclass
class ConstraintRule:
    rule_id: str
    name: str
    description: str
    constraint_type: ConstraintType
    severity: ConstraintSeverity
    action: ViolationAction
    check_function: Optional[Callable] = None
    check_code: Optional[str] = None
    target_pattern: Optional[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "constraint_type": self.constraint_type.value,
            "severity": self.severity.value,
            "action": self.action.value,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class ConstraintViolation:
    violation_id: str
    rule_id: str
    rule_name: str
    constraint_type: ConstraintType
    severity: ConstraintSeverity
    action: ViolationAction
    target: Optional[str] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_id": self.violation_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "constraint_type": self.constraint_type.value,
            "severity": self.severity.value,
            "action": self.action.value,
            "target": self.target,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "stack_trace": self.stack_trace,
            "metadata": self.metadata
        }


class ConstraintContext:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._timestamp: datetime = datetime.now()

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> "ConstraintContext":
        self._data[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {"data": dict(self._data), "timestamp": self._timestamp.isoformat()}


class Constraint(ABC):
    @abstractmethod
    def check(self, context: ConstraintContext) -> List[ConstraintViolation]:
        pass

    def is_enabled(self) -> bool:
        return True


class FunctionConstraint(Constraint):
    def __init__(self, rule: ConstraintRule, func: Callable):
        self._rule = rule
        self._func = func

    def check(self, context: ConstraintContext) -> List[ConstraintViolation]:
        if not self._rule.enabled:
            return []
        try:
            result = self._func(context)
            if isinstance(result, bool):
                return [] if result else [self._create_violation(context)]
            elif isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error(f"Constraint {self._rule.name} failed: {e}")
            return []

    def _create_violation(self, context: ConstraintContext) -> ConstraintViolation:
        return ConstraintViolation(
            violation_id=str(uuid.uuid4()),
            rule_id=self._rule.rule_id,
            rule_name=self._rule.name,
            constraint_type=self._rule.constraint_type,
            severity=self._rule.severity,
            action=self._rule.action,
            target=context.get("target"),
            message=f"Constraint {self._rule.name} violated"
        )

    def is_enabled(self) -> bool:
        return self._rule.enabled


class CodeConstraint(Constraint):
    def __init__(self, rule: ConstraintRule):
        self._rule = rule
        self._compiled: Optional[Callable] = None
        self._compile_code()

    def _compile_code(self) -> None:
        if not self._rule.check_code:
            return
        try:
            namespace = {}
            exec(self._rule.check_code, namespace)
            if "check" in namespace:
                self._compiled = namespace["check"]
        except Exception as e:
            logger.error(f"Failed to compile constraint {self._rule.name}: {e}")

    def check(self, context: ConstraintContext) -> List[ConstraintViolation]:
        if not self._rule.enabled or not self._compiled:
            return []
        try:
            result = self._compiled(context)
            if isinstance(result, bool):
                return [] if result else [self._create_violation(context)]
            elif isinstance(result, list):
                return result
            return []
        except Exception as e:
            logger.error(f"Constraint {self._rule.name} failed: {e}")
            return []

    def update_code(self, new_code: str) -> bool:
        self._rule.check_code = new_code
        self._rule.updated_at = datetime.now()
        try:
            self._compile_code()
            return True
        except Exception as e:
            logger.error(f"Failed to update constraint {self._rule.name}: {e}")
            return False

    def _create_violation(self, context: ConstraintContext) -> ConstraintViolation:
        return ConstraintViolation(
            violation_id=str(uuid.uuid4()),
            rule_id=self._rule.rule_id,
            rule_name=self._rule.name,
            constraint_type=self._rule.constraint_type,
            severity=self._rule.severity,
            action=self._rule.action,
            target=context.get("target"),
            message=f"Constraint {self._rule.name} violated"
        )

    def is_enabled(self) -> bool:
        return self._rule.enabled


class ConstraintRuleRegistry:
    def __init__(self):
        self._rules: Dict[str, ConstraintRule] = {}
        self._constraints: Dict[str, Constraint] = {}
        self._lock = threading.RLock()
        self._callbacks: List[Callable] = []

    def add_rule(self, rule: ConstraintRule, constraint: Optional[Constraint] = None) -> None:
        with self._lock:
            self._rules[rule.rule_id] = rule
            if constraint:
                self._constraints[rule.rule_id] = constraint
            elif rule.check_function:
                self._constraints[rule.rule_id] = FunctionConstraint(rule, rule.check_function)
            elif rule.check_code:
                self._constraints[rule.rule_id] = CodeConstraint(rule)
            self._notify_callbacks("add", rule)

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        with self._lock:
            if rule_id not in self._rules:
                return False
            rule = self._rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            rule.updated_at = datetime.now()
            if "check_code" in updates and rule_id in self._constraints:
                if isinstance(self._constraints[rule_id], CodeConstraint):
                    self._constraints[rule_id].update_code(updates["check_code"])
            self._notify_callbacks("update", rule)
            return True

    def remove_rule(self, rule_id: str) -> bool:
        with self._lock:
            if rule_id not in self._rules:
                return False
            rule = self._rules.pop(rule_id)
            self._constraints.pop(rule_id, None)
            self._notify_callbacks("remove", rule)
            return True

    def get_rule(self, rule_id: str) -> Optional[ConstraintRule]:
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[ConstraintRule]:
        return list(self._rules.values())

    def get_constraint(self, rule_id: str) -> Optional[Constraint]:
        return self._constraints.get(rule_id)

    def get_all_constraints(self) -> List[Constraint]:
        return list(self._constraints.values())

    def register_callback(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def _notify_callbacks(self, action: str, rule: ConstraintRule) -> None:
        for callback in self._callbacks:
            try:
                callback(action, rule)
            except Exception as e:
                logger.error(f"Callback error: {e}")


class ConstraintExecutor:
    def __init__(self, registry: ConstraintRuleRegistry):
        self._registry = registry
        self._violations: List[ConstraintViolation] = []
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)

    def check_sync(
        self,
        context: ConstraintContext,
        rule_ids: Optional[List[str]] = None
    ) -> List[ConstraintViolation]:
        constraints = self._get_constraints(rule_ids)
        violations: List[ConstraintViolation] = []
        for constraint in constraints:
            try:
                result = constraint.check(context)
                violations.extend(result)
                for violation in result:
                    self._handle_violation(violation)
            except Exception as e:
                logger.error(f"Constraint check failed: {e}")
        with self._lock:
            self._violations.extend(violations)
        return violations

    def check_async(
        self,
        context: ConstraintContext,
        rule_ids: Optional[List[str]] = None
    ) -> Future[List[ConstraintViolation]]:
        return self._executor.submit(self.check_sync, context, rule_ids)

    def _get_constraints(self, rule_ids: Optional[List[str]]) -> List[Constraint]:
        if rule_ids:
            return [
                self._registry.get_constraint(rid)
                for rid in rule_ids
                if self._registry.get_constraint(rid) is not None
            ]
        return self._registry.get_all_constraints()

    def _handle_violation(self, violation: ConstraintViolation) -> None:
        if violation.action == ViolationAction.LOG:
            logger.warning(f"Constraint violation: {violation.message}")
        elif violation.action == ViolationAction.WARN:
            logger.warning(f"Constraint violation (warning): {violation.message}")
        elif violation.action == ViolationAction.BLOCK:
            logger.error(f"Constraint violation (blocked): {violation.message}")

    def get_violations(self) -> List[ConstraintViolation]:
        with self._lock:
            return list(self._violations)

    def clear_violations(self) -> None:
        with self._lock:
            self._violations = []


class ConstraintEnforcer:
    def __init__(self, executor: ConstraintExecutor):
        self._executor = executor
        self._enabled: bool = True

    def enforce(
        self,
        context: ConstraintContext,
        rule_ids: Optional[List[str]] = None
    ) -> Tuple[bool, List[ConstraintViolation]]:
        if not self._enabled:
            return True, []
        violations = self._executor.check_sync(context, rule_ids)
        has_block = any(v.action == ViolationAction.BLOCK for v in violations)
        return not has_block, violations

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled


class ConstraintManager:
    def __init__(self):
        self._registry = ConstraintRuleRegistry()
        self._executor = ConstraintExecutor(self._registry)
        self._enforcer = ConstraintEnforcer(self._executor)

    @property
    def registry(self) -> ConstraintRuleRegistry:
        return self._registry

    @property
    def executor(self) -> ConstraintExecutor:
        return self._executor

    @property
    def enforcer(self) -> ConstraintEnforcer:
        return self._enforcer

    def add_rule(self, rule: ConstraintRule, constraint: Optional[Constraint] = None) -> None:
        self._registry.add_rule(rule, constraint)

    def check(self, context: ConstraintContext, rule_ids: Optional[List[str]] = None) -> List[ConstraintViolation]:
        return self._executor.check_sync(context, rule_ids)

    def enforce(self, context: ConstraintContext, rule_ids: Optional[List[str]] = None) -> Tuple[bool, List[ConstraintViolation]]:
        return self._enforcer.enforce(context, rule_ids)


_global_manager: Optional[ConstraintManager] = None


def get_constraint_manager() -> ConstraintManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = ConstraintManager()
    return _global_manager


def reset_constraint_manager() -> None:
    global _global_manager
    _global_manager = None
