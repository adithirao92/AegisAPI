from datetime import datetime, timedelta

from app.schemas.auth import (
    ApiKeyCredentialMetadata,
    AuthenticationContext,
    AuthenticationProfile,
    AuthenticationType,
    AuthenticationValidationStatus,
    RequestAuthenticationData,
)
from app.services.auth.exceptions import CredentialValidationError
from app.services.auth.validator import AuthenticationValidator


def make_profile(profile_id: str, auth_type: AuthenticationType) -> AuthenticationProfile:
    return AuthenticationProfile(
        id=profile_id,
        name="Test Profile",
        auth_type=auth_type,
        credential_reference="secret:test",
        credential_metadata=ApiKeyCredentialMetadata(key_name="x-api-key", location="header"),
    )


def test_validate_profile_success() -> None:
    validator = AuthenticationValidator()
    profile = make_profile("profile-1", AuthenticationType.API_KEY)

    result = validator.validate_profile(profile)

    assert result.success is True
    assert result.status == AuthenticationValidationStatus.VALID


def test_validate_profile_expired() -> None:
    validator = AuthenticationValidator()
    profile = make_profile("profile-2", AuthenticationType.API_KEY)
    profile.expires_at = datetime.now() - timedelta(minutes=1)

    result = validator.validate_profile(profile)

    assert result.success is False
    assert result.status == AuthenticationValidationStatus.EXPIRED


def test_validate_profile_invalid_metadata() -> None:
    validator = AuthenticationValidator()
    profile = make_profile("profile-3", AuthenticationType.API_KEY)
    profile.credential_metadata = None

    result = validator.validate_profile(profile)

    assert result.success is False
    assert result.status == AuthenticationValidationStatus.INVALID


def test_validate_context_missing_profile_id() -> None:
    validator = AuthenticationValidator()
    context = AuthenticationContext(
        endpoint_id="endpoint-1",
        authentication_type=AuthenticationType.API_KEY,
        profile_id=None,
        validation_status=AuthenticationValidationStatus.VALID,
        credential_metadata={"key_name": "x-api-key", "location": "header", "value": "token"},
    )

    try:
        validator.validate_context(context)
        assert False, "Expected CredentialValidationError"
    except CredentialValidationError as exc:
        assert "missing profile_id" in str(exc)


def test_validate_request_auth_empty_data() -> None:
    validator = AuthenticationValidator()
    request_data = RequestAuthenticationData(headers={}, query_params={}, cookies={})

    try:
        validator.validate_request_auth(request_data)
        assert False, "Expected CredentialValidationError"
    except CredentialValidationError as exc:
        assert "empty" in str(exc)


def test_validate_request_auth_malformed_headers() -> None:
    validator = AuthenticationValidator()
    request_data = RequestAuthenticationData(headers={"Authorization": ""}, query_params={}, cookies={})

    try:
        validator.validate_request_auth(request_data)
        assert False, "Expected CredentialValidationError"
    except CredentialValidationError as exc:
        assert "Malformed authentication header data" in str(exc)
