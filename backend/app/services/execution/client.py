"""HTTP client abstractions for execution transport layers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.execution.models import ExecutionRequest, ExecutionResponse


class BaseHttpClient(ABC):
    """Interface for transport clients that send execution requests."""

    @abstractmethod
    def send(self, request: ExecutionRequest) -> ExecutionResponse:
        """Send an execution request and return a normalized response."""
        raise NotImplementedError


HttpClient = BaseHttpClient
