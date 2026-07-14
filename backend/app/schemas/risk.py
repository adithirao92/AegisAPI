"""Risk assessment and severity scoring schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.services.scanning.models import ScanFinding


class RiskLevel(str, Enum):
    """Normalized risk levels assigned to assessed scanner findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessment(BaseModel):
    """Risk score and level associated with one original scanner finding."""

    model_config = ConfigDict(extra="forbid")

    finding: ScanFinding
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
