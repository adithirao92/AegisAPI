from __future__ import annotations

from app.schemas.auth import (
    AuthenticationContext,
    AuthenticationType,
    AuthenticationValidationStatus,
)
from app.services.auth.auth_injector import AuthenticationInjector
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


def make_context(
    auth_type: AuthenticationType,
    metadata: dict[str, str],
) -> AuthenticationContext:
    return AuthenticationContext(
        endpoint_id="endpoint-1",
        authentication_type=auth_type,
        profile_id="profile-1",
        validation_status=AuthenticationValidationStatus.VALID,
        credential_metadata=metadata,
    )


def test_rest_executor_apikey_header_injection() -> None:
    injector = AuthenticationInjector()
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)

    auth_context = make_context(
        AuthenticationType.API_KEY,
        {
            "location": "header",
            "key_name": "X-Api-Key",
            "value": "secret-value",
        },
    )
    auth_data = injector.build_request_auth(auth_context)

    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
    )

    executor.execute(request, auth_data=auth_data)

    assert client.last_request is not None
    assert client.last_request.headers["X-Api-Key"] == "secret-value"


def test_rest_executor_bearer_token_authorization_header() -> None:
    injector = AuthenticationInjector()
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)

    auth_context = make_context(
        AuthenticationType.BEARER_TOKEN,
        {
            "token": "bearer-token",
            "header_name": "Authorization",
            "prefix": "Bearer",
        },
    )
    auth_data = injector.build_request_auth(auth_context)

    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
    )

    executor.execute(request, auth_data=auth_data)

    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer bearer-token"


def test_rest_executor_jwt_authorization_header() -> None:
    injector = AuthenticationInjector()
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)

    auth_context = make_context(
        AuthenticationType.JWT,
        {
            "token": "jwt-token",
            "header_name": "Authorization",
            "prefix": "Bearer",
        },
    )
    auth_data = injector.build_request_auth(auth_context)

    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
    )

    executor.execute(request, auth_data=auth_data)

    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer jwt-token"


def test_rest_executor_query_parameter_injection() -> None:
    injector = AuthenticationInjector()
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)

    auth_context = make_context(
        AuthenticationType.API_KEY,
        {
            "location": "query",
            "key_name": "api_key",
            "value": "query-value",
        },
    )
    auth_data = injector.build_request_auth(auth_context)

    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
    )

    executor.execute(request, auth_data=auth_data)

    assert client.last_request is not None
    assert client.last_request.query_params["api_key"] == "query-value"


def test_rest_executor_cookie_injection() -> None:
    injector = AuthenticationInjector()
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)

    auth_context = make_context(
        AuthenticationType.API_KEY,
        {
            "location": "cookie",
            "key_name": "session_id",
            "value": "cookie-value",
        },
    )
    auth_data = injector.build_request_auth(auth_context)

    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
    )

    executor.execute(request, auth_data=auth_data)

    assert client.last_request is not None
    assert client.last_request.cookies["session_id"] == "cookie-value"


def test_rest_executor_preserves_existing_request_data() -> None:
    injector = AuthenticationInjector()
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)

    auth_context = make_context(
        AuthenticationType.API_KEY,
        {
            "location": "header",
            "key_name": "X-Api-Key",
            "value": "secret-value",
        },
    )
    auth_data = injector.build_request_auth(auth_context)

    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
        headers={"Accept": "application/json"},
        query_params={"page": "1"},
        cookies={"session": "abc"},
    )

    executor.execute(request, auth_data=auth_data)

    assert client.last_request is not None
    assert client.last_request.headers["Accept"] == "application/json"
    assert client.last_request.query_params["page"] == "1"
    assert client.last_request.cookies["session"] == "abc"
    assert client.last_request.headers["X-Api-Key"] == "secret-value"


def test_rest_executor_conflict_resolution_prefers_auth_data() -> None:
    injector = AuthenticationInjector()
    client = DummyHttpClient()
    executor = RestRequestExecutor(client)

    auth_context = make_context(
        AuthenticationType.BEARER_TOKEN,
        {
            "token": "new-token",
            "header_name": "Authorization",
            "prefix": "Bearer",
        },
    )
    auth_data = injector.build_request_auth(auth_context)

    request = ExecutionRequest(
        endpoint_id="endpoint-1",
        method="GET",
        url="https://example.com/api/v1/resource",
        headers={"Authorization": "OldValue"},
        query_params={"page": "1"},
        cookies={"session": "old-cookie"},
    )

    # Add conflicting auth values for header/query/cookie
    auth_data.query_params["page"] = "2"
    auth_data.cookies["session"] = "new-cookie"

    executor.execute(request, auth_data=auth_data)

    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer new-token"
    assert client.last_request.query_params["page"] == "2"
    assert client.last_request.cookies["session"] == "new-cookie"
