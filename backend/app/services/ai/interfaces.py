"""Provider-neutral attack planning interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.api_specification import NormalizedEndpoint
from app.services.ai.models import PlanningResult


class AttackPlanner(ABC):
    """Generate bounded attack hypotheses from one discovered endpoint."""

    @abstractmethod
    def plan(self, endpoint: NormalizedEndpoint) -> PlanningResult:
        """Return validated planning hypotheses without executing any request."""
        raise NotImplementedError
