from app.services.execution.client import HttpClient
from app.services.execution.errors import (
    InvalidRequestError,
    RequestExecutionError,
    RequestTimeoutError,
    UnsupportedMethodError,
)
from app.services.execution.executor import RequestExecutor
from app.services.execution.models import ExecutionRequest, ExecutionResponse


class DummyHttpClient(HttpClient):
    def send(self, request: ExecutionRequest) -> ExecutionResponse:
        return ExecutionResponse(status=ExecutionResponse.model_fields["status"].default)


class DummyRequestExecutor(RequestExecutor):
    def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        return ExecutionResponse(status=ExecutionResponse.model_fields["status"].default)


def test_http_client_interface_accepts_execution_request() -> None:
    client = DummyHttpClient()
    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
    )

    response = client.send(request)

    assert isinstance(response, ExecutionResponse)


def test_request_executor_interface_accepts_execution_request() -> None:
    executor = DummyRequestExecutor()
    request = ExecutionRequest(
        endpoint_id="endpoint-2",
        method="POST",
        url="https://example.com/api/v1/resource",
    )

    response = executor.execute(request)

    assert isinstance(response, ExecutionResponse)


def test_exception_inheritance() -> None:
    assert issubclass(UnsupportedMethodError, RequestExecutionError)
    assert issubclass(RequestTimeoutError, RequestExecutionError)
    assert issubclass(InvalidRequestError, RequestExecutionError)


def test_exceptions_store_details() -> None:
    error = InvalidRequestError("Invalid request", details={"reason": "empty body"})

    assert str(error) == "Invalid request"
    assert error.details == {"reason": "empty body"}
