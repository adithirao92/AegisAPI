"""Resolves $ref references across OpenAPI specification documents."""

from __future__ import annotations

from typing import Any, Mapping


class OpenAPIReferenceResolver:
    """Resolve schema references using the OpenAPI components section."""

    def __init__(self, spec: Mapping[str, Any]) -> None:
        self._spec = spec

    def resolve(self, schema: Any) -> Any:
        """Resolve a schema fragment or return it unchanged when no reference exists."""
        if not isinstance(schema, Mapping):
            return schema

        ref = schema.get("$ref")
        if not isinstance(ref, str) or not ref.startswith("#/"):
            return schema

        target = self._resolve_ref(ref)
        if isinstance(target, Mapping):
            return {**target, **{k: v for k, v in schema.items() if k != "$ref"}}
        return target

    def _resolve_ref(self, ref: str) -> Any:
        parts = [part for part in ref.lstrip("#/").split("/") if part]
        current: Any = self._spec
        for part in parts:
            if isinstance(current, Mapping) and part in current:
                current = current[part]
                continue
            raise ValueError(f"Unresolved OpenAPI reference: {ref}")
        return current
