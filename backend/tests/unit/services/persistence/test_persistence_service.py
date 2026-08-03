from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import create_database_engine, create_session_factory, initialize_database
from app.models.records import (
    AdvisoryRecord,
    CloudRecommendationRecord,
    FindingRecord,
    RiskAssessmentRecord,
)
from app.schemas.api_specification import NormalizedEndpoint
from app.schemas.risk import RiskAssessment, RiskLevel
from app.services.advisory import CloudSecurityAdvisor
from app.services.cloud import CloudRiskMapper
from app.services.persistence import PersistenceService
from app.services.scanning.models import ScanFinding, Severity


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    initialize_database(engine)
    yield create_session_factory(engine)
    engine.dispose()


@pytest.fixture
def service(session_factory: sessionmaker[Session]) -> PersistenceService:
    return PersistenceService(session_factory)


def make_advisory(vulnerability_type: str = "broken_authentication"):
    finding = ScanFinding(
        vulnerability_type=vulnerability_type,
        severity=Severity.HIGH,
        confidence=0.8,
        evidence={"path": "/users/{id}", "status_code": 200},
        affected_endpoint=NormalizedEndpoint(
            id="endpoint-1",
            endpoint_type="rest",
            path="/users/{id}",
            method="GET",
        ),
        remediation="Require authentication.",
    )
    assessment = RiskAssessment(finding=finding, risk_score=80, risk_level=RiskLevel.CRITICAL)
    return CloudSecurityAdvisor().advise(CloudRiskMapper().map(assessment))


def test_save_and_retrieve_scan_with_complete_relationships(service: PersistenceService) -> None:
    saved = service.save_scan("Customer API", "rest", [make_advisory()])

    retrieved = service.get_scan(saved.id)

    assert retrieved is not None
    assert retrieved.target_api_name == "Customer API"
    assert retrieved.target_api_type == "rest"
    assert retrieved.total_findings == 1
    assert len(retrieved.findings) == 1
    finding = retrieved.findings[0]
    assert finding.vulnerability_type == "broken_authentication"
    assert finding.severity == "high"
    assert finding.endpoint == "/users/{id}"
    assert finding.evidence == {"path": "/users/{id}", "status_code": 200}
    assert finding.remediation == "Require authentication."
    assert finding.risk_assessment is not None
    assert finding.risk_assessment.risk_score == 80
    assert finding.risk_assessment.risk_level == "critical"
    assert len(finding.risk_assessment.cloud_recommendations) == 7
    assert len(finding.risk_assessment.advisories) == 7


def test_list_scans_returns_all_saved_scans(service: PersistenceService) -> None:
    first = service.save_scan("First API", "rest", [make_advisory("bola")])
    second = service.save_scan("Second API", "graphql", [make_advisory("mass_assignment")])

    scans = service.list_scans()

    assert {scan.id for scan in scans} == {first.id, second.id}
    assert {scan.target_api_name for scan in scans} == {"First API", "Second API"}


def test_delete_scan_removes_the_full_relationship_hierarchy(
    service: PersistenceService,
    session_factory: sessionmaker[Session],
) -> None:
    saved = service.save_scan("Customer API", "rest", [make_advisory()])

    assert service.delete_scan(saved.id) is True
    assert service.get_scan(saved.id) is None
    assert service.delete_scan(saved.id) is False

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(FindingRecord)) == 0
        assert session.scalar(select(func.count()).select_from(RiskAssessmentRecord)) == 0
        assert session.scalar(select(func.count()).select_from(CloudRecommendationRecord)) == 0
        assert session.scalar(select(func.count()).select_from(AdvisoryRecord)) == 0


def test_save_scan_persists_one_hierarchy_per_advisory(service: PersistenceService) -> None:
    saved = service.save_scan(
        "Customer API",
        "rest",
        [make_advisory("bola"), make_advisory("excessive_data_exposure")],
    )

    retrieved = service.get_scan(saved.id)

    assert retrieved is not None
    assert retrieved.total_findings == 2
    assert [finding.vulnerability_type for finding in retrieved.findings] == [
        "bola",
        "excessive_data_exposure",
    ]
    assert all(finding.risk_assessment is not None for finding in retrieved.findings)
