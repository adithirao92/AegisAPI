"""Deterministic cloud-security recommendations for risk assessments."""

from __future__ import annotations

from typing import Sequence

from app.schemas.cloud import CloudProvider, CloudRecommendation, CloudRiskAssessment
from app.schemas.risk import RiskAssessment


def _recommendation(
    provider: CloudProvider,
    service_name: str,
    recommendation: str,
    rationale: str,
) -> CloudRecommendation:
    return CloudRecommendation(
        provider=provider,
        service_name=service_name,
        recommendation=recommendation,
        rationale=rationale,
    )


CLOUD_RECOMMENDATIONS: dict[str, tuple[CloudRecommendation, ...]] = {
    "broken_authentication": (
        _recommendation(CloudProvider.AWS, "Cognito", "Centralize user authentication with Cognito.", "Provides managed identity controls for API users."),
        _recommendation(CloudProvider.AWS, "API Gateway Authorizers", "Protect API routes with authorizers.", "Enforces authentication before requests reach backend services."),
        _recommendation(CloudProvider.AWS, "IAM", "Apply least-privilege IAM policies.", "Limits access to cloud resources after authentication."),
        _recommendation(CloudProvider.AZURE, "Microsoft Entra ID", "Use Entra ID for centralized authentication.", "Provides managed identity and access controls."),
        _recommendation(CloudProvider.AZURE, "API Management", "Configure API Management authentication policies.", "Enforces authentication at the API gateway."),
        _recommendation(CloudProvider.GCP, "Identity Platform", "Use Identity Platform for application authentication.", "Provides managed identity services for API consumers."),
        _recommendation(CloudProvider.GCP, "API Gateway", "Require authentication at API Gateway.", "Blocks unauthenticated requests before they reach workloads."),
    ),
    "security_misconfiguration": (
        _recommendation(CloudProvider.AWS, "WAF", "Deploy WAF protections for exposed APIs.", "Filters common malicious traffic and request patterns."),
        _recommendation(CloudProvider.AWS, "CloudWatch", "Monitor API and infrastructure security events.", "Improves detection of configuration-related failures."),
        _recommendation(CloudProvider.AWS, "Security Hub", "Aggregate and review security posture findings.", "Highlights configuration gaps across AWS services."),
        _recommendation(CloudProvider.AZURE, "Defender for Cloud", "Enable Defender for Cloud recommendations.", "Identifies and prioritizes cloud configuration weaknesses."),
        _recommendation(CloudProvider.GCP, "Security Command Center", "Enable Security Command Center posture findings.", "Provides centralized visibility into configuration risks."),
    ),
    "excessive_data_exposure": (
        _recommendation(CloudProvider.AWS, "Macie", "Use Macie to discover sensitive data exposure.", "Identifies sensitive data stored in AWS data services."),
        _recommendation(CloudProvider.AWS, "CloudTrail", "Audit access to sensitive API data with CloudTrail.", "Provides an audit trail for data-access investigations."),
        _recommendation(CloudProvider.AZURE, "Purview", "Classify and govern sensitive data with Purview.", "Improves visibility and protection of exposed data."),
        _recommendation(CloudProvider.GCP, "Sensitive Data Protection", "Inspect and classify sensitive data.", "Detects sensitive content that should not be exposed by APIs."),
    ),
    "bola": (
        _recommendation(CloudProvider.AWS, "API Gateway Authorizers", "Enforce object-level authorization in gateway authorizers.", "Helps validate caller access before backend object retrieval."),
        _recommendation(CloudProvider.AWS, "IAM", "Restrict service access with least-privilege IAM policies.", "Limits backend permissions available to API workloads."),
        _recommendation(CloudProvider.AZURE, "API Management", "Apply authorization policies at API Management.", "Adds a gateway control point for protected resources."),
        _recommendation(CloudProvider.AZURE, "Microsoft Entra ID", "Use Entra ID roles and claims for authorization.", "Supplies identity context for object-level access decisions."),
        _recommendation(CloudProvider.GCP, "API Gateway", "Enforce authenticated access at API Gateway.", "Provides a gateway layer for access controls."),
        _recommendation(CloudProvider.GCP, "Identity Platform", "Use identity claims in authorization checks.", "Supplies verified user context for resource ownership checks."),
    ),
    "mass_assignment": (
        _recommendation(CloudProvider.AWS, "API Gateway", "Validate request models and allowlisted fields at the gateway.", "Reduces exposure of unsafe writable attributes."),
        _recommendation(CloudProvider.AWS, "WAF", "Add WAF rules for suspicious request payloads.", "Provides an additional edge control for malicious inputs."),
        _recommendation(CloudProvider.AZURE, "API Management", "Apply request validation policies in API Management.", "Rejects requests that violate approved API contracts."),
        _recommendation(CloudProvider.AZURE, "Defender for Cloud", "Review API workload security recommendations.", "Helps identify cloud workload configuration gaps."),
        _recommendation(CloudProvider.GCP, "API Gateway", "Enforce API schema validation before backend routing.", "Reduces unvalidated writes reaching application services."),
        _recommendation(CloudProvider.GCP, "Security Command Center", "Review workload posture findings.", "Provides centralized visibility into supporting security gaps."),
    ),
}


class CloudRiskMapper:
    """Map risk assessments to static, provider-specific security guidance."""

    def map(self, risk_assessment: RiskAssessment) -> CloudRiskAssessment:
        """Return advisory cloud recommendations for one risk assessment."""
        vulnerability_type = risk_assessment.finding.vulnerability_type.strip().lower()
        recommendations = [
            recommendation.model_copy(deep=True)
            for recommendation in CLOUD_RECOMMENDATIONS.get(vulnerability_type, ())
        ]
        return CloudRiskAssessment(
            risk_assessment=risk_assessment,
            recommendations=recommendations,
        )

    def map_all(self, risk_assessments: Sequence[RiskAssessment]) -> list[CloudRiskAssessment]:
        """Map every risk assessment in its original order."""
        return [self.map(risk_assessment) for risk_assessment in risk_assessments]
