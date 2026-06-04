from __future__ import annotations

import ast
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.core import get_logger


logger = get_logger("entropy_manager")


class EntropyType(str, Enum):
    """熵值类型"""
    STRUCTURAL = "structural"
    NAMING = "naming"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    COUPLING = "coupling"
    COHESION = "cohesion"


@dataclass
class EntropyMetric:
    """熵值指标"""
    metric_type: EntropyType
    name: str
    value: float
    weight: float = 1.0
    description: str = ""
    threshold: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)

    def is_violation(self) -> bool:
        """检查是否违反阈值"""
        return self.value > self.threshold

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "metric_type": self.metric_type.value,
            "name": self.name,
            "value": self.value,
            "weight": self.weight,
            "description": self.description,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "is_violation": self.is_violation()
        }


@dataclass
class EntropyReport:
    """熵值报告"""
    report_id: str
    file_path: str
    overall_entropy: float
    metrics: List[EntropyMetric]
    violations: List[EntropyMetric]
    suggestions: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "report_id": self.report_id,
            "file_path": self.file_path,
            "overall_entropy": self.overall_entropy,
            "metrics": [m.to_dict() for m in self.metrics],
            "violations": [v.to_dict() for v in self.violations],
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }


class EntropyCalculator:
    """熵值计算器"""

    @staticmethod
    def calculate_structural_entropy(code: str) -> float:
        """计算结构熵"""
        try:
            tree = ast.parse(code)
            complexity = 0
            lines = code.split('\n')
            non_empty_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])

            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity += 2
                elif isinstance(node, ast.ClassDef):
                    complexity += 2

            max_complexity = max(non_empty_lines, 1)
            return min(complexity / max_complexity, 1.0)
        except:
            return 0.5

    @staticmethod
    def calculate_naming_entropy(code: str) -> float:
        """计算命名熵"""
        identifiers = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    identifiers.append(node.id)
                elif isinstance(node, ast.FunctionDef):
                    identifiers.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    identifiers.append(node.name)

            if not identifiers:
                return 0.0

            unique_ratio = len(set(identifiers)) / len(identifiers)
            short_name_ratio = len([i for i in identifiers if len(i) <= 2]) / len(identifiers)

            return (1 - unique_ratio) * 0.5 + short_name_ratio * 0.5
        except:
            return 0.5

    @staticmethod
    def calculate_complexity_entropy(code: str) -> float:
        """计算复杂度熵"""
        try:
            tree = ast.parse(code)
            complexity = 0
            max_complexity = 10

            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    complexity += 1
                elif isinstance(node, ast.Try):
                    complexity += 2
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity += len([n for n in node.args.args])

            return min(complexity / max_complexity, 1.0)
        except:
            return 0.5

    @staticmethod
    def calculate_duplication_entropy(code: str) -> float:
        """计算重复熵"""
        lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        if len(lines) < 3:
            return 0.0

        duplicate_count = 0
        for i, line in enumerate(lines):
            for j in range(i + 1, len(lines)):
                if len(line) > 10 and line == lines[j]:
                    duplicate_count += 1

        return min(duplicate_count / len(lines), 1.0)

    @staticmethod
    def calculate_coupling_entropy(imports: List[str]) -> float:
        """计算耦合熵"""
        if not imports:
            return 0.0

        stdlib_count = sum(1 for imp in imports if imp.startswith('.'))
        external_count = len(imports) - stdlib_count
        return min(external_count / 10, 1.0)


class EntropyReducer:
    """熵减工具集"""

    @staticmethod
    def reduce_complexity(code: str) -> Tuple[str, List[str]]:
        """降低复杂度"""
        suggestions = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len([n for n in ast.walk(node) if isinstance(n, (ast.If, ast.While, ast.For))]) > 5:
                        suggestions.append(f"函数 {node.name} 复杂度过高，考虑拆分")

                if isinstance(node, (ast.If,)):
                    if len(node.orelse) > 3:
                        suggestions.append("嵌套过深，考虑使用策略模式重构")

        except SyntaxError:
            suggestions.append("代码存在语法错误")

        return code, suggestions

    @staticmethod
    def reduce_duplication(code: str) -> Tuple[str, List[str]]:
        """减少重复"""
        suggestions = []

        lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
        seen = {}
        duplicates = []

        for i, line in enumerate(lines):
            if len(line) > 15:
                if line in seen:
                    duplicates.append((seen[line], i))
                else:
                    seen[line] = i

        if duplicates:
            suggestions.append(f"发现 {len(duplicates)} 处重复代码，建议提取为函数或常量")

        return code, suggestions

    @staticmethod
    def improve_naming(code: str) -> Tuple[str, List[str]]:
        """改进命名"""
        suggestions = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.name) <= 2:
                        suggestions.append(f"函数名 {node.name} 过短，建议使用更有意义的名称")

                if isinstance(node, ast.Name):
                    if len(node.id) <= 1:
                        suggestions.append(f"变量名 {node.id} 过短，建议使用完整名称")

        except:
            pass

        return code, suggestions

    @staticmethod
    def reduce_coupling(code: str, imports: List[str]) -> Tuple[str, List[str]]:
        """降低耦合"""
        suggestions = []

        if len(imports) > 10:
            suggestions.append(f"导入过多（{len(imports)}个），考虑重新设计模块结构")

        for imp in imports:
            if '..' in imp or imp.count('.') > 2:
                suggestions.append(f"导入路径 {imp} 过深，考虑重构模块结构")

        return code, suggestions

    @staticmethod
    def auto_reduce(code: str, imports: Optional[List[str]] = None) -> Tuple[str, List[str]]:
        """自动熵减"""
        all_suggestions = []

        code, suggestions = EntropyReducer.reduce_complexity(code)
        all_suggestions.extend(suggestions)

        code, suggestions = EntropyReducer.reduce_duplication(code)
        all_suggestions.extend(suggestions)

        code, suggestions = EntropyReducer.improve_naming(code)
        all_suggestions.extend(suggestions)

        if imports:
            code, suggestions = EntropyReducer.reduce_coupling(code, imports)
            all_suggestions.extend(suggestions)

        return code, all_suggestions


class EntropyRule:
    """熵值规范"""

    def __init__(self):
        self.rules = {
            "max_complexity": 10,
            "max_function_length": 50,
            "max_imports": 10,
            "min_naming_length": 3,
            "max_nesting_depth": 4,
            "max_parameters": 5
        }

    def get_rule(self, rule_name: str) -> Any:
        """获取规则值"""
        return self.rules.get(rule_name)

    def set_rule(self, rule_name: str, value: Any) -> None:
        """设置规则值"""
        if rule_name in self.rules:
            self.rules[rule_name] = value
            logger.info(f"设置熵值规则: {rule_name} = {value}")

    def validate(self, code: str, imports: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """验证代码是否符合规范"""
        violations = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len([n for n in ast.walk(node)]) > self.rules["max_function_length"] * 2:
                        violations.append(f"函数 {node.name} 过长")

                    if len(node.args.args) > self.rules["max_parameters"]:
                        violations.append(f"函数 {node.name} 参数过多")

        except:
            violations.append("代码存在语法错误")

        if imports and len(imports) > self.rules["max_imports"]:
            violations.append(f"导入过多（{len(imports)} > {self.rules['max_imports']}）")

        return len(violations) == 0, violations


class EntropyMonitor:
    """熵值监控器"""

    def __init__(self):
        self.history: List[EntropyReport] = []
        self.alerts: List[Dict[str, Any]] = []

    def add_report(self, report: EntropyReport) -> None:
        """添加报告"""
        self.history.append(report)
        logger.info(f"添加熵值报告: {report.file_path}, 整体熵值: {report.overall_entropy:.2f}")

        if report.overall_entropy > 0.7:
            self._create_alert(report)

    def _create_alert(self, report: EntropyReport) -> None:
        """创建告警"""
        alert = {
            "alert_id": str(uuid.uuid4()),
            "report_id": report.report_id,
            "file_path": report.file_path,
            "entropy": report.overall_entropy,
            "violations": [v.name for v in report.violations],
            "timestamp": datetime.now().isoformat(),
            "severity": "high" if report.overall_entropy > 0.9 else "medium"
        }
        self.alerts.append(alert)
        logger.warning(f"熵值告警: {report.file_path} 整体熵值过高 ({report.overall_entropy:.2f})")

    def get_trend(self, file_path: str, limit: int = 10) -> List[EntropyReport]:
        """获取熵值趋势"""
        reports = [r for r in self.history if r.file_path == file_path]
        return reports[-limit:]

    def get_alerts(self) -> List[Dict[str, Any]]:
        """获取告警列表"""
        return self.alerts

    def get_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        if not self.history:
            return {
                "total_files": 0,
                "average_entropy": 0.0,
                "high_entropy_count": 0,
                "total_alerts": 0
            }

        entropies = [r.overall_entropy for r in self.history]
        return {
            "total_files": len(self.history),
            "average_entropy": sum(entropies) / len(entropies),
            "high_entropy_count": len([e for e in entropies if e > 0.7]),
            "total_alerts": len(self.alerts),
            "latest_report": self.history[-1].to_dict() if self.history else None
        }


class EntropyManager:
    """熵值管理器"""

    def __init__(self):
        self.calculator = EntropyCalculator()
        self.reducer = EntropyReducer()
        self.rule = EntropyRule()
        self.monitor = EntropyMonitor()
        self.logger = get_logger("entropy_manager")

    def analyze_file(self, file_path: str) -> EntropyReport:
        """分析文件熵值"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            imports = []
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        imports.append(node.module or '')
            except:
                pass

            structural = self.calculator.calculate_structural_entropy(code)
            naming = self.calculator.calculate_naming_entropy(code)
            complexity = self.calculator.calculate_complexity_entropy(code)
            duplication = self.calculator.calculate_duplication_entropy(code)
            coupling = self.calculator.calculate_coupling_entropy(imports)

            metrics = [
                EntropyMetric(
                    metric_type=EntropyType.STRUCTURAL,
                    name="结构熵",
                    value=structural,
                    weight=1.5,
                    threshold=0.6
                ),
                EntropyMetric(
                    metric_type=EntropyType.NAMING,
                    name="命名熵",
                    value=naming,
                    weight=1.0,
                    threshold=0.5
                ),
                EntropyMetric(
                    metric_type=EntropyType.COMPLEXITY,
                    name="复杂度熵",
                    value=complexity,
                    weight=1.5,
                    threshold=0.7
                ),
                EntropyMetric(
                    metric_type=EntropyType.DUPLICATION,
                    name="重复熵",
                    value=duplication,
                    weight=1.2,
                    threshold=0.3
                ),
                EntropyMetric(
                    metric_type=EntropyType.COUPLING,
                    name="耦合熵",
                    value=coupling,
                    weight=1.0,
                    threshold=0.6
                )
            ]

            violations = [m for m in metrics if m.is_violation()]
            overall = sum(m.value * m.weight for m in metrics) / sum(m.weight for m in metrics)

            code_reduced, suggestions = self.reducer.auto_reduce(code, imports)

            report = EntropyReport(
                report_id=str(uuid.uuid4()),
                file_path=file_path,
                overall_entropy=overall,
                metrics=metrics,
                violations=violations,
                suggestions=suggestions
            )

            self.monitor.add_report(report)
            return report

        except Exception as e:
            self.logger.error(f"分析文件 {file_path} 失败: {e}")
            raise

    def reduce_entropy(self, file_path: str) -> Tuple[str, List[str]]:
        """降低文件熵值"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            code, suggestions = self.reducer.auto_reduce(code)
            return code, suggestions

        except Exception as e:
            self.logger.error(f"降低文件 {file_path} 熵值失败: {e}")
            raise

    def get_monitor_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        return self.monitor.get_summary()

    def get_alerts(self) -> List[Dict[str, Any]]:
        """获取告警"""
        return self.monitor.get_alerts()


def create_entropy_manager() -> EntropyManager:
    """创建熵值管理器"""
    return EntropyManager()
