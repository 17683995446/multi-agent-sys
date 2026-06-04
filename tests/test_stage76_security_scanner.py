"""
阶段76验收测试 - 代码安全漏洞扫描
"""

import pytest
from src.architecture.security_scanner import (
    VulnerabilityType,
    VulnerabilitySeverity,
    Vulnerability,
    SecurityScanner,
    SecurityScanService,
)


class TestVulnerabilityType:
    """测试漏洞类型枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert VulnerabilityType.INJECTION.value == "injection"
        assert VulnerabilityType.XSS.value == "xss"
        assert VulnerabilityType.CSRF.value == "csrf"
        assert VulnerabilityType.AUTH_BYPASS.value == "auth_bypass"
        assert VulnerabilityType.DATA_LEAK.value == "data_leak"
        assert VulnerabilityType.MISCONFIG.value == "misconfig"

    def test_all_types(self):
        """测试所有漏洞类型"""
        types = list(VulnerabilityType)
        assert len(types) == 6


class TestVulnerabilitySeverity:
    """测试漏洞严重程度枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        assert VulnerabilitySeverity.INFO.value == "info"
        assert VulnerabilitySeverity.LOW.value == "low"
        assert VulnerabilitySeverity.MEDIUM.value == "medium"
        assert VulnerabilitySeverity.HIGH.value == "high"
        assert VulnerabilitySeverity.CRITICAL.value == "critical"

    def test_all_severities(self):
        """测试所有严重程度"""
        severities = list(VulnerabilitySeverity)
        assert len(severities) == 5


class TestVulnerability:
    """测试漏洞记录"""

    def test_default_creation(self):
        """测试默认创建"""
        vuln = Vulnerability()
        assert vuln.vuln_id != ""
        assert vuln.vuln_type == VulnerabilityType.INJECTION
        assert vuln.severity == VulnerabilitySeverity.MEDIUM
        assert vuln.location == ""
        assert vuln.description == ""
        assert vuln.remediation == ""

    def test_custom_creation(self):
        """测试自定义创建"""
        vuln = Vulnerability(
            vuln_type=VulnerabilityType.XSS,
            severity=VulnerabilitySeverity.HIGH,
            location="app.py:42",
            description="XSS漏洞",
            remediation="对输出进行HTML转义",
        )
        assert vuln.vuln_type == VulnerabilityType.XSS
        assert vuln.severity == VulnerabilitySeverity.HIGH
        assert vuln.location == "app.py:42"
        assert vuln.description == "XSS漏洞"
        assert vuln.remediation == "对输出进行HTML转义"

    def test_vuln_id_unique(self):
        """测试漏洞ID唯一性"""
        v1 = Vulnerability()
        v2 = Vulnerability()
        assert v1.vuln_id != v2.vuln_id


class TestSecurityScanner:
    """测试安全扫描器"""

    def test_initialization(self):
        """测试初始化"""
        scanner = SecurityScanner()
        assert scanner._vulnerabilities == []
        assert scanner._scan_results == {}

    def test_scan_clean_code(self):
        """测试扫描安全代码"""
        scanner = SecurityScanner()
        code = "def hello():\n    return 'world'"
        vulns = scanner.scan(code, "clean.py")
        assert isinstance(vulns, list)
        assert len(vulns) == 0

    def test_scan_injection_vulnerability(self):
        """测试检测注入漏洞"""
        scanner = SecurityScanner()
        code = "cursor.execute('SELECT * FROM users WHERE id=' + user_id)"
        vulns = scanner.scan(code, "db.py")
        assert len(vulns) > 0
        injection_vulns = [v for v in vulns if v.vuln_type == VulnerabilityType.INJECTION]
        assert len(injection_vulns) > 0
        assert injection_vulns[0].severity == VulnerabilitySeverity.HIGH

    def test_scan_eval_injection(self):
        """测试检测eval注入"""
        scanner = SecurityScanner()
        code = "result = eval(user_input)"
        vulns = scanner.scan(code, "eval_code.py")
        injection_vulns = [v for v in vulns if v.vuln_type == VulnerabilityType.INJECTION]
        assert len(injection_vulns) > 0

    def test_scan_auth_bypass(self):
        """测试检测认证绕过"""
        scanner = SecurityScanner()
        code = "password = 'admin123'\nsecret_key = 'my_secret'"
        vulns = scanner.scan(code, "config.py")
        auth_vulns = [v for v in vulns if v.vuln_type == VulnerabilityType.AUTH_BYPASS]
        assert len(auth_vulns) > 0
        assert auth_vulns[0].severity == VulnerabilitySeverity.CRITICAL

    def test_scan_data_leak(self):
        """测试检测数据泄露"""
        scanner = SecurityScanner()
        code = "print(password)\ndebug=True"
        vulns = scanner.scan(code, "debug.py")
        leak_vulns = [v for v in vulns if v.vuln_type == VulnerabilityType.DATA_LEAK]
        assert len(leak_vulns) > 0

    def test_scan_misconfig(self):
        """测试检测配置错误"""
        scanner = SecurityScanner()
        code = "ALLOWED_HOSTS = ['*']\nDEBUG = True"
        vulns = scanner.scan(code, "settings.py")
        misconfig_vulns = [v for v in vulns if v.vuln_type == VulnerabilityType.MISCONFIG]
        assert len(misconfig_vulns) > 0

    def test_scan_multiple_vulnerabilities(self):
        """测试检测多种漏洞"""
        scanner = SecurityScanner()
        code = "cursor.execute(query)\npassword = 'admin'\ndebug=True"
        vulns = scanner.scan(code, "app.py")
        assert len(vulns) >= 2

    def test_generate_report(self):
        """测试生成报告"""
        scanner = SecurityScanner()
        scanner.scan("eval(data)", "test.py")
        report = scanner.generate_report()
        assert "total_vulnerabilities" in report
        assert "by_type" in report
        assert "by_severity" in report
        assert "risk_level" in report
        assert report["total_vulnerabilities"] > 0

    def test_generate_report_safe(self):
        """测试安全代码的报告"""
        scanner = SecurityScanner()
        scanner.scan("def safe(): pass", "safe.py")
        report = scanner.generate_report()
        assert report["risk_level"] == "安全"
        assert report["total_vulnerabilities"] == 0

    def test_generate_report_critical(self):
        """测试严重风险的报告"""
        scanner = SecurityScanner()
        scanner.scan("password = 'admin'", "config.py")
        report = scanner.generate_report()
        assert report["risk_level"] in ("严重", "高危")

    def test_scan_results_stored(self):
        """测试扫描结果存储"""
        scanner = SecurityScanner()
        scanner.scan("eval(x)", "test.py")
        assert "test.py" in scanner._scan_results
        assert scanner._scan_results["test.py"]["scanned"] is True


class TestSecurityScanService:
    """测试安全扫描服务"""

    def test_initialization(self):
        """测试初始化"""
        service = SecurityScanService()
        assert service.scanner is not None

    def test_initialization_with_scanner(self):
        """测试使用自定义扫描器初始化"""
        scanner = SecurityScanner()
        service = SecurityScanService(scanner=scanner)
        assert service.scanner is scanner

    def test_scan(self):
        """测试扫描"""
        service = SecurityScanService()
        vulns = service.scan("eval(user_input)", "app.py")
        assert len(vulns) > 0

    def test_get_vulnerabilities(self):
        """测试获取漏洞列表"""
        service = SecurityScanService()
        service.scan("eval(x)", "test.py")
        vulns = service.get_vulnerabilities()
        assert len(vulns) > 0

    def test_get_vulnerabilities_by_type(self):
        """测试按类型获取漏洞"""
        service = SecurityScanService()
        service.scan("eval(x)", "test.py")
        vulns = service.get_vulnerabilities(vuln_type=VulnerabilityType.INJECTION)
        assert all(v.vuln_type == VulnerabilityType.INJECTION for v in vulns)

    def test_get_vulnerabilities_by_severity(self):
        """测试按严重程度获取漏洞"""
        service = SecurityScanService()
        service.scan("password = 'admin'", "config.py")
        vulns = service.get_vulnerabilities(severity=VulnerabilitySeverity.CRITICAL)
        assert all(v.severity == VulnerabilitySeverity.CRITICAL for v in vulns)

    def test_get_report(self):
        """测试获取报告"""
        service = SecurityScanService()
        service.scan("eval(x)", "test.py")
        report = service.get_report()
        assert "total_vulnerabilities" in report

    def test_get_vulnerabilities_empty(self):
        """测试空漏洞列表"""
        service = SecurityScanService()
        vulns = service.get_vulnerabilities()
        assert vulns == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
