import pytest

from app.schemas.auth import (
    AuthenticationContext,
    AuthenticationType,
    AuthenticationValidationStatus,
    RequestAuthenticationData,
)
from app.services.auth.auth_injector import AuthenticationInjector
from app.services.execution.errors import InvalidRequestError
from app.services.execution.graphql_executor import GraphQLRequestExecutor
from app.services.execution.models import ExecutionRequest, ExecutionResponse, ExecutionStatus


class DummyHttpClient:
    def __init__(self) -> None:
        self.last_request = None
        self.response = ExecutionResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            response_body={"data": {"user": {"id": "1"}}},
            status=ExecutionStatus.SUCCESS,
            response_time_ms=10.0,
        )

    def send(self, request: ExecutionRequest) -> ExecutionResponse:
        self.last_request = request
        return self.response


def make_context(auth_type: AuthenticationType, metadata: dict[str, str]) -> AuthenticationContext:
    return AuthenticationContext(
        endpoint_id="endpoint-1",
        authentication_type=auth_type,
        profile_id="profile-1",
        validation_status=AuthenticationValidationStatus.VALID,
        credential_metadata=metadata,
    )


def test_graphql_query_execution() -> None:
    client = DummyHttpClient()
    executor = GraphQLRequestExecutor(client)
    request = ExecutionRequest(
        endpoint_id="graphql-1",
        method="POST",
        url="https://example.com/graphql",
        request_body={"query": "query { user { id } }"},
    )

    response = executor.execute(request)

    assert response.status == ExecutionStatus.SUCCESS
    assert response.response_body == {"data": {"user": {"id": "1"}}}
    assert client.last_request is not None
    assert client.last_request.request_body == {"query": "query { user { id } }"}
    assert client.last_request.headers["Content-Type"] == "application/json"


def test_graphql_mutation_execution() -> None:
    client = DummyHttpClient()
    executor = GraphQLRequestExecutor(client)
    request = ExecutionRequest(
        endpoint_id="graphql-2",
        method="POST",
        url="https://example.com/graphql",
        request_body={
            "mutation": "mutation { updateUser(id: 1) { id } }",
            "operationName": "UpdateUser",
            "variables": {"id": 1},
        },
    )

    response = executor.execute(request)

    assert response.status == ExecutionStatus.SUCCESS
    assert client.last_request is not None
    assert client.last_request.request_body["query"] == "mutation { updateUser(id: 1) { id } }"
    assert client.last_request.request_body["operationName"] == "UpdateUser"
    assert client.last_request.request_body["variables"] == {"id": 1}


def test_graphql_error_response_is_normalized_to_failure() -> None:
    client = DummyHttpClient()
    client.response = ExecutionResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        response_body={"errors": [{"message": "Bad request"}]},
        status=ExecutionStatus.SUCCESS,
        response_time_ms=20.0,
    )
    executor = GraphQLRequestExecutor(client)
    request = ExecutionRequest(
        endpoint_id="graphql-3",
        method="POST",
        url="https://example.com/graphql",
        request_body={"query": "query { invalid }"},
    )

    response = executor.execute(request)

    assert response.status == ExecutionStatus.FAILURE
    assert response.error_details is not None
    assert response.error_details.code == "graphql_errors"
    assert response.error_details.details == {"errors": [{"message": "Bad request"}]}
    assert response.response_body == {"errors": [{"message": "Bad request"}]}


def test_graphql_http_failure_propagates() -> None:
    client = DummyHttpClient()
    client.response = ExecutionResponse(
        status_code=500,
        headers={"Content-Type": "application/json"},
        response_body={"message": "Server error"},
        status=ExecutionStatus.ERROR,
        response_time_ms=15.0,
        error_details=None,
    )
    executor = GraphQLRequestExecutor(client)
    request = ExecutionRequest(
        endpoint_id="graphql-4",
        method="POST",
        url="https://example.com/graphql",
        request_body={"query": "query { user { id } }"},
    )

    response = executor.execute(request)

    assert response.status == ExecutionStatus.ERROR
    assert response.status_code == 500
    assert response.response_body == {"message": "Server error"}


def test_graphql_request_requires_post() -> None:
    client = DummyHttpClient()
    executor = GraphQLRequestExecutor(client)
    request = ExecutionRequest(
        endpoint_id="graphql-5",
        method="GET",
        url="https://example.com/graphql",
        request_body={"query": "query { user { id } }"},
    )

    with pytest.raises(InvalidRequestError):
        executor.execute(request)


def test_graphql_authentication_integration() -> None:
    injector = AuthenticationInjector()
    client = DummyHttpClient()
    executor = GraphQLRequestExecutor(client)

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
        endpoint_id="graphql-6",
        method="POST",
        url="https://example.com/graphql",
        request_body={"query": "query { user { id } }"},
    )

    executor.execute(request, auth_data=auth_data)

    assert client.last_request is not None
    assert client.last_request.headers["Authorization"] == "Bearer bearer-token"
    assert client.last_request.headers["Content-Type"] == "application/json"
