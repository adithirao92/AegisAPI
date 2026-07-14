from __future__ import annotations

import json

from app.schemas.api_specification import NormalizedEndpoint
from app.services.reporting import ReportGenerator
from app.services.scanning.models import ScanFinding, Severity


def make_finding(
    vulnerability_type: str,
    severity: Severity,
    remediation: str,
) -> ScanFinding:
    return ScanFinding(
        vulnerability_type=vulnerability_type,
        severity=severity,
        confidence=0.8,
        evidence={"source": "unit-test"},
        affected_endpoint=NormalizedEndpoint(
            id="endpoint-1",
            endpoint_type="rest",
            path="/users/{id}",
            method="GET",
        ),
        remediation=remediation,
    )


def test_generate_aggregates_findings_and_enriches_them_for_reporting() -> None:
    findings = [
        make_finding("bola", Severity.HIGH, "Enforce object-level authorization."),
        make_finding("bola", Severity.MEDIUM, "Enforce object-level authorization."),
        make_finding("mass_assignment", Severity.LOW, "Allowlist writable fields."),
    ]

    report = ReportGenerator().generate(findings)

    assert report.findings == findings
    assert report.summary.total_findings == 3
    assert report.summary.findings_by_severity == {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 1,
        Severity.LOW: 1,
        Severity.INFORMATIONAL: 0,
    }
    assert report.summary.findings_by_vulnerability_type == {
        "bola": 2,
        "mass_assignment": 1,
    }
    assert report.remediation_recommendations == {
        "bola": ["Enforce object-level authorization."],
        "mass_assignment": ["Allowlist writable fields."],
    }
    assert report.owasp_api_mappings == {
        "bola": "API1:2023 Broken Object Level Authorization",
        "mass_assignment": "API3:2023 Broken Object Property Level Authorization",
    }


def test_generate_handles_an_empty_finding_set() -> None:
    report = ReportGenerator().generate([])

    assert report.summary.total_findings == 0
    assert all(count == 0 for count in report.summary.findings_by_severity.values())
    assert report.summary.findings_by_vulnerability_type == {}
    assert report.findings == []
    assert report.remediation_recommendations == {}
    assert report.owasp_api_mappings == {}


def test_generate_json_returns_a_json_serialization_of_the_report() -> None:
    report_json = ReportGenerator().generate_json(
        [make_finding("broken_authentication", Severity.HIGH, "Require authentication.")]
    )

    payload = json.loads(report_json)

    assert payload["summary"]["total_findings"] == 1
    assert payload["summary"]["findings_by_severity"]["high"] == 1
    assert payload["owasp_api_mappings"] == {
        "broken_authentication": "API2:2023 Broken Authentication"
    }
