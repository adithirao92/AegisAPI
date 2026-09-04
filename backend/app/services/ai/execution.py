"""Controlled execution of validator-approved BOLA test hypotheses.

This module intentionally collects response evidence only. It never creates a
finding, assigns risk, or decides whether a vulnerability exists.
"""

from __future__ import annotations

from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.api_specification import NormalizedEndpoint
from app.schemas.auth import RequestAuthenticationData
from app.services.ai.models import AttackPlan
from app.services.ai.validator import AttackPlanValidator
from app.services.execution.executor import RequestExecutor
from app.services.execution.models import ExecutionRequest, ExecutionResponse, ExecutionStatus


class AttackExecutionEvidence(BaseModel):
    """Observed response data for a controlled BOLA hypothesis execution."""

    model_config = ConfigDict(extra="forbid")

    original_value: str
    test_value: str
    modified_response_status: int | None = None
    modified_response_body: object | str | None = None
    modified_response_headers: dict[str, str] = Field(default_factory=dict)
    comparison: Literal["baseline_not_executed"] = "baseline_not_executed"
    indicators: list[str] = Field(default_factory=list)


class ControlledTestExecutionResult(BaseModel):
    """A plan, its controlled execution response, and non-verdict evidence."""

    model_config = ConfigDict(extra="forbid")

    attack_plan: AttackPlan
    execution_request: ExecutionRequest
    execution_response: ExecutionResponse
    execution_status: ExecutionStatus
    evidence: AttackExecutionEvidence


class ControlledTestExecutionError(ValueError):
    """Raised before execution when a plan or source request violates controls."""


class ControlledTestExecutor:
    """Translate one validated BOLA plan into one tightly constrained request.

    ``request_executor`` is the existing :class:`RequestExecutor`. Authentication
    remains owned by the existing authentication injector and executor; this
    adapter only passes through its resulting ``RequestAuthenticationData``.
    """

    def __init__(
        self,
        request_executor: RequestExecutor,
        validator: AttackPlanValidator | None = None,
    ) -> None:
        self._request_executor = request_executor
        self._validator = validator or AttackPlanValidator()

    def execute(
        self,
        attack_plan: AttackPlan,
        endpoint: NormalizedEndpoint,
        original_request: ExecutionRequest,
        auth_data: RequestAuthenticationData | None = None,
    ) -> ControlledTestExecutionResult:
        """Execute one approved BOLA hypothesis through the supplied executor.

        The original request supplies the base URL, all non-target parameters,
        headers, cookies, body, timeout, and existing authentication data.
        """
        if attack_plan.attack_type != "bola":
            raise ControlledTestExecutionError("Unsupported controlled test type.")
        validation = self._validator.validate(attack_plan, [endpoint])
        if not validation.is_valid or validation.plan is None:
            raise ControlledTestExecutionError("Invalid attack plan: " + "; ".join(validation.errors))
        plan = validation.plan
        self._validate_source_request(plan, endpoint, original_request)

        controlled_request = self._build_request(plan, original_request)
        response = self._request_executor.execute(controlled_request, auth_data)
        evidence = AttackExecutionEvidence(
            original_value=plan.original_value,
            test_value=plan.test_value,
            modified_response_status=response.status_code,
            modified_response_body=response.response_body,
            modified_response_headers=response.headers,
            indicators=self._response_indicators(response),
        )
        return ControlledTestExecutionResult(
            attack_plan=plan,
            execution_request=controlled_request,
            execution_response=response,
            execution_status=response.status,
            evidence=evidence,
        )

    def _validate_source_request(
        self,
        plan: AttackPlan,
        endpoint: NormalizedEndpoint,
        original_request: ExecutionRequest,
    ) -> None:
        if original_request.endpoint_id != endpoint.id:
            raise ControlledTestExecutionError("Source request does not belong to the supplied endpoint.")
        if original_request.method != plan.method:
            raise ControlledTestExecutionError("Source request method does not match the validated plan.")
        if plan.parameter_location == "path":
            self._validate_path_value(plan, original_request)
            return
        if plan.parameter_location == "query":
            if original_request.query_params.get(plan.parameter_name) != plan.original_value:
                raise ControlledTestExecutionError("Source request does not contain the validated query value.")
            return
        raise ControlledTestExecutionError("Unsupported parameter location for controlled BOLA execution.")

    def _build_request(self, plan: AttackPlan, original_request: ExecutionRequest) -> ExecutionRequest:
        values = original_request.model_dump()
        if plan.parameter_location == "path":
            values["url"] = self._replace_path_value(str(original_request.url), plan.original_value, plan.test_value)
        else:
            query_parameters = dict(original_request.query_params)
            query_parameters[plan.parameter_name] = plan.test_value
            values["query_params"] = query_parameters
        return ExecutionRequest.model_validate(values)

    def _validate_path_value(self, plan: AttackPlan, request: ExecutionRequest) -> None:
        path_segments = [segment for segment in urlsplit(str(request.url)).path.split("/") if segment]
        if plan.original_value not in path_segments:
            raise ControlledTestExecutionError("Source request does not contain the validated path value.")

    def _replace_path_value(self, url: str, original_value: str, test_value: str) -> str:
        parts = urlsplit(url)
        segments = parts.path.split("/")
        changed = False
        for index, segment in enumerate(segments):
            if segment == original_value:
                segments[index] = test_value
                changed = True
                break
        if not changed:
            raise ControlledTestExecutionError("Source request does not contain the validated path value.")
        return urlunsplit((parts.scheme, parts.netloc, "/".join(segments), parts.query, parts.fragment))

    def _response_indicators(self, response: ExecutionResponse) -> list[str]:
        if response.status == ExecutionStatus.TIMEOUT:
            return ["execution_timeout"]
        if response.status == ExecutionStatus.ERROR:
            return ["execution_error"]
        if response.status_code is None:
            return ["no_http_response"]
        return ["http_response_captured"]
