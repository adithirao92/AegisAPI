"""Trusted, in-memory inputs for controlled AI test execution.

Contexts are registered by server-side orchestration only. They deliberately
have no API serialization or registration route: a browser receives only the
opaque context identifier and cannot provide a URL, headers, or credentials.
"""

from __future__ import annotations

from threading import Lock
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from app.schemas.api_specification import NormalizedEndpoint
from app.schemas.auth import RequestAuthenticationData
from app.services.execution.models import ExecutionRequest


class ControlledTestContext(BaseModel):
    """Server-established inputs required by one controlled test execution."""

    model_config = ConfigDict(extra="forbid")

    endpoint: NormalizedEndpoint
    original_request: ExecutionRequest
    auth_data: RequestAuthenticationData | None = None


class ControlledTestContextStore:
    """Ephemeral registry of trusted execution contexts; it is not persistence."""

    def __init__(self) -> None:
        self._contexts: dict[str, ControlledTestContext] = {}
        self._lock = Lock()

    def register(self, context: ControlledTestContext) -> str:
        """Store trusted server-side input and return an opaque context identifier."""
        context_id = str(uuid4())
        with self._lock:
            self._contexts[context_id] = context
        return context_id

    def get(self, context_id: str) -> ControlledTestContext:
        """Return a trusted context or raise ``KeyError`` when it is unavailable."""
        with self._lock:
            try:
                return self._contexts[context_id]
            except KeyError as exc:
                raise KeyError("Controlled test context was not found.") from exc
