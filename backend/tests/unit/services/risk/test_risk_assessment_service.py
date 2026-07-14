from __future__ import annotations

import pytest

from app.schemas.api_specification import EndpointEnrichmentMetadata, NormalizedEndpoint
from app.schemas.risk import RiskLevel
from app.services.risk import RiskAssessmentService
from app.services.scanning.models import ScanFinding, Severity


def make_finding(
    *,
    severity: Severity = Severity.INFORMATIONAL,
    vulnerability_type: str = "other",
    sensitivity: str = "low",
    auth_required: bool = True,
    resource_group: str | None = "generic",
) -> ScanFinding:
    return ScanFinding(
        vulnerability_type=vulnerability_type,
        severity=severity,
        confidence=0.8,
        evidence={},
        affected_endpoint=NormalizedEndpoint(
            id="endpoint-1",
            endpoint_type="rest",
            path="/items",
            method="GET",
            enrichment=EndpointEnrichmentMetadata(
                sensitivity=sensitivity,  # type: ignore[arg-type]
                auth_required=auth_required,
                resource_group=resource_group,
            ),
        ),
        remediation="Fix the issue.",
    )


@pytest.mark.parametrize(
    ("severity", "expected_score"),
    [
        (Severity.INFORMATIONAL, 0),
        (Severity.LOW, 20),
        (Severity.MEDIUM, 40),
        (Severity.HIGH, 70),
        (Severity.CRITICAL, 90),
    ],
)
def test_assess_uses_the_shared_severity_scores(severity: Severity, expected_score: int) -> None:
    assessment = RiskAssessmentService().assess(make_finding(severity=severity))

    assert assessment.risk_score == expected_score
    assert assessment.finding.severity is severity


def test_assess_applies_each_contextual_bonus() -> None:
    service = RiskAssessmentService()

    assert service.assess(make_finding(sensitivity="medium")).risk_score == 10
    assert service.assess(make_finding(auth_required=False)).risk_score == 10
    assert service.assess(make_finding(vulnerability_type="excessive_data_exposure")).risk_score == 10
    assert service.assess(make_finding(vulnerability_type="bola", resource_group="users")).risk_score == 10


def test_assess_caps_the_score_at_one_hundred() -> None:
    finding = make_finding(
        severity=Severity.CRITICAL,
        vulnerability_type="bola",
        sensitivity="high",
        auth_required=False,
        resource_group="users",
    )

    assessment = RiskAssessmentService().assess(finding)

    assert assessment.risk_score == 100
    assert assessment.risk_level is RiskLevel.CRITICAL
    assert assessment.finding is finding


@pytest.mark.parametrize(
    ("score", "expected_level"),
    [
        (0, RiskLevel.LOW),
        (24, RiskLevel.LOW),
        (25, RiskLevel.MEDIUM),
        (49, RiskLevel.MEDIUM),
        (50, RiskLevel.HIGH),
        (74, RiskLevel.HIGH),
        (75, RiskLevel.CRITICAL),
        (100, RiskLevel.CRITICAL),
    ],
)
def test_risk_level_for_score_handles_all_boundaries(score: int, expected_level: RiskLevel) -> None:
    assert RiskAssessmentService().risk_level_for_score(score) is expected_level


@pytest.mark.parametrize("score", [-1, 101])
def test_risk_level_for_score_rejects_scores_outside_the_normalized_range(score: int) -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        RiskAssessmentService().risk_level_for_score(score)


def test_assess_all_preserves_finding_order() -> None:
    findings = [
        make_finding(severity=Severity.LOW),
        make_finding(severity=Severity.HIGH, vulnerability_type="bola", resource_group="users"),
    ]

    assessments = RiskAssessmentService().assess_all(findings)

    assert [assessment.finding for assessment in assessments] == findings
    assert [assessment.risk_score for assessment in assessments] == [20, 80]
