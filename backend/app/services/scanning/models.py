"""Core models for the scanning framework."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.api_specification import NormalizedEndpoint
from app.schemas.auth import AuthenticationContext
from app.services.execution.models import ExecutionRequest, ExecutionResponse


class Severity(str, Enum):
    """Supported severity levels for normalized findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ScanConfiguration(BaseModel):
    """Configuration options for orchestration and scanner execution."""

    model_config = ConfigDict(extra="forbid")

    enabled_vulnerabilities: set[str] = Field(default_factory=set)
    max_depth: int = Field(default=1, ge=1)
    timeout: float = Field(default=30.0, gt=0.0)
    use_authentication: bool = True
    allow_ai_execution: bool = False


class ScanRequest(BaseModel):
    """Input context passed to scanners during a scan run."""

    model_config = ConfigDict(extra="forbid")

    endpoint: NormalizedEndpoint
    execution_request: ExecutionRequest
    execution_response: ExecutionResponse
    authentication_context: AuthenticationContext | None = None
    scan_configuration: ScanConfiguration = Field(default_factory=ScanConfiguration)


class ScanFinding(BaseModel):
    """Normalized finding emitted by a scanner."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str | None = None
    vulnerability_type: str
    severity: Severity = Severity.MEDIUM
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: dict[str, Any] = Field(default_factory=dict)
    affected_endpoint: NormalizedEndpoint
    remediation: str = "Review the affected endpoint and apply a remediation"
    references: list[str] = Field(default_factory=list)
