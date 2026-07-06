from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.models import ScanConfiguration, Severity
from app.services.scanning.orchestrator import ScannerOrchestrator
from app.services.scanning.registry import ScannerRegistry
from app.services.scanning.scanners.mass_assignment import MassAssignmentScanner


def make_endpoint(request_schema: dict[str, object] | None = None) -> NormalizedEndpoint:
    return NormalizedEndpoint(
        id="endpoint:users",
        endpoint_type="rest",
        path="/users",
        method="POST",
        request_schema=request_schema or {},
    )


def test_mass_assignment_scanner_detects_sensitive_field() -> None:
    scanner = MassAssignmentScanner()
    endpoint = make_endpoint({"properties": {"role": {"type": "string"}}})

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert len(findings) == 1
    assert findings[0].vulnerability_type == "mass_assignment"
    assert findings[0].severity == Severity.MEDIUM
    assert "role" in findings[0].evidence["sensitive_fields"]


def test_mass_assignment_scanner_detects_multiple_sensitive_fields() -> None:
    scanner = MassAssignmentScanner()
    endpoint = make_endpoint({"properties": {"role": {"type": "string"}, "is_admin": {"type": "boolean"}}})

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert len(findings) == 1
    assert {"role", "is_admin"}.issubset(set(findings[0].evidence["sensitive_fields"]))


def test_mass_assignment_scanner_ignores_safe_schema() -> None:
    scanner = MassAssignmentScanner()
    endpoint = make_endpoint({"properties": {"name": {"type": "string"}, "email": {"type": "string"}}})

    findings = scanner.scan(type("ScanRequest", (), {"endpoint": endpoint})())

    assert findings == []


def test_mass_assignment_scanner_integration_with_orchestrator() -> None:
    registry = ScannerRegistry()
    registry.register(MassAssignmentScanner())
    orchestrator = ScannerOrchestrator(registry)

    endpoint = make_endpoint({"properties": {"status": {"type": "string"}}})
    scan_request = type(
        "ScanRequest",
        (),
        {"endpoint": endpoint, "scan_configuration": ScanConfiguration(enabled_vulnerabilities={"mass_assignment"})},
    )()

    findings = orchestrator.run(scan_request)

    assert len(findings) == 1
    assert findings[0].vulnerability_type == "mass_assignment"
