"""Strict, non-executing attack-planning contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AttackPlan(BaseModel):
    """A BOLA test hypothesis; this is never a vulnerability finding."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    attack_type: Literal["bola"]
    endpoint: str = Field(min_length=1)
    method: str = Field(min_length=1)
    parameter_name: str = Field(min_length=1)
    parameter_location: Literal["path", "query"]
    original_value: str = Field(min_length=1)
    test_value: str = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=1000)
    evidence_required: bool


class ValidationResult(BaseModel):
    """Controlled result returned by the attack-plan trust boundary."""

    model_config = ConfigDict(extra="forbid")

    plan: AttackPlan | None = None
    errors: list[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.plan is not None and not self.errors


class PlanningResult(BaseModel):
    """Controlled result from a planner; plans require validator approval."""

    model_config = ConfigDict(extra="forbid")

    plans: list[AttackPlan] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
