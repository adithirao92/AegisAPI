"""Requests-based HTTP client implementation for the execution layer."""

from __future__ import annotations

import requests
from requests import RequestException

from app.services.execution.errors import RequestExecutionError
from app.services.execution.models import (
    ExecutionError,
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatus,
)
from app.services.execution.client import BaseHttpClient


class RequestsHttpClient(BaseHttpClient):
    """HTTP transport implementation using the requests library."""

    def send(self, request: ExecutionRequest) -> ExecutionResponse:
        """Send an execution request and return a normalized response."""
        try:
            response = requests.request(
                method=request.method,
                url=str(request.url),
                headers=request.headers,
                params=request.query_params,
                cookies=request.cookies,
                json=request.request_body if self._is_json_body(request.request_body) else None,
                data=request.request_body if not self._is_json_body(request.request_body) else None,
                timeout=request.timeout,
            )

            return ExecutionResponse(
                status_code=response.status_code,
                headers={k: v for k, v in response.headers.items()},
                response_body=self._parse_response_body(response),
                response_time_ms=response.elapsed.total_seconds() * 1000,
                status=ExecutionStatus.SUCCESS,
                error_details=None,
            )
        except requests.Timeout as exc:
            return ExecutionResponse(
                status=ExecutionStatus.TIMEOUT,
                error_details=ExecutionError(
                    code="timeout",
                    message=str(exc),
                    details={"request_url": str(request.url)},
                ),
            )
        except requests.RequestException as exc:
            return ExecutionResponse(
                status=ExecutionStatus.ERROR,
                error_details=ExecutionError(
                    code="request_error",
                    message=str(exc),
                    details={"request_url": str(request.url)},
                ),
            )
        except Exception as exc:
            raise RequestExecutionError("Unexpected transport failure", details={"error": str(exc)}) from exc

    def _is_json_body(self, body: object | None) -> bool:
        return body is not None and not isinstance(body, (str, bytes))

    def _parse_response_body(self, response: requests.Response) -> object | str | None:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type.lower():
            try:
                return response.json()
            except ValueError:
                return response.text
        return response.text
