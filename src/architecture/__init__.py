"""
架构层 - 依赖管理模块

职责：管理模块间的依赖关系，确保单向依赖无环

第一性原理：
- 依赖单向性：整体架构与代码结构保持有向无环DAG
- 成本最小：仅管理依赖关系，不涉及业务逻辑
"""

from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
import os
import re

from src.architecture.dag_validator import (
    DirectedAcyclicGraph,
    LayeredDAGValidator,
    RuntimeDependencyMonitor,
    DependencyViolation,
    DependencyViolationType,
    DAGError,
    create_module_dependency_validator
)

from src.architecture.state_manager import (
    TaskStatus,
    TaskState,
    TaskStateMachine,
    BusinessState,
    SystemState,
    StateNamespace,
    StateManager,
    get_state_manager,
    reset_state_manager
)

from src.architecture.explicit_manager import (
    ImplicitStateType,
    ImplicitState,
    TraceLink,
    ImplicitStateDetector,
    ExplicitConverter,
    TraceChain,
    ExplicitRule,
    ExplicitChecker,
    ExplicitManager,
    create_explicit_manager
)

from src.architecture.entropy_manager import (
    EntropyType,
    EntropyMetric,
    EntropyReport,
    EntropyCalculator,
    EntropyReducer,
    EntropyRule,
    EntropyMonitor,
    EntropyManager,
    create_entropy_manager
)

from src.architecture.entity_definitions import (
    TaskPriority,
    TaskType,
    CodeEntityType,
    MessageType,
    StateType,
    TaskEntity,
    VariableEntity,
    MethodEntity,
    ClassEntity,
    ModuleEntity,
    CodeEntity,
    MessageEntity,
    StateEntity,
    StateMachine,
    EntityRegistry,
    get_entity_registry,
    reset_entity_registry
)

from src.architecture.error_codes import (
    ErrorSeverity,
    ErrorCategory,
    ErrorCode,
    ErrorCodes,
    ErrorContext,
    MASError,
    ErrorChain,
    ErrorRegistry,
    get_error_registry,
    reset_error_registry,
    create_error,
    format_error_for_display,
    ErrorHandler,
    get_error_handler
)

from src.architecture.trace_manager import (
    TraceLevel,
    TraceSpan,
    Trace,
    TraceIDGenerator,
    TraceContext,
    TraceContextManager,
    TraceStorage,
    TraceExporter,
    TraceManager,
    get_trace_manager,
    reset_trace_manager
)

from src.architecture.permission_manager import (
    ActionType,
    AccessLevel,
    Permission,
    Role,
    User,
    AuditLog,
    ReadOnlyResource,
    PermissionTree,
    AuditLogger,
    RoleBasedAccessControl,
    get_rbac,
    reset_rbac
)

from src.architecture.constraint_manager import (
    ConstraintSeverity,
    ConstraintType,
    ViolationAction,
    ConstraintRule,
    ConstraintViolation,
    ConstraintContext,
    Constraint,
    FunctionConstraint,
    CodeConstraint,
    ConstraintRuleRegistry,
    ConstraintExecutor,
    ConstraintEnforcer,
    ConstraintManager,
    get_constraint_manager,
    reset_constraint_manager
)

from src.architecture.variable_analyzer import (
    VariableType,
    VariableCategory,
    VariableIssueType,
    VariableInfo,
    NamingSuggestion,
    VariableScanner,
    VariableClassifier,
    NamingHelper,
    VariableFixer,
    VariableAnalyzer,
    get_variable_analyzer,
    reset_variable_analyzer
)

from src.architecture.method_analyzer import (
    MethodType,
    ResponsibilityCategory,
    SplittingStrategy,
    Parameter,
    CodeBlock,
    Responsibility,
    MethodInfo,
    MethodSplit,
    RefactorReport,
    MethodScanner,
    ComplexityAnalyzer,
    ResponsibilityAnalyzer,
    MethodSplitter,
    MethodAnalyzer,
    get_method_analyzer,
    reset_method_analyzer
)

from src.architecture.four_section_refactor import (
    SectionType,
    RefactorStrategy,
    CodeSegment,
    MethodStructure,
    RefactoredMethod,
    FourSectionTemplate,
    SectionIdentifier,
    FourSectionRefactor,
    RefactorValidator,
    FourSectionRefactorEngine,
    get_four_section_refactor_engine,
    reset_four_section_refactor_engine
)

from src.architecture.class_zone_separator import (
    ZoneType,
    MethodGroupType,
    ConstantType,
    StateType,
    ClassConstant,
    ClassState,
    ClassMethod,
    ClassZone,
    ClassStructure,
    RefactoredClass,
    ClassZoneIdentifier,
    ClassStructureAnalyzer,
    ClassZoneTemplate,
    ClassZoneValidator,
    ClassZoneRefactorEngine,
    get_class_zone_refactor_engine,
    reset_class_zone_refactor_engine
)

from src.architecture.class_decoupling import (
    IssueType,
    IssueSeverity,
    CohesionMetric,
    CouplingMetric,
    ClassViolation,
    RefactoringSuggestion,
    RefactoringAction,
    ClassAnalysisResult,
    CohesionAnalyzer,
    CouplingAnalyzer,
    ViolationDetector,
    SuggestionGenerator,
    DecouplingExecutor,
    ClassDecouplingAnalyzer,
    get_class_decoupling_analyzer,
    reset_class_decoupling_analyzer
)

from src.architecture.module_boundary import (
    InterfaceType,
    BoundaryType,
    ModuleInterface,
    ModuleBoundary,
    ModuleInfo,
    BoundaryReport,
    DirectoryBoundaryDetector,
    SemanticBoundaryDetector,
    InterfaceRecognizer,
    BoundaryValidator,
    BoundaryReporter,
    ModuleBoundaryAnalyzer,
    get_module_boundary_analyzer,
    reset_module_boundary_analyzer
)

from src.architecture.cycle_dependency import (
    DependencyType,
    Dependency,
    CyclePath,
    DependencyGraph,
    CycleReport,
    DependencyGraphBuilder,
    CycleDetector,
    CycleBreaker,
    CycleReporter,
    CycleDependencyAnalyzer,
    get_cycle_dependency_analyzer,
    reset_cycle_dependency_analyzer
)

from src.architecture.layered_compliance import (
    LayerDefinition,
    Violation,
    FixSuggestion,
    ComplianceReport,
    LayeredArchitecture,
    LayeredArchitectureValidator,
    ComplianceReporter,
    LayeredArchitectureAnalyzer,
    get_layered_architecture_analyzer,
    reset_layered_architecture_analyzer
)

from src.architecture.atomic_scanner import (
    ScanLevel,
    ExecutionMode,
    VariableInfo,
    MethodInfo,
    ClassInfo,
    ModuleInfo,
    ScanConfig,
    ScanResult,
    ScanReport,
    AtomicScanner,
    ReportGenerator,
    ConfigManager,
    get_atomic_scanner,
    reset_atomic_scanner
)

from src.architecture.code_fix_engine import (
    FixStatus,
    FixType,
    FixAction,
    FixPlan,
    Backup,
    FixResult,
    CodeRewriter,
    BackupManager,
    SyntaxValidator,
    FixPlanGenerator,
    FixExecutor,
    RollbackManager,
    CodeFixEngine,
    get_code_fix_engine,
    reset_code_fix_engine
)

from src.architecture.control_agent import (
    AgentStatus,
    PermissionLevel,
    TaskStatus,
    Permission,
    Task,
    AgentConfig,
    CoordinationState,
    PermissionManager,
    TaskManager,
    Coordinator,
    ControlAgent,
    get_control_agent,
    reset_control_agent
)

from src.architecture.requirement_agent import (
    RequirementType,
    RequirementStatus,
    ImpactLevel,
    RequirementNode,
    ImpactAnalysis,
    RequirementConfig,
    DecompositionResult,
    HierarchicalDecomposer,
    ImpactAnalyzer,
    SchemaOutputGenerator,
    RequirementAgent,
    get_requirement_agent,
    reset_requirement_agent
)


class LayerType(str, Enum):
    """层级类型枚举"""
    INPUT = "input_layer"      # 输入收敛层
    SCHEDULER = "scheduler"     # 调度中枢层
    AGENTS = "agents"           # 智能协作层
    EXECUTORS = "executors"     # 原子执行层
    CORE = "core"               # 核心基础设施


class DependencyRule:
    """依赖规则"""

    ALLOWED_DEPENDENCIES = {
        LayerType.INPUT: {LayerType.SCHEDULER},
        LayerType.SCHEDULER: {LayerType.AGENTS},
        LayerType.AGENTS: {LayerType.EXECUTORS},
        LayerType.EXECUTORS: set(),
        LayerType.CORE: {
            LayerType.INPUT,
            LayerType.SCHEDULER,
            LayerType.AGENTS,
            LayerType.EXECUTORS
        }
    }

    @classmethod
    def can_depend(cls, from_layer: LayerType, to_layer: LayerType) -> bool:
        """检查依赖是否允许"""
        allowed = cls.ALLOWED_DEPENDENCIES.get(from_layer, set())
        return to_layer in allowed


class ModuleDependency:
    """模块依赖"""

    def __init__(self, module_name: str, layer: LayerType):
        self.module_name = module_name
        self.layer = layer
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()

    def add_dependency(self, dep_module: str):
        """添加依赖"""
        self.dependencies.add(dep_module)

    def add_dependent(self, dep_module: str):
        """添加依赖者"""
        self.dependents.add(dep_module)


class DependencyGraph:
    """依赖图"""

    def __init__(self):
        self.modules: Dict[str, ModuleDependency] = {}
        self.layer_map: Dict[str, LayerType] = {}

    def add_module(self, module_name: str, layer: LayerType):
        """添加模块"""
        if module_name not in self.modules:
            self.modules[module_name] = ModuleDependency(module_name, layer)
            self.layer_map[module_name] = layer

    def add_dependency(self, from_module: str, to_module: str) -> bool:
        """添加依赖关系"""
        if from_module not in self.modules or to_module not in self.modules:
            return False

        from_layer = self.layer_map.get(from_module)
        to_layer = self.layer_map.get(to_module)

        if not from_layer or not to_layer:
            return False

        if not DependencyRule.can_depend(from_layer, to_layer):
            return False

        self.modules[from_module].add_dependency(to_module)
        self.modules[to_module].add_dependent(from_module)
        return True

    def detect_cycles(self) -> List[List[str]]:
        """检测循环依赖（使用DFS）"""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.modules[node].dependencies:
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            path.pop()
            rec_stack.remove(node)
            return False

        for module in self.modules:
            if module not in visited:
                dfs(module, [])

        return cycles

    def topological_sort(self) -> List[str]:
        """拓扑排序（Kahn算法）"""
        in_degree = {module: 0 for module in self.modules}

        for module in self.modules:
            for dep in self.modules[module].dependencies:
                in_degree[dep] += 1

        queue = [module for module, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for dep in self.modules[node].dependencies:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(result) != len(self.modules):
            raise ValueError("存在循环依赖，无法完成拓扑排序")

        return result

    def validate(self) -> Tuple[bool, List[str]]:
        """验证依赖图"""
        errors = []

        cycles = self.detect_cycles()
        if cycles:
            errors.append(f"检测到循环依赖: {cycles}")

        for module_name, module in self.modules.items():
            for dep in module.dependencies:
                if dep not in self.modules:
                    errors.append(f"模块 {module_name} 依赖不存在的模块 {dep}")

        return len(errors) == 0, errors


class DependencyAnalyzer:
    """依赖分析器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.graph = DependencyGraph()

    def scan_imports(self, file_path: str) -> List[str]:
        """扫描文件导入"""
        imports = []
        pattern = r'^import\s+(\w+)|^from\s+(\w+)\s+import'

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    match = re.match(pattern, line.strip())
                    if match:
                        module = match.group(1) or match.group(2)
                        if module.startswith('src.'):
                            imports.append(module)
        except Exception:
            pass

        return imports

    def build_graph(self):
        """构建依赖图"""
        src_dir = os.path.join(self.project_root, 'src')

        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.project_root)
                    module_name = rel_path.replace('/', '.').replace('\\', '.').replace('.py', '')

                    layer = self._detect_layer(module_name)
                    self.graph.add_module(module_name, layer)

        for module_name in self.graph.modules:
            file_path = os.path.join(self.project_root, module_name.replace('.', '/') + '.py')
            if os.path.exists(file_path):
                imports = self.scan_imports(file_path)
                for imp in imports:
                    if imp in self.graph.modules:
                        self.graph.add_dependency(module_name, imp)

    def _detect_layer(self, module_name: str) -> LayerType:
        """检测模块所属层级"""
        if 'input_layer' in module_name:
            return LayerType.INPUT
        elif 'scheduler' in module_name:
            return LayerType.SCHEDULER
        elif 'agents' in module_name:
            return LayerType.AGENTS
        elif 'executors' in module_name:
            return LayerType.EXECUTORS
        elif 'architecture' in module_name or 'core' in module_name:
            return LayerType.CORE
        return LayerType.CORE

    def validate(self) -> Tuple[bool, List[str]]:
        """验证项目依赖"""
        self.build_graph()
        return self.graph.validate()

    def get_dependency_report(self) -> Dict[str, Any]:
        """生成依赖报告"""
        valid, errors = self.validate()

        return {
            'valid': valid,
            'errors': errors,
            'modules': {
                name: {
                    'layer': module.layer.value,
                    'dependencies': list(module.dependencies),
                    'dependents': list(module.dependents)
                }
                for name, module in self.graph.modules.items()
            },
            'topological_order': self.graph.topological_sort() if valid else []
        }

from src.architecture.refactor_module import (
    RefactorType,
    RefactorStatus,
    ModuleRefactorPlan,
    ModuleRefactorer,
    ModuleRefactorService
)

from src.architecture.refactor_class import (
    CouplingType,
    DecouplingStrategy,
    ClassCouplingReport,
    ClassDecoupler,
    ClassRefactorService
)

from src.architecture.refactor_method import (
    MethodComplexity,
    SplitStrategy,
    MethodAnalysis,
    MethodSplitter,
    MethodRefactorService
)

from src.architecture.var_normalize import (
    NormalizationType,
    VariableIssue,
    NormalizationResult,
    VariableNormalizer,
    NormalizationService
)

from src.architecture.bug_locator import (
    BugSeverity,
    BugCategory,
    BugReport,
    BugLocator,
    BugLocationService
)
