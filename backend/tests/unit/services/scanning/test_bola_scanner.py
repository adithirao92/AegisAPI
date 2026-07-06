from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint, ParameterDefinition
from app.services.scanning.models import ScanConfiguration, Severity
from app.services.scanning.orchestrator import ScannerOrchestrator
from app.services.scanning.registry import ScannerRegistry
from app.services.scanning.scanners.bola import BOLAScanner


def make_endpoint(path: str, parameters: list[ParameterDefinition] | None = None) -> NormalizedEndpoint:
    return NormalizedEndpoint(
        id=f"endpoint:{path}",
        endpoint_type="rest",
        path=path,
        method="GET",
        parameters=parameters or [],
    )


def test_bola_scanner_detects_path_parameter() -> None:
    scanner = BOLAScanner()
    endpoint = make_endpoint("/users/{user_id}")

    findings = scanner.scan(
        type(
            "ScanRequest",
            (),
            {"endpoint": endpoint},
        )()
    )

    assert len(findings) == 1
    assert findings[0].vulnerability_type == "bola"
    assert findings[0].severity == Severity.MEDIUM
    assert "user_id" in findings[0].evidence["path_parameters"]


def test_bola_scanner_detects_query_parameter() -> None:
    scanner = BOLAScanner()
    endpoint = make_endpoint(
        "/accounts",
        [ParameterDefinition(name="account_id", location="query", required=False)],
    )

    findings = scanner.scan(
        type(
            "ScanRequest",
            (),
            {"endpoint": endpoint},
        )()
    )

    assert len(findings) == 1
    assert "account_id" in findings[0].evidence["query_parameters"]


def test_bola_scanner_ignores_non_sensitive_endpoint() -> None:
    scanner = BOLAScanner()
    endpoint = make_endpoint("/health", [ParameterDefinition(name="status", location="query", required=False)])

    findings = scanner.scan(
        type(
            "ScanRequest",
            (),
            {"endpoint": endpoint},
        )()
    )

    assert findings == []


def test_bola_scanner_integrates_with_registry_and_orchestrator() -> None:
    registry = ScannerRegistry()
    registry.register(BOLAScanner())
    orchestrator = ScannerOrchestrator(registry)

    endpoint = make_endpoint("/orders/{order_id}")
    scan_request = type(
        "ScanRequest",
        (),
        {"endpoint": endpoint, "scan_configuration": ScanConfiguration(enabled_vulnerabilities={"bola"})},
    )()

    findings = orchestrator.run(scan_request)

    assert len(findings) == 1
    assert findings[0].vulnerability_type == "bola"
