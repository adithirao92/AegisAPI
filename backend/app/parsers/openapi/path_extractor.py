"""Extracts REST paths and operations from OpenAPI specifications."""

from __future__ import annotations

from typing import Any, Iterator, Mapping


def iter_operations(spec: Mapping[str, Any]) -> Iterator[tuple[str, str, Mapping[str, Any]]]:
    """Yield normalized path + method + operation tuples from an OpenAPI document."""
    paths = spec.get("paths") or {}
    if not isinstance(paths, Mapping):
        raise ValueError("OpenAPI paths section must be an object")

    for path, path_item in paths.items():
        if not isinstance(path_item, Mapping):
            continue

        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            operation = path_item.get(method)
            if isinstance(operation, Mapping):
                yield path, method.upper(), operation
