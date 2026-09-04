"""Local Ollama adapter for bounded BOLA test planning."""

from __future__ import annotations

import json
from typing import Any

import requests

from app.config.settings import settings
from app.schemas.api_specification import NormalizedEndpoint
from app.services.ai.interfaces import AttackPlanner
from app.services.ai.models import AttackPlan, PlanningResult
from app.services.ai.prompts import build_bola_prompt
from app.services.ai.validator import AttackPlanValidator


class OllamaAttackPlanner(AttackPlanner):
    """Generate and validate local-model BOLA hypotheses; never execute them."""

    def __init__(
        self,
        validator: AttackPlanValidator | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._validator = validator or AttackPlanValidator()
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.ollama_model
        self._timeout_seconds = timeout_seconds or settings.ollama_timeout_seconds

    def plan(self, endpoint: NormalizedEndpoint) -> PlanningResult:
        """Return only validator-approved BOLA plans for a discovered REST endpoint."""
        if not self._has_bola_candidate(endpoint):
            return PlanningResult()

        try:
            response = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": build_bola_prompt(endpoint),
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0},
                },
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            return PlanningResult(errors=["Local Ollama planner is unavailable. No attack plan was generated."])
        except ValueError:
            return PlanningResult(errors=["Ollama returned a malformed response. No attack plan was generated."])

        candidates, parse_error = self._parse_candidates(payload)
        if parse_error:
            return PlanningResult(errors=[parse_error])

        valid_plans: list[AttackPlan] = []
        errors: list[str] = []
        for candidate in candidates:
            validation = self._validator.validate(candidate, [endpoint])
            if validation.is_valid and validation.plan is not None:
                valid_plans.append(validation.plan)
            else:
                errors.extend(validation.errors)
        return PlanningResult(plans=valid_plans, errors=errors)

    def _parse_candidates(self, payload: Any) -> tuple[list[dict[str, Any]], str | None]:
        if not isinstance(payload, dict) or "response" not in payload:
            return [], "Ollama returned a malformed response. No attack plan was generated."
        response_content = payload["response"]
        try:
            document = json.loads(response_content) if isinstance(response_content, str) else response_content
        except json.JSONDecodeError:
            return [], "Ollama returned malformed JSON. No attack plan was generated."
        if not isinstance(document, dict) or set(document) != {"plans"} or not isinstance(document["plans"], list):
            return [], "Ollama returned an invalid plan envelope. No attack plan was generated."
        if not all(isinstance(plan, dict) for plan in document["plans"]):
            return [], "Ollama returned an invalid attack plan. No attack plan was generated."
        return document["plans"], None

    def _has_bola_candidate(self, endpoint: NormalizedEndpoint) -> bool:
        if endpoint.endpoint_type != "rest" or not endpoint.path or not endpoint.method:
            return False
        path_parameters = any(
            segment.startswith("{") and segment.endswith("}")
            for segment in endpoint.path.split("/")
        )
        query_identifier = any(
            parameter.location.lower() == "query" and self._is_identifier(parameter.name)
            for parameter in endpoint.parameters
        )
        return path_parameters or query_identifier

    def _is_identifier(self, name: str) -> bool:
        normalized = name.lower().strip()
        return normalized in {"id", "user_id", "account_id", "order_id", "profile_id"} or normalized.endswith("_id")
