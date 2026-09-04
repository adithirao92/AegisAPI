from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from app.schemas.api_specification import NormalizedEndpoint, ParameterDefinition
from app.schemas.auth import RequestAuthenticationData
from app.services.ai import AttackPlan, ControlledTestExecutionError, ControlledTestExecutor
from app.services.execution.models import ExecutionRequest, ExecutionResponse, ExecutionStatus


@dataclass
class FakeRequestExecutor:
    response: ExecutionResponse
    calls: list[tuple[ExecutionRequest, object | None]] = field(default_factory=list)

    def execute(self, request: ExecutionRequest, auth_data: object | None = None) -> ExecutionResponse:
        self.calls.append((request, auth_data))
        return self.response


def make_endpoint() -> NormalizedEndpoint:
    return NormalizedEndpoint(
        id="users-get",
        endpoint_type="rest",
        path="/users/{id}",
        method="GET",
        parameters=[ParameterDefinition(name="include", location="query")],
    )


def make_plan(**changes: object) -> AttackPlan:
    values: dict[str, object] = {
        "attack_type": "bola",
        "endpoint": "/users/{id}",
        "method": "GET",
        "parameter_name": "id",
        "parameter_location": "path",
        "original_value": "123",
        "test_value": "124",
        "rationale": "Object identifier must be tested using the validated hypothesis.",
        "evidence_required": True,
    }
    values.update(changes)
    return AttackPlan.model_validate(values)


def make_request(**changes: object) -> ExecutionRequest:
    values: dict[str, object] = {
        "endpoint_id": "users-get",
        "method": "GET",
        "url": "https://api.example.test/users/123",
        "query_params": {"include": "profile"},
        "headers": {"X-Request-Id": "original"},
        "cookies": {"session": "existing"},
        "timeout": 5.0,
    }
    values.update(changes)
    return ExecutionRequest.model_validate(values)


def successful_response() -> ExecutionResponse:
    return ExecutionResponse(
        status=ExecutionStatus.SUCCESS,
        status_code=200,
        headers={"content-type": "application/json"},
        response_body={"id": "124"},
    )


def test_valid_bola_plan_translates_only_the_validated_path_value_and_executes() -> None:
    fake_executor = FakeRequestExecutor(successful_response())
    auth_data = RequestAuthenticationData(headers={"Authorization": "Bearer existing-token"})
    original_request = make_request()

    result = ControlledTestExecutor(fake_executor).execute(
        make_plan(),
        make_endpoint(),
        original_request,
        auth_data,
    )

    assert len(fake_executor.calls) == 1
    executed_request, executed_authentication = fake_executor.calls[0]
    assert str(executed_request.url) == "https://api.example.test/users/124"
    assert executed_request.method == "GET"
    assert executed_request.endpoint_id == "users-get"
    assert executed_request.query_params == {"include": "profile"}
    assert executed_request.headers == {"X-Request-Id": "original"}
    assert executed_request.cookies == {"session": "existing"}
    assert executed_authentication is auth_data
    assert result.execution_response == successful_response()
    assert result.execution_status == ExecutionStatus.SUCCESS
    assert result.evidence.original_value == "123"
    assert result.evidence.test_value == "124"
    assert result.evidence.modified_response_body == {"id": "124"}
    assert result.evidence.comparison == "baseline_not_executed"
    assert not hasattr(result, "finding")
    assert not hasattr(result, "vulnerability_confirmed")


def test_query_bola_plan_changes_only_the_validated_query_parameter() -> None:
    fake_executor = FakeRequestExecutor(successful_response())
    endpoint = NormalizedEndpoint(
        id="users-query", endpoint_type="rest", path="/users", method="GET",
        parameters=[ParameterDefinition(name="id", location="query")],
    )
    request = make_request(
        endpoint_id="users-query",
        url="https://api.example.test/users?tenant=blue",
        query_params={"id": "123", "include": "profile"},
    )
    plan = make_plan(endpoint="/users", parameter_name="id", parameter_location="query")

    result = ControlledTestExecutor(fake_executor).execute(plan, endpoint, request)

    assert result.execution_request.query_params == {"id": "124", "include": "profile"}
    assert str(result.execution_request.url) == "https://api.example.test/users?tenant=blue"


@pytest.mark.parametrize(
    ("plan_changes", "request_changes"),
    [
        ({"endpoint": "/admin/{id}"}, {}),
        ({"parameter_name": "owner_id"}, {}),
        ({"method": "POST"}, {}),
        ({}, {"endpoint_id": "another-endpoint"}),
    ],
)
def test_invalid_endpoint_parameter_method_or_source_request_is_rejected(
    plan_changes: dict[str, object], request_changes: dict[str, object],
) -> None:
    fake_executor = FakeRequestExecutor(successful_response())

    with pytest.raises(ControlledTestExecutionError):
        ControlledTestExecutor(fake_executor).execute(
            make_plan(**plan_changes), make_endpoint(), make_request(**request_changes)
        )

    assert fake_executor.calls == []


def test_unsupported_attack_type_is_rejected_without_executor_call() -> None:
    fake_executor = FakeRequestExecutor(successful_response())
    unsupported = AttackPlan.model_construct(**{**make_plan().model_dump(), "attack_type": "ssrf"})

    with pytest.raises(ControlledTestExecutionError, match="Unsupported"):
        ControlledTestExecutor(fake_executor).execute(unsupported, make_endpoint(), make_request())

    assert fake_executor.calls == []


@pytest.mark.parametrize(
    ("status", "expected_indicator"),
    [
        (ExecutionStatus.TIMEOUT, "execution_timeout"),
        (ExecutionStatus.ERROR, "execution_error"),
    ],
)
def test_timeout_and_connection_error_responses_are_preserved(
    status: ExecutionStatus, expected_indicator: str,
) -> None:
    response = ExecutionResponse(status=status)
    result = ControlledTestExecutor(FakeRequestExecutor(response)).execute(
        make_plan(), make_endpoint(), make_request()
    )

    assert result.execution_status == status
    assert result.execution_response == response
    assert result.evidence.indicators == [expected_indicator]
