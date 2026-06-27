from pathlib import Path

from app.schemas.api_specification import EndpointModel, GraphQLArgument, GraphQLOperation
from app.services.discovery.endpoint_normalizer import EndpointNormalizer


def make_rest_endpoint(path: str, method: str, operation_id: str = "") -> EndpointModel:
    return EndpointModel(
        path=path,
        method=method,
        operation_id=operation_id,
        summary="summary",
        description="description",
        parameters=[],
        request_schema={"type": "object"},
        response_schema={"type": "object"},
        security_schemes=["BearerAuth"],
    )


def make_graphql_operation(name: str, operation_type: str, return_type: str = "User") -> GraphQLOperation:
    return GraphQLOperation(
        name=name,
        operation_type=operation_type,
        description="description",
        arguments=[GraphQLArgument(name="id", type_name="ID", kind="SCALAR", required=True)],
        return_type=return_type,
        fields=["id"],
    )


def test_rest_path_normalization_removes_redundant_slashes() -> None:
    normalizer = EndpointNormalizer()
    endpoint = make_rest_endpoint("//users//{id}//", "get")

    normalized = normalizer.normalize_rest(endpoint, str(Path("spec.json")))

    assert normalized.canonical_path == "/users/{param}"
    assert normalized.method == "GET"


def test_rest_parameter_normalization_stable_ids() -> None:
    normalizer = EndpointNormalizer()
    endpoint_a = make_rest_endpoint("/users/{id}", "get")
    endpoint_b = make_rest_endpoint("/users/{userId}", "get")

    normalized_a = normalizer.normalize_rest(endpoint_a, "spec1.json")
    normalized_b = normalizer.normalize_rest(endpoint_b, "spec2.json")

    assert normalized_a.id == normalized_b.id


def test_graphql_operation_normalization_order_independent() -> None:
    normalizer = EndpointNormalizer()
    op_a = make_graphql_operation("user", "query")
    op_b = GraphQLOperation(
        name="user",
        operation_type="query",
        description="description",
        arguments=[GraphQLArgument(name="id", type_name="ID", kind="SCALAR", required=True)],
        return_type="User",
        fields=["id"],
    )

    normalized_a = normalizer.normalize_graphql(op_a, "spec.graphql")
    normalized_b = normalizer.normalize_graphql(op_b, "spec.graphql")

    assert normalized_a.id == normalized_b.id


def test_deduplication_merges_duplicate_rest_endpoints() -> None:
    normalizer = EndpointNormalizer()
    endpoint_a = make_rest_endpoint("/users/{id}", "get", operation_id="getUser")
    endpoint_b = make_rest_endpoint("/users/{userId}", "get", operation_id="getUserById")

    catalog = normalizer.normalize_catalog([endpoint_a], [], "spec1.json")
    catalog = normalizer.normalize_catalog([endpoint_b], [], "spec2.json", existing=catalog)
    deduped = normalizer.deduplicate_catalog(catalog)

    assert len(deduped.items) == 1
    assert len(deduped.items[0].sources) == 2


def test_mixed_rest_and_graphql_imports_merge_by_resource_token() -> None:
    normalizer = EndpointNormalizer()
    rest_endpoint = make_rest_endpoint("/users/{id}", "get", operation_id="getUser")
    graphql_operation = make_graphql_operation("user", "query")

    catalog = normalizer.normalize_catalog([rest_endpoint], [], "rest.json")
    catalog = normalizer.normalize_catalog([], [graphql_operation], "schema.graphql", existing=catalog)
    deduped = normalizer.deduplicate_catalog(catalog)

    assert len(deduped.items) == 1
    assert any(item.endpoint_type == "rest" for item in deduped.items)
    assert any("schema.graphql" in source["file"] for item in deduped.items for source in item.sources)


def test_normalizer_rejects_malformed_rest_input() -> None:
    normalizer = EndpointNormalizer()
    bad_endpoint = make_rest_endpoint("", "get")

    try:
        normalizer.normalize_rest(bad_endpoint, "spec.json")
    except ValueError as exc:
        assert "REST path must be a non-empty string" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
