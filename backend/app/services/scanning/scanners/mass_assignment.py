"""Static mass assignment scanner based on request schema metadata."""

from __future__ import annotations

from typing import Any

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.interfaces import BaseScanner
from app.services.scanning.models import ScanFinding, ScanRequest, Severity


class MassAssignmentScanner(BaseScanner):
    """Detect schema fields that look like sensitive writable properties."""

    name = "mass_assignment_scanner"

    def __init__(self) -> None:
        self._sensitive_field_names = {
            "role",
            "roles",
            "permission",
            "permissions",
            "is_admin",
            "admin",
            "isAdmin",
            "user_type",
            "account_type",
            "credit_limit",
            "balance",
            "salary",
            "status",
            "verified",
            "is_verified",
        }

    def scan(self, request: ScanRequest) -> list[ScanFinding]:
        """Return a finding when the endpoint request schema contains sensitive writable fields."""
        endpoint = request.endpoint
        sensitive_fields = self._detect_sensitive_fields(endpoint)
        if not sensitive_fields:
            return []

        evidence = {
            "path": endpoint.path,
            "method": endpoint.method,
            "sensitive_fields": sorted(sensitive_fields),
        }

        return [
            ScanFinding(
                vulnerability_type="mass_assignment",
                severity=Severity.MEDIUM,
                confidence=0.75,
                evidence=evidence,
                affected_endpoint=endpoint,
                remediation="Restrict writable fields and explicitly allow only safe attributes in request payloads.",
                references=[
                    "https://owasp.org/www-project-top-10/",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html",
                ],
            )
        ]

    def supports(self, endpoint: NormalizedEndpoint, config: object | None = None) -> bool:
        """Return True when the endpoint request schema exposes sensitive writable fields."""
        return bool(self._detect_sensitive_fields(endpoint))

    def supported_vulnerabilities(self) -> tuple[str, ...]:
        """Expose the vulnerability type this scanner reports."""
        return ("mass_assignment",)

    def _detect_sensitive_fields(self, endpoint: NormalizedEndpoint) -> set[str]:
        schema = endpoint.request_schema or {}
        if not isinstance(schema, dict):
            return set()

        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return set()

        candidates = set(properties.keys())
        return {
            field_name
            for field_name in candidates
            if self._looks_sensitive(field_name)
        }

    def _looks_sensitive(self, field_name: str) -> bool:
        normalized = field_name.lower().strip()
        return normalized in self._sensitive_field_names or normalized.startswith("is_")
