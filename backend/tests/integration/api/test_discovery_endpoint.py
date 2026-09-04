from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_discovery_endpoint_returns_enriched_endpoints() -> None:
    response = client.post(
        "/api/v1/discovery",
        json={
            "filename": "openapi.json",
            "content": '{"openapi":"3.0.0","paths":{"/users/{id}":{"get":{"responses":{"200":{"description":"ok"}}}}}}',
        },
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["path"] == "/users/{id}"
    assert item["method"] == "GET"
    assert item["enrichment"]["resource_group"] == "users"


def test_discovery_endpoint_returns_friendly_invalid_specification_error() -> None:
    response = client.post(
        "/api/v1/discovery",
        json={"filename": "invalid.json", "content": "{not valid json"},
    )

    assert response.status_code == 400
    assert "Invalid JSON specification" in response.json()["detail"]


def test_discovery_endpoint_rejects_missing_or_ambiguous_sources() -> None:
    response = client.post("/api/v1/discovery", json={})

    assert response.status_code == 400
    assert "exactly one" in response.json()["detail"]
