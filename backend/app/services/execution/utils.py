"""Utility helpers for execution request construction and authentication merging."""

from __future__ import annotations

from app.schemas.auth import RequestAuthenticationData
from app.services.execution.models import ExecutionRequest


def merge_authentication(
    request: ExecutionRequest,
    auth_data: RequestAuthenticationData | None,
) -> ExecutionRequest:
    """Merge request-level and authentication-level header/query/cookie data."""
    if auth_data is None:
        return request

    return ExecutionRequest(
        endpoint_id=request.endpoint_id,
        method=request.method,
        url=request.url,
        headers={**request.headers, **auth_data.headers},
        query_params={**request.query_params, **auth_data.query_params},
        cookies={**request.cookies, **auth_data.cookies},
        request_body=request.request_body,
        timeout=request.timeout,
    )
