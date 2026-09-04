"""Trust boundary for LLM-generated attack plans."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from pydantic import ValidationError

from app.schemas.api_specification import NormalizedEndpoint
from app.services.ai.models import AttackPlan, ValidationResult


class AttackPlanValidator:
    """Reject any plan that is not an exact hypothesis for supplied endpoint data."""

    def validate(
        self,
        plan: AttackPlan | dict[str, Any],
        endpoints: Sequence[NormalizedEndpoint],
    ) -> ValidationResult:
        """Validate a candidate without repairing hallucinated values."""
        try:
            raw_plan = plan.model_dump() if isinstance(plan, AttackPlan) else plan
            parsed_plan = AttackPlan.model_validate(raw_plan)
        except ValidationError as exc:
            return ValidationResult(errors=[f"Invalid attack plan: {error['msg']}" for error in exc.errors()])

        matching_endpoint = next(
            (endpoint for endpoint in endpoints if endpoint.path == parsed_plan.endpoint),
            None,
        )
        if matching_endpoint is None:
            return ValidationResult(errors=["Plan references an endpoint outside the discovered catalog."])
        if matching_endpoint.endpoint_type != "rest":
            return ValidationResult(errors=["BOLA planning supports REST endpoints only."])
        if matching_endpoint.method != parsed_plan.method:
            return ValidationResult(errors=["Plan method does not match the discovered endpoint."])
        if parsed_plan.original_value == parsed_plan.test_value:
            return ValidationResult(errors=["Plan test_value must differ from original_value."])
        if not self._parameter_exists(matching_endpoint, parsed_plan.parameter_name, parsed_plan.parameter_location):
            return ValidationResult(errors=["Plan parameter does not match the discovered endpoint."])
        return ValidationResult(plan=parsed_plan)

    def _parameter_exists(self, endpoint: NormalizedEndpoint, name: str, location: str) -> bool:
        if location == "path":
            path_names = {
                segment[1:-1]
                for segment in (endpoint.path or "").split("/")
                if segment.startswith("{") and segment.endswith("}")
            }
            if name in path_names:
                return True
        return any(parameter.name == name and parameter.location.lower() == location for parameter in endpoint.parameters)
