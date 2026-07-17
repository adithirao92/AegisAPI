"""Actionable cloud-security advisory schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cloud import CloudRecommendation, CloudRiskAssessment


class SecurityRecommendation(CloudRecommendation):
    """Cloud recommendation enriched with implementation guidance and benefit."""

    implementation_guidance: str = Field(min_length=1)
    expected_security_benefit: str = Field(min_length=1)


class CloudSecurityAdvisory(BaseModel):
    """Actionable advisory generated for one cloud risk assessment."""

    model_config = ConfigDict(extra="forbid")

    cloud_risk_assessment: CloudRiskAssessment
    recommendations: list[SecurityRecommendation] = Field(default_factory=list)
