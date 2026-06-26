"""Extracts security scheme references from OpenAPI security requirements."""

from __future__ import annotations

from typing import Any, Mapping


def extract_security_schemes(operation: Mapping[str, Any], path_item: Mapping[str, Any], spec: Mapping[str, Any]) -> list[str]:
    """Collect security scheme names for an operation using the OpenAPI security rules."""
    security_requirements = operation.get("security")
    if security_requirements is None:
        security_requirements = path_item.get("security")
    if security_requirements is None:
        security_requirements = spec.get("security")

    if not isinstance(security_requirements, list):
        return []

    schemes: list[str] = []
    for requirement in security_requirements:
        if not isinstance(requirement, Mapping):
            continue
        schemes.extend(str(name) for name in requirement.keys())
    return sorted(set(schemes))
