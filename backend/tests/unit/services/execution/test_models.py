from datetime import datetime

import pytest

from app.services.execution.models import (
    ExecutionError,
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatus,
)


def test_execution_request_creates_with_defaults() -> None:
    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
    )

    assert request.endpoint_id == "endpoint-1"
    assert request.method == "GET"
    assert str(request.url) == "https://example.com/api/v1/resource"
    assert request.headers == {}
    assert request.query_params == {}
    assert request.cookies == {}
    assert request.request_body is None
    assert request.timeout == 30.0


def test_execution_request_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError):
        ExecutionRequest(
            endpoint_id="endpoint-2",
            method="POST",
            url="https://example.com/api/v1/resource",
            timeout=0,
        )


def test_execution_error_creates_with_details() -> None:
    error = ExecutionError(
        code="timeout",
        message="Request timed out",
        details={"timeout_seconds": 10},
    )

    assert error.code == "timeout"
    assert error.message == "Request timed out"
    assert error.details == {"timeout_seconds": 10}


def test_execution_response_defaults_to_error() -> None:
    response = ExecutionResponse()

    assert response.status == ExecutionStatus.ERROR
    assert response.status_code is None
    assert response.headers == {}
    assert response.response_body is None
    assert response.response_time_ms is None
    assert response.error_details is None


def test_execution_response_accepts_success_values() -> None:
    response = ExecutionResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        response_body={"ok": True},
        response_time_ms=123.45,
        status=ExecutionStatus.SUCCESS,
    )

    assert response.status == ExecutionStatus.SUCCESS
    assert response.status_code == 200
    assert response.headers == {"Content-Type": "application/json"}
    assert response.response_body == {"ok": True}
    assert response.response_time_ms == 123.45
