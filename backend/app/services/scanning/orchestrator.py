"""Orchestrates scanner execution and aggregates results."""

from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.deduplication import FindingDeduplicator
from app.services.scanning.models import ScanRequest, ScanFinding, ScanConfiguration
from app.services.scanning.registry import ScannerRegistry


class ScannerOrchestrator:
    """Select scanners, run them, aggregate findings, and deduplicate results."""

    def __init__(
        self,
        registry: ScannerRegistry,
        deduplicator: FindingDeduplicator | None = None,
    ) -> None:
        self._registry = registry
        self._deduplicator = deduplicator or FindingDeduplicator()

    def run(self, scan_request: ScanRequest) -> list[ScanFinding]:
        """Execute eligible scanners and return deduplicated findings."""
        scanners = self.select_scanners(scan_request.endpoint, scan_request.scan_configuration)
        findings: list[ScanFinding] = []

        for scanner in scanners:
            findings.extend(scanner.scan(scan_request))

        return self._deduplicator.deduplicate(findings)

    def select_scanners(
        self,
        endpoint: NormalizedEndpoint,
        config: ScanConfiguration | None = None,
    ) -> list[object]:
        """Return scanners eligible for the endpoint and configuration."""
        return self._registry.get_eligible_scanners(endpoint, config)
