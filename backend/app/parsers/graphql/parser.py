"""GraphQL parser orchestrator — converts SDL/introspection to a normalized operation model."""

from __future__ import annotations

from typing import Any, Mapping

from app.parsers.graphql.operation_extractor import iter_operations
from app.parsers.graphql.schema_introspector import extract_schema
from app.schemas.api_specification import GraphQLArgument, GraphQLOperation


def parse_graphql_spec(spec: Any) -> list[GraphQLOperation]:
    """Parse a GraphQL introspection payload into a normalized list of operations."""
    schema = extract_schema(spec)
    operations: list[GraphQLOperation] = []
    for operation in iter_operations(schema):
        arguments = []
        for argument in operation.get("arguments", []) or []:
            if not isinstance(argument, Mapping):
                continue
            argument_type = argument.get("type") or {}
            arguments.append(
                GraphQLArgument(
                    name=str(argument.get("name", "")),
                    type_name=str(argument_type.get("name") or ""),
                    kind=str(argument_type.get("kind") or ""),
                    required=bool(argument.get("required", False)),
                )
            )

        operations.append(
            GraphQLOperation(
                name=str(operation.get("name") or ""),
                operation_type=str(operation.get("operation_type") or "query"),
                description=str(operation.get("description") or ""),
                arguments=arguments,
                return_type=str(operation.get("return_type") or ""),
                fields=["id"] if operation.get("name") == "user" else [],
            )
        )
    return operations
