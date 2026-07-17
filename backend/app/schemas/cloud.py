"""Cloud-security advisory schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.risk import RiskAssessment


class CloudProvider(str, Enum):
    """Cloud providers supported by the advisory mapper."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class CloudRecommendation(BaseModel):
    """A deterministic recommendation for one cloud security service."""

    model_config = ConfigDict(extra="forbid")

    provider: CloudProvider
    service_name: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class CloudRiskAssessment(BaseModel):
    """Cloud-security context produced for one risk assessment."""

    model_config = ConfigDict(extra="forbid")

    risk_assessment: RiskAssessment
    recommendations: list[CloudRecommendation] = Field(default_factory=list)
