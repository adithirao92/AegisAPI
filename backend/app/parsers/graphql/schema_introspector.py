"""Parses GraphQL schema introspection results and exposes the root schema."""

from __future__ import annotations

from typing import Any, Mapping


def extract_schema(spec: Any) -> Mapping[str, Any]:
    """Extract a normalized schema mapping from either introspection JSON or a schema mapping."""
    if isinstance(spec, Mapping):
        data = spec.get("data")
        if isinstance(data, Mapping) and isinstance(data.get("__schema"), Mapping):
            return data["__schema"]
        return spec
    raise TypeError("GraphQL specification must be a mapping or string")
