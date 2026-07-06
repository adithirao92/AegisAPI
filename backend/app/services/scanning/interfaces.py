"""Scanner interfaces for the phase 4 scanning framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.models import ScanFinding, ScanRequest


class BaseScanner(ABC):
    """Base contract for all scanners in the framework."""

    name: str = "base_scanner"

    @abstractmethod
    def scan(self, request: ScanRequest) -> list[ScanFinding]:
        """Execute the scanner against the provided scan request."""
        raise NotImplementedError

    def supports(self, endpoint: NormalizedEndpoint, config: Any | None = None) -> bool:
        """Return True when the scanner is eligible for the endpoint and configuration."""
        return True

    def supported_vulnerabilities(self) -> tuple[str, ...]:
        """Expose the vulnerability classes that this scanner can report."""
        return tuple()
