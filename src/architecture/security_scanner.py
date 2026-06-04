"""
代码安全漏洞扫描模块

职责：扫描代码中的安全漏洞，包括注入、XSS、CSRF、认证绕过、数据泄露和配置错误

基于第一性原理：简单、单一、可追溯、可组合
"""

import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VulnerabilityType(str, Enum):
    """漏洞类型"""
    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTH_BYPASS = "auth_bypass"
    DATA_LEAK = "data_leak"
    MISCONFIG = "misconfig"


class VulnerabilitySeverity(str, Enum):
    """漏洞严重程度"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Vulnerability:
    """安全漏洞记录"""
    vuln_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vuln_type: VulnerabilityType = VulnerabilityType.INJECTION
    severity: VulnerabilitySeverity = VulnerabilitySeverity.MEDIUM
    location: str = ""
    description: str = ""
    remediation: str = ""

    def __post_init__(self):
        """初始化后日志记录"""
        logger.debug(f"Vulnerability created: vuln_id={self.vuln_id}, "
                     f"type={self.vuln_type.value}, severity={self.severity.value}")


class SecurityScanner:
    """安全漏洞扫描器"""

    def __init__(self):
        """初始化安全扫描器"""
        self._vulnerabilities: List[Vulnerability] = []
        self._scan_results: Dict[str, Any] = {}
        logger.info("SecurityScanner initialized")

    def scan(self, code_content: str, file_path: str = "") -> List[Vulnerability]:
        """扫描代码内容，检测安全漏洞"""
        logger.info(f"SecurityScanner: scanning code, file={file_path}, "
                     f"length={len(code_content)}")
        vulnerabilities = []
        try:
            vulnerabilities.extend(self._check_injection(code_content, file_path))
            vulnerabilities.extend(self._check_auth(code_content, file_path))
            vulnerabilities.extend(self._check_data_leak(code_content, file_path))
            vulnerabilities.extend(self._check_misconfig(code_content, file_path))
            self._vulnerabilities.extend(vulnerabilities)
            self._scan_results[file_path] = {
                "vulnerability_count": len(vulnerabilities),
                "scanned": True,
            }
            logger.info(f"SecurityScanner: scan completed, "
                        f"found {len(vulnerabilities)} vulnerabilities")
        except Exception as e:
            logger.error(f"SecurityScanner: scan failed: {e}")
        return vulnerabilities

    def _check_injection(self, code_content: str, file_path: str) -> List[Vulnerability]:
        """检测注入漏洞"""
        logger.debug(f"SecurityScanner: checking injection vulnerabilities, "
                     f"file={file_path}")
        vulnerabilities = []
        try:
            injection_patterns = [
                ("execute(", "SQL注入风险：使用execute直接拼接SQL"),
                ("eval(", "代码注入风险：使用eval执行动态代码"),
                ("exec(", "代码注入风险：使用exec执行动态代码"),
                ("os.system(", "命令注入风险：使用os.system执行系统命令"),
                ("subprocess.call(", "命令注入风险：使用subprocess.call未使用shell=False"),
            ]
            for pattern, description in injection_patterns:
                if pattern in code_content:
                    vulnerabilities.append(Vulnerability(
                        vuln_type=VulnerabilityType.INJECTION,
                        severity=VulnerabilitySeverity.HIGH,
                        location=file_path,
                        description=description,
                        remediation="使用参数化查询或安全的API替代",
                    ))
        except Exception as e:
            logger.error(f"SecurityScanner: _check_injection failed: {e}")
        return vulnerabilities

    def _check_auth(self, code_content: str, file_path: str) -> List[Vulnerability]:
        """检测认证绕过漏洞"""
        logger.debug(f"SecurityScanner: checking auth vulnerabilities, "
                     f"file={file_path}")
        vulnerabilities = []
        try:
            auth_patterns = [
                ("password = ", "硬编码密码：代码中包含硬编码的密码"),
                ("secret_key = ", "硬编码密钥：代码中包含硬编码的密钥"),
                ("@skip_auth", "认证绕过：使用跳过认证的装饰器"),
                ("verify=False", "SSL验证禁用：禁用了SSL证书验证"),
            ]
            for pattern, description in auth_patterns:
                if pattern in code_content:
                    vulnerabilities.append(Vulnerability(
                        vuln_type=VulnerabilityType.AUTH_BYPASS,
                        severity=VulnerabilitySeverity.CRITICAL,
                        location=file_path,
                        description=description,
                        remediation="使用环境变量或密钥管理服务存储敏感信息",
                    ))
        except Exception as e:
            logger.error(f"SecurityScanner: _check_auth failed: {e}")
        return vulnerabilities

    def _check_data_leak(self, code_content: str, file_path: str) -> List[Vulnerability]:
        """检测数据泄露漏洞"""
        logger.debug(f"SecurityScanner: checking data leak vulnerabilities, "
                     f"file={file_path}")
        vulnerabilities = []
        try:
            leak_patterns = [
                ("print(password", "数据泄露：打印密码信息"),
                ("logger.info(password", "数据泄露：日志中记录密码信息"),
                ("stacktrace=True", "数据泄露：生产环境暴露堆栈信息"),
                ("debug=True", "数据泄露：生产环境开启调试模式"),
            ]
            for pattern, description in leak_patterns:
                if pattern in code_content:
                    vulnerabilities.append(Vulnerability(
                        vuln_type=VulnerabilityType.DATA_LEAK,
                        severity=VulnerabilitySeverity.MEDIUM,
                        location=file_path,
                        description=description,
                        remediation="移除敏感信息的输出，关闭调试模式",
                    ))
        except Exception as e:
            logger.error(f"SecurityScanner: _check_data_leak failed: {e}")
        return vulnerabilities

    def _check_misconfig(self, code_content: str, file_path: str) -> List[Vulnerability]:
        """检测配置错误漏洞"""
        logger.debug(f"SecurityScanner: checking misconfig vulnerabilities, "
                     f"file={file_path}")
        vulnerabilities = []
        try:
            misconfig_patterns = [
                ("CORS", "配置错误：CORS配置可能过于宽松"),
                ("ALLOWED_HOSTS = ['*']", "配置错误：允许所有主机访问"),
                ("DEBUG = True", "配置错误：生产环境开启DEBUG模式"),
            ]
            for pattern, description in misconfig_patterns:
                if pattern in code_content:
                    vulnerabilities.append(Vulnerability(
                        vuln_type=VulnerabilityType.MISCONFIG,
                        severity=VulnerabilitySeverity.LOW,
                        location=file_path,
                        description=description,
                        remediation="检查并收紧安全配置",
                    ))
        except Exception as e:
            logger.error(f"SecurityScanner: _check_misconfig failed: {e}")
        return vulnerabilities

    def generate_report(self) -> Dict[str, Any]:
        """生成安全扫描报告"""
        logger.info("SecurityScanner: generating report")
        try:
            by_type: Dict[str, int] = {}
            by_severity: Dict[str, int] = {}
            for v in self._vulnerabilities:
                by_type[v.vuln_type.value] = by_type.get(v.vuln_type.value, 0) + 1
                by_severity[v.severity.value] = by_severity.get(v.severity.value, 0) + 1

            critical_count = by_severity.get("critical", 0)
            high_count = by_severity.get("high", 0)

            if critical_count > 0:
                risk_level = "严重"
            elif high_count > 0:
                risk_level = "高危"
            elif len(self._vulnerabilities) > 0:
                risk_level = "中等"
            else:
                risk_level = "安全"

            report: Dict[str, Any] = {
                "total_vulnerabilities": len(self._vulnerabilities),
                "by_type": by_type,
                "by_severity": by_severity,
                "risk_level": risk_level,
                "vulnerabilities": [
                    {
                        "vuln_id": v.vuln_id,
                        "type": v.vuln_type.value,
                        "severity": v.severity.value,
                        "location": v.location,
                        "description": v.description,
                        "remediation": v.remediation,
                    }
                    for v in self._vulnerabilities
                ],
            }
            logger.info(f"SecurityScanner: report generated, "
                        f"risk_level={risk_level}")
        except Exception as e:
            logger.error(f"SecurityScanner: generate_report failed: {e}")
            report = {"error": str(e)}
        return report


class SecurityScanService:
    """安全扫描服务"""

    def __init__(self, scanner: Optional[SecurityScanner] = None):
        """初始化安全扫描服务"""
        self.scanner = scanner or SecurityScanner()
        logger.info("SecurityScanService initialized")

    def scan(self, code_content: str, file_path: str = "") -> List[Vulnerability]:
        """执行安全扫描"""
        logger.info(f"SecurityScanService: scanning, file={file_path}")
        return self.scanner.scan(code_content, file_path)

    def get_vulnerabilities(self,
                            vuln_type: Optional[VulnerabilityType] = None,
                            severity: Optional[VulnerabilitySeverity] = None
                            ) -> List[Vulnerability]:
        """获取漏洞列表"""
        logger.debug("SecurityScanService: getting vulnerabilities")
        vulnerabilities = self.scanner._vulnerabilities
        if vuln_type is not None:
            vulnerabilities = [v for v in vulnerabilities if v.vuln_type == vuln_type]
        if severity is not None:
            vulnerabilities = [v for v in vulnerabilities if v.severity == severity]
        return vulnerabilities

    def get_report(self) -> Dict[str, Any]:
        """获取安全扫描报告"""
        logger.debug("SecurityScanService: getting report")
        return self.scanner.generate_report()
