"""Deduplication helpers for scanner findings."""

from __future__ import annotations

from app.services.scanning.models import ScanFinding, Severity


class FindingDeduplicator:
    """Remove duplicate findings and preserve the highest severity instance."""

    def deduplicate(self, findings: list[ScanFinding]) -> list[ScanFinding]:
        """Return unique findings keyed by vulnerability type and endpoint path."""
        grouped: dict[tuple[str, str], ScanFinding] = {}

        for finding in findings:
            endpoint_key = finding.affected_endpoint.path or finding.affected_endpoint.id
            key = (finding.vulnerability_type, endpoint_key)
            existing = grouped.get(key)

            if existing is None:
                grouped[key] = finding
                continue

            grouped[key] = self._pick_preferred(existing, finding)

        return list(grouped.values())

    def _pick_preferred(self, existing: ScanFinding, candidate: ScanFinding) -> ScanFinding:
        if self._severity_rank(candidate.severity) > self._severity_rank(existing.severity):
            return candidate
        if self._severity_rank(candidate.severity) == self._severity_rank(existing.severity):
            if candidate.confidence > existing.confidence:
                return candidate
        return existing

    def _severity_rank(self, severity: Severity) -> int:
        ranking = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFORMATIONAL: 1,
        }
        return ranking[severity]
