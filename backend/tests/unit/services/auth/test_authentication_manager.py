from datetime import datetime, timedelta

from app.schemas.api_specification import EndpointEnrichmentMetadata
from app.schemas.auth import (
    ApiKeyCredentialMetadata,
    AuthenticationProfile,
    AuthenticationType,
    AuthenticationValidationStatus,
)
from app.services.auth.credential_store import InMemoryCredentialStore
from app.services.auth.manager import AuthenticationManager


class DummyEndpoint:
    def __init__(self, endpoint_id: str) -> None:
        self.id = endpoint_id


def make_profile(profile_id: str, *, auth_type: AuthenticationType = AuthenticationType.API_KEY) -> AuthenticationProfile:
    return AuthenticationProfile(
        id=profile_id,
        name=f"Profile {profile_id}",
        auth_type=auth_type,
        credential_reference=f"secret:{profile_id}",
        credential_metadata=ApiKeyCredentialMetadata(key_name="x-api-key", location="header"),
    )


def test_manager_resolves_valid_credentials() -> None:
    store = InMemoryCredentialStore()
    store.store(make_profile("profile-1"))
    manager = AuthenticationManager(store)
    endpoint = DummyEndpoint("endpoint-1")
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="api_key")

    result = manager.resolve_authentication(endpoint, enrichment)

    assert result.success is True
    assert result.status == AuthenticationValidationStatus.VALID


def test_manager_returns_missing_when_profile_not_found() -> None:
    store = InMemoryCredentialStore()
    manager = AuthenticationManager(store)
    endpoint = DummyEndpoint("endpoint-2")
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="api_key")

    result = manager.resolve_authentication(endpoint, enrichment)

    assert result.success is False
    assert result.status == AuthenticationValidationStatus.MISSING


def test_manager_returns_expired_for_expired_profiles() -> None:
    store = InMemoryCredentialStore()
    profile = make_profile("profile-2")
    profile.expires_at = datetime.now() - timedelta(minutes=1)
    store.store(profile)
    manager = AuthenticationManager(store)
    endpoint = DummyEndpoint("endpoint-3")
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="api_key")

    result = manager.resolve_authentication(endpoint, enrichment)

    assert result.success is False
    assert result.status == AuthenticationValidationStatus.EXPIRED


def test_manager_returns_unsupported_for_unsupported_auth_type() -> None:
    store = InMemoryCredentialStore()
    manager = AuthenticationManager(store)
    endpoint = DummyEndpoint("endpoint-4")
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="digest")

    result = manager.resolve_authentication(endpoint, enrichment)

    assert result.success is False
    assert result.status == AuthenticationValidationStatus.UNSUPPORTED


def test_manager_returns_invalid_when_metadata_missing() -> None:
    store = InMemoryCredentialStore()
    profile = make_profile("profile-4")
    profile.credential_metadata = None
    store.store(profile)
    manager = AuthenticationManager(store)
    endpoint = DummyEndpoint("endpoint-5")
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="api_key")

    result = manager.resolve_authentication(endpoint, enrichment)

    assert result.success is False
    assert result.status == AuthenticationValidationStatus.INVALID


def test_manager_creates_authentication_context() -> None:
    store = InMemoryCredentialStore()
    store.store(make_profile("profile-5"))
    manager = AuthenticationManager(store)
    endpoint = DummyEndpoint("endpoint-6")
    enrichment = EndpointEnrichmentMetadata(auth_required=True, auth_type="api_key")

    context = manager.get_authentication_context(endpoint, enrichment)

    assert context.endpoint_id == "endpoint-6"
    assert context.authentication_type == AuthenticationType.API_KEY
    assert context.profile_id == "profile-5"
    assert context.validation_status == AuthenticationValidationStatus.VALID
