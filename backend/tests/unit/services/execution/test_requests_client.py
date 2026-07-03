from unittest.mock import MagicMock, patch

import pytest

from app.services.execution.models import ExecutionRequest, ExecutionResponse, ExecutionStatus
from app.services.execution.requests_client import RequestsHttpClient


def make_request() -> ExecutionRequest:
    return ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
        headers={"Accept": "application/json"},
        query_params={"q": "test"},
        cookies={"session": "abc"},
        request_body={"key": "value"},
        timeout=10.0,
    )


@patch("app.services.execution.requests_client.requests.request")
def test_requests_http_client_success(mock_request: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"ok": True}
    mock_response.text = "{\"ok\": true}"
    mock_response.elapsed.total_seconds.return_value = 0.123
    mock_request.return_value = mock_response

    client = RequestsHttpClient()
    response = client.send(make_request())

    assert response.status == ExecutionStatus.SUCCESS
    assert response.status_code == 200
    assert response.response_body == {"ok": True}
    assert response.headers == {"Content-Type": "application/json"}
    assert response.response_time_ms == 123.0


@patch("app.services.execution.requests_client.requests.request")
def test_requests_http_client_timeout(mock_request: MagicMock) -> None:
    from requests import Timeout

    mock_request.side_effect = Timeout("timed out")

    client = RequestsHttpClient()
    response = client.send(make_request())

    assert response.status == ExecutionStatus.TIMEOUT
    assert response.error_details is not None
    assert response.error_details.code == "timeout"


@patch("app.services.execution.requests_client.requests.request")
def test_requests_http_client_connection_error(mock_request: MagicMock) -> None:
    from requests import RequestException

    mock_request.side_effect = RequestException("connect failed")

    client = RequestsHttpClient()
    response = client.send(make_request())

    assert response.status == ExecutionStatus.ERROR
    assert response.error_details is not None
    assert response.error_details.code == "request_error"


@patch("app.services.execution.requests_client.requests.request")
def test_requests_http_client_invalid_json_responds_text(mock_request: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.side_effect = ValueError("invalid json")
    mock_response.text = "not json"
    mock_response.elapsed.total_seconds.return_value = 0.045
    mock_request.return_value = mock_response

    client = RequestsHttpClient()
    response = client.send(make_request())

    assert response.response_body == "not json"
