"""GraphQL request executor implementation."""

from __future__ import annotations

from app.schemas.auth import RequestAuthenticationData
from app.services.execution.client import BaseHttpClient
from app.services.execution.errors import InvalidRequestError
from app.services.execution.executor import RequestExecutor
from app.services.execution.models import ExecutionError, ExecutionRequest, ExecutionResponse, ExecutionStatus
from app.services.execution.utils import merge_authentication


class GraphQLRequestExecutor(RequestExecutor):
    """Execute GraphQL operations via an HTTP client."""

    def __init__(self, http_client: BaseHttpClient) -> None:
        self._http_client = http_client

    def execute(
        self,
        request: ExecutionRequest,
        auth_data: RequestAuthenticationData | None = None,
    ) -> ExecutionResponse:
        """Execute a GraphQL request and normalize the response."""
        self._validate_request(request)

        executable_request = self._build_graphql_request(request)
        merged_request = merge_authentication(executable_request, auth_data)
        response = self._http_client.send(merged_request)
        return self._normalize_response(response)

    def _validate_request(self, request: ExecutionRequest) -> None:
        if request.method.upper() != "POST":
            raise InvalidRequestError("GraphQL requests must use POST")

        if not request.request_body or not isinstance(request.request_body, dict):
            raise InvalidRequestError("GraphQL request body must be a mapping containing 'query' or 'mutation'")

        if "query" not in request.request_body and "mutation" not in request.request_body:
            raise InvalidRequestError("GraphQL request body must include either 'query' or 'mutation'")

    def _build_graphql_request(self, request: ExecutionRequest) -> ExecutionRequest:
        payload = request.request_body
        graphql_body: dict[str, object] = {}

        if "query" in payload:
            graphql_body["query"] = payload["query"]
        if "mutation" in payload:
            graphql_body["query"] = payload["mutation"]
        if "variables" in payload:
            graphql_body["variables"] = payload["variables"]
        if "operationName" in payload:
            graphql_body["operationName"] = payload["operationName"]

        return ExecutionRequest(
            endpoint_id=request.endpoint_id,
            method=request.method,
            url=request.url,
            headers={**request.headers, "Content-Type": "application/json"},
            query_params=request.query_params,
            cookies=request.cookies,
            request_body=graphql_body,
            timeout=request.timeout,
        )

    def _normalize_response(self, response: ExecutionResponse) -> ExecutionResponse:
        if response.status_code is None or response.status_code >= 400:
            return response

        body = response.response_body
        if isinstance(body, dict) and "errors" in body:
            return ExecutionResponse(
                status_code=response.status_code,
                headers=response.headers,
                response_body=body,
                response_time_ms=response.response_time_ms,
                status=ExecutionStatus.FAILURE,
                error_details=ExecutionError(
                    code="graphql_errors",
                    message="GraphQL returned errors",
                    details={"errors": body["errors"]},
                ),
            )

        return ExecutionResponse(
            status_code=response.status_code,
            headers=response.headers,
            response_body=body,
            response_time_ms=response.response_time_ms,
            status=ExecutionStatus.SUCCESS,
            error_details=None,
        )
