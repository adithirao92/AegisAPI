"""Deterministic risk assessment for normalized scanner findings."""

from __future__ import annotations

from typing import Sequence

from app.schemas.risk import RiskAssessment, RiskLevel
from app.services.scanning.models import ScanFinding, Severity


SEVERITY_SCORES: dict[Severity, int] = {
    Severity.INFORMATIONAL: 0,
    Severity.LOW: 20,
    Severity.MEDIUM: 40,
    Severity.HIGH: 70,
    Severity.CRITICAL: 90,
}
SENSITIVE_ENDPOINT_BONUS = 10
MISSING_AUTHENTICATION_BONUS = 10
EXCESSIVE_DATA_EXPOSURE_BONUS = 10
USER_RESOURCE_BOLA_BONUS = 10
MAX_RISK_SCORE = 100


class RiskAssessmentService:
    """Assign normalized, rule-based risk scores to scanner findings."""

    def assess(self, finding: ScanFinding) -> RiskAssessment:
        """Assess one finding without modifying the scanner output."""
        risk_score = min(MAX_RISK_SCORE, self._calculate_score(finding))
        return RiskAssessment(
            finding=finding,
            risk_score=risk_score,
            risk_level=self.risk_level_for_score(risk_score),
        )

    def assess_all(self, findings: Sequence[ScanFinding]) -> list[RiskAssessment]:
        """Assess every finding from a scan in its original order."""
        return [self.assess(finding) for finding in findings]

    def risk_level_for_score(self, score: int) -> RiskLevel:
        """Map a normalized score to its deterministic risk level."""
        if not 0 <= score <= MAX_RISK_SCORE:
            raise ValueError(f"Risk score must be between 0 and {MAX_RISK_SCORE}.")
        if score <= 24:
            return RiskLevel.LOW
        if score <= 49:
            return RiskLevel.MEDIUM
        if score <= 74:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def _calculate_score(self, finding: ScanFinding) -> int:
        score = SEVERITY_SCORES[finding.severity]
        endpoint = finding.affected_endpoint
        enrichment = endpoint.enrichment
        vulnerability_type = finding.vulnerability_type.strip().lower()

        if enrichment.sensitivity in {"medium", "high"}:
            score += SENSITIVE_ENDPOINT_BONUS
        if not enrichment.auth_required:
            score += MISSING_AUTHENTICATION_BONUS
        if vulnerability_type == "excessive_data_exposure":
            score += EXCESSIVE_DATA_EXPOSURE_BONUS
        if vulnerability_type == "bola" and enrichment.resource_group == "users":
            score += USER_RESOURCE_BOLA_BONUS

        return score
