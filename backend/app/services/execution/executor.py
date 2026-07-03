"""Request executor abstractions for specific execution strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.auth import RequestAuthenticationData
from app.services.execution.models import ExecutionRequest, ExecutionResponse


class RequestExecutor(ABC):
    """Interface for executors that perform a single request execution."""

    @abstractmethod
    def execute(
        self,
        request: ExecutionRequest,
        auth_data: RequestAuthenticationData | None = None,
    ) -> ExecutionResponse:
        """Execute a request and return a normalized response."""
        raise NotImplementedError
