"""Endpoint normalization and deduplication for the discovery pipeline."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.schemas.api_specification import (
    DiscoveryCatalog,
    EndpointModel,
    GraphQLOperation,
    GraphQLArgument,
    NormalizedEndpoint,
)

PATH_PARAM_PATTERN = re.compile(r"\{[^/]+?\}")
NON_ALPHANUMERIC = re.compile(r"[^a-z0-9_]+")
CAMEL_TO_SNAKE = re.compile(r"([a-z0-9])([A-Z])")


def _normalize_name(value: str) -> str:
    text = str(value or "").strip()
    text = CAMEL_TO_SNAKE.sub(r"\1_\2", text)
    text = text.replace("-", "_").replace(" ", "_")
    text = NON_ALPHANUMERIC.sub("_", text.lower())
    text = re.sub(r"__+", "_", text)
    return text.strip("_")


def _canonicalize_path(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("REST path must be a non-empty string")

    normalized = re.sub(r"//+", "/", path.strip())
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized[:-1]

    normalized = PATH_PARAM_PATTERN.sub("{param}", normalized)
    return normalized


def _canonicalize_method(method: str) -> str:
    if not isinstance(method, str) or not method.strip():
        raise ValueError("HTTP method must be a non-empty string")
    return method.strip().upper()


def _fingerprint_schema(schema: dict[str, Any]) -> str:
    if not isinstance(schema, dict):
        schema = {}
    serialized = json.dumps(schema, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _parameter_signature(parameter: Any) -> str:
    if not hasattr(parameter, "name"):
        raise ValueError("Parameter is missing required metadata")
    normalized = {
        "name": _normalize_name(parameter.name),
        "location": str(getattr(parameter, "location", "")).strip().lower(),
        "required": bool(getattr(parameter, "required", False)),
        "schema": _fingerprint_schema(getattr(parameter, "schema_definition", {})),
    }
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def _canonicalize_rest_key(endpoint: EndpointModel) -> str:
    canonical_path = _canonicalize_path(endpoint.path)
    method = _canonicalize_method(endpoint.method)
    parameter_signatures = sorted(_parameter_signature(param) for param in endpoint.parameters)
    response_fingerprint = _fingerprint_schema(endpoint.response_schema or {})
    return "|".join([method, canonical_path, ";".join(parameter_signatures), response_fingerprint])


def _normalize_graphql_argument(argument: GraphQLArgument) -> dict[str, Any]:
    return {
        "name": _normalize_name(argument.name),
        "type_name": _normalize_name(str(argument.type_name or "")),
        "kind": _normalize_name(str(argument.kind or "")),
        "required": bool(argument.required),
    }


def _canonicalize_graphql_key(operation: GraphQLOperation) -> str:
    op_type = _normalize_name(operation.operation_type)
    name = _normalize_name(operation.name)
    argument_signatures = sorted(
        json.dumps(_normalize_graphql_argument(arg), sort_keys=True, separators=(",", ":"))
        for arg in operation.arguments
    )
    return_type = _normalize_name(str(operation.return_type or ""))
    return "|".join([op_type, name, ";".join(argument_signatures), return_type])


def _stable_id(prefix: str, canonical_key: str) -> str:
    digest = hashlib.sha256(canonical_key.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def _normalize_resource_token(token: str | None) -> str | None:
    if not token:
        return None
    normalized = _normalize_name(token)
    if normalized.endswith("ies"):
        return normalized[:-3] + "y"
    if normalized.endswith("s"):
        return normalized[:-1]
    return normalized


def _rest_resource_token(canonical_path: str) -> str | None:
    if not canonical_path:
        return None
    segments = [segment for segment in canonical_path.split("/") if segment and segment != "{param}"]
    return _normalize_resource_token(segments[-1]) if segments else None


def _graphq_lingual_token(operation: GraphQLOperation) -> str:
    return _normalize_resource_token(operation.name or operation.return_type or "")


class EndpointNormalizer:
    """Normalizes parsed endpoint and operation models and enforces de-duplication."""

    @staticmethod
    def normalize_rest(endpoint: EndpointModel, source_path: str) -> NormalizedEndpoint:
        canonical_path = _canonicalize_path(endpoint.path)
        method = _canonicalize_method(endpoint.method)
        canonical_key = _canonicalize_rest_key(endpoint)
        endpoint_id = _stable_id("rest", canonical_key)

        return NormalizedEndpoint(
            id=endpoint_id,
            endpoint_type="rest",
            path=endpoint.path,
            canonical_path=canonical_path,
            method=method,
            operation_type=None,
            name=endpoint.operation_id or "",
            canonical_name=f"{method} {canonical_path}",
            summary=endpoint.summary,
            description=endpoint.description,
            parameters=endpoint.parameters,
            arguments=[],
            request_schema=endpoint.request_schema,
            response_schema=endpoint.response_schema,
            return_type=None,
            security_schemes=endpoint.security_schemes,
            sources=[{"file": source_path, "origin": endpoint.operation_id or endpoint.path}],
        )

    @staticmethod
    def normalize_graphql(operation: GraphQLOperation, source_path: str) -> NormalizedEndpoint:
        canonical_key = _canonicalize_graphql_key(operation)
        endpoint_id = _stable_id("graphql", canonical_key)

        return NormalizedEndpoint(
            id=endpoint_id,
            endpoint_type="graphql",
            path=None,
            canonical_path=None,
            method=None,
            operation_type=operation.operation_type,
            name=operation.name,
            canonical_name=f"{_normalize_name(operation.operation_type)} {_normalize_name(operation.name)}",
            summary=None,
            description=operation.description,
            parameters=[],
            arguments=operation.arguments,
            request_schema={},
            response_schema={},
            return_type=operation.return_type,
            security_schemes=[],
            sources=[{"file": source_path, "origin": operation.name}],
        )

    @staticmethod
    def merge(existing: NormalizedEndpoint, incoming: NormalizedEndpoint) -> NormalizedEndpoint:
        if existing.id != incoming.id:
            raise ValueError("Cannot merge endpoints with different stable ids")

        merged_sources = existing.sources[:]
        for source in incoming.sources:
            if source not in merged_sources:
                merged_sources.append(source)

        return NormalizedEndpoint(
            id=existing.id,
            endpoint_type=existing.endpoint_type,
            path=existing.path or incoming.path,
            canonical_path=existing.canonical_path or incoming.canonical_path,
            method=existing.method or incoming.method,
            operation_type=existing.operation_type or incoming.operation_type,
            name=existing.name or incoming.name,
            canonical_name=existing.canonical_name or incoming.canonical_name,
            summary=existing.summary or incoming.summary,
            description=existing.description or incoming.description,
            parameters=existing.parameters or incoming.parameters,
            arguments=existing.arguments or incoming.arguments,
            request_schema=existing.request_schema or incoming.request_schema,
            response_schema=existing.response_schema or incoming.response_schema,
            return_type=existing.return_type or incoming.return_type,
            security_schemes=existing.security_schemes or incoming.security_schemes,
            sources=merged_sources,
        )

    @staticmethod
    def merge_cross_type(existing: NormalizedEndpoint, incoming: NormalizedEndpoint) -> NormalizedEndpoint:
        merged_sources = existing.sources[:]
        for source in incoming.sources:
            if source not in merged_sources:
                merged_sources.append(source)

        return NormalizedEndpoint(
            id=existing.id,
            endpoint_type=existing.endpoint_type,
            path=existing.path or incoming.path,
            canonical_path=existing.canonical_path or incoming.canonical_path,
            method=existing.method or incoming.method,
            operation_type=existing.operation_type or incoming.operation_type,
            name=existing.name or incoming.name,
            canonical_name=existing.canonical_name or incoming.canonical_name,
            summary=existing.summary or incoming.summary,
            description=existing.description or incoming.description,
            parameters=existing.parameters or incoming.parameters,
            arguments=existing.arguments or incoming.arguments,
            request_schema=existing.request_schema or incoming.request_schema,
            response_schema=existing.response_schema or incoming.response_schema,
            return_type=existing.return_type or incoming.return_type,
            security_schemes=existing.security_schemes or incoming.security_schemes,
            sources=merged_sources,
        )

    def normalize_catalog(
        self,
        endpoints: list[EndpointModel],
        operations: list[GraphQLOperation],
        source_path: str,
        existing: DiscoveryCatalog | None = None,
    ) -> DiscoveryCatalog:
        catalog = existing or DiscoveryCatalog()
        items = {item.id: item for item in catalog.items}

        for endpoint in endpoints:
            normalized = self.normalize_rest(endpoint, source_path)
            items[normalized.id] = self.merge(items[normalized.id], normalized) if normalized.id in items else normalized

        for operation in operations:
            normalized = self.normalize_graphql(operation, source_path)
            items[normalized.id] = self.merge(items[normalized.id], normalized) if normalized.id in items else normalized

        catalog.items = list(items.values())
        return catalog

    def deduplicate_catalog(self, catalog: DiscoveryCatalog) -> DiscoveryCatalog:
        cross_map: dict[str, str] = {}
        for item in catalog.items:
            if item.endpoint_type != "rest" or not item.canonical_path or item.method != "GET":
                continue
            token = _rest_resource_token(item.canonical_path)
            if token:
                cross_map.setdefault(token, item.id)

        merged: dict[str, NormalizedEndpoint] = {}
        for item in catalog.items:
            if item.endpoint_type == "graphql":
                token = _graphq_lingual_token(item)
                if token and token in cross_map:
                    rest_id = cross_map[token]
                    primary = merged.get(rest_id) or next(x for x in catalog.items if x.id == rest_id)
                    merged[rest_id] = self.merge_cross_type(primary, item)
                    continue
            merged[item.id] = self.merge(merged[item.id], item) if item.id in merged else item

        catalog.items = list(merged.values())
        return catalog
