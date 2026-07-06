"""Static excessive data exposure scanner based on response schema metadata."""

from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.interfaces import BaseScanner
from app.services.scanning.models import ScanFinding, ScanRequest, Severity


class ExcessiveDataExposureScanner(BaseScanner):
    """Detect response schema fields that look like sensitive data."""

    name = "excessive_data_exposure_scanner"

    def __init__(self) -> None:
        self._sensitive_field_names = {
            "password",
            "password_hash",
            "secret",
            "token",
            "access_token",
            "refresh_token",
            "api_key",
            "ssn",
            "social_security_number",
            "dob",
            "birth_date",
            "credit_card",
            "card_number",
            "cvv",
        }

    def scan(self, request: ScanRequest) -> list[ScanFinding]:
        endpoint = request.endpoint
        sensitive_fields = self._detect_sensitive_fields(endpoint)
        if not sensitive_fields:
            return []

        return [
            ScanFinding(
                vulnerability_type="excessive_data_exposure",
                severity=Severity.MEDIUM,
                confidence=0.75,
                evidence={"path": endpoint.path, "method": endpoint.method, "sensitive_fields": sorted(sensitive_fields)},
                affected_endpoint=endpoint,
                remediation="Limit response payloads to the minimum required data and avoid returning sensitive fields by default.",
                references=[
                    "https://owasp.org/www-project-api-security/",
                    "https://cheatsheetseries.owasp.org/cheatsheets/REST_Assessment_Cheat_Sheet.html",
                ],
            )
        ]

    def supports(self, endpoint: NormalizedEndpoint, config: object | None = None) -> bool:
        return bool(self._detect_sensitive_fields(endpoint))

    def supported_vulnerabilities(self) -> tuple[str, ...]:
        return ("excessive_data_exposure",)

    def _detect_sensitive_fields(self, endpoint: NormalizedEndpoint) -> set[str]:
        schema = endpoint.response_schema or {}
        if not isinstance(schema, dict):
            return set()

        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return set()

        return {
            field_name
            for field_name in properties.keys()
            if self._looks_sensitive(field_name)
        }

    def _looks_sensitive(self, field_name: str) -> bool:
        normalized = field_name.lower().strip()
        return normalized in self._sensitive_field_names or normalized.endswith("_token") or normalized.endswith("_hash")
