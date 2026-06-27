"""Rule-based endpoint enrichment for normalized discovery records."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.api_specification import (
    DiscoveryCatalog,
    EndpointEnrichmentMetadata,
    NormalizedEndpoint,
)


RESOURCE_KEYWORDS = {
    "admin": {"admin", "administration", "management", "manage"},
    "auth": {"auth", "login", "logout", "token", "session", "sessions", "credentials"},
    "payments": {"payment", "payments", "checkout", "invoice", "billing"},
    "users": {"user", "users", "account", "accounts", "profile", "profiles"},
    "orders": {"order", "orders", "purchase", "purchases"},
    "products": {"product", "products", "catalog", "item", "items"},
    "cart": {"cart", "carts"},
}

IDENTIFIER_KEYWORDS = {"id", "uuid", "guid", "user_id", "order_id", "transaction_id", "reference"}
SECRET_KEYWORDS = {"password", "secret", "token", "api_key", "api-key", "refresh_token", "client_secret"}
CREDENTIAL_KEYWORDS = {"username", "email", "password", "client_id", "client_secret"}
USER_CONTROLLED_KEYWORDS = {"comment", "message", "query", "search", "input", "payload", "data", "text", "description"}
FILE_UPLOAD_KEYWORDS = {"file", "attachment", "upload", "image", "document", "binary"}
AUTH_SCHEME_KEYWORDS = {
    "bearer": "bearer",
    "jwt": "bearer",
    "oauth2": "oauth",
    "oauth": "oauth",
    "api_key": "api_key",
    "apikey": "api_key",
    "api-key": "api_key",
    "basic": "basic",
}

AUTH_PARAM_KEYWORDS = {
    "authorization": "bearer",
    "auth": "bearer",
    "api_key": "api_key",
    "api-key": "api_key",
    "x-api-key": "api_key",
    "x_api_key": "api_key",
    "access_token": "oauth",
    "refresh_token": "oauth",
    "client_secret": "oauth",
    "client_id": "oauth",
    "password": "password",
}

AUTH_FLOW_KEYWORDS = {"login", "logout", "refresh", "authenticate", "token", "signup", "register"}

HIGH_SENSITIVITY_GROUPS = {"admin", "auth", "payments", "credentials"}
MEDIUM_SENSITIVITY_GROUPS = {"users", "orders", "products", "cart"}


def _normalize_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.strip().lower())


def _flatten_schema(schema: Any) -> list[dict[str, Any]]:
    if not isinstance(schema, dict):
        return []

    items = [schema]
    for value in schema.values():
        if isinstance(value, dict):
            items.extend(_flatten_schema(value))
        elif isinstance(value, list):
            for element in value:
                if isinstance(element, dict):
                    items.extend(_flatten_schema(element))
    return items


def _schema_depth(schema: Any, depth: int = 0) -> int:
    if not isinstance(schema, dict) or not schema:
        return depth
    nested = [value for value in schema.values() if isinstance(value, dict)]
    if not nested:
        return depth
    return max(_schema_depth(value, depth + 1) for value in nested)


def _contains_file_upload_schema(schema: dict[str, Any]) -> bool:
    if not isinstance(schema, dict):
        return False
    schema_items = _flatten_schema(schema)
    for item in schema_items:
        if str(item.get("type", "")).lower() == "string" and str(item.get("format", "")).lower() == "binary":
            return True
        if str(item.get("content", "")).lower().find("multipart") >= 0:
            return True
    return False


class EndpointEnrichmentService:
    """Enrich normalized endpoints with deterministic metadata."""

    def enrich_catalog(self, catalog: DiscoveryCatalog) -> DiscoveryCatalog:
        for item in catalog.items:
            item.enrichment = self.enrich_endpoint(item)
        return catalog

    def enrich_endpoint(self, endpoint: NormalizedEndpoint) -> EndpointEnrichmentMetadata:
        auth_required, auth_type, auth_hints = self._infer_auth(endpoint)
        resource_group = self._infer_resource_group(endpoint)
        parameter_classification = self._classify_parameters(endpoint)
        request_complexity = self._compute_request_complexity(endpoint, parameter_classification)
        sensitivity = self._classify_sensitivity(
            endpoint,
            auth_required,
            auth_hints,
            resource_group,
            parameter_classification,
            request_complexity,
        )

        return EndpointEnrichmentMetadata(
            auth_required=auth_required,
            auth_type=auth_type,
            auth_hints=auth_hints,
            resource_group=resource_group,
            parameter_classification=parameter_classification,
            request_complexity=request_complexity,
            sensitivity=sensitivity,
        )

    def _infer_auth(self, endpoint: NormalizedEndpoint) -> tuple[bool, str | None, list[str]]:
        hints: list[str] = []
        auth_type: str | None = None
        auth_required = False

        for scheme in endpoint.security_schemes:
            normalized = _normalize_identifier(str(scheme))
            for token, hint in AUTH_SCHEME_KEYWORDS.items():
                if token in normalized:
                    auth_required = True
                    auth_type = auth_type or hint
                    hints.append(hint)

        for param in endpoint.parameters:
            name = _normalize_identifier(param.name)
            location = _normalize_identifier(param.location)
            for token, hint in AUTH_PARAM_KEYWORDS.items():
                if token == name or token == location or token in name or token in location:
                    hints.append(f"param:{token}")
                    auth_required = True
                    auth_type = auth_type or hint

        if endpoint.endpoint_type == "graphql":
            name = _normalize_identifier(str(endpoint.name or ""))
            description = _normalize_identifier(str(endpoint.description or ""))
            if any(token in name or token in description for token in AUTH_FLOW_KEYWORDS):
                hints.append("auth_flow")
                auth_required = True
                auth_type = auth_type or "oauth"

        if not auth_required and endpoint.endpoint_type == "rest" and endpoint.method == "GET":
            auth_type = auth_type or "none"

        if auth_required and auth_type is None:
            auth_type = "unknown"

        hints = sorted(set(hints))
        return auth_required, auth_type, hints

    def _infer_resource_group(self, endpoint: NormalizedEndpoint) -> str | None:
        tokens = []
        if endpoint.canonical_path:
            tokens.extend(segment for segment in endpoint.canonical_path.lower().split("/") if segment)
        if endpoint.name:
            tokens.append(_normalize_identifier(endpoint.name))
        if endpoint.return_type:
            tokens.append(_normalize_identifier(endpoint.return_type))

        for group, keywords in RESOURCE_KEYWORDS.items():
            if any(token in keywords for token in tokens):
                return group

        for token in reversed(tokens):
            if token and token not in {"{param}", "query", "mutation", "get", "post", "put", "delete"}:
                return token

        return "generic"

    def _classify_parameters(self, endpoint: NormalizedEndpoint) -> dict[str, list[str]]:
        classification: dict[str, list[str]] = {}

        def classify_item(name: str, schema: dict[str, Any]) -> list[str]:
            normalized = _normalize_identifier(name)
            categories: list[str] = []

            if any(keyword in normalized for keyword in IDENTIFIER_KEYWORDS):
                categories.append("identifier")
            if any(keyword in normalized for keyword in SECRET_KEYWORDS):
                categories.append("secret")
            if any(keyword in normalized for keyword in CREDENTIAL_KEYWORDS):
                categories.append("credential")
            if any(keyword in normalized for keyword in USER_CONTROLLED_KEYWORDS):
                categories.append("user_controlled")
            if any(keyword in normalized for keyword in FILE_UPLOAD_KEYWORDS) or _contains_file_upload_schema(schema):
                categories.append("file_upload")
            return sorted(set(categories))

        for param in endpoint.parameters:
            if not param.name:
                continue
            categories = classify_item(param.name, getattr(param, "schema_definition", {}) or {})
            if categories:
                classification[param.name] = categories

        for arg in endpoint.arguments:
            categories = classify_item(arg.name, {"type_name": arg.type_name or ""})
            if categories:
                classification[arg.name] = categories

        return classification

    def _compute_request_complexity(
        self,
        endpoint: NormalizedEndpoint,
        parameter_classification: dict[str, list[str]],
    ) -> str:
        score = 0

        if endpoint.method and endpoint.method.upper() != "GET":
            score += 1
        if endpoint.operation_type == "mutation":
            score += 1

        param_count = len(endpoint.parameters) + len(endpoint.arguments)
        score += min(param_count, 2)

        if _schema_depth(endpoint.request_schema) >= 3:
            score += 1

        if any("file_upload" in categories for categories in parameter_classification.values()):
            score += 2

        if param_count >= 4:
            score += 1

        if score <= 1:
            return "low"
        if score <= 3:
            return "medium"
        return "high"

    def _classify_sensitivity(
        self,
        endpoint: NormalizedEndpoint,
        auth_required: bool,
        auth_hints: list[str],
        resource_group: str | None,
        parameter_classification: dict[str, list[str]],
        request_complexity: str,
    ) -> str:
        if resource_group in HIGH_SENSITIVITY_GROUPS:
            return "high"

        if any("secret" in categories or "credential" in categories for categories in parameter_classification.values()):
            return "high"

        if "auth_flow" in auth_hints:
            return "high"

        if auth_required and resource_group in MEDIUM_SENSITIVITY_GROUPS:
            return "medium"

        if request_complexity == "high":
            return "medium"

        if auth_required:
            return "medium"

        return "low"
