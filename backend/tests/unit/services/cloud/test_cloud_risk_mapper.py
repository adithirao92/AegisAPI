from __future__ import annotations

import pytest

from app.schemas.api_specification import NormalizedEndpoint
from app.schemas.cloud import CloudProvider
from app.schemas.risk import RiskAssessment, RiskLevel
from app.services.cloud import CloudRiskMapper
from app.services.scanning.models import ScanFinding, Severity


def make_assessment(vulnerability_type: str) -> RiskAssessment:
    finding = ScanFinding(
        vulnerability_type=vulnerability_type,
        severity=Severity.HIGH,
        confidence=0.8,
        evidence={},
        affected_endpoint=NormalizedEndpoint(
            id="endpoint-1",
            endpoint_type="rest",
            path="/users/{id}",
            method="GET",
        ),
        remediation="Fix the issue.",
    )
    return RiskAssessment(finding=finding, risk_score=70, risk_level=RiskLevel.HIGH)


@pytest.mark.parametrize(
    ("vulnerability_type", "expected_services"),
    [
        (
            "broken_authentication",
            {
                CloudProvider.AWS: {"Cognito", "API Gateway Authorizers", "IAM"},
                CloudProvider.AZURE: {"Microsoft Entra ID", "API Management"},
                CloudProvider.GCP: {"Identity Platform", "API Gateway"},
            },
        ),
        (
            "security_misconfiguration",
            {
                CloudProvider.AWS: {"WAF", "CloudWatch", "Security Hub"},
                CloudProvider.AZURE: {"Defender for Cloud"},
                CloudProvider.GCP: {"Security Command Center"},
            },
        ),
        (
            "excessive_data_exposure",
            {
                CloudProvider.AWS: {"Macie", "CloudTrail"},
                CloudProvider.AZURE: {"Purview"},
                CloudProvider.GCP: {"Sensitive Data Protection"},
            },
        ),
    ],
)
def test_map_returns_the_required_provider_recommendations(
    vulnerability_type: str,
    expected_services: dict[CloudProvider, set[str]],
) -> None:
    assessment = make_assessment(vulnerability_type)

    cloud_assessment = CloudRiskMapper().map(assessment)

    assert cloud_assessment.risk_assessment is assessment
    assert {
        provider: {
            recommendation.service_name
            for recommendation in cloud_assessment.recommendations
            if recommendation.provider is provider
        }
        for provider in CloudProvider
    } == expected_services
    assert all(recommendation.recommendation for recommendation in cloud_assessment.recommendations)
    assert all(recommendation.rationale for recommendation in cloud_assessment.recommendations)


@pytest.mark.parametrize("vulnerability_type", ["bola", "mass_assignment"])
def test_map_returns_cross_provider_guidance_for_remaining_scanner_types(
    vulnerability_type: str,
) -> None:
    cloud_assessment = CloudRiskMapper().map(make_assessment(vulnerability_type))

    assert {recommendation.provider for recommendation in cloud_assessment.recommendations} == set(CloudProvider)


def test_map_is_case_insensitive_and_returns_no_guidance_for_unknown_types() -> None:
    mapper = CloudRiskMapper()

    known = mapper.map(make_assessment("  BOLA  "))
    unknown = mapper.map(make_assessment("unknown_vulnerability"))

    assert known.recommendations
    assert unknown.recommendations == []


def test_map_returns_independent_recommendation_models() -> None:
    mapper = CloudRiskMapper()

    first = mapper.map(make_assessment("broken_authentication"))
    second = mapper.map(make_assessment("broken_authentication"))
    first.recommendations[0].service_name = "Changed"

    assert second.recommendations[0].service_name == "Cognito"


def test_map_all_preserves_input_order() -> None:
    assessments = [make_assessment("bola"), make_assessment("security_misconfiguration")]

    cloud_assessments = CloudRiskMapper().map_all(assessments)

    assert [assessment.risk_assessment for assessment in cloud_assessments] == assessments
