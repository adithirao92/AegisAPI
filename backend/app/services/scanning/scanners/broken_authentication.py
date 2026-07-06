"""Static broken authentication scanner based on endpoint security metadata."""

from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.interfaces import BaseScanner
from app.services.scanning.models import ScanFinding, ScanRequest, Severity


class BrokenAuthenticationScanner(BaseScanner):
    """Detect endpoints that appear to be unauthenticated or inconsistently configured."""

    name = "broken_authentication_scanner"

    def scan(self, request: ScanRequest) -> list[ScanFinding]:
        endpoint = request.endpoint
        findings: list[ScanFinding] = []

        if self._has_sensitive_endpoint_without_auth(endpoint):
            findings.append(
                self._build_finding(
                    endpoint,
                    "Sensitive endpoint without authentication",
                    "The endpoint is sensitive but lacks authentication requirements.",
                    {"path": endpoint.path, "method": endpoint.method, "security_schemes": endpoint.security_schemes},
                )
            )

        if self._has_missing_auth_metadata(endpoint):
            findings.append(
                self._build_finding(
                    endpoint,
                    "Missing authentication metadata",
                    "No explicit authentication metadata is defined for the endpoint.",
                    {"path": endpoint.path, "method": endpoint.method},
                )
            )

        if self._has_inconsistent_auth_configuration(endpoint):
            findings.append(
                self._build_finding(
                    endpoint,
                    "Inconsistent authentication configuration",
                    "The endpoint security configuration appears inconsistent or incomplete.",
                    {"path": endpoint.path, "method": endpoint.method, "auth_required": getattr(endpoint.enrichment, "auth_required", False)},
                )
            )

        return findings

    def supports(self, endpoint: NormalizedEndpoint, config: object | None = None) -> bool:
        return bool(self._has_sensitive_endpoint_without_auth(endpoint) or self._has_missing_auth_metadata(endpoint) or self._has_inconsistent_auth_configuration(endpoint))

    def supported_vulnerabilities(self) -> tuple[str, ...]:
        return ("broken_authentication",)

    def _has_sensitive_endpoint_without_auth(self, endpoint: NormalizedEndpoint) -> bool:
        path = (endpoint.path or "").lower()
        sensitive_path = any(marker in path for marker in ["admin", "user", "account", "profile"])
        auth_required = getattr(endpoint.enrichment, "auth_required", False)
        return sensitive_path and not auth_required

    def _has_missing_auth_metadata(self, endpoint: NormalizedEndpoint) -> bool:
        return not endpoint.security_schemes and not getattr(endpoint.enrichment, "auth_required", False)

    def _has_inconsistent_auth_configuration(self, endpoint: NormalizedEndpoint) -> bool:
        auth_required = getattr(endpoint.enrichment, "auth_required", False)
        security_schemes = endpoint.security_schemes or []
        return auth_required and not security_schemes

    def _build_finding(self, endpoint: NormalizedEndpoint, title: str, description: str, evidence: dict[str, object]) -> ScanFinding:
        return ScanFinding(
            vulnerability_type="broken_authentication",
            severity=Severity.HIGH,
            confidence=0.8,
            evidence={"title": title, **evidence},
            affected_endpoint=endpoint,
            remediation="Require authentication for sensitive endpoints and define explicit security schemes.",
            references=[
                "https://owasp.org/www-project-top-10/",
                "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
            ],
        )
