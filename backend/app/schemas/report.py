"""Report generation schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.services.scanning.models import ScanFinding, Severity


class ReportSummary(BaseModel):
    """Aggregated counts for a security scan report."""

    model_config = ConfigDict(extra="forbid")

    total_findings: int = Field(ge=0)
    findings_by_severity: dict[Severity, int]
    findings_by_vulnerability_type: dict[str, int]


class ScanReport(BaseModel):
    """JSON-serializable security report generated from scanner findings."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime
    summary: ReportSummary
    findings: list[ScanFinding]
    remediation_recommendations: dict[str, list[str]]
    owasp_api_mappings: dict[str, str]
