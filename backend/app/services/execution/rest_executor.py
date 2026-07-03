"""REST request executor for HTTP execution flows."""

from __future__ import annotations

from typing import cast

from app.schemas.auth import RequestAuthenticationData
from app.services.execution.client import BaseHttpClient
from app.services.execution.errors import (
    InvalidRequestError,
    UnsupportedMethodError,
)
from app.services.execution.models import ExecutionRequest, ExecutionResponse
from app.services.execution.models import ExecutionStatus
from app.services.execution.errors import RequestExecutionError

SUPPORTED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


class RestRequestExecutor:
    """Execute REST requests using a configured HTTP client."""

    def __init__(self, http_client: BaseHttpClient) -> None:
        self._http_client = http_client

    def execute(
        self,
        request: ExecutionRequest,
        auth_data: RequestAuthenticationData | None = None,
    ) -> ExecutionResponse:
        """Execute a REST request and return a normalized response."""
        self._validate_request(request)
        merged_request = self._merge_authentication(request, auth_data)
        return self._http_client.send(merged_request)

    def _validate_request(self, request: ExecutionRequest) -> None:
        if request.method.upper() not in SUPPORTED_METHODS:
            raise UnsupportedMethodError(
                f"HTTP method not supported: {request.method}",
                details={"method": request.method},
            )

        if not request.endpoint_id:
            raise InvalidRequestError("ExecutionRequest.endpoint_id is required")

        if not request.url:
            raise InvalidRequestError("ExecutionRequest.url is required")

    def _merge_authentication(
        self,
        request: ExecutionRequest,
        auth_data: RequestAuthenticationData | None,
    ) -> ExecutionRequest:
        if auth_data is None:
            return request

        merged_headers = {**request.headers, **auth_data.headers}
        merged_query_params = {**request.query_params, **auth_data.query_params}
        merged_cookies = {**request.cookies, **auth_data.cookies}

        return ExecutionRequest(
            endpoint_id=request.endpoint_id,
            method=request.method,
            url=str(request.url),
            headers=merged_headers,
            query_params=merged_query_params,
            cookies=merged_cookies,
            request_body=request.request_body,
            timeout=request.timeout,
        )
