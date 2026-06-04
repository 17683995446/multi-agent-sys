import pytest
import time
from src.architecture import (
    ConstraintSeverity,
    ConstraintType,
    ViolationAction,
    ConstraintRule,
    ConstraintViolation,
    ConstraintContext,
    FunctionConstraint,
    CodeConstraint,
    ConstraintRuleRegistry,
    ConstraintExecutor,
    ConstraintEnforcer,
    ConstraintManager,
    get_constraint_manager,
    reset_constraint_manager
)


class TestConstraintRule:
    """测试约束规则"""

    def test_create_rule(self):
        rule = ConstraintRule(
            rule_id="rule-1",
            name="MaxLength",
            description="Limit string length",
            constraint_type=ConstraintType.STRUCTURAL,
            severity=ConstraintSeverity.ERROR,
            action=ViolationAction.BLOCK
        )
        assert rule.rule_id == "rule-1"
        assert rule.name == "MaxLength"
        assert rule.enabled is True

    def test_rule_to_dict(self):
        rule = ConstraintRule(
            rule_id="rule-1",
            name="TestRule",
            description="Test rule",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG
        )
        data = rule.to_dict()
        assert data["rule_id"] == "rule-1"
        assert data["severity"] == "warning"


class TestConstraintViolation:
    """测试违规记录"""

    def test_create_violation(self):
        violation = ConstraintViolation(
            violation_id="viol-1",
            rule_id="rule-1",
            rule_name="TestRule",
            constraint_type=ConstraintType.STRUCTURAL,
            severity=ConstraintSeverity.ERROR,
            action=ViolationAction.BLOCK,
            target="file:test.txt",
            message="Violation detected"
        )
        assert violation.violation_id == "viol-1"
        assert violation.rule_id == "rule-1"
        assert violation.action == ViolationAction.BLOCK


class TestConstraintContext:
    """测试约束上下文"""

    def test_context_set_get(self):
        ctx = ConstraintContext()
        ctx["key"] = "value"
        ctx.set("number", 42)
        assert ctx["key"] == "value"
        assert ctx.get("number") == 42

    def test_context_to_dict(self):
        ctx = ConstraintContext()
        ctx.set("name", "test")
        data = ctx.to_dict()
        assert "data" in data
        assert data["data"]["name"] == "test"


class TestFunctionConstraint:
    """测试函数约束"""

    def test_check_pass(self):
        def check_ok(ctx: ConstraintContext) -> bool:
            return True

        rule = ConstraintRule(
            rule_id="rule-ok",
            name="OkRule",
            description="Always OK",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_function=check_ok
        )
        constraint = FunctionConstraint(rule, check_ok)
        violations = constraint.check(ConstraintContext())
        assert len(violations) == 0

    def test_check_fail(self):
        def check_fail(ctx: ConstraintContext) -> bool:
            return False

        rule = ConstraintRule(
            rule_id="rule-fail",
            name="FailRule",
            description="Always fails",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_function=check_fail
        )
        constraint = FunctionConstraint(rule, check_fail)
        violations = constraint.check(ConstraintContext())
        assert len(violations) == 1

    def test_disabled_constraint(self):
        def check(ctx: ConstraintContext) -> bool:
            return False

        rule = ConstraintRule(
            rule_id="rule-disabled",
            name="Disabled",
            description="Disabled rule",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_function=check,
            enabled=False
        )
        constraint = FunctionConstraint(rule, check)
        violations = constraint.check(ConstraintContext())
        assert len(violations) == 0


class TestCodeConstraint:
    """测试代码约束"""

    def test_compile_and_check(self):
        rule = ConstraintRule(
            rule_id="rule-code",
            name="CodeRule",
            description="Code-based rule",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_code="""
def check(ctx):
    value = ctx.get('value')
    return value < 100
"""
        )
        constraint = CodeConstraint(rule)
        
        ctx_pass = ConstraintContext()
        ctx_pass.set("value", 50)
        violations_pass = constraint.check(ctx_pass)
        assert len(violations_pass) == 0
        
        ctx_fail = ConstraintContext()
        ctx_fail.set("value", 150)
        violations_fail = constraint.check(ctx_fail)
        assert len(violations_fail) == 1

    def test_hot_update_code(self):
        rule = ConstraintRule(
            rule_id="rule-hot",
            name="HotRule",
            description="Hot update test",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_code="""
def check(ctx):
    return True
"""
        )
        constraint = CodeConstraint(rule)
        
        ctx = ConstraintContext()
        assert len(constraint.check(ctx)) == 0
        
        success = constraint.update_code("""
def check(ctx):
    return False
""")
        assert success is True
        assert len(constraint.check(ctx)) == 1


class TestConstraintRuleRegistry:
    """测试约束规则注册"""

    def test_add_and_get_rule(self):
        registry = ConstraintRuleRegistry()
        rule = ConstraintRule(
            rule_id="reg-1",
            name="RegRule",
            description="Registry test",
            constraint_type=ConstraintType.STRUCTURAL,
            severity=ConstraintSeverity.ERROR,
            action=ViolationAction.WARN
        )
        registry.add_rule(rule)
        
        assert registry.get_rule("reg-1") is rule
        assert len(registry.get_all_rules()) == 1

    def test_update_rule(self):
        registry = ConstraintRuleRegistry()
        rule = ConstraintRule(
            rule_id="update-1",
            name="UpdateTest",
            description="Update test",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG
        )
        registry.add_rule(rule)
        
        success = registry.update_rule("update-1", {"name": "UpdatedName"})
        assert success is True
        
        updated = registry.get_rule("update-1")
        assert updated.name == "UpdatedName"

    def test_remove_rule(self):
        registry = ConstraintRuleRegistry()
        rule = ConstraintRule(
            rule_id="remove-1",
            name="RemoveTest",
            description="Remove test",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG
        )
        registry.add_rule(rule)
        
        success = registry.remove_rule("remove-1")
        assert success is True
        assert registry.get_rule("remove-1") is None


class TestConstraintExecutor:
    """测试约束执行器"""

    def test_sync_check(self):
        registry = ConstraintRuleRegistry()
        executor = ConstraintExecutor(registry)
        
        def check_pass(ctx: ConstraintContext) -> bool:
            return True
        
        def check_fail(ctx: ConstraintContext) -> bool:
            return False
        
        rule_pass = ConstraintRule(
            rule_id="exec-pass",
            name="ExecPass",
            description="Pass",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_function=check_pass
        )
        
        rule_fail = ConstraintRule(
            rule_id="exec-fail",
            name="ExecFail",
            description="Fail",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.ERROR,
            action=ViolationAction.WARN,
            check_function=check_fail
        )
        
        registry.add_rule(rule_pass)
        registry.add_rule(rule_fail)
        
        violations = executor.check_sync(ConstraintContext())
        assert len(violations) == 1

    def test_async_check(self):
        registry = ConstraintRuleRegistry()
        executor = ConstraintExecutor(registry)
        
        def check_slow(ctx: ConstraintContext) -> bool:
            time.sleep(0.1)
            return False
        
        rule = ConstraintRule(
            rule_id="async-1",
            name="AsyncRule",
            description="Async test",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_function=check_slow
        )
        
        registry.add_rule(rule)
        
        future = executor.check_async(ConstraintContext())
        violations = future.result(timeout=1.0)
        assert len(violations) == 1


class TestConstraintEnforcer:
    """测试约束强制执行器"""

    def test_enforce_no_block(self):
        registry = ConstraintRuleRegistry()
        executor = ConstraintExecutor(registry)
        enforcer = ConstraintEnforcer(executor)
        
        def check_pass(ctx: ConstraintContext) -> bool:
            return True
        
        rule = ConstraintRule(
            rule_id="enforce-pass",
            name="EnforcePass",
            description="Enforce test",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_function=check_pass
        )
        
        registry.add_rule(rule)
        allowed, violations = enforcer.enforce(ConstraintContext())
        assert allowed is True
        assert len(violations) == 0

    def test_enforce_block(self):
        registry = ConstraintRuleRegistry()
        executor = ConstraintExecutor(registry)
        enforcer = ConstraintEnforcer(executor)
        
        def check_block(ctx: ConstraintContext) -> bool:
            return False
        
        rule = ConstraintRule(
            rule_id="enforce-block",
            name="EnforceBlock",
            description="Enforce block",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.CRITICAL,
            action=ViolationAction.BLOCK,
            check_function=check_block
        )
        
        registry.add_rule(rule)
        allowed, violations = enforcer.enforce(ConstraintContext())
        assert allowed is False
        assert len(violations) == 1

    def test_enable_disable(self):
        registry = ConstraintRuleRegistry()
        executor = ConstraintExecutor(registry)
        enforcer = ConstraintEnforcer(executor)
        
        def check(ctx: ConstraintContext) -> bool:
            return False
        
        rule = ConstraintRule(
            rule_id="toggle",
            name="Toggle",
            description="Toggle",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.CRITICAL,
            action=ViolationAction.BLOCK,
            check_function=check
        )
        
        registry.add_rule(rule)
        
        allowed1, _ = enforcer.enforce(ConstraintContext())
        assert allowed1 is False
        
        enforcer.set_enabled(False)
        allowed2, _ = enforcer.enforce(ConstraintContext())
        assert allowed2 is True


class TestConstraintManager:
    """测试约束管理器"""

    def test_manager_add_check(self):
        manager = ConstraintManager()
        
        def check(ctx: ConstraintContext) -> bool:
            return ctx.get("value", 0) < 10
        
        rule = ConstraintRule(
            rule_id="mgr-1",
            name="MgrTest",
            description="Manager test",
            constraint_type=ConstraintType.CUSTOM,
            severity=ConstraintSeverity.WARNING,
            action=ViolationAction.LOG,
            check_function=check
        )
        
        manager.add_rule(rule)
        
        ctx_ok = ConstraintContext()
        ctx_ok.set("value", 5)
        violations_ok = manager.check(ctx_ok)
        assert len(violations_ok) == 0
        
        ctx_fail = ConstraintContext()
        ctx_fail.set("value", 15)
        violations_fail = manager.check(ctx_fail)
        assert len(violations_fail) == 1

    def test_global_manager(self):
        reset_constraint_manager()
        mgr1 = get_constraint_manager()
        mgr2 = get_constraint_manager()
        assert mgr1 is mgr2
        
        reset_constraint_manager()
        mgr3 = get_constraint_manager()
        assert mgr3 is not mgr1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
