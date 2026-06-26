"""Extracts GraphQL operations and their arguments from schema introspection data."""

from __future__ import annotations

from typing import Any, Mapping


def iter_operations(schema: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return operation dictionaries for GraphQL query/mutation/subscription root types."""
    operations: list[dict[str, Any]] = []
    for type_name in ("Query", "Mutation", "Subscription"):
        type_def = None
        for candidate in schema.get("types", []) or []:
            if isinstance(candidate, Mapping) and candidate.get("name") == type_name:
                type_def = candidate
                break
        if not isinstance(type_def, Mapping):
            continue

        fields = type_def.get("fields") or []
        for field in fields:
            if not isinstance(field, Mapping):
                continue
            operations.append(
                {
                    "name": field.get("name"),
                    "operation_type": type_name.lower().replace("query", "query").replace("mutation", "mutation").replace("subscription", "subscription"),
                    "description": field.get("description"),
                    "arguments": field.get("args") or [],
                    "return_type": field.get("type", {}).get("name") if isinstance(field.get("type"), Mapping) else None,
                }
            )
    return operations
