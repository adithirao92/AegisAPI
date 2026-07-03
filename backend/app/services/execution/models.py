"""Execution models for request dispatch and response normalization."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ExecutionStatus(str, Enum):
    """Execution lifecycle status values."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED_METHOD = "unsupported_method"
    ERROR = "error"


class ExecutionRequest(BaseModel):
    """Model describing an outbound execution request."""

    model_config = ConfigDict(extra="forbid")

    endpoint_id: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    url: HttpUrl
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
    request_body: Any | None = None
    timeout: float = Field(default=30.0, gt=0.0)


class ExecutionError(BaseModel):
    """Structured error information for execution failures."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    """Normalized response returned from a request execution."""

    model_config = ConfigDict(extra="forbid")

    status_code: int | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    response_body: Any | None = None
    response_time_ms: float | None = None
    status: ExecutionStatus = ExecutionStatus.ERROR
    error_details: ExecutionError | None = None
