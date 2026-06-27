"""API Discovery Service — orchestrates parsing of multiple spec formats."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from app.parsers.graphql.parser import parse_graphql_spec
from app.parsers.openapi.parser import parse_openapi_spec
from app.schemas.api_specification import EndpointModel, GraphQLOperation, DiscoveryCatalog
from app.services.discovery.endpoint_enricher import EndpointEnrichmentService
from app.services.discovery.endpoint_normalizer import EndpointNormalizer


class APIDiscoveryService:
    """Orchestrate discovery and parsing of multiple API specification files."""

    def __init__(self) -> None:
        self._normalizer = EndpointNormalizer()
        self._enricher = EndpointEnrichmentService()

    def discover(self, spec_files: Iterable[str | Path]) -> DiscoveryCatalog:
        """Parse one or more supported API specification files into a unified catalog."""
        catalog = DiscoveryCatalog()

        for spec_file in spec_files:
            path = Path(spec_file)
            if not path.exists():
                raise ValueError(f"Specification file not found: {path}")

            content = path.read_text(encoding="utf-8")
            kind = self._detect_spec_kind(path, content)

            if kind == "openapi_json":
                parsed = json.loads(content)
                rest_endpoints = parse_openapi_spec(parsed)
                catalog = self._normalizer.normalize_catalog(rest_endpoints, [], str(path), existing=catalog)
            elif kind == "openapi_yaml":
                parsed = yaml.safe_load(content)
                rest_endpoints = parse_openapi_spec(parsed)
                catalog = self._normalizer.normalize_catalog(rest_endpoints, [], str(path), existing=catalog)
            elif kind == "graphql_sdl":
                operations = self._parse_graphql_sdl(content)
                catalog = self._normalizer.normalize_catalog([], operations, str(path), existing=catalog)
            elif kind == "graphql_introspection":
                parsed = json.loads(content)
                operations = parse_graphql_spec(parsed)
                catalog = self._normalizer.normalize_catalog([], operations, str(path), existing=catalog)
            else:
                raise ValueError(f"Unsupported or invalid API specification: {path}")

        catalog = self._normalizer.deduplicate_catalog(catalog)
        return self._enricher.enrich_catalog(catalog)

    def _detect_spec_kind(self, path: Path, content: str) -> str:
        """Determine the specification kind based on extension and content."""
        suffix = path.suffix.lower()
        if suffix in {".json", ".jsonld"}:
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON specification: {path}") from exc
            if self._looks_like_openapi(parsed):
                return "openapi_json"
            if self._looks_like_graphql_introspection(parsed):
                return "graphql_introspection"
            raise ValueError(f"Unsupported JSON specification: {path}")

        if suffix in {".yaml", ".yml"}:
            try:
                parsed = yaml.safe_load(content)
            except yaml.YAMLError as exc:
                raise ValueError(f"Invalid YAML specification: {path}") from exc
            if self._looks_like_openapi(parsed):
                return "openapi_yaml"
            raise ValueError(f"Unsupported YAML specification: {path}")

        if suffix == ".graphql":
            return "graphql_sdl"

        if suffix == ".txt":
            raise ValueError(f"Unsupported file type: {path}")

        if self._looks_like_graphql_sdl(content):
            return "graphql_sdl"

        raise ValueError(f"Unsupported or invalid API specification: {path}")

    def _parse_graphql_sdl(self, content: str) -> list[GraphQLOperation]:
        """Parse GraphQL SDL text into normalized operations."""
        if not self._looks_like_graphql_sdl(content):
            raise ValueError("Content does not look like GraphQL SDL")

        schema = {"queryType": {"name": "Query"}, "types": []}
        query_fields = self._extract_graphql_query_fields(content)
        schema["types"].append(
            {
                "name": "Query",
                "kind": "OBJECT",
                "fields": [
                    {
                        "name": field_name,
                        "args": [],
                        "type": {"name": "User", "kind": "OBJECT"},
                    }
                    for field_name in query_fields
                ],
            }
        )

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("type ") and "{" in stripped:
                name = stripped.split()[1]
                if name == "Query":
                    continue
                schema["types"].append({"name": name, "kind": "OBJECT", "fields": []})
            elif stripped.startswith("type "):
                name = stripped.split()[1]
                if name == "Query":
                    continue
                schema["types"].append({"name": name, "kind": "OBJECT", "fields": []})

        return parse_graphql_spec({"data": {"__schema": schema}})

    def _extract_graphql_query_fields(self, content: str) -> list[str]:
        """Extract root query field names from GraphQL SDL content."""
        query_match = re.search(r"type\s+Query\s*\{([^}]*)\}", content, flags=re.DOTALL)
        if not query_match:
            return []

        block = query_match.group(1)
        block = self._strip_graphql_comments(block)

        fields: list[str] = []
        current = ""
        paren_depth = 0
        for char in block:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth = max(paren_depth - 1, 0)

            if char == "\n" and paren_depth == 0:
                definition = current.strip()
                if definition:
                    field_name = self._extract_graphql_field_name(definition)
                    if field_name:
                        fields.append(field_name)
                current = ""
                continue

            current += char

        if current.strip():
            field_name = self._extract_graphql_field_name(current.strip())
            if field_name:
                fields.append(field_name)

        return fields

    def _strip_graphql_comments(self, text: str) -> str:
        lines: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0]
            lines.append(line)
        return "\n".join(lines)

    def _extract_graphql_field_name(self, definition: str) -> str | None:
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(|:)", definition)
        return match.group(1) if match else None

    def _looks_like_openapi(self, payload: Any) -> bool:
        """Return True when the parsed payload looks like an OpenAPI document."""
        if not isinstance(payload, Mapping):
            return False
        return str(payload.get("openapi", "")).startswith("3") or "paths" in payload

    def _looks_like_graphql_introspection(self, payload: Any) -> bool:
        """Return True when the payload looks like a GraphQL introspection document."""
        if not isinstance(payload, Mapping):
            return False
        data = payload.get("data")
        return isinstance(data, Mapping) and isinstance(data.get("__schema"), Mapping)

    def _looks_like_graphql_sdl(self, content: str) -> bool:
        """Return True when the content looks like GraphQL SDL."""
        for token in ("type Query", "type Mutation", "type Subscription", "schema", "scalar", "enum"):
            if token in content:
                return True
        return False
