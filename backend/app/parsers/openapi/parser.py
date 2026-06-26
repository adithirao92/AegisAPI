"""OpenAPI parser orchestrator — converts specs to a normalized endpoint model."""

from __future__ import annotations

from typing import Any, Mapping

from app.parsers.openapi.path_extractor import iter_operations
from app.parsers.openapi.schema_resolver import OpenAPIReferenceResolver
from app.parsers.openapi.security_extractor import extract_security_schemes
from app.schemas.api_specification import EndpointModel, ParameterDefinition


def parse_openapi_spec(spec: Mapping[str, Any]) -> list[EndpointModel]:
    """Parse an OpenAPI document into a normalized list of REST endpoints."""
    if not isinstance(spec, Mapping):
        raise TypeError("OpenAPI specification must be a mapping")

    resolver = OpenAPIReferenceResolver(spec)
    endpoints: list[EndpointModel] = []

    for path, method, operation in iter_operations(spec):
        path_item = (spec.get("paths") or {}).get(path)
        if not isinstance(path_item, Mapping):
            path_item = {}

        parameters: list[ParameterDefinition] = []
        for parameter in list(path_item.get("parameters", [])) + list(operation.get("parameters", [])):
            if not isinstance(parameter, Mapping):
                continue
            schema = parameter.get("schema") or {}
            parameters.append(
                ParameterDefinition(
                    name=str(parameter.get("name", "")),
                    location=str(parameter.get("in", "query")),
                    required=bool(parameter.get("required", False)),
                    schema=dict(resolver.resolve(schema)),
                )
            )

        request_schema: dict[str, Any] = {}
        request_body = operation.get("requestBody")
        if isinstance(request_body, Mapping):
            content = request_body.get("content") or {}
            if isinstance(content, Mapping):
                for media_type in content.values():
                    if isinstance(media_type, Mapping):
                        schema = media_type.get("schema")
                        if schema is not None:
                            request_schema = dict(resolver.resolve(schema))
                            break

        response_schema: dict[str, Any] = {}
        responses = operation.get("responses") or {}
        if isinstance(responses, Mapping):
            for status_code in ("200", "201", "202", "default"):
                response = responses.get(status_code)
                if isinstance(response, Mapping):
                    content = response.get("content") or {}
                    if isinstance(content, Mapping):
                        for media_type in content.values():
                            if isinstance(media_type, Mapping):
                                schema = media_type.get("schema")
                                if schema is not None:
                                    response_schema = dict(resolver.resolve(schema))
                                    break
                    if response_schema:
                        break

        endpoints.append(
            EndpointModel(
                path=path,
                method=method,
                operation_id=str(operation.get("operationId") or ""),
                summary=str(operation.get("summary") or ""),
                description=str(operation.get("description") or ""),
                parameters=parameters,
                request_schema=request_schema,
                response_schema=response_schema,
                security_schemes=extract_security_schemes(operation, path_item, spec),
            )
        )

    return endpoints
