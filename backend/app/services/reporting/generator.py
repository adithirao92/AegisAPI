"""Generate structured security reports from normalized scan findings."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Sequence

from app.schemas.report import ReportSummary, ScanReport
from app.services.scanning.models import ScanFinding, Severity


class ReportGenerator:
    """Aggregate Phase 4 scanner findings into an in-memory JSON report."""

    _OWASP_API_MAPPINGS = {
        "bola": "API1:2023 Broken Object Level Authorization",
        "broken_authentication": "API2:2023 Broken Authentication",
        "mass_assignment": "API3:2023 Broken Object Property Level Authorization",
        "excessive_data_exposure": "API3:2023 Broken Object Property Level Authorization",
        "security_misconfiguration": "API8:2023 Security Misconfiguration",
    }

    def generate(self, findings: Sequence[ScanFinding]) -> ScanReport:
        """Build a structured report from normalized, deduplicated findings."""
        report_findings = list(findings)
        severity_counts = Counter(finding.severity for finding in report_findings)
        vulnerability_counts = Counter(finding.vulnerability_type for finding in report_findings)
        remediations: defaultdict[str, set[str]] = defaultdict(set)

        for finding in report_findings:
            remediations[finding.vulnerability_type].add(finding.remediation)

        summary = ReportSummary(
            total_findings=len(report_findings),
            findings_by_severity={severity: severity_counts[severity] for severity in Severity},
            findings_by_vulnerability_type=dict(sorted(vulnerability_counts.items())),
        )
        vulnerability_types = sorted(vulnerability_counts)

        return ScanReport(
            generated_at=datetime.now(UTC),
            summary=summary,
            findings=report_findings,
            remediation_recommendations={
                vulnerability_type: sorted(remediations[vulnerability_type])
                for vulnerability_type in vulnerability_types
            },
            owasp_api_mappings={
                vulnerability_type: self._OWASP_API_MAPPINGS[vulnerability_type]
                for vulnerability_type in vulnerability_types
                if vulnerability_type in self._OWASP_API_MAPPINGS
            },
        )

    def generate_json(self, findings: Sequence[ScanFinding]) -> str:
        """Generate a JSON representation of a structured security report."""
        return self.generate(findings).model_dump_json()
