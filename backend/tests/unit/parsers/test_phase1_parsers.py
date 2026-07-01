import pytest

from app.parsers.graphql.parser import parse_graphql_spec
from app.parsers.openapi.parser import parse_openapi_spec


def test_openapi_parser_normalizes_paths_and_schemas() -> None:
    spec = {
        "openapi": "3.0.3",
        "paths": {
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "summary": "Get a user",
                    "description": "Retrieve a specific user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                }
            }
        },
    }

    endpoints = parse_openapi_spec(spec)

    assert len(endpoints) == 1
    endpoint = endpoints[0]
    assert endpoint.path == "/users/{id}"
    assert endpoint.method == "GET"
    assert endpoint.operation_id == "getUser"
    assert endpoint.parameters[0].name == "id"
    assert endpoint.parameters[0].location == "path"
    assert endpoint.response_schema["type"] == "object"


def test_graphql_parser_extracts_operations_and_arguments() -> None:
    spec = {
        "data": {
            "__schema": {
                "queryType": {"name": "Query"},
                "types": [
                    {
                        "name": "Query",
                        "kind": "OBJECT",
                        "fields": [
                            {
                                "name": "user",
                                "args": [
                                    {
                                        "name": "id",
                                        "type": {"name": "ID", "kind": "SCALAR"},
                                    }
                                ],
                                "type": {"name": "User", "kind": "OBJECT"},
                            }
                        ],
                    },
                    {
                        "name": "User",
                        "kind": "OBJECT",
                        "fields": [
                            {"name": "id", "type": {"name": "ID", "kind": "SCALAR"}}
                        ],
                    },
                ],
            }
        }
    }

    operations = parse_graphql_spec(spec)

    assert len(operations) == 1
    operation = operations[0]
    assert operation.name == "user"
    assert operation.operation_type == "query"
    assert operation.arguments[0].name == "id"
    assert operation.return_type == "User"
    assert operation.fields == []


def test_openapi_parser_raises_for_unresolved_references() -> None:
    spec = {
        "openapi": "3.0.3",
        "paths": {
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MissingUser"}
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    with pytest.raises(ValueError, match="Unresolved OpenAPI reference"):
        parse_openapi_spec(spec)
