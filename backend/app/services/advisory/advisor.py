"""Deterministic actionable guidance for cloud risk recommendations."""

from __future__ import annotations

from typing import Sequence

from app.schemas.advisory import CloudSecurityAdvisory, SecurityRecommendation
from app.schemas.cloud import CloudProvider, CloudRiskAssessment


AdvisoryTemplate = tuple[str, str]

ADVISORY_TEMPLATES: dict[tuple[CloudProvider, str], AdvisoryTemplate] = {
    (
        CloudProvider.AWS,
        "Cognito",
    ): (
        "Configure Cognito user pools and JWT validation, then integrate API Gateway authorizers.",
        "Prevents unauthorized access to protected resources.",
    ),
    (
        CloudProvider.AWS,
        "API Gateway Authorizers",
    ): (
        "Attach JWT, Lambda, or Cognito authorizers to protected API routes and enforce claims.",
        "Blocks unauthenticated or unauthorized requests before they reach backend services.",
    ),
    (
        CloudProvider.AWS,
        "IAM",
    ): (
        "Define least-privilege IAM roles and policies for API workloads and dependent services.",
        "Limits the impact of compromised identities and excessive service permissions.",
    ),
    (
        CloudProvider.AWS,
        "API Gateway",
    ): (
        "Enable request validation and enforce documented request models at the API Gateway stage.",
        "Rejects malformed or unsafe requests before they reach application services.",
    ),
    (
        CloudProvider.AWS,
        "WAF",
    ): (
        "Associate a Web ACL with the API and enable managed rules with application-specific filters.",
        "Filters common malicious traffic and reduces exposure to hostile request patterns.",
    ),
    (
        CloudProvider.AWS,
        "CloudWatch",
    ): (
        "Enable API access logs, define security alarms, and review anomalous request metrics.",
        "Improves timely detection and investigation of security-relevant events.",
    ),
    (
        CloudProvider.AWS,
        "Security Hub",
    ): (
        "Enable Security Hub standards and route prioritized findings to the security team.",
        "Centralizes posture findings and accelerates remediation of cloud configuration gaps.",
    ),
    (
        CloudProvider.AWS,
        "Macie",
    ): (
        "Run Macie discovery jobs for data stores used by the API and review sensitive-data findings.",
        "Improves visibility into sensitive data that could be exposed through API responses.",
    ),
    (
        CloudProvider.AWS,
        "CloudTrail",
    ): (
        "Enable CloudTrail data events for relevant resources and retain logs for investigation.",
        "Provides auditable evidence of sensitive-data access and configuration changes.",
    ),
    (
        CloudProvider.AZURE,
        "Microsoft Entra ID",
    ): (
        "Register the API in Entra ID, require token validation, and assign least-privilege app roles.",
        "Establishes centralized identity controls for API consumers and workloads.",
    ),
    (
        CloudProvider.AZURE,
        "API Management",
    ): (
        "Apply authentication, authorization, and request-validation policies to protected API operations.",
        "Enforces consistent gateway controls before requests reach backend services.",
    ),
    (
        CloudProvider.AZURE,
        "Defender for Cloud",
    ): (
        "Enable Defender for Cloud plans and review prioritized recommendations for API workloads.",
        "Identifies security posture gaps and helps prioritize configuration remediation.",
    ),
    (
        CloudProvider.AZURE,
        "Purview",
    ): (
        "Catalog API-connected data stores and apply sensitivity classifications in Microsoft Purview.",
        "Improves governance and visibility of sensitive data exposed by API workflows.",
    ),
    (
        CloudProvider.GCP,
        "Identity Platform",
    ): (
        "Configure Identity Platform sign-in flows and validate identity tokens in protected API paths.",
        "Prevents unauthenticated use of resources that require verified user identities.",
    ),
    (
        CloudProvider.GCP,
        "API Gateway",
    ): (
        "Configure API Gateway authentication and request validation before routing to backend services.",
        "Enforces gateway-level access and input controls for protected APIs.",
    ),
    (
        CloudProvider.GCP,
        "Security Command Center",
    ): (
        "Enable Security Command Center and review posture findings for API-supporting workloads.",
        "Centralizes cloud security visibility and supports prioritized remediation.",
    ),
    (
        CloudProvider.GCP,
        "Sensitive Data Protection",
    ): (
        "Inspect API-connected data with Sensitive Data Protection and apply de-identification controls.",
        "Reduces the likelihood of exposing sensitive data through API responses.",
    ),
}


class CloudSecurityAdvisor:
    """Convert cloud risk mapping output into actionable security guidance."""

    def advise(self, cloud_risk_assessment: CloudRiskAssessment) -> CloudSecurityAdvisory:
        """Generate supported service advisories for one cloud risk assessment."""
        recommendations: list[SecurityRecommendation] = []

        for cloud_recommendation in cloud_risk_assessment.recommendations:
            template = ADVISORY_TEMPLATES.get(
                (cloud_recommendation.provider, cloud_recommendation.service_name)
            )
            if template is None:
                continue

            implementation_guidance, expected_security_benefit = template
            recommendations.append(
                SecurityRecommendation(
                    provider=cloud_recommendation.provider,
                    service_name=cloud_recommendation.service_name,
                    recommendation=cloud_recommendation.recommendation,
                    rationale=cloud_recommendation.rationale,
                    implementation_guidance=implementation_guidance,
                    expected_security_benefit=expected_security_benefit,
                )
            )

        return CloudSecurityAdvisory(
            cloud_risk_assessment=cloud_risk_assessment,
            recommendations=recommendations,
        )

    def advise_all(
        self,
        cloud_risk_assessments: Sequence[CloudRiskAssessment],
    ) -> list[CloudSecurityAdvisory]:
        """Generate advisories for every cloud risk assessment in original order."""
        return [self.advise(cloud_risk_assessment) for cloud_risk_assessment in cloud_risk_assessments]
