from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    ApiKeyCredentialMetadata,
    AuthenticationProfile,
    AuthenticationType,
    AuthenticationValidationResult,
    AuthenticationValidationStatus,
    BasicAuthCredentialMetadata,
    BearerTokenCredentialMetadata,
    JwtCredentialMetadata,
    OAuth2CredentialMetadata,
)


def test_authentication_profile_accepts_supported_auth_types() -> None:
    profile = AuthenticationProfile(
        id="profile-1",
        name="Primary API Key",
        auth_type=AuthenticationType.API_KEY,
        credential_reference="secret:api-key",
    )

    assert profile.auth_type == AuthenticationType.API_KEY
    assert profile.validation_status == AuthenticationValidationStatus.PENDING
    assert profile.is_required is True


def test_authentication_profile_rejects_invalid_expiration_order() -> None:
    with pytest.raises(ValidationError):
        AuthenticationProfile(
            id="profile-2",
            name="Expired Profile",
            auth_type=AuthenticationType.BEARER_TOKEN,
            last_validated_at=datetime.now(),
            expires_at=datetime.now() - timedelta(minutes=1),
        )


def test_api_key_metadata_validation() -> None:
    metadata = ApiKeyCredentialMetadata(key_name="x-api-key", location="header")

    assert metadata.key_name == "x-api-key"
    assert metadata.location == "header"


def test_bearer_token_metadata_defaults() -> None:
    metadata = BearerTokenCredentialMetadata()

    assert metadata.header_name == "Authorization"
    assert metadata.prefix == "Bearer"


def test_jwt_metadata_requires_expected_fields() -> None:
    metadata = JwtCredentialMetadata(issuer="issuer.example", audience="aud.example")

    assert metadata.issuer == "issuer.example"
    assert metadata.audience == "aud.example"
    assert metadata.claim_name == "sub"


def test_basic_auth_metadata_supports_custom_fields() -> None:
    metadata = BasicAuthCredentialMetadata(username_field="user", password_field="pass")

    assert metadata.username_field == "user"
    assert metadata.password_field == "pass"


def test_oauth2_metadata_supports_scopes_and_urls() -> None:
    metadata = OAuth2CredentialMetadata(
        token_url="https://example.com/oauth/token",
        authorization_url="https://example.com/oauth/authorize",
        scopes=["read", "write"],
    )

    assert metadata.grant_type == "client_credentials"
    assert metadata.scopes == ["read", "write"]


def test_validation_result_model_captures_status_and_details() -> None:
    result = AuthenticationValidationResult(
        success=False,
        status=AuthenticationValidationStatus.INVALID,
        message="Invalid credentials",
        profile_id="profile-1",
        error_code="invalid_credentials",
        details={"reason": "expired"},
    )

    assert result.success is False
    assert result.status == AuthenticationValidationStatus.INVALID
    assert result.error_code == "invalid_credentials"
