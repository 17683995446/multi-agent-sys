"""
LangGraph状态机调度内核
职责：状态机配置、状态转换、状态持久化、状态回退
"""

import uuid
import time
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type
from collections import defaultdict


class StateType(str, Enum):
    """状态类型"""
    INITIAL = "initial"
    INTERMEDIATE = "intermediate"
    FINAL = "final"
    ERROR = "error"


@dataclass
class Transition:
    """状态转换定义"""
    from_state: str
    to_state: str
    condition: Optional[str] = None
    action: Optional[str] = None
    timeout: Optional[float] = None
    
    def __hash__(self):
        return hash((self.from_state, self.to_state, self.condition))


@dataclass
class StateDefinition:
    """状态定义"""
    state_name: str
    state_type: StateType = StateType.INTERMEDIATE
    on_enter: Optional[str] = None
    on_exit: Optional[str] = None
    on_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateMachineConfig:
    """状态机配置"""
    machine_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    initial_state: str = ""
    states: Dict[str, StateDefinition] = field(default_factory=dict)
    transitions: List[Transition] = field(default_factory=list)
    final_states: Set[str] = field(default_factory=set)
    error_state: str = "error"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StateContext:
    """状态上下文"""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    machine_id: str = ""
    current_state: str = ""
    previous_state: Optional[str] = None
    state_history: List[Dict[str, Any]] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransitionResult:
    """转换结果"""
    success: bool
    from_state: str
    to_state: str
    context: StateContext
    message: str = ""
    error: Optional[str] = None


class StatePersistence:
    """状态持久化基类"""
    
    def save(self, context: StateContext) -> bool:
        """保存状态"""
        raise NotImplementedError
    
    def load(self, context_id: str) -> Optional[StateContext]:
        """加载状态"""
        raise NotImplementedError
    
    def delete(self, context_id: str) -> bool:
        """删除状态"""
        raise NotImplementedError
    
    def exists(self, context_id: str) -> bool:
        """检查状态是否存在"""
        raise NotImplementedError


class InMemoryPersistence(StatePersistence):
    """内存持久化"""
    
    def __init__(self):
        self._storage: Dict[str, StateContext] = {}
    
    def save(self, context: StateContext) -> bool:
        try:
            self._storage[context.context_id] = context
            return True
        except Exception:
            return False
    
    def load(self, context_id: str) -> Optional[StateContext]:
        return self._storage.get(context_id)
    
    def delete(self, context_id: str) -> bool:
        if context_id in self._storage:
            del self._storage[context_id]
            return True
        return False
    
    def exists(self, context_id: str) -> bool:
        return context_id in self._storage


class FilePersistence(StatePersistence):
    """文件持久化"""
    
    def __init__(self, storage_dir: str = "/tmp/state_machines"):
        self.storage_dir = storage_dir
        import os
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_file_path(self, context_id: str) -> str:
        return f"{self.storage_dir}/{context_id}.json"
    
    def save(self, context: StateContext) -> bool:
        try:
            import os
            file_path = self._get_file_path(context.context_id)
            with open(file_path, 'w') as f:
                json.dump(asdict(context), f, default=str)
            return True
        except Exception:
            return False
    
    def load(self, context_id: str) -> Optional[StateContext]:
        try:
            import os
            file_path = self._get_file_path(context_id)
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r') as f:
                data = json.load(f)
            return StateContext(**data)
        except Exception:
            return None
    
    def delete(self, context_id: str) -> bool:
        import os
        file_path = self._get_file_path(context_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    def exists(self, context_id: str) -> bool:
        import os
        return os.path.exists(self._get_file_path(context_id))


class StateMachine:
    """状态机"""
    
    def __init__(self, config: StateMachineConfig):
        self.config = config
        self.transition_graph: Dict[str, Dict[str, List[Transition]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._build_transition_graph()
        self._validate_config()
    
    def _build_transition_graph(self):
        """构建转换图"""
        for transition in self.config.transitions:
            self.transition_graph[transition.from_state][transition.to_state].append(
                transition
            )
    
    def _validate_config(self):
        """验证配置"""
        if self.config.initial_state not in self.config.states:
            raise ValueError(f"Initial state '{self.config.initial_state}' not defined")
        
        for state_name in self.config.final_states:
            if state_name not in self.config.states:
                raise ValueError(f"Final state '{state_name}' not defined")
        
        if self.config.error_state and self.config.error_state not in self.config.states:
            # 自动添加error状态
            self.config.states[self.config.error_state] = StateDefinition(
                state_name=self.config.error_state,
                state_type=StateType.ERROR
            )
    
    def get_available_transitions(self, from_state: str) -> List[Transition]:
        """获取可用的转换"""
        return list(self.transition_graph.get(from_state, {}).keys())
    
    def can_transition(self, from_state: str, to_state: str) -> bool:
        """检查是否可以转换"""
        return to_state in self.transition_graph.get(from_state, {})
    
    def execute_transition(
        self,
        context: StateContext,
        to_state: str,
        action_result: Any = None
    ) -> TransitionResult:
        """执行状态转换"""
        from_state = context.current_state
        
        if not self.can_transition(from_state, to_state):
            return TransitionResult(
                success=False,
                from_state=from_state,
                to_state=to_state,
                context=context,
                error=f"Invalid transition from '{from_state}' to '{to_state}'"
            )
        
        previous_state = context.current_state
        
        try:
            state_def = self.config.states.get(to_state)
            if state_def and state_def.on_enter:
                pass
            
            context.previous_state = previous_state
            context.current_state = to_state
            context.updated_at = time.time()
            
            history_entry = {
                "from_state": from_state,
                "to_state": to_state,
                "timestamp": time.time(),
                "action_result": str(action_result) if action_result else None
            }
            context.state_history.append(history_entry)
            
            return TransitionResult(
                success=True,
                from_state=from_state,
                to_state=to_state,
                context=context,
                message=f"Successfully transitioned from {from_state} to {to_state}"
            )
            
        except Exception as e:
            return TransitionResult(
                success=False,
                from_state=from_state,
                to_state=to_state,
                context=context,
                error=str(e)
            )
    
    def is_final_state(self, state: str) -> bool:
        """检查是否是最终状态"""
        return state in self.config.final_states
    
    def is_error_state(self, state: str) -> bool:
        """检查是否是错误状态"""
        return state == self.config.error_state


class StateMachineExecutor:
    """状态机执行器"""
    
    def __init__(self, persistence: Optional[StatePersistence] = None):
        self.machines: Dict[str, StateMachine] = {}
        self.contexts: Dict[str, StateContext] = {}
        self.persistence = persistence or InMemoryPersistence()
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    def register_machine(self, config: StateMachineConfig) -> StateMachine:
        """注册状态机"""
        machine = StateMachine(config)
        self.machines[config.machine_id] = machine
        return machine
    
    def get_machine(self, machine_id: str) -> Optional[StateMachine]:
        """获取状态机"""
        return self.machines.get(machine_id)
    
    def create_context(
        self,
        machine_id: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Optional[StateContext]:
        """创建状态上下文"""
        machine = self.machines.get(machine_id)
        if not machine:
            return None
        
        context = StateContext(
            machine_id=machine_id,
            current_state=machine.config.initial_state,
            data=initial_data or {}
        )
        
        self.contexts[context.context_id] = context
        self.persistence.save(context)
        
        self._emit_event("context_created", context)
        
        return context
    
    def get_context(self, context_id: str) -> Optional[StateContext]:
        """获取状态上下文"""
        context = self.contexts.get(context_id)
        if context:
            return context
        
        context = self.persistence.load(context_id)
        if context:
            self.contexts[context_id] = context
        return context
    
    def transition(
        self,
        context_id: str,
        to_state: str,
        action_result: Any = None
    ) -> Optional[TransitionResult]:
        """执行状态转换"""
        context = self.get_context(context_id)
        if not context:
            return None
        
        machine = self.machines.get(context.machine_id)
        if not machine:
            return None
        
        result = machine.execute_transition(context, to_state, action_result)
        
        if result.success:
            self.contexts[context_id] = context
            self.persistence.save(context)
            self._emit_event("state_changed", result)
            
            if machine.is_final_state(to_state):
                self._emit_event("final_state_reached", result)
            
            if machine.is_error_state(to_state):
                self._emit_event("error_state_reached", result)
        else:
            self._emit_event("transition_failed", result)
        
        return result
    
    def rollback(self, context_id: str, steps: int = 1) -> Optional[TransitionResult]:
        """回退状态"""
        context = self.get_context(context_id)
        if not context or not context.state_history:
            return None
        
        if len(context.state_history) < steps:
            return None
        
        target_history = context.state_history[-(steps + 1)] if len(context.state_history) > steps else context.state_history[0]
        target_state = target_history["from_state"]
        
        from_state = context.state_history[-1]["to_state"] if context.state_history else context.current_state
        
        context.current_state = target_state
        context.updated_at = time.time()
        context.state_history = context.state_history[:-steps]
        
        self.contexts[context_id] = context
        self.persistence.save(context)
        
        self._emit_event("state_rollback", context)
        
        return TransitionResult(
            success=True,
            from_state=from_state,
            to_state=target_state,
            context=context,
            message=f"Rolled back {steps} step(s)"
        )
    
    def register_event_handler(self, event: str, handler: Callable):
        """注册事件处理器"""
        self.event_handlers[event].append(handler)
    
    def _emit_event(self, event: str, data: Any):
        """触发事件"""
        for handler in self.event_handlers.get(event, []):
            try:
                handler(data)
            except Exception:
                pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        state_counts = defaultdict(int)
        for context in self.contexts.values():
            state_counts[context.current_state] += 1
        
        return {
            "total_machines": len(self.machines),
            "total_contexts": len(self.contexts),
            "state_distribution": dict(state_counts),
            "persistence_type": type(self.persistence).__name__
        }


class StateMachineBuilder:
    """状态机构建器"""
    
    def __init__(self, name: str):
        self.config = StateMachineConfig(
            machine_id=name,
            name=name,
            initial_state="initial"
        )
    
    def add_state(
        self,
        name: str,
        state_type: StateType = StateType.INTERMEDIATE,
        on_enter: Optional[str] = None,
        on_exit: Optional[str] = None,
        on_error: Optional[str] = None
    ) -> "StateMachineBuilder":
        """添加状态"""
        self.config.states[name] = StateDefinition(
            state_name=name,
            state_type=state_type,
            on_enter=on_enter,
            on_exit=on_exit,
            on_error=on_error
        )
        return self
    
    def add_transition(
        self,
        from_state: str,
        to_state: str,
        condition: Optional[str] = None,
        action: Optional[str] = None
    ) -> "StateMachineBuilder":
        """添加转换"""
        self.config.transitions.append(Transition(
            from_state=from_state,
            to_state=to_state,
            condition=condition,
            action=action
        ))
        return self
    
    def set_initial_state(self, state: str) -> "StateMachineBuilder":
        """设置初始状态"""
        self.config.initial_state = state
        return self
    
    def set_final_state(self, state: str) -> "StateMachineBuilder":
        """设置最终状态"""
        self.config.final_states.add(state)
        return self
    
    def set_error_state(self, state: str) -> "StateMachineBuilder":
        """设置错误状态"""
        self.config.error_state = state
        return self
    
    def build(self) -> StateMachineConfig:
        """构建配置"""
        if not self.config.initial_state:
            raise ValueError("Initial state not set")
        
        if not self.config.final_states:
            raise ValueError("No final states defined")
        
        return self.config


class LangGraphStateMachineAdapter:
    """LangGraph状态机适配器"""
    
    def __init__(self):
        self.executor = StateMachineExecutor()
        self._setup_default_machine()
    
    def _setup_default_machine(self):
        """设置默认状态机"""
        builder = StateMachineBuilder("workflow")
        builder.add_state("start", StateType.INITIAL)
        builder.add_state("processing", StateType.INTERMEDIATE)
        builder.add_state("review", StateType.INTERMEDIATE)
        builder.add_state("completed", StateType.FINAL)
        builder.add_state("error", StateType.ERROR)
        
        builder.set_initial_state("start")
        builder.set_final_state("completed")
        builder.set_error_state("error")
        
        builder.add_transition("start", "processing")
        builder.add_transition("processing", "review")
        builder.add_transition("review", "processing", condition="needs_revision")
        builder.add_transition("review", "completed", condition="approved")
        builder.add_transition("processing", "error")
        
        config = builder.build()
        self.executor.register_machine(config)
    
    def create_workflow(self, initial_data: Optional[Dict[str, Any]] = None) -> str:
        """创建工作流"""
        context = self.executor.create_context(
            machine_id=list(self.executor.machines.keys())[0],
            initial_data=initial_data
        )
        return context.context_id if context else None
    
    def advance_workflow(self, context_id: str, to_state: str) -> bool:
        """推进工作流"""
        result = self.executor.transition(context_id, to_state)
        return result.success if result else False
    
    def rollback_workflow(self, context_id: str, steps: int = 1) -> bool:
        """回退工作流"""
        result = self.executor.rollback(context_id, steps)
        return result.success if result else False
    
    def get_workflow_state(self, context_id: str) -> Optional[str]:
        """获取工作流状态"""
        context = self.executor.get_context(context_id)
        return context.current_state if context else None


_global_adapter: Optional[LangGraphStateMachineAdapter] = None


def get_state_machine_adapter() -> LangGraphStateMachineAdapter:
    """获取全局状态机适配器"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = LangGraphStateMachineAdapter()
    return _global_adapter


def reset_state_machine_adapter() -> None:
    """重置全局状态机适配器"""
    global _global_adapter
    _global_adapter = None
