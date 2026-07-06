"""Registry for scanner discovery and selection."""

from __future__ import annotations

from typing import Any

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.interfaces import BaseScanner
from app.services.scanning.models import ScanConfiguration


class ScannerRegistry:
    """Register and retrieve scanners eligible for a given endpoint."""

    def __init__(self) -> None:
        self._scanners: list[BaseScanner] = []

    def register(self, scanner: BaseScanner) -> None:
        """Register a scanner instance."""
        self._scanners.append(scanner)

    def get_eligible_scanners(
        self,
        endpoint: NormalizedEndpoint,
        config: ScanConfiguration | None = None,
    ) -> list[BaseScanner]:
        """Return scanners that support the endpoint and configuration."""
        active_config = config or ScanConfiguration()
        return [
            scanner
            for scanner in self._scanners
            if scanner.supports(endpoint, active_config)
            and self._matches_enabled_vulnerabilities(scanner, active_config)
        ]

    def _matches_enabled_vulnerabilities(self, scanner: BaseScanner, config: ScanConfiguration) -> bool:
        if not config.enabled_vulnerabilities:
            return True

        scanner_vulns = set(scanner.supported_vulnerabilities())
        return bool(scanner_vulns & config.enabled_vulnerabilities)
