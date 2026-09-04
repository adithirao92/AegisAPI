"""Thin HTTP adapter for controlled Phase 11 BOLA test execution."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.ai_execution import ControlledTestRequest, ControlledTestResponse
from app.services.ai.execution import ControlledTestExecutionError, ControlledTestExecutor
from app.services.ai.test_context import ControlledTestContextStore
from app.services.ai.validator import AttackPlanValidator
from app.services.execution.requests_client import RequestsHttpClient
from app.services.execution.errors import RequestExecutionError
from app.services.execution.rest_executor import RestRequestExecutor


router = APIRouter(prefix="/ai", tags=["ai"])

_test_contexts = ControlledTestContextStore()


def get_controlled_test_context_store() -> ControlledTestContextStore:
    """Provide the server-only registry of trusted controlled-test contexts."""
    return _test_contexts


def get_controlled_test_executor() -> ControlledTestExecutor:
    """Build the Phase 11 adapter on the project's existing REST executor."""
    return ControlledTestExecutor(RestRequestExecutor(RequestsHttpClient()))


@router.post("/test", response_model=ControlledTestResponse)
def run_controlled_test(
    request: ControlledTestRequest,
    executor: Annotated[ControlledTestExecutor, Depends(get_controlled_test_executor)],
    contexts: Annotated[ControlledTestContextStore, Depends(get_controlled_test_context_store)],
) -> ControlledTestResponse:
    """Execute a pre-validated BOLA hypothesis against trusted server-side input."""
    try:
        context = contexts.get(str(request.context_id))
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Controlled test context was not found.",
        ) from exc

    validation = AttackPlanValidator().validate(request.attack_plan, [context.endpoint])
    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"errors": validation.errors},
        )

    try:
        result = executor.execute(
            attack_plan=request.attack_plan,
            endpoint=context.endpoint,
            original_request=context.original_request,
            auth_data=context.auth_data,
        )
    except ControlledTestExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except RequestExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Controlled test execution could not be completed.",
        ) from exc

    return ControlledTestResponse.from_result(result)
