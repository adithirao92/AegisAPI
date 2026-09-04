"""Integration coverage for the Phase 11 controlled-test HTTP adapter."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes.ai import (
    get_controlled_test_context_store,
    get_controlled_test_executor,
)
from app.main import app
from app.schemas.api_specification import NormalizedEndpoint, ParameterDefinition
from app.schemas.auth import RequestAuthenticationData
from app.services.ai.execution import (
    AttackExecutionEvidence,
    ControlledTestExecutionResult,
)
from app.services.ai.models import AttackPlan
from app.services.ai.test_context import ControlledTestContext, ControlledTestContextStore
from app.services.execution.errors import InvalidRequestError
from app.services.execution.models import ExecutionRequest, ExecutionResponse, ExecutionStatus


@dataclass
class FakeControlledTestExecutor:
    response: ExecutionResponse
    calls: list[dict[str, object]] = field(default_factory=list)

    def execute(
        self,
        attack_plan: AttackPlan,
        endpoint: NormalizedEndpoint,
        original_request: ExecutionRequest,
        auth_data: RequestAuthenticationData | None = None,
    ) -> ControlledTestExecutionResult:
        self.calls.append(
            {
                "attack_plan": attack_plan,
                "endpoint": endpoint,
                "original_request": original_request,
                "auth_data": auth_data,
            }
        )
        controlled_request = original_request.model_copy(
            update={"url": "https://api.example.test/users/124"}
        )
        return ControlledTestExecutionResult(
            attack_plan=attack_plan,
            execution_request=controlled_request,
            execution_response=self.response,
            execution_status=self.response.status,
            evidence=AttackExecutionEvidence(
                original_value=attack_plan.original_value,
                test_value=attack_plan.test_value,
                modified_response_status=self.response.status_code,
                modified_response_body=self.response.response_body,
                modified_response_headers=self.response.headers,
                indicators=["http_response_captured"],
            ),
        )


def make_context() -> ControlledTestContext:
    return ControlledTestContext(
        endpoint=NormalizedEndpoint(
            id="users-get",
            endpoint_type="rest",
            path="/users/{id}",
            method="GET",
            parameters=[ParameterDefinition(name="include", location="query")],
        ),
        original_request=ExecutionRequest(
            endpoint_id="users-get",
            method="GET",
            url="https://api.example.test/users/123",
            query_params={"include": "profile"},
            headers={"X-Server-Request": "trusted"},
        ),
        auth_data=RequestAuthenticationData(headers={"Authorization": "Bearer server-managed-token"}),
    )


def make_plan(**changes: object) -> dict[str, object]:
    plan: dict[str, object] = {
        "attack_type": "bola",
        "endpoint": "/users/{id}",
        "method": "GET",
        "parameter_name": "id",
        "parameter_location": "path",
        "original_value": "123",
        "test_value": "124",
        "rationale": "Test the validated user object identifier.",
        "evidence_required": True,
    }
    plan.update(changes)
    return plan


@pytest.fixture
def controlled_test_client() -> tuple[TestClient, ControlledTestContextStore, FakeControlledTestExecutor]:
    contexts = ControlledTestContextStore()
    executor = FakeControlledTestExecutor(
        ExecutionResponse(
            status=ExecutionStatus.SUCCESS,
            status_code=200,
            headers={"content-type": "application/json"},
            response_body={"id": "124"},
        )
    )
    app.dependency_overrides[get_controlled_test_context_store] = lambda: contexts
    app.dependency_overrides[get_controlled_test_executor] = lambda: executor
    try:
        yield TestClient(app), contexts, executor
    finally:
        app.dependency_overrides.clear()


def test_valid_controlled_bola_test_invokes_executor_and_returns_evidence(
    controlled_test_client: tuple[TestClient, ControlledTestContextStore, FakeControlledTestExecutor],
) -> None:
    client, contexts, executor = controlled_test_client
    context_id = contexts.register(make_context())

    response = client.post("/api/v1/ai/test", json={"context_id": context_id, "attack_plan": make_plan()})

    assert response.status_code == 200
    payload = response.json()
    assert payload["execution_status"] == "success"
    assert payload["execution_response"]["status_code"] == 200
    assert payload["evidence"]["original_value"] == "123"
    assert payload["evidence"]["test_value"] == "124"
    assert len(executor.calls) == 1
    assert executor.calls[0]["auth_data"] == make_context().auth_data
    assert "execution_request" not in payload
    assert "ScanFinding" not in str(payload)
    assert "vulnerability_confirmed" not in payload


@pytest.mark.parametrize(
    "changes",
    [
        {"endpoint": "/admin/{id}"},
        {"parameter_name": "owner_id"},
    ],
)
def test_invalid_endpoint_or_parameter_is_rejected(
    controlled_test_client: tuple[TestClient, ControlledTestContextStore, FakeControlledTestExecutor],
    changes: dict[str, object],
) -> None:
    client, contexts, executor = controlled_test_client
    context_id = contexts.register(make_context())

    response = client.post(
        "/api/v1/ai/test", json={"context_id": context_id, "attack_plan": make_plan(**changes)}
    )

    assert response.status_code == 422
    assert executor.calls == []


def test_invalid_or_unsupported_attack_plan_is_rejected(
    controlled_test_client: tuple[TestClient, ControlledTestContextStore, FakeControlledTestExecutor],
) -> None:
    client, contexts, executor = controlled_test_client
    context_id = contexts.register(make_context())

    response = client.post(
        "/api/v1/ai/test",
        json={"context_id": context_id, "attack_plan": make_plan(attack_type="ssrf")},
    )

    assert response.status_code == 422
    assert executor.calls == []


def test_execution_failure_is_returned_as_evidence_without_a_verdict(
    controlled_test_client: tuple[TestClient, ControlledTestContextStore, FakeControlledTestExecutor],
) -> None:
    client, contexts, executor = controlled_test_client
    executor.response = ExecutionResponse(status=ExecutionStatus.ERROR)
    context_id = contexts.register(make_context())

    response = client.post("/api/v1/ai/test", json={"context_id": context_id, "attack_plan": make_plan()})

    assert response.status_code == 200
    payload = response.json()
    assert payload["execution_status"] == "error"
    assert payload["execution_response"]["status"] == "error"
    assert "finding" not in payload
    assert "confirmed" not in payload


def test_expected_execution_exception_returns_a_safe_client_error(
    controlled_test_client: tuple[TestClient, ControlledTestContextStore, FakeControlledTestExecutor],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, contexts, executor = controlled_test_client
    context_id = contexts.register(make_context())

    def reject_execution(**_: object) -> ControlledTestExecutionResult:
        raise InvalidRequestError("Internal request detail must not be exposed")

    monkeypatch.setattr(executor, "execute", reject_execution)
    response = client.post("/api/v1/ai/test", json={"context_id": context_id, "attack_plan": make_plan()})

    assert response.status_code == 422
    assert response.json()["detail"] == "Controlled test execution could not be completed."
