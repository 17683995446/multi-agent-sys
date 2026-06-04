"""
四级原子化扫描器模块

职责：集成并整合变量、方法、类、模块四级扫描功能

基于第一性原理：简单、单一、可追溯、可组合
"""

import ast
import os
import json
import time
import uuid
import threading
import multiprocessing
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable


class ScanLevel(str, Enum):
    """扫描级别"""
    VARIABLE = "variable"  # 变量级
    METHOD = "method"  # 方法级
    CLASS = "class"  # 类级
    MODULE = "module"  # 模块级
    ALL = "all"  # 全部四级


class ExecutionMode(str, Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行


@dataclass
class VariableInfo:
    """变量信息"""
    name: str
    line_no: int
    col_offset: int
    var_type: str = "unknown"
    value: Optional[str] = None
    file_path: str = ""


@dataclass
class MethodInfo:
    """方法信息"""
    name: str
    line_no: int
    params: List[str] = field(default_factory=list)
    return_type: str = "unknown"
    cyclomatic_complexity: int = 1
    lines_of_code: int = 0
    file_path: str = ""


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    line_no: int
    methods: List[MethodInfo] = field(default_factory=list)
    attributes: List[VariableInfo] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    cohesion_score: float = 0.0
    file_path: str = ""


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    file_path: str
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[MethodInfo] = field(default_factory=list)
    variables: List[VariableInfo] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    total_lines: int = 0


@dataclass
class ScanConfig:
    """扫描配置"""
    scan_levels: List[ScanLevel] = field(default_factory=lambda: [l for l in ScanLevel if l != ScanLevel.ALL])
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    max_workers: int = 4
    include_patterns: List[str] = field(default_factory=lambda: ["*.py"])
    exclude_patterns: List[str] = field(default_factory=list)
    report_formats: List[str] = field(default_factory=lambda: ["json"])
    enable_performance_metrics: bool = True


@dataclass
class ScanResult:
    """扫描结果"""
    scan_start_time: datetime = field(default_factory=datetime.now)
    scan_end_time: Optional[datetime] = None
    scan_duration_seconds: float = 0.0
    files_scanned: int = 0
    variables_found: int = 0
    methods_found: int = 0
    classes_found: int = 0
    modules_found: int = 0
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    modules: List[ModuleInfo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class ScanReport:
    """扫描报告"""
    scan_result: ScanResult = field(default_factory=ScanResult)
    summary: Dict[str, Any] = field(default_factory=dict)
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=datetime.now)


class AtomicScanner:
    """四级原子化扫描器"""
    
    def __init__(self, config: Optional[ScanConfig] = None):
        self.config = config or ScanConfig()
        self.result = ScanResult()
    
    def scan_directory(self, directory: str) -> ScanResult:
        """扫描整个目录"""
        self.result = ScanResult()
        self.result.scan_start_time = datetime.now()
        start_time = time.time()
        
        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                self.result.errors.append(f"Directory not found: {directory}")
                return self.result
            
            # 获取所有Python文件
            python_files = []
            for pattern in self.config.include_patterns:
                python_files.extend(dir_path.rglob(pattern))
            
            # 排除文件
            excluded_files = set()
            for pattern in self.config.exclude_patterns:
                excluded_files.update(dir_path.rglob(pattern))
            
            files_to_scan = [f for f in python_files if f not in excluded_files]
            
            # 根据执行模式选择
            if self.config.execution_mode == ExecutionMode.SEQUENTIAL:
                self._scan_files_sequential(files_to_scan)
            else:
                self._scan_files_parallel(files_to_scan)
                
        except Exception as e:
            self.result.errors.append(f"Scan error: {str(e)}")
        
        self.result.scan_end_time = datetime.now()
        self.result.scan_duration_seconds = time.time() - start_time
        
        return self.result
    
    def _scan_files_sequential(self, files: List[Path]):
        """顺序扫描文件"""
        for file_path in files:
            if file_path.name.startswith('.'):
                continue
            self._scan_file(file_path)
    
    def _scan_files_parallel(self, files: List[Path]):
        """并行扫描文件（使用多进程）"""
        # 过滤隐藏文件
        valid_files = [f for f in files if not f.name.startswith('.')]
        
        if self.config.max_workers <= 1 or len(valid_files) <= 1:
            self._scan_files_sequential(valid_files)
            return
        
        # 使用简单的线程池模拟并行
        results = []
        threads = []
        
        def worker(file_path):
            try:
                module_info = self._analyze_file(file_path)
                results.append(module_info)
            except Exception as e:
                pass
        
        for file_path in valid_files:
            thread = threading.Thread(target=worker, args=(file_path,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 合并结果
        for module_info in results:
            if module_info:
                self.result.modules.append(module_info)
                self.result.files_scanned += 1
                self._update_counts(module_info)
    
    def _scan_file(self, file_path: Path):
        """扫描单个文件"""
        try:
            module_info = self._analyze_file(file_path)
            if module_info:
                self.result.modules.append(module_info)
                self.result.files_scanned += 1
                self._update_counts(module_info)
        except Exception as e:
            self.result.errors.append(f"Error scanning {file_path}: {str(e)}")
    
    def _analyze_file(self, file_path: Path) -> Optional[ModuleInfo]:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            module_name = file_path.stem
            
            module_info = ModuleInfo(
                name=module_name,
                file_path=str(file_path),
                total_lines=len(source_code.splitlines())
            )
            
            # 根据扫描级别分析
            if ScanLevel.VARIABLE in self.config.scan_levels or ScanLevel.ALL in self.config.scan_levels:
                module_info.variables = self._extract_variables(tree, str(file_path))
            
            if ScanLevel.METHOD in self.config.scan_levels or ScanLevel.ALL in self.config.scan_levels:
                module_info.functions = self._extract_functions(tree, str(file_path))
            
            if ScanLevel.CLASS in self.config.scan_levels or ScanLevel.ALL in self.config.scan_levels:
                module_info.classes = self._extract_classes(tree, str(file_path))
            
            if ScanLevel.MODULE in self.config.scan_levels or ScanLevel.ALL in self.config.scan_levels:
                module_info.dependencies = self._extract_dependencies(tree)
            
            return module_info
            
        except Exception:
            return None
    
    def _extract_variables(self, tree: ast.AST, file_path: str) -> List[VariableInfo]:
        """提取变量信息"""
        variables = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var = VariableInfo(
                            name=target.id,
                            line_no=target.lineno,
                            col_offset=target.col_offset,
                            file_path=file_path
                        )
                        variables.append(var)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    var = VariableInfo(
                        name=node.target.id,
                        line_no=node.target.lineno,
                        col_offset=node.target.col_offset,
                        file_path=file_path
                    )
                    variables.append(var)
        return variables
    
    def _extract_functions(self, tree: ast.AST, file_path: str) -> List[MethodInfo]:
        """提取函数信息"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                method = MethodInfo(
                    name=node.name,
                    line_no=node.lineno,
                    params=[arg.arg for arg in node.args.args],
                    file_path=file_path
                )
                functions.append(method)
        return functions
    
    def _extract_classes(self, tree: ast.AST, file_path: str) -> List[ClassInfo]:
        """提取类信息"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls = ClassInfo(
                    name=node.name,
                    line_no=node.lineno,
                    base_classes=[b.id for b in node.bases if isinstance(b, ast.Name)],
                    file_path=file_path
                )
                # 提取方法
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                        method = MethodInfo(
                            name=item.name,
                            line_no=item.lineno,
                            params=[arg.arg for arg in item.args.args],
                            file_path=file_path
                        )
                        cls.methods.append(method)
                classes.append(cls)
        return classes
    
    def _extract_dependencies(self, tree: ast.AST) -> List[str]:
        """提取依赖信息"""
        dependencies = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module.split('.')[0])
        return list(set(dependencies))
    
    def _update_counts(self, module_info: ModuleInfo):
        """更新计数"""
        self.result.variables_found += len(module_info.variables)
        self.result.methods_found += len(module_info.functions)
        self.result.classes_found += len(module_info.classes)
        for cls in module_info.classes:
            self.result.methods_found += len(cls.methods)
        self.result.modules_found += 1


class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def generate_json_report(scan_result: ScanResult) -> str:
        """生成JSON报告"""
        report_data = {
            "result_id": scan_result.result_id,
            "scan_start_time": scan_result.scan_start_time.isoformat(),
            "scan_end_time": scan_result.scan_end_time.isoformat() if scan_result.scan_end_time else None,
            "scan_duration_seconds": scan_result.scan_duration_seconds,
            "files_scanned": scan_result.files_scanned,
            "variables_found": scan_result.variables_found,
            "methods_found": scan_result.methods_found,
            "classes_found": scan_result.classes_found,
            "modules_found": scan_result.modules_found,
            "modules": [
                {
                    "name": m.name,
                    "file_path": m.file_path,
                    "total_lines": m.total_lines,
                    "variables_count": len(m.variables),
                    "functions_count": len(m.functions),
                    "classes_count": len(m.classes),
                    "dependencies": m.dependencies
                }
                for m in scan_result.modules
            ],
            "errors": scan_result.errors
        }
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_text_report(scan_result: ScanResult) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("四级原子化扫描报告")
        lines.append("=" * 80)
        lines.append(f"扫描开始: {scan_result.scan_start_time}")
        if scan_result.scan_end_time:
            lines.append(f"扫描结束: {scan_result.scan_end_time}")
        lines.append(f"扫描耗时: {scan_result.scan_duration_seconds:.2f}秒")
        lines.append("")
        lines.append(f"扫描文件数: {scan_result.files_scanned}")
        lines.append(f"发现变量数: {scan_result.variables_found}")
        lines.append(f"发现方法数: {scan_result.methods_found}")
        lines.append(f"发现类数: {scan_result.classes_found}")
        lines.append(f"发现模块数: {scan_result.modules_found}")
        lines.append("")
        
        if scan_result.modules:
            lines.append("-" * 80)
            lines.append("模块详情")
            lines.append("-" * 80)
            for module in scan_result.modules:
                lines.append(f"\n模块: {module.name}")
                lines.append(f"  文件: {module.file_path}")
                lines.append(f"  行数: {module.total_lines}")
                lines.append(f"  变量: {len(module.variables)}")
                lines.append(f"  函数: {len(module.functions)}")
                lines.append(f"  类: {len(module.classes)}")
                if module.dependencies:
                    lines.append(f"  依赖: {', '.join(module.dependencies)}")
        
        if scan_result.errors:
            lines.append("\n" + "-" * 80)
            lines.append("错误信息")
            lines.append("-" * 80)
            for error in scan_result.errors:
                lines.append(f"  - {error}")
        
        return "\n".join(lines)


class ConfigManager:
    """配置管理器"""
    
    @staticmethod
    def load_config_from_file(config_path: str) -> Optional[ScanConfig]:
        """从文件加载配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = ScanConfig()
            if 'scan_levels' in data:
                config.scan_levels = [ScanLevel(l) for l in data['scan_levels']]
            if 'execution_mode' in data:
                config.execution_mode = ExecutionMode(data['execution_mode'])
            if 'max_workers' in data:
                config.max_workers = data['max_workers']
            if 'include_patterns' in data:
                config.include_patterns = data['include_patterns']
            if 'exclude_patterns' in data:
                config.exclude_patterns = data['exclude_patterns']
            if 'report_formats' in data:
                config.report_formats = data['report_formats']
            if 'enable_performance_metrics' in data:
                config.enable_performance_metrics = data['enable_performance_metrics']
            
            return config
            
        except Exception:
            return None
    
    @staticmethod
    def save_config_to_file(config: ScanConfig, config_path: str):
        """保存配置到文件"""
        data = {
            'scan_levels': [l.value for l in config.scan_levels],
            'execution_mode': config.execution_mode.value,
            'max_workers': config.max_workers,
            'include_patterns': config.include_patterns,
            'exclude_patterns': config.exclude_patterns,
            'report_formats': config.report_formats,
            'enable_performance_metrics': config.enable_performance_metrics
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# 全局扫描器
_global_scanner: Optional[AtomicScanner] = None


def get_atomic_scanner(config: Optional[ScanConfig] = None) -> AtomicScanner:
    """获取全局扫描器"""
    global _global_scanner
    if _global_scanner is None:
        _global_scanner = AtomicScanner(config)
    return _global_scanner


def reset_atomic_scanner():
    """重置扫描器"""
    global _global_scanner
    _global_scanner = None
