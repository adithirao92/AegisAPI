"""Static security misconfiguration scanner based on endpoint metadata."""

from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint
from app.services.scanning.interfaces import BaseScanner
from app.services.scanning.models import ScanFinding, ScanRequest, Severity


class SecurityMisconfigurationScanner(BaseScanner):
    """Detect obvious security misconfiguration issues from endpoint metadata."""

    name = "security_misconfiguration_scanner"

    def __init__(self) -> None:
        self._dangerous_methods = {"DELETE", "PUT", "PATCH"}

    def scan(self, request: ScanRequest) -> list[ScanFinding]:
        endpoint = request.endpoint
        findings: list[ScanFinding] = []

        if self._is_insecure_http(endpoint):
            findings.append(
                self._build_finding(
                    endpoint,
                    "Insecure HTTP endpoint",
                    "The endpoint is exposed over HTTP instead of HTTPS.",
                    {"path": endpoint.path, "method": endpoint.method, "scheme": "http"},
                )
            )

        if self._has_dangerous_unauthenticated_method(endpoint):
            findings.append(
                self._build_finding(
                    endpoint,
                    "Dangerous method without authentication",
                    "A state-changing method is exposed without authentication requirements.",
                    {"path": endpoint.path, "method": endpoint.method, "auth_required": False},
                )
            )

        if self._has_missing_security_requirements(endpoint):
            findings.append(
                self._build_finding(
                    endpoint,
                    "Missing security requirements on sensitive endpoint",
                    "The endpoint lacks explicit security requirements despite being sensitive.",
                    {"path": endpoint.path, "method": endpoint.method, "security_schemes": endpoint.security_schemes},
                )
            )

        return findings

    def supports(self, endpoint: NormalizedEndpoint, config: object | None = None) -> bool:
        return bool(self._is_insecure_http(endpoint) or self._has_dangerous_unauthenticated_method(endpoint) or self._has_missing_security_requirements(endpoint))

    def supported_vulnerabilities(self) -> tuple[str, ...]:
        return ("security_misconfiguration",)

    def _is_insecure_http(self, endpoint: NormalizedEndpoint) -> bool:
        path = endpoint.path or ""
        return path.startswith("http://") or endpoint.path is not None and endpoint.path.startswith("http://")

    def _has_dangerous_unauthenticated_method(self, endpoint: NormalizedEndpoint) -> bool:
        method = (endpoint.method or "").upper()
        auth_required = getattr(endpoint.enrichment, "auth_required", False)
        return method in self._dangerous_methods and not auth_required

    def _has_missing_security_requirements(self, endpoint: NormalizedEndpoint) -> bool:
        path = (endpoint.path or "").lower()
        sensitive_path = any(marker in path for marker in ["admin", "user", "account", "profile"])
        return sensitive_path and not endpoint.security_schemes

    def _build_finding(self, endpoint: NormalizedEndpoint, title: str, description: str, evidence: dict[str, object]) -> ScanFinding:
        return ScanFinding(
            vulnerability_type="security_misconfiguration",
            severity=Severity.MEDIUM,
            confidence=0.7,
            evidence={"title": title, **evidence},
            affected_endpoint=endpoint,
            remediation="Enforce HTTPS, require authentication for sensitive operations, and define explicit security requirements.",
            references=[
                "https://owasp.org/www-project-api-security/",
                "https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html",
            ],
        )
