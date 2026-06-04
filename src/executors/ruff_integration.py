from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class RuleCategory(Enum):
    """Ruff规则分类"""
    ERROR = "E"
    FLAKE8_BUILTIN = "F"
    IMPORT = "I"
    WARNING = "W"
    NAMING = "N"
    PYTHON_UPGRADE = "UP"
    BUG_BEAR = "B"
    COM_PREHENSION = "C4"


class ViolationSeverity(Enum):
    """违规严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Violation:
    """代码违规信息"""
    file: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    rule_code: str = ""
    message: str = ""
    severity: ViolationSeverity = ViolationSeverity.WARNING
    fix_available: bool = False

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}: {self.rule_code} {self.message}"


@dataclass
class ScanResult:
    """代码扫描结果"""
    file: str
    violations: List[Violation] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    total_violations: int = 0
    scan_time_ms: float = 0.0

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


@dataclass
class FixResult:
    """修复结果"""
    file: str
    fixed: bool = False
    applied_fixes: List[str] = field(default_factory=list)
    remaining_violations: List[Violation] = field(default_factory=list)


@dataclass
class RuleConfig:
    """规则配置"""
    
    enabled_rules: List[str] = field(default_factory=lambda: ["E", "F", "I", "W", "N", "UP", "B", "C4"])
    disabled_rules: List[str] = field(default_factory=lambda: ["E501"])  # Line length handled by config
    line_length: int = 120
    target_version: str = "py311"
    custom_rules: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def enable_rule(self, rule: str) -> "RuleConfig":
        if rule not in self.enabled_rules:
            self.enabled_rules.append(rule)
        return self
    
    def disable_rule(self, rule: str) -> "RuleConfig":
        if rule not in self.disabled_rules:
            self.disabled_rules.append(rule)
        return self
    
    def to_toml_config(self) -> str:
        """生成TOML格式配置"""
        config_lines = [
            "[tool.ruff]",
            f'line-length = {self.line_length}',
            f'target-version = "{self.target_version}"',
            "",
            "[tool.ruff.lint]",
            f'select = {json.dumps(self.enabled_rules)}',
            f'ignore = {json.dumps(self.disabled_rules)}',
        ]
        return "\n".join(config_lines)


class RuffChecker:
    """Ruff代码检查器"""
    
    def __init__(self, config: Optional[RuleConfig] = None):
        self.config = config or RuleConfig()
        self._ruff_available = self._check_ruff_available()
    
    def _check_ruff_available(self) -> bool:
        """检查Ruff是否可用"""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def check_code(
        self,
        code: str,
        filename: str = "temp.py",
        fix: bool = False
    ) -> Union[ScanResult, FixResult]:
        """检查代码"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / filename
            temp_path.write_text(code, encoding="utf-8")
            
            if fix:
                return self._fix_file(str(temp_path), code)
            else:
                return self._scan_file(str(temp_path))
    
    def check_file(
        self,
        file_path: str,
        fix: bool = False
    ) -> Union[ScanResult, FixResult]:
        """检查文件"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if fix:
            return self._fix_file(file_path)
        else:
            return self._scan_file(file_path)
    
    def _scan_file(self, file_path: str) -> ScanResult:
        """扫描单个文件"""
        import time
        start_time = time.time()
        
        result = ScanResult(file=Path(file_path).name)
        
        if not self._ruff_available:
            self._fallback_scan(file_path, result)
        else:
            try:
                cmd = [
                    "ruff", "check",
                    "--output-format", "json",
                    file_path
                ]
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if process.stdout:
                    self._parse_ruff_output(process.stdout, result)
                
            except subprocess.TimeoutExpired:
                self._fallback_scan(file_path, result)
        
        result.scan_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _fallback_scan(self, file_path: str, result: ScanResult):
        """当Ruff不可用时的备用扫描方法"""
        content = Path(file_path).read_text(encoding="utf-8")
        
        if not content.strip():
            return
        
        lines = content.split("\n")
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if not stripped:
                continue
            
            if len(line) > self.config.line_length:
                result.violations.append(Violation(
                    file=Path(file_path).name,
                    line=i,
                    column=len(line),
                    rule_code="E501",
                    message=f"Line too long ({len(line)} > {self.config.line_length} characters)",
                    severity=ViolationSeverity.WARNING
                ))
            
            if stripped.startswith("print(") and "# noqa" not in line.lower():
                result.violations.append(Violation(
                    file=Path(file_path).name,
                    line=i,
                    column=line.find("print(") + 1,
                    rule_code="T201",
                    message="Print statement found, consider using logging",
                    severity=ViolationSeverity.WARNING
                ))
        
        self._count_violations(result)
    
    def _fix_file(self, file_path: str, original_code: Optional[str] = None) -> FixResult:
        """修复文件"""
        fix_result = FixResult(file=Path(file_path).name)
        
        if not self._ruff_available:
            fix_result.fixed = False
            return fix_result
        
        try:
            cmd = [
                "ruff", "check",
                "--fix",
                file_path
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            scan_result = self._scan_file(file_path)
            fix_result.fixed = scan_result.has_violations  # 简化版逻辑
            
        except subprocess.SubprocessError:
            pass
        
        return fix_result
    
    def _parse_ruff_output(self, output: str, result: ScanResult):
        """解析Ruff JSON输出"""
        try:
            data = json.loads(output)
            for item in data:
                violation = Violation(
                    file=Path(item.get("filename", "")).name,
                    line=item.get("location", {}).get("row", 0),
                    column=item.get("location", {}).get("column", 0),
                    end_line=item.get("end_location", {}).get("row"),
                    end_column=item.get("end_location", {}).get("column"),
                    rule_code=item.get("code", ""),
                    message=item.get("message", ""),
                    fix_available=bool(item.get("fix")),
                    severity=self._determine_severity(item.get("code", ""))
                )
                result.violations.append(violation)
            self._count_violations(result)
        except json.JSONDecodeError:
            pass
    
    def _count_violations(self, result: ScanResult):
        """统计违规数量"""
        result.total_violations = len(result.violations)
        result.error_count = sum(
            1 for v in result.violations 
            if v.severity == ViolationSeverity.ERROR
        )
        result.warning_count = result.total_violations - result.error_count
    
    def _determine_severity(self, rule_code: str) -> ViolationSeverity:
        """根据规则代码确定严重程度"""
        if rule_code.startswith(("E", "F")):
            return ViolationSeverity.ERROR
        return ViolationSeverity.WARNING


class CustomRule:
    """自定义规则基类"""
    
    def __init__(self, code: str, name: str, description: str = ""):
        self.code = code
        self.name = name
        self.description = description
    
    def check(self, code: str) -> List[Violation]:
        raise NotImplementedError()


class CustomRuleRegistry:
    """自定义规则注册表"""
    
    def __init__(self):
        self._rules: Dict[str, CustomRule] = {}
    
    def register(self, rule: CustomRule) -> "CustomRuleRegistry":
        self._rules[rule.code] = rule
        return self
    
    def unregister(self, code: str) -> "CustomRuleRegistry":
        if code in self._rules:
            del self._rules[code]
        return self
    
    def get(self, code: str) -> Optional[CustomRule]:
        return self._rules.get(code)
    
    def check_all(self, code: str, filename: str = "temp.py") -> List[Violation]:
        violations = []
        for rule in self._rules.values():
            violations.extend(rule.check(code))
        return violations


class CodeQualityChecker:
    """综合代码质量检查器"""
    
    def __init__(self):
        self.ruff_checker = RuffChecker()
        self.custom_rules = CustomRuleRegistry()
    
    def check(
        self,
        code: str,
        filename: str = "temp.py",
        apply_fixes: bool = False
    ) -> Dict[str, Any]:
        """综合检查代码质量"""
        scan_result = self.ruff_checker.check_code(code, filename, fix=apply_fixes)
        custom_violations = self.custom_rules.check_all(code, filename)
        
        if isinstance(scan_result, ScanResult):
            scan_result.violations.extend(custom_violations)
        
        return {
            "file": filename,
            "scan_result": scan_result,
            "custom_violations": custom_violations,
            "total_issues": len(getattr(scan_result, "violations", [])) + len(custom_violations)
        }
    
    def format_code(self, code: str) -> str:
        """格式化代码"""
        if not self.ruff_checker._ruff_available:
            return code
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "format.py"
            temp_path.write_text(code, encoding="utf-8")
            
            try:
                cmd = ["ruff", "format", str(temp_path)]
                subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return temp_path.read_text(encoding="utf-8")
            except subprocess.SubprocessError:
                return code
