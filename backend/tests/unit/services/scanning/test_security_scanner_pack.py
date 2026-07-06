from __future__ import annotations

from app.schemas.api_specification import EndpointEnrichmentMetadata, NormalizedEndpoint
from app.services.scanning.models import ScanConfiguration, Severity
from app.services.scanning.orchestrator import ScannerOrchestrator
from app.services.scanning.registry import ScannerRegistry
from app.services.scanning.scanners.broken_authentication import BrokenAuthenticationScanner
from app.services.scanning.scanners.excessive_data_exposure import ExcessiveDataExposureScanner
from app.services.scanning.scanners.security_misconfiguration import SecurityMisconfigurationScanner


def make_endpoint(
    path: str,
    method: str = "GET",
    security_schemes: list[str] | None = None,
    auth_required: bool = False,
    request_schema: dict[str, object] | None = None,
    response_schema: dict[str, object] | None = None,
) -> NormalizedEndpoint:
    return NormalizedEndpoint(
        id=f"endpoint:{path}",
        endpoint_type="rest",
        path=path,
        method=method,
        security_schemes=security_schemes or [],
        request_schema=request_schema or {},
        response_schema=response_schema or {},
        enrichment=EndpointEnrichmentMetadata(auth_required=auth_required),
    )


def test_security_misconfiguration_detects_insecure_http_endpoint() -> None:
    scanner = SecurityMisconfigurationScanner()
    endpoint = make_endpoint("http://example.com/users")

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert len(findings) >= 1
    assert any(finding.vulnerability_type == "security_misconfiguration" for finding in findings)
    assert any(finding.severity == Severity.MEDIUM for finding in findings)


def test_security_misconfiguration_detects_dangerous_unauthenticated_method() -> None:
    scanner = SecurityMisconfigurationScanner()
    endpoint = make_endpoint("/users/{id}", method="DELETE")

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert any(finding.vulnerability_type == "security_misconfiguration" for finding in findings)


def test_security_misconfiguration_safe_endpoint() -> None:
    scanner = SecurityMisconfigurationScanner()
    endpoint = make_endpoint("https://example.com/admin", method="GET", security_schemes=["bearerAuth"], auth_required=True)

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert findings == []


def test_broken_authentication_detects_sensitive_endpoint_without_auth() -> None:
    scanner = BrokenAuthenticationScanner()
    endpoint = make_endpoint("/admin/users", method="GET")

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert len(findings) >= 1
    assert findings[0].vulnerability_type == "broken_authentication"
    assert findings[0].severity == Severity.HIGH


def test_broken_authentication_protected_endpoint_with_auth() -> None:
    scanner = BrokenAuthenticationScanner()
    endpoint = make_endpoint("/admin/users", method="GET", security_schemes=["bearerAuth"], auth_required=True)

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert findings == []


def test_broken_authentication_detects_inconsistent_security_metadata() -> None:
    scanner = BrokenAuthenticationScanner()
    endpoint = make_endpoint("/admin/users", method="GET", auth_required=True)

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert any(finding.vulnerability_type == "broken_authentication" for finding in findings)


def test_excessive_data_exposure_detects_password_field() -> None:
    scanner = ExcessiveDataExposureScanner()
    endpoint = make_endpoint("/users", response_schema={"properties": {"password": {"type": "string"}}})

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert len(findings) == 1
    assert findings[0].vulnerability_type == "excessive_data_exposure"


def test_excessive_data_exposure_detects_token_field() -> None:
    scanner = ExcessiveDataExposureScanner()
    endpoint = make_endpoint("/users", response_schema={"properties": {"access_token": {"type": "string"}}})

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert len(findings) == 1


def test_excessive_data_exposure_safe_schema() -> None:
    scanner = ExcessiveDataExposureScanner()
    endpoint = make_endpoint("/users", response_schema={"properties": {"id": {"type": "string"}}})

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert findings == []


def test_security_scanner_pack_registers_and_runs_via_orchestrator() -> None:
    registry = ScannerRegistry()
    registry.register(SecurityMisconfigurationScanner())
    registry.register(BrokenAuthenticationScanner())
    registry.register(ExcessiveDataExposureScanner())
    orchestrator = ScannerOrchestrator(registry)

    endpoint = make_endpoint(
        "/admin/users",
        method="DELETE",
        response_schema={"properties": {"password": {"type": "string"}}},
    )
    scan_request = type(
        "ScanRequest",
        (),
        {"endpoint": endpoint, "scan_configuration": ScanConfiguration(enabled_vulnerabilities={"security_misconfiguration", "broken_authentication", "excessive_data_exposure"})},
    )()

    findings = orchestrator.run(scan_request)

    assert len(findings) >= 3
