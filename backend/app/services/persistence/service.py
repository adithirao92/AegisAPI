"""Persist existing security-analysis outputs without changing analysis logic."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.models.records import (
    AdvisoryRecord,
    CloudRecommendationRecord,
    FindingRecord,
    RiskAssessmentRecord,
    ScanRecord,
)
from app.schemas.advisory import CloudSecurityAdvisory


class PersistenceService:
    """Store and retrieve completed advisory-wrapped scan analysis."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save_scan(
        self,
        target_api_name: str,
        target_api_type: str,
        advisories: Sequence[CloudSecurityAdvisory],
    ) -> ScanRecord:
        """Persist one scan and its complete finding-to-advisory hierarchy."""
        with self._session_factory() as session:
            scan = ScanRecord(
                target_api_name=target_api_name,
                target_api_type=target_api_type,
                total_findings=len(advisories),
            )
            for advisory in advisories:
                self._append_hierarchy(scan, advisory)
            session.add(scan)
            session.commit()
            return scan

    def get_scan(self, scan_id: str) -> ScanRecord | None:
        """Retrieve one scan with all persistence relationships loaded."""
        with self._session_factory() as session:
            return session.scalar(self._query().where(ScanRecord.id == scan_id))

    def list_scans(self) -> list[ScanRecord]:
        """List persisted scans newest first."""
        with self._session_factory() as session:
            return list(session.scalars(self._query().order_by(ScanRecord.scanned_at.desc())))

    def delete_scan(self, scan_id: str) -> bool:
        """Delete a scan and its child records, returning whether it existed."""
        with self._session_factory() as session:
            scan = session.get(ScanRecord, scan_id)
            if scan is None:
                return False
            session.delete(scan)
            session.commit()
            return True

    def _append_hierarchy(self, scan: ScanRecord, advisory: CloudSecurityAdvisory) -> None:
        cloud_risk = advisory.cloud_risk_assessment
        assessment = cloud_risk.risk_assessment
        finding = assessment.finding
        finding_record = FindingRecord(
            vulnerability_type=finding.vulnerability_type,
            severity=finding.severity.value,
            endpoint=(
                finding.affected_endpoint.path
                or finding.affected_endpoint.canonical_path
                or finding.affected_endpoint.name
                or finding.affected_endpoint.id
            ),
            evidence=finding.evidence,
            remediation=finding.remediation,
        )
        risk_record = RiskAssessmentRecord(
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
        )
        finding_record.risk_assessment = risk_record
        scan.findings.append(finding_record)
        risk_record.cloud_recommendations.extend(
            CloudRecommendationRecord(
                provider=item.provider.value,
                service_name=item.service_name,
                recommendation=item.recommendation,
            )
            for item in cloud_risk.recommendations
        )
        risk_record.advisories.extend(
            AdvisoryRecord(
                provider=item.provider.value,
                recommendation=item.recommendation,
                rationale=item.rationale,
                implementation_guidance=item.implementation_guidance,
                expected_security_benefit=item.expected_security_benefit,
            )
            for item in advisory.recommendations
        )

    def _query(self):
        return select(ScanRecord).options(
            selectinload(ScanRecord.findings)
            .selectinload(FindingRecord.risk_assessment)
            .selectinload(RiskAssessmentRecord.cloud_recommendations),
            selectinload(ScanRecord.findings)
            .selectinload(FindingRecord.risk_assessment)
            .selectinload(RiskAssessmentRecord.advisories),
        )
