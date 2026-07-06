from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint
from app.schemas.auth import AuthenticationContext, AuthenticationType, AuthenticationValidationStatus
from app.services.execution.models import ExecutionRequest, ExecutionResponse, ExecutionStatus
from app.services.scanning.deduplication import FindingDeduplicator
from app.services.scanning.interfaces import BaseScanner
from app.services.scanning.models import ScanConfiguration, ScanFinding, ScanRequest, Severity
from app.services.scanning.orchestrator import ScannerOrchestrator
from app.services.scanning.registry import ScannerRegistry


class StubScanner(BaseScanner):
    def __init__(self, name: str, vulnerabilities: tuple[str, ...]) -> None:
        self.name = name
        self._vulnerabilities = vulnerabilities

    def scan(self, request: ScanRequest) -> list[ScanFinding]:
        return [
            ScanFinding(
                vulnerability_type=self.supported_vulnerabilities()[0],
                severity=Severity.MEDIUM,
                confidence=0.8,
                evidence={"source": self.name},
                affected_endpoint=request.endpoint,
                remediation="Fix it",
                references=["https://example.com/docs"],
            )
        ]

    def supported_vulnerabilities(self) -> tuple[str, ...]:
        return self._vulnerabilities


def make_endpoint() -> NormalizedEndpoint:
    return NormalizedEndpoint(
        id="endpoint-1",
        endpoint_type="rest",
        path="/users/{id}",
        method="GET",
    )


def make_scan_request(endpoint: NormalizedEndpoint) -> ScanRequest:
    return ScanRequest(
        endpoint=endpoint,
        execution_request=ExecutionRequest(
            endpoint_id=endpoint.id,
            method=endpoint.method or "GET",
            url="https://example.com/users/1",
        ),
        execution_response=ExecutionResponse(status=ExecutionStatus.SUCCESS, status_code=200),
        authentication_context=AuthenticationContext(
            endpoint_id=endpoint.id,
            authentication_type=AuthenticationType.BEARER_TOKEN,
            profile_id="profile-1",
            validation_status=AuthenticationValidationStatus.VALID,
            credential_metadata={"token": "abc"},
        ),
        scan_configuration=ScanConfiguration(),
    )


def test_registry_registers_and_returns_eligible_scanners() -> None:
    registry = ScannerRegistry()
    scanner = StubScanner("idor", ("bola",))
    registry.register(scanner)

    endpoint = make_endpoint()
    eligible = registry.get_eligible_scanners(endpoint, ScanConfiguration(enabled_vulnerabilities={"bola"}))

    assert eligible == [scanner]


def test_orchestrator_runs_registered_scanners_and_aggregates_findings() -> None:
    registry = ScannerRegistry()
    registry.register(StubScanner("idor", ("bola",)))
    registry.register(StubScanner("mass-assignment", ("mass_assignment",)))

    orchestrator = ScannerOrchestrator(registry)
    scan_request = make_scan_request(make_endpoint())

    findings = orchestrator.run(scan_request)

    assert len(findings) == 2
    assert {finding.vulnerability_type for finding in findings} == {"bola", "mass_assignment"}


def test_deduplicator_preserves_highest_severity_instance() -> None:
    deduplicator = FindingDeduplicator()
    endpoint = make_endpoint()
    low = ScanFinding(
        vulnerability_type="bola",
        severity=Severity.LOW,
        confidence=0.4,
        evidence={"path": "/users/1"},
        affected_endpoint=endpoint,
        remediation="Low",
        references=["https://example.com/a"],
    )
    high = ScanFinding(
        vulnerability_type="bola",
        severity=Severity.HIGH,
        confidence=0.9,
        evidence={"path": "/users/1"},
        affected_endpoint=endpoint,
        remediation="High",
        references=["https://example.com/b"],
    )

    deduped = deduplicator.deduplicate([low, high])

    assert len(deduped) == 1
    assert deduped[0].severity == Severity.HIGH
    assert deduped[0].remediation == "High"
