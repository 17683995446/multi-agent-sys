"""
CSP约束满足冲突检测算法
职责：约束定义、冲突检测、冲突解决、约束验证
"""

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class ConstraintType(str, Enum):
    """约束类型"""
    UNARY = "unary"
    BINARY = "binary"
    NARY = "nary"
    GLOBAL = "global"


class ConflictStatus(str, Enum):
    """冲突状态"""
    NONE = "none"
    POTENTIAL = "potential"
    ACTIVE = "active"
    RESOLVED = "resolved"


@dataclass
class Variable:
    """变量"""
    var_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    domain: Set[Any] = field(default_factory=set)
    current_value: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_assigned(self) -> bool:
        """是否已赋值"""
        return self.current_value is not None
    
    def is_valid(self) -> bool:
        """值是否在域中"""
        return self.current_value in self.domain if self.current_value else False
    
    def has_domain(self) -> bool:
        """是否有域"""
        return len(self.domain) > 0


@dataclass
class Constraint:
    """约束"""
    constraint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    constraint_type: ConstraintType = ConstraintType.BINARY
    variables: List[str] = field(default_factory=list)
    predicate: Callable[[List[Any]], bool] = None
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def check(self, variable_map: Dict[str, Variable]) -> bool:
        """检查约束是否满足"""
        if not self.predicate:
            return True
        
        values = []
        for var_id in self.variables:
            var = variable_map.get(var_id)
            if var:
                values.append(var.current_value)
            else:
                return True
        
        if None in values:
            return True
        
        try:
            return self.predicate(values)
        except Exception:
            return True
    
    def is_satisfied(self, variable_map: Dict[str, Variable]) -> bool:
        """检查约束是否完全满足"""
        if not self.predicate:
            return True
        
        values = []
        for var_id in self.variables:
            var = variable_map.get(var_id)
            if not var or not var.is_assigned():
                return True
            values.append(var.current_value)
        
        try:
            return self.predicate(values)
        except Exception:
            return True


@dataclass
class Conflict:
    """冲突"""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    constraint_id: str = ""
    involved_variables: List[str] = field(default_factory=list)
    status: ConflictStatus = ConflictStatus.POTENTIAL
    description: str = ""
    severity: int = 1
    detected_at: float = field(default_factory=time.time)
    resolution: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CSPResult:
    """CSP求解结果"""
    success: bool
    assignments: Dict[str, Any] = field(default_factory=dict)
    conflicts: List[Conflict] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    solve_time: float = 0.0


class ConstraintDefinition:
    """约束定义器"""
    
    @staticmethod
    def all_different(variables: List[str]) -> Constraint:
        """所有值不同"""
        def predicate(values: List[Any]) -> bool:
            return len(values) == len(set(values))
        
        return Constraint(
            name="all_different",
            constraint_type=ConstraintType.NARY,
            variables=variables,
            predicate=predicate
        )
    
    @staticmethod
    def all_equal(variables: List[str]) -> Constraint:
        """所有值相等"""
        def predicate(values: List[Any]) -> bool:
            return all(v == values[0] for v in values)
        
        return Constraint(
            name="all_equal",
            constraint_type=ConstraintType.NARY,
            variables=variables,
            predicate=predicate
        )
    
    @staticmethod
    def sum_equals(variables: List[str], target: float) -> Constraint:
        """和等于目标值"""
        def predicate(values: List[Any]) -> bool:
            try:
                return sum(values) == target
            except (TypeError, ValueError):
                return True
        
        return Constraint(
            name=f"sum_equals_{target}",
            constraint_type=ConstraintType.NARY,
            variables=variables,
            predicate=predicate
        )
    
    @staticmethod
    def less_than(var1_id: str, var2_id: str) -> Constraint:
        """小于"""
        def predicate(values: List[Any]) -> bool:
            return values[0] < values[1]
        
        return Constraint(
            name="less_than",
            constraint_type=ConstraintType.BINARY,
            variables=[var1_id, var2_id],
            predicate=predicate
        )
    
    @staticmethod
    def greater_than(var1_id: str, var2_id: str) -> Constraint:
        """大于"""
        def predicate(values: List[Any]) -> bool:
            return values[0] > values[1]
        
        return Constraint(
            name="greater_than",
            constraint_type=ConstraintType.BINARY,
            variables=[var1_id, var2_id],
            predicate=predicate
        )
    
    @staticmethod
    def in_domain(var_id: str, allowed_values: Set[Any]) -> Constraint:
        """值在域中"""
        def predicate(values: List[Any]) -> bool:
            return values[0] in allowed_values
        
        return Constraint(
            name="in_domain",
            constraint_type=ConstraintType.UNARY,
            variables=[var_id],
            predicate=predicate
        )
    
    @staticmethod
    def not_equal(var1_id: str, var2_id: str) -> Constraint:
        """不等于"""
        def predicate(values: List[Any]) -> bool:
            return values[0] != values[1]
        
        return Constraint(
            name="not_equal",
            constraint_type=ConstraintType.BINARY,
            variables=[var1_id, var2_id],
            predicate=predicate
        )


class ConflictDetector:
    """冲突检测器"""
    
    def __init__(self):
        self.variables: Dict[str, Variable] = {}
        self.constraints: List[Constraint] = []
        self.conflicts: List[Conflict] = []
    
    def add_variable(self, var_id: str, name: str, 
                   domain: Set[Any]) -> Variable:
        """添加变量"""
        var = Variable(var_id=var_id, name=name, domain=domain)
        self.variables[var_id] = var
        return var
    
    def add_constraint(self, constraint: Constraint) -> None:
        """添加约束"""
        self.constraints.append(constraint)
    
    def detect_conflicts(self) -> List[Conflict]:
        """检测冲突"""
        self.conflicts = []
        
        for constraint in self.constraints:
            if not constraint.is_satisfied(self.variables):
                conflict = Conflict(
                    constraint_id=constraint.constraint_id,
                    involved_variables=constraint.variables.copy(),
                    status=ConflictStatus.ACTIVE,
                    description=f"Constraint '{constraint.name}' is violated",
                    severity=int(constraint.weight)
                )
                self.conflicts.append(conflict)
        
        return self.conflicts
    
    def detect_potential_conflicts(self) -> List[Conflict]:
        """检测潜在冲突"""
        potential_conflicts = []
        
        for constraint in self.constraints:
            unassigned_vars = [
                var_id for var_id in constraint.variables
                if var_id not in self.variables or 
                not self.variables[var_id].is_assigned()
            ]
            
            if unassigned_vars:
                conflict = Conflict(
                    constraint_id=constraint.constraint_id,
                    involved_variables=unassigned_vars,
                    status=ConflictStatus.POTENTIAL,
                    description=f"Potential conflict: unassigned variables in '{constraint.name}'",
                    severity=1
                )
                potential_conflicts.append(conflict)
        
        return potential_conflicts
    
    def has_conflicts(self) -> bool:
        """是否有冲突"""
        return len(self.detect_conflicts()) > 0
    
    def get_conflicts(self) -> List[Conflict]:
        """获取冲突列表"""
        return self.conflicts


class ConflictResolver:
    """冲突解决器"""
    
    def __init__(self, detector: ConflictDetector):
        self.detector = detector
        self.resolution_strategies: Dict[str, Callable] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认策略"""
        self.register_strategy("domain_reduction", self._domain_reduction)
        self.register_strategy("value_assignment", self._value_assignment)
        self.register_strategy("constraint_relaxation", self._constraint_relaxation)
        self.register_strategy("variable_swap", self._variable_swap)
    
    def register_strategy(self, name: str, strategy: Callable):
        """注册解决策略"""
        self.resolution_strategies[name] = strategy
    
    def resolve(self, conflict: Conflict, 
               strategy: str = "domain_reduction") -> bool:
        """解决冲突"""
        resolver = self.resolution_strategies.get(strategy)
        if not resolver:
            return False
        
        result = resolver(conflict)
        
        if result:
            conflict.status = ConflictStatus.RESOLVED
            conflict.resolution = strategy
        
        return result
    
    def resolve_all(self, strategy: str = "domain_reduction") -> int:
        """解决所有冲突"""
        resolved_count = 0
        
        for conflict in self.detector.conflicts:
            if self.resolve(conflict, strategy):
                resolved_count += 1
        
        return resolved_count
    
    def _domain_reduction(self, conflict: Conflict) -> bool:
        """域缩减策略"""
        for var_id in conflict.involved_variables:
            var = self.detector.variables.get(var_id)
            if var and var.current_value and var.current_value in var.domain:
                if len(var.domain) > 1:
                    var.domain = {var.current_value}
                    return True
        
        return False
    
    def _value_assignment(self, conflict: Conflict) -> bool:
        """赋值策略"""
        for var_id in conflict.involved_variables:
            var = self.detector.variables.get(var_id)
            if var and not var.is_assigned() and len(var.domain) > 0:
                for value in var.domain:
                    var.current_value = value
                    conflicts = self.detector.detect_conflicts()
                    if not conflicts:
                        return True
                var.current_value = None
                return False
        
        return False
    
    def _constraint_relaxation(self, conflict: Conflict) -> bool:
        """约束松弛策略"""
        for constraint in self.detector.constraints:
            if constraint.constraint_id == conflict.constraint_id:
                constraint.weight *= 0.5
                return True
        
        return False
    
    def _variable_swap(self, conflict: Conflict) -> bool:
        """变量交换策略"""
        assigned_vars = [
            (var_id, self.detector.variables[var_id])
            for var_id in conflict.involved_variables
            if var_id in self.detector.variables and
            self.detector.variables[var_id].is_assigned()
        ]
        
        unassigned_vars = [
            (var_id, self.detector.variables[var_id])
            for var_id in conflict.involved_variables
            if var_id in self.detector.variables and
            not self.detector.variables[var_id].is_assigned()
        ]
        
        if assigned_vars and unassigned_vars:
            assigned_id, assigned_var = assigned_vars[0]
            unassigned_id, unassigned_var = unassigned_vars[0]
            
            temp = assigned_var.current_value
            assigned_var.current_value = unassigned_var.current_value
            unassigned_var.current_value = temp
            
            return True
        
        return False


class CSPSolver:
    """CSP求解器"""
    
    def __init__(self):
        self.detector = ConflictDetector()
        self.resolver = ConflictResolver(self.detector)
        self.search_order: List[str] = []
        self.max_iterations: int = 1000
    
    def add_variable(self, var_id: str, name: str, 
                   domain: Set[Any]) -> Variable:
        """添加变量"""
        return self.detector.add_variable(var_id, name, domain)
    
    def add_constraint(self, constraint: Constraint) -> None:
        """添加约束"""
        self.detector.add_constraint(constraint)
    
    def solve(self) -> CSPResult:
        """求解"""
        start_time = time.time()
        
        unassigned_vars = [
            var_id for var_id, var in self.detector.variables.items()
            if not var.is_assigned()
        ]
        
        for var_id in unassigned_vars:
            var = self.detector.variables[var_id]
            if len(var.domain) > 0:
                var.current_value = next(iter(var.domain))
        
        for iteration in range(self.max_iterations):
            conflicts = self.detector.detect_conflicts()
            
            if not conflicts:
                assignments = {
                    var_id: var.current_value
                    for var_id, var in self.detector.variables.items()
                    if var.is_assigned()
                }
                
                return CSPResult(
                    success=True,
                    assignments=assignments,
                    conflicts=[],
                    statistics={
                        "iterations": iteration + 1,
                        "assigned_vars": len(assignments),
                        "total_constraints": len(self.detector.constraints)
                    },
                    message="CSP solved successfully",
                    solve_time=time.time() - start_time
                )
            
            resolved = self.resolver.resolve_all("domain_reduction")
            if resolved == 0:
                resolved = self.resolver.resolve_all("value_assignment")
            
            if resolved == 0:
                break
        
        return CSPResult(
            success=False,
            assignments={},
            conflicts=self.detector.get_conflicts(),
            statistics={
                "iterations": self.max_iterations,
                "unresolved_conflicts": len(self.detector.get_conflicts())
            },
            message="Failed to resolve all conflicts",
            solve_time=time.time() - start_time
        )
    
    def validate(self) -> Tuple[bool, List[Conflict]]:
        """验证CSP是否满足约束"""
        conflicts = self.detector.detect_conflicts()
        return len(conflicts) == 0, conflicts


class CSPFramework:
    """CSP框架"""
    
    def __init__(self):
        self.solvers: Dict[str, CSPSolver] = {}
        self.global_constraints: List[Constraint] = []
    
    def create_solver(self, solver_id: str) -> CSPSolver:
        """创建求解器"""
        solver = CSPSolver()
        self.solvers[solver_id] = solver
        return solver
    
    def get_solver(self, solver_id: str) -> Optional[CSPSolver]:
        """获取求解器"""
        return self.solvers.get(solver_id)
    
    def add_global_constraint(self, constraint: Constraint) -> None:
        """添加全局约束"""
        self.global_constraints.append(constraint)
    
    def detect_cross_solver_conflicts(self) -> List[Conflict]:
        """检测跨求解器冲突"""
        all_variables: Dict[str, List[str]] = {}
        
        for solver_id, solver in self.solvers.items():
            for var_id, var in solver.detector.variables.items():
                if var.current_value is not None:
                    if var_id not in all_variables:
                        all_variables[var_id] = []
                    all_variables[var_id].append(solver_id)
        
        conflicts = []
        for var_id, solver_ids in all_variables.items():
            if len(solver_ids) > 1:
                conflict = Conflict(
                    constraint_id="cross_solver",
                    involved_variables=[var_id],
                    status=ConflictStatus.POTENTIAL,
                    description=f"Variable '{var_id}' assigned in multiple solvers: {solver_ids}",
                    severity=2
                )
                conflicts.append(conflict)
        
        return conflicts


_global_csp_framework: Optional[CSPFramework] = None


def get_csp_framework() -> CSPFramework:
    """获取全局CSP框架"""
    global _global_csp_framework
    if _global_csp_framework is None:
        _global_csp_framework = CSPFramework()
    return _global_csp_framework


def reset_csp_framework() -> None:
    """重置全局CSP框架"""
    global _global_csp_framework
    _global_csp_framework = None
