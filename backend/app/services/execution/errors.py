"""Execution-specific exception hierarchy."""

from __future__ import annotations

from typing import Any


class RequestExecutionError(Exception):
    """Base exception for request execution failures."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class UnsupportedMethodError(RequestExecutionError):
    """Raised when a request uses an HTTP method that is not supported."""


class RequestTimeoutError(RequestExecutionError):
    """Raised when a request exceeds the configured timeout."""


class InvalidRequestError(RequestExecutionError):
    """Raised when the request is malformed or not suitable for execution."""
