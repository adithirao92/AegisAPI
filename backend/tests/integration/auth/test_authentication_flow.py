from datetime import datetime, timedelta
import base64

import pytest

from app.schemas.api_specification import EndpointEnrichmentMetadata
from app.schemas.auth import (
    ApiKeyCredentialMetadata,
    AuthenticationContext,
    AuthenticationProfile,
    AuthenticationType,
    AuthenticationValidationStatus,
    BasicAuthCredentialMetadata,
    BearerTokenCredentialMetadata,
    JwtCredentialMetadata,
    OAuth2CredentialMetadata,
)
from app.services.auth import AuthenticationInjector, AuthenticationManager, InMemoryCredentialStore
from app.services.auth.exceptions import CredentialValidationError


class DummyEndpoint:
    def __init__(self, endpoint_id: str) -> None:
        self.id = endpoint_id


def build_profile(
    profile_id: str,
    auth_type: AuthenticationType,
    metadata: dict,
    expires_at: datetime | None = None,
) -> AuthenticationProfile:
    return AuthenticationProfile(
        id=profile_id,
        name=f"Profile {profile_id}",
        auth_type=auth_type,
        credential_reference=f"secret:{profile_id}",
        credential_metadata=metadata,
        expires_at=expires_at,
    )


def execute_auth_flow(
    profile: AuthenticationProfile | None,
    enrichment: EndpointEnrichmentMetadata,
) -> tuple[AuthenticationValidationStatus, AuthenticationContext, dict[str, str], dict[str, str], dict[str, str]]:
    store = InMemoryCredentialStore()
    if profile is not None:
        store.store(profile)

    manager = AuthenticationManager(store)
    injector = AuthenticationInjector()
    endpoint = DummyEndpoint("endpoint-1")

    validation_result = manager.resolve_authentication(endpoint, enrichment)
    auth_context = manager.get_authentication_context(endpoint, enrichment)

    if validation_result.success and auth_context.validation_status == AuthenticationValidationStatus.VALID:
        request_auth = injector.build_request_auth(auth_context)
        return (
            validation_result.status,
            auth_context,
            request_auth.headers,
            request_auth.query_params,
            request_auth.cookies,
        )

    raise CredentialValidationError(
        f"Authentication flow failed with status: {validation_result.status}"
    )


def test_api_key_flow_end_to_end() -> None:
    profile = build_profile(
        "profile-api-key",
        AuthenticationType.API_KEY,
        ApiKeyCredentialMetadata(key_name="x-api-key", location="header", value="secret-value"),
    )
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="api_key")

    status, context, headers, query_params, cookies = execute_auth_flow(profile, enrichment)

    assert status == AuthenticationValidationStatus.VALID
    assert context.endpoint_id == "endpoint-1"
    assert context.profile_id == "profile-api-key"
    assert context.validation_status == AuthenticationValidationStatus.VALID
    assert headers == {"x-api-key": "secret-value"}
    assert query_params == {}
    assert cookies == {}


def test_bearer_token_flow_end_to_end() -> None:
    profile = build_profile(
        "profile-bearer",
        AuthenticationType.BEARER_TOKEN,
        BearerTokenCredentialMetadata(token="bearer-token", header_name="Authorization", prefix="Bearer"),
    )
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="bearer")

    status, context, headers, query_params, cookies = execute_auth_flow(profile, enrichment)

    assert status == AuthenticationValidationStatus.VALID
    assert headers == {"Authorization": "Bearer bearer-token"}
    assert query_params == {}
    assert cookies == {}


def test_jwt_flow_end_to_end() -> None:
    profile = build_profile(
        "profile-jwt",
        AuthenticationType.JWT,
        JwtCredentialMetadata(token="jwt-token", header_name="Authorization", prefix="Bearer"),
    )
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="jwt")

    status, context, headers, query_params, cookies = execute_auth_flow(profile, enrichment)

    assert status == AuthenticationValidationStatus.VALID
    assert headers == {"Authorization": "Bearer jwt-token"}
    assert query_params == {}
    assert cookies == {}


def test_basic_auth_flow_end_to_end() -> None:
    profile = build_profile(
        "profile-basic",
        AuthenticationType.BASIC_AUTH,
        BasicAuthCredentialMetadata(username="user", password="pass"),
    )
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="basic")

    status, context, headers, query_params, cookies = execute_auth_flow(profile, enrichment)
    expected_token = base64.b64encode(b"user:pass").decode("utf-8")

    assert status == AuthenticationValidationStatus.VALID
    assert headers == {"Authorization": f"Basic {expected_token}"}
    assert query_params == {}
    assert cookies == {}


def test_oauth2_flow_end_to_end() -> None:
    profile = build_profile(
        "profile-oauth2",
        AuthenticationType.OAUTH2,
        OAuth2CredentialMetadata(access_token="oauth-token"),
    )
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="oauth2")

    status, context, headers, query_params, cookies = execute_auth_flow(profile, enrichment)

    assert status == AuthenticationValidationStatus.VALID
    assert headers == {"Authorization": "Bearer oauth-token"}
    assert query_params == {}
    assert cookies == {}


def test_missing_credential_flow_raises() -> None:
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="api_key")
    store = InMemoryCredentialStore()
    manager = AuthenticationManager(store)
    injector = AuthenticationInjector()
    endpoint = DummyEndpoint("endpoint-1")

    validation_result = manager.resolve_authentication(endpoint, enrichment)
    auth_context = manager.get_authentication_context(endpoint, enrichment)

    assert validation_result.success is False
    assert validation_result.status == AuthenticationValidationStatus.MISSING
    assert auth_context.validation_status == AuthenticationValidationStatus.MISSING
    assert auth_context.profile_id is None

    with pytest.raises(CredentialValidationError):
        injector.build_request_auth(auth_context)


def test_expired_credential_flow_raises() -> None:
    profile = build_profile(
        "profile-expired",
        AuthenticationType.API_KEY,
        ApiKeyCredentialMetadata(key_name="x-api-key", location="header", value="expired-value"),
        expires_at=datetime.now() - timedelta(minutes=1),
    )
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="api_key")
    store = InMemoryCredentialStore()
    store.store(profile)
    manager = AuthenticationManager(store)
    injector = AuthenticationInjector()
    endpoint = DummyEndpoint("endpoint-1")

    validation_result = manager.resolve_authentication(endpoint, enrichment)
    auth_context = manager.get_authentication_context(endpoint, enrichment)

    assert validation_result.success is False
    assert validation_result.status == AuthenticationValidationStatus.EXPIRED
    assert auth_context.validation_status == AuthenticationValidationStatus.EXPIRED
    assert auth_context.profile_id == "profile-expired"

    with pytest.raises(CredentialValidationError):
        injector.build_request_auth(auth_context)


def test_unsupported_auth_type_flow_raises() -> None:
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="digest")
    store = InMemoryCredentialStore()
    manager = AuthenticationManager(store)
    injector = AuthenticationInjector()
    endpoint = DummyEndpoint("endpoint-1")

    validation_result = manager.resolve_authentication(endpoint, enrichment)
    auth_context = manager.get_authentication_context(endpoint, enrichment)

    assert validation_result.success is False
    assert validation_result.status == AuthenticationValidationStatus.UNSUPPORTED
    assert auth_context.validation_status == AuthenticationValidationStatus.UNSUPPORTED

    with pytest.raises(CredentialValidationError):
        injector.build_request_auth(auth_context)
