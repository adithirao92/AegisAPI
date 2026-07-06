"""Static BOLA / IDOR scanner based on endpoint metadata only."""

from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.interfaces import BaseScanner
from app.services.scanning.models import ScanFinding, ScanRequest, Severity


class BOLAScanner(BaseScanner):
    """Detect potential object-id based authorization issues from endpoint metadata."""

    name = "bola_scanner"

    def __init__(self) -> None:
        self._sensitive_parameter_names = {
            "id",
            "user_id",
            "account_id",
            "customer_id",
            "order_id",
            "profile_id",
        }

    def scan(self, request: ScanRequest) -> list[ScanFinding]:
        """Return a finding when the endpoint exposes object-like identifiers in path or query parameters."""
        endpoint = request.endpoint
        detected_parameters = self._detect_sensitive_parameters(endpoint)
        if not detected_parameters:
            return []

        evidence = {
            "path": endpoint.path,
            "method": endpoint.method,
            "path_parameters": [param for param in detected_parameters if param in self._extract_path_parameters(endpoint)],
            "query_parameters": [param for param in detected_parameters if param in self._extract_query_parameters(endpoint)],
        }

        return [
            ScanFinding(
                vulnerability_type="bola",
                severity=Severity.MEDIUM,
                confidence=0.75,
                evidence=evidence,
                affected_endpoint=endpoint,
                remediation="Review object reference handling and enforce authorization checks for identifier-based access.",
                references=[
                    "https://owasp.org/www-project-api-security/",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html",
                ],
            )
        ]

    def supports(self, endpoint: NormalizedEndpoint, config: object | None = None) -> bool:
        """Return True for REST endpoints that expose identifier-like parameters."""
        return bool(self._detect_sensitive_parameters(endpoint))

    def supported_vulnerabilities(self) -> tuple[str, ...]:
        """Expose the vulnerability type this scanner reports."""
        return ("bola",)

    def _detect_sensitive_parameters(self, endpoint: NormalizedEndpoint) -> set[str]:
        path_parameters = self._extract_path_parameters(endpoint)
        query_parameters = self._extract_query_parameters(endpoint)
        sensitive = set(path_parameters) | set(query_parameters)
        return {
            parameter
            for parameter in sensitive
            if self._looks_like_object_identifier(parameter)
        }

    def _extract_path_parameters(self, endpoint: NormalizedEndpoint) -> set[str]:
        path = endpoint.path or ""
        segments = [segment for segment in path.split("/") if segment.startswith("{") and segment.endswith("}")]
        return {segment[1:-1] for segment in segments}

    def _extract_query_parameters(self, endpoint: NormalizedEndpoint) -> set[str]:
        query_fields: set[str] = set()
        for parameter in endpoint.parameters:
            if parameter.location.lower() == "query":
                query_fields.add(parameter.name)
        return query_fields

    def _looks_like_object_identifier(self, parameter: str) -> bool:
        normalized = parameter.lower().strip()
        return normalized in self._sensitive_parameter_names or normalized.endswith("_id")
