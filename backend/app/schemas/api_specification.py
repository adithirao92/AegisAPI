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


class NormalizedEndpoint(BaseModel):
    """A unified normalized entry for REST and GraphQL endpoints."""

    id: str
    endpoint_type: str
    path: str | None = None
    canonical_path: str | None = None
    method: str | None = None
    operation_type: str | None = None
    name: str | None = None
    canonical_name: str | None = None
    summary: str | None = None
    description: str | None = None
    parameters: list[ParameterDefinition] = Field(default_factory=list)
    arguments: list[GraphQLArgument] = Field(default_factory=list)
    request_schema: dict[str, Any] = Field(default_factory=dict)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    return_type: str | None = None
    security_schemes: list[str] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)


class DiscoveryCatalog(BaseModel):
    """Unified catalog returned by the API discovery service."""

    items: list[NormalizedEndpoint] = Field(default_factory=list)

    @property
    def endpoints(self) -> list[NormalizedEndpoint]:
        return [item for item in self.items if item.endpoint_type == "rest"]

    @property
    def operations(self) -> list[NormalizedEndpoint]:
        return [item for item in self.items if item.endpoint_type == "graphql"]
