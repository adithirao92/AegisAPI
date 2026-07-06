"""Phase 4 scanning framework foundation."""

from app.services.scanning.deduplication import FindingDeduplicator
from app.services.scanning.interfaces import BaseScanner
from app.services.scanning.models import ScanConfiguration, ScanFinding, ScanRequest, Severity
from app.services.scanning.orchestrator import ScannerOrchestrator
from app.services.scanning.registry import ScannerRegistry
from app.services.scanning.scanners.bola import BOLAScanner
from app.services.scanning.scanners.broken_authentication import BrokenAuthenticationScanner
from app.services.scanning.scanners.excessive_data_exposure import ExcessiveDataExposureScanner
from app.services.scanning.scanners.mass_assignment import MassAssignmentScanner
from app.services.scanning.scanners.security_misconfiguration import SecurityMisconfigurationScanner

__all__ = [
    "BaseScanner",
    "ScannerRegistry",
    "ScannerOrchestrator",
    "FindingDeduplicator",
    "ScanRequest",
    "ScanFinding",
    "ScanConfiguration",
    "Severity",
]
