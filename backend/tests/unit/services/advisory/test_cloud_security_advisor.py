from __future__ import annotations

import pytest

from app.schemas.api_specification import NormalizedEndpoint
from app.schemas.cloud import CloudProvider, CloudRecommendation, CloudRiskAssessment
from app.schemas.risk import RiskAssessment, RiskLevel
from app.services.advisory import CloudSecurityAdvisor
from app.services.cloud import CloudRiskMapper
from app.services.scanning.models import ScanFinding, Severity


def make_risk_assessment(vulnerability_type: str) -> RiskAssessment:
    return RiskAssessment(
        finding=ScanFinding(
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
        ),
        risk_score=70,
        risk_level=RiskLevel.HIGH,
    )


def make_cloud_assessment(vulnerability_type: str) -> CloudRiskAssessment:
    return CloudRiskMapper().map(make_risk_assessment(vulnerability_type))


def test_advise_generates_actionable_cognito_guidance() -> None:
    cloud_assessment = make_cloud_assessment("broken_authentication")

    advisory = CloudSecurityAdvisor().advise(cloud_assessment)
    cognito = next(
        recommendation
        for recommendation in advisory.recommendations
        if recommendation.provider is CloudProvider.AWS and recommendation.service_name == "Cognito"
    )

    assert advisory.cloud_risk_assessment is cloud_assessment
    assert cognito.recommendation == "Centralize user authentication with Cognito."
    assert cognito.rationale == "Provides managed identity controls for API users."
    assert cognito.implementation_guidance == (
        "Configure Cognito user pools and JWT validation, then integrate API Gateway authorizers."
    )
    assert cognito.expected_security_benefit == "Prevents unauthorized access to protected resources."


@pytest.mark.parametrize(
    ("vulnerability_type", "expected_services"),
    [
        ("security_misconfiguration", {"WAF", "CloudWatch", "Security Hub"}),
        ("excessive_data_exposure", {"Macie", "CloudTrail"}),
        ("bola", {"IAM", "API Gateway Authorizers"}),
        ("mass_assignment", {"API Gateway"}),
    ],
)
def test_advise_generates_templates_for_key_services(
    vulnerability_type: str,
    expected_services: set[str],
) -> None:
    advisory = CloudSecurityAdvisor().advise(make_cloud_assessment(vulnerability_type))
    generated_services = {recommendation.service_name for recommendation in advisory.recommendations}

    assert expected_services <= generated_services
    assert all(recommendation.implementation_guidance for recommendation in advisory.recommendations)
    assert all(recommendation.expected_security_benefit for recommendation in advisory.recommendations)


def test_advise_skips_unsupported_cloud_recommendations() -> None:
    cloud_assessment = CloudRiskAssessment(
        risk_assessment=make_risk_assessment("unknown_vulnerability"),
        recommendations=[
            CloudRecommendation(
                provider=CloudProvider.AWS,
                service_name="Unsupported Service",
                recommendation="Do something.",
                rationale="Testing unsupported mappings.",
            )
        ],
    )

    advisory = CloudSecurityAdvisor().advise(cloud_assessment)

    assert advisory.cloud_risk_assessment is cloud_assessment
    assert advisory.recommendations == []


def test_advise_handles_empty_cloud_recommendations() -> None:
    cloud_assessment = CloudRiskAssessment(risk_assessment=make_risk_assessment("unknown"))

    advisory = CloudSecurityAdvisor().advise(cloud_assessment)

    assert advisory.recommendations == []


def test_advise_all_preserves_input_order_and_wrappers() -> None:
    cloud_assessments = [
        make_cloud_assessment("bola"),
        make_cloud_assessment("excessive_data_exposure"),
    ]

    advisories = CloudSecurityAdvisor().advise_all(cloud_assessments)

    assert [advisory.cloud_risk_assessment for advisory in advisories] == cloud_assessments
