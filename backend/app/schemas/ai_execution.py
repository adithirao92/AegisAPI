"""HTTP contracts for controlled AI test execution."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.services.ai.execution import AttackExecutionEvidence, ControlledTestExecutionResult
from app.services.ai.models import AttackPlan
from app.services.execution.models import ExecutionResponse, ExecutionStatus


class ControlledTestRequest(BaseModel):
    """Browser-safe request: plan plus a server-issued context reference only."""

    model_config = ConfigDict(extra="forbid")

    context_id: UUID
    attack_plan: AttackPlan


class ControlledTestResponse(BaseModel):
    """Evidence-only result; it intentionally omits execution request secrets."""

    model_config = ConfigDict(extra="forbid")

    attack_plan: AttackPlan
    execution_status: ExecutionStatus
    execution_response: ExecutionResponse
    evidence: AttackExecutionEvidence

    @classmethod
    def from_result(cls, result: ControlledTestExecutionResult) -> "ControlledTestResponse":
        """Expose the safe subset of a Phase 11 execution result."""
        return cls(
            attack_plan=result.attack_plan,
            execution_status=result.execution_status,
            execution_response=result.execution_response,
            evidence=result.evidence,
        )
