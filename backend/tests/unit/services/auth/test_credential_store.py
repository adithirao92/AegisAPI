from datetime import datetime, timedelta

import pytest

from app.schemas.auth import AuthenticationProfile, AuthenticationType
from app.services.auth.credential_store import InMemoryCredentialStore
from app.services.auth.exceptions import (
    CredentialNotFoundError,
    CredentialValidationError,
    DuplicateCredentialError,
)


def make_profile(profile_id: str, *, expires_at: datetime | None = None) -> AuthenticationProfile:
    return AuthenticationProfile(
        id=profile_id,
        name=f"Profile {profile_id}",
        auth_type=AuthenticationType.API_KEY,
        credential_reference=f"secret:{profile_id}",
        expires_at=expires_at,
    )


def test_store_and_retrieve_profile() -> None:
    store = InMemoryCredentialStore()
    profile = make_profile("profile-1")

    stored = store.store(profile)
    retrieved = store.retrieve("profile-1")

    assert stored is profile
    assert retrieved is profile
    assert store.exists("profile-1") is True


def test_update_existing_profile() -> None:
    store = InMemoryCredentialStore()
    profile = make_profile("profile-2")
    store.store(profile)

    updated = make_profile("profile-2", expires_at=datetime.now() + timedelta(hours=1))
    store.update(updated)

    assert store.retrieve("profile-2").expires_at == updated.expires_at


def test_delete_profile() -> None:
    store = InMemoryCredentialStore()
    store.store(make_profile("profile-3"))

    store.delete("profile-3")

    assert store.exists("profile-3") is False
    with pytest.raises(CredentialNotFoundError):
        store.retrieve("profile-3")


def test_duplicate_profile_rejected() -> None:
    store = InMemoryCredentialStore()
    store.store(make_profile("profile-4"))

    with pytest.raises(DuplicateCredentialError):
        store.store(make_profile("profile-4"))


def test_missing_profile_raises_not_found() -> None:
    store = InMemoryCredentialStore()

    with pytest.raises(CredentialNotFoundError):
        store.retrieve("missing")


def test_list_profiles_returns_all_stored_profiles() -> None:
    store = InMemoryCredentialStore()
    profile_a = make_profile("profile-a")
    profile_b = make_profile("profile-b")
    store.store(profile_a)
    store.store(profile_b)

    profiles = store.list_profiles()

    assert len(profiles) == 2
    assert {profile.id for profile in profiles} == {"profile-a", "profile-b"}


def test_expiration_validation_rejected() -> None:
    store = InMemoryCredentialStore()
    invalid_profile = make_profile("profile-5")
    invalid_profile.last_validated_at = datetime.now()
    invalid_profile.expires_at = datetime.now() - timedelta(minutes=1)

    with pytest.raises(CredentialValidationError):
        store.store(invalid_profile)
