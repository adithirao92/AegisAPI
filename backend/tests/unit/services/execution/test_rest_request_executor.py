import pytest

from app.schemas.auth import RequestAuthenticationData
from app.services.execution.errors import UnsupportedMethodError
from app.services.execution.models import ExecutionRequest, ExecutionResponse, ExecutionStatus
from app.services.execution.rest_executor import RestRequestExecutor


class DummyHttpClient:
    def __init__(self) -> None:
        self.last_request = None

    def send(self, request: ExecutionRequest) -> ExecutionResponse:
        self.last_request = request
        return ExecutionResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            response_body={"success": True},
            status=ExecutionStatus.SUCCESS,
        )


def test_rest_request_executor_merges_authentication() -> None:
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)
    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="POST",
        url="https://example.com/api/v1/resource",
        headers={"Accept": "application/json"},
        query_params={"page": "1"},
        cookies={"session": "abc"},
        request_body={"key": "value"},
        timeout=10.0,
    )
    auth_data = RequestAuthenticationData(
        headers={"Authorization": "Bearer token"},
        query_params={"debug": "true"},
        cookies={"auth": "yes"},
    )

    response = executor.execute(request, auth_data=auth_data)

    assert response.status == ExecutionStatus.SUCCESS
    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer token"
    assert client.last_request.query_params["debug"] == "true"
    assert client.last_request.cookies["auth"] == "yes"


def test_rest_request_executor_unsupported_method_raises() -> None:
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)
    request = ExecutionRequest(
        endpoint_id="endpoint-2",
        method="OPTIONS",
        url="https://example.com/api/v1/resource",
    )

    with pytest.raises(UnsupportedMethodError):
        executor.execute(request)
