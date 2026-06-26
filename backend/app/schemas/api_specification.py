"""Normalized API specification models for parsing and downstream scanning."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ParameterDefinition(BaseModel):
    """Represents a normalized parameter extracted from a source API definition."""

    name: str
    location: str
    required: bool = False
    schema_definition: dict[str, Any] = Field(default_factory=dict, alias="schema")

    model_config = {"populate_by_name": True}


class EndpointModel(BaseModel):
    """Normalized REST endpoint representation used throughout the scanning pipeline."""

    path: str
    method: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    parameters: list[ParameterDefinition] = Field(default_factory=list)
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    security_schemes: list[str] = Field(default_factory=list)


class GraphQLArgument(BaseModel):
    """Represents a normalized GraphQL argument definition."""

    name: str
    type_name: str | None = None
    kind: str | None = None
    required: bool = False


class GraphQLOperation(BaseModel):
    """Normalized GraphQL operation representation used for scanning and analysis."""

    name: str
    operation_type: str
    description: str | None = None
    arguments: list[GraphQLArgument] = Field(default_factory=list)
    return_type: str | None = None
    fields: list[str] = Field(default_factory=list)


class DiscoveryCatalog(BaseModel):
    """Unified catalog returned by the API discovery service."""

    endpoints: list[EndpointModel] = Field(default_factory=list)
    operations: list[GraphQLOperation] = Field(default_factory=list)
