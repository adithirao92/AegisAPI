from pathlib import Path

import pytest

from app.services.discovery.engine import APIDiscoveryService


@pytest.fixture
def service() -> APIDiscoveryService:
    return APIDiscoveryService()


def test_discovery_service_parses_openapi_json(tmp_path: Path, service: APIDiscoveryService) -> None:
    spec_path = tmp_path / "petstore.json"
    spec_path.write_text(
        '{"openapi":"3.0.3","paths":{"/pets":{"get":{"operationId":"listPets","responses":{"200":{"description":"ok"}}}}}}',
        encoding="utf-8",
    )

    catalog = service.discover([spec_path])

    assert len(catalog.endpoints) == 1
    assert catalog.endpoints[0].path == "/pets"
    assert catalog.endpoints[0].method == "GET"


def test_discovery_service_parses_openapi_yaml(tmp_path: Path, service: APIDiscoveryService) -> None:
    spec_path = tmp_path / "petstore.yaml"
    spec_path.write_text(
        "openapi: 3.0.3\npaths:\n  /pets:\n    get:\n      operationId: listPets\n      responses:\n        '200':\n          description: ok\n",
        encoding="utf-8",
    )

    catalog = service.discover([spec_path])

    assert len(catalog.endpoints) == 1
    assert catalog.endpoints[0].path == "/pets"
    assert catalog.endpoints[0].method == "GET"


def test_discovery_service_parses_graphql_sdl(tmp_path: Path, service: APIDiscoveryService) -> None:
    spec_path = tmp_path / "schema.graphql"
    spec_path.write_text("type Query { user(id: ID): User }\ntype User { id: ID }\n", encoding="utf-8")

    catalog = service.discover([spec_path])

    assert len(catalog.operations) == 1
    assert catalog.operations[0].name == "user"
    assert catalog.operations[0].operation_type == "query"


def test_discovery_service_parses_graphql_introspection(tmp_path: Path, service: APIDiscoveryService) -> None:
    spec_path = tmp_path / "schema.json"
    spec_path.write_text(
        '{"data":{"__schema":{"queryType":{"name":"Query"},"types":[{"name":"Query","kind":"OBJECT","fields":[{"name":"user","args":[],"type":{"name":"User","kind":"OBJECT"}}]},{"name":"User","kind":"OBJECT","fields":[{"name":"id","type":{"name":"ID","kind":"SCALAR"}}]}]}}}',
        encoding="utf-8",
    )

    catalog = service.discover([spec_path])

    assert len(catalog.operations) == 1
    assert catalog.operations[0].name == "user"
    assert catalog.operations[0].operation_type == "query"


def test_discovery_service_rejects_invalid_or_unsupported_files(tmp_path: Path, service: APIDiscoveryService) -> None:
    spec_path = tmp_path / "unsupported.txt"
    spec_path.write_text("not a spec", encoding="utf-8")

    with pytest.raises(ValueError):
        service.discover([spec_path])
