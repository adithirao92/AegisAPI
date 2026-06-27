from pathlib import Path

from app.schemas.api_specification import (
    DiscoveryCatalog,
    GraphQLArgument,
    NormalizedEndpoint,
)
from app.services.discovery.endpoint_enricher import EndpointEnrichmentService


def make_rest_endpoint(path: str, method: str, operation_id: str = "", params: list[dict] | None = None) -> NormalizedEndpoint:
    parameters = []
    for param in params or []:
        parameters.append(
            {
                "name": param["name"],
                "location": param.get("location", "query"),
                "required": param.get("required", False),
                "schema": param.get("schema", {}),
            }
        )

    return NormalizedEndpoint(
        id=f"rest:{path}:{method}",
        endpoint_type="rest",
        path=path,
        canonical_path=path,
        method=method,
        operation_type=None,
        name=operation_id,
        canonical_name=f"{method} {path}",
        summary="summary",
        description="description",
        parameters=parameters,
        arguments=[],
        request_schema={"type": "object"},
        response_schema={"type": "object"},
        security_schemes=["BearerAuth"],
        sources=[{"file": "test", "origin": operation_id or path}],
    )


def make_graphql_endpoint(name: str, operation_type: str, args: list[GraphQLArgument] | None = None) -> NormalizedEndpoint:
    return NormalizedEndpoint(
        id=f"graphql:{name}:{operation_type}",
        endpoint_type="graphql",
        path=None,
        canonical_path=None,
        method=None,
        operation_type=operation_type,
        name=name,
        canonical_name=f"{operation_type} {name}",
        summary=None,
        description="description",
        parameters=[],
        arguments=args or [GraphQLArgument(name="id", type_name="ID", kind="SCALAR", required=True)],
        request_schema={},
        response_schema={},
        return_type="User",
        security_schemes=[],
        sources=[{"file": "test", "origin": name}],
    )


def test_enrich_rest_endpoint_auth_inference() -> None:
    endpoint = make_rest_endpoint("/users/{id}", "GET", operation_id="getUser")
    catalog = DiscoveryCatalog(items=[endpoint])

    enriched = EndpointEnrichmentService().enrich_catalog(catalog)
    assert enriched.items[0].enrichment.auth_required
    assert enriched.items[0].enrichment.auth_type == "bearer"
    assert "bearer" in enriched.items[0].enrichment.auth_hints


def test_enrich_graphql_auth_flow_hint() -> None:
    operation = make_graphql_endpoint("login", "mutation")
    catalog = DiscoveryCatalog(items=[operation])

    enriched = EndpointEnrichmentService().enrich_catalog(catalog)
    assert "auth_flow" in enriched.items[0].enrichment.auth_hints
    assert enriched.items[0].enrichment.sensitivity == "high"


def test_resource_grouping_rest_endpoint() -> None:
    endpoint = make_rest_endpoint("/orders/{order_id}", "POST", operation_id="createOrder")
    catalog = DiscoveryCatalog(items=[endpoint])

    enriched = EndpointEnrichmentService().enrich_catalog(catalog)
    assert enriched.items[0].enrichment.resource_group == "orders"
    assert enriched.items[0].enrichment.sensitivity == "medium"


def test_parameter_classification_identifiers_and_secrets() -> None:
    endpoint = make_rest_endpoint(
        "/users/{id}",
        "POST",
        operation_id="updateUser",
        params=[
            {"name": "user_id", "location": "path", "required": True},
            {"name": "password", "location": "body", "required": True},
        ],
    )
    catalog = DiscoveryCatalog(items=[endpoint])

    enriched = EndpointEnrichmentService().enrich_catalog(catalog)
    assert enriched.items[0].enrichment.parameter_classification["user_id"] == ["identifier"]
    assert "secret" in enriched.items[0].enrichment.parameter_classification["password"]
    assert enriched.items[0].enrichment.sensitivity == "high"


def test_request_complexity_high_for_file_upload() -> None:
    endpoint = make_rest_endpoint(
        "/files/upload",
        "POST",
        operation_id="uploadFile",
        params=[{"name": "file", "location": "formData", "required": True, "schema": {"type": "string", "format": "binary"}}],
    )
    catalog = DiscoveryCatalog(items=[endpoint])

    enriched = EndpointEnrichmentService().enrich_catalog(catalog)
    assert enriched.items[0].enrichment.request_complexity == "high"
    assert "file_upload" in enriched.items[0].enrichment.parameter_classification["file"]


def test_sensitivity_low_for_public_get() -> None:
    endpoint = make_rest_endpoint("/products", "GET", operation_id="listProducts", params=[{"name": "page", "location": "query", "required": False}])
    endpoint.security_schemes = []
    catalog = DiscoveryCatalog(items=[endpoint])

    enriched = EndpointEnrichmentService().enrich_catalog(catalog)
    assert enriched.items[0].enrichment.sensitivity == "low"


def test_edge_case_empty_endpoint_still_enriches() -> None:
    endpoint = make_rest_endpoint("/health", "GET")
    endpoint.security_schemes = []
    catalog = DiscoveryCatalog(items=[endpoint])

    enriched = EndpointEnrichmentService().enrich_catalog(catalog)
    assert enriched.items[0].enrichment.resource_group == "health"
    assert enriched.items[0].enrichment.request_complexity == "low"
