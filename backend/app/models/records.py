"""SQLAlchemy persistence records for security analysis history."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for the Phase 9 persistence records."""


class RecordMixin:
    """Portable UUID identity and UTC creation time for records."""

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class ScanRecord(RecordMixin, Base):
    """A persisted security scan."""

    __tablename__ = "scan_records"

    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    target_api_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_api_type: Mapped[str] = mapped_column(String(64), nullable=False)
    total_findings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    findings: Mapped[list[FindingRecord]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )


class FindingRecord(RecordMixin, Base):
    """A scanner finding stored under one scan."""

    __tablename__ = "finding_records"

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("scan_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vulnerability_type: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(2048), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    remediation: Mapped[str] = mapped_column(Text, nullable=False)
    scan: Mapped[ScanRecord] = relationship(back_populates="findings")
    risk_assessment: Mapped[RiskAssessmentRecord | None] = relationship(
        back_populates="finding", cascade="all, delete-orphan", uselist=False
    )


class RiskAssessmentRecord(RecordMixin, Base):
    """A normalized risk assessment stored for exactly one finding."""

    __tablename__ = "risk_assessment_records"

    finding_id: Mapped[str] = mapped_column(
        ForeignKey("finding_records.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    finding: Mapped[FindingRecord] = relationship(back_populates="risk_assessment")
    cloud_recommendations: Mapped[list[CloudRecommendationRecord]] = relationship(
        back_populates="risk_assessment", cascade="all, delete-orphan", passive_deletes=True
    )
    advisories: Mapped[list[AdvisoryRecord]] = relationship(
        back_populates="risk_assessment", cascade="all, delete-orphan", passive_deletes=True
    )


class CloudRecommendationRecord(RecordMixin, Base):
    """Cloud mapper recommendation stored for a risk assessment."""

    __tablename__ = "cloud_recommendation_records"

    risk_assessment_id: Mapped[str] = mapped_column(
        ForeignKey("risk_assessment_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    risk_assessment: Mapped[RiskAssessmentRecord] = relationship(
        back_populates="cloud_recommendations"
    )


class AdvisoryRecord(RecordMixin, Base):
    """Actionable cloud advisory stored for a risk assessment."""

    __tablename__ = "advisory_records"

    risk_assessment_id: Mapped[str] = mapped_column(
        ForeignKey("risk_assessment_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    implementation_guidance: Mapped[str] = mapped_column(Text, nullable=False)
    expected_security_benefit: Mapped[str] = mapped_column(Text, nullable=False)
    risk_assessment: Mapped[RiskAssessmentRecord] = relationship(back_populates="advisories")
