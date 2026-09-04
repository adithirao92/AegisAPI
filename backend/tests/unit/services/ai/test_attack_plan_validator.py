from __future__ import annotations

from app.schemas.api_specification import NormalizedEndpoint, ParameterDefinition
from app.services.ai import AttackPlan, AttackPlanValidator


def endpoint() -> NormalizedEndpoint:
    return NormalizedEndpoint(
        id="users-get",
        endpoint_type="rest",
        path="/users/{id}",
        method="GET",
        parameters=[ParameterDefinition(name="account_id", location="query")],
    )


def plan(**changes: object) -> dict[str, object]:
    result: dict[str, object] = {
        "attack_type": "bola", "endpoint": "/users/{id}", "method": "GET",
        "parameter_name": "id", "parameter_location": "path", "original_value": "123",
        "test_value": "124", "rationale": "Object identifier may need authorization checks.",
        "evidence_required": True,
    }
    result.update(changes)
    return result


def test_valid_bola_plan_passes_validation() -> None:
    result = AttackPlanValidator().validate(AttackPlan.model_validate(plan()), [endpoint()])

    assert result.is_valid
    assert result.plan is not None


def test_validator_rejects_hallucinated_endpoint() -> None:
    result = AttackPlanValidator().validate(plan(endpoint="/admin/{id}"), [endpoint()])

    assert not result.is_valid
    assert "outside the discovered catalog" in result.errors[0]


def test_validator_rejects_hallucinated_parameter() -> None:
    result = AttackPlanValidator().validate(plan(parameter_name="owner_id"), [endpoint()])

    assert not result.is_valid
    assert "parameter" in result.errors[0]


def test_validator_rejects_wrong_http_method() -> None:
    result = AttackPlanValidator().validate(plan(method="POST"), [endpoint()])

    assert not result.is_valid
    assert "method" in result.errors[0]


def test_validator_rejects_unsupported_attack_type_and_missing_fields() -> None:
    unsupported = AttackPlanValidator().validate(plan(attack_type="ssrf"), [endpoint()])
    missing = AttackPlanValidator().validate({"attack_type": "bola"}, [endpoint()])

    assert not unsupported.is_valid
    assert not missing.is_valid
