"""Credential storage abstractions for authentication profiles."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock
from typing import Protocol

from app.schemas.auth import AuthenticationProfile
from app.services.auth.exceptions import (
    CredentialNotFoundError,
    CredentialValidationError,
    DuplicateCredentialError,
)


class CredentialStore(Protocol):
    """Abstract interface for storing authentication profiles."""

    def store(self, profile: AuthenticationProfile) -> AuthenticationProfile:
        """Persist a new credential profile."""

    def retrieve(self, profile_id: str) -> AuthenticationProfile:
        """Retrieve a credential profile by identifier."""

    def update(self, profile: AuthenticationProfile) -> AuthenticationProfile:
        """Replace an existing credential profile."""

    def delete(self, profile_id: str) -> None:
        """Remove a credential profile by identifier."""

    def list_profiles(self) -> list[AuthenticationProfile]:
        """Return all stored credential profiles."""

    def exists(self, profile_id: str) -> bool:
        """Return whether a profile with the given identifier exists."""


class InMemoryCredentialStore(CredentialStore):
    """Thread-safe in-memory credential store for authentication profiles."""

    def __init__(self) -> None:
        self._profiles: dict[str, AuthenticationProfile] = {}
        self._lock = RLock()

    def store(self, profile: AuthenticationProfile) -> AuthenticationProfile:
        """Store a new profile if it does not already exist."""
        self._validate_profile(profile)

        with self._lock:
            if profile.id in self._profiles:
                raise DuplicateCredentialError(f"Credential profile already exists: {profile.id}")
            self._profiles[profile.id] = profile
            return profile

    def retrieve(self, profile_id: str) -> AuthenticationProfile:
        """Retrieve a stored profile by identifier."""
        if not profile_id:
            raise CredentialValidationError("Profile id must not be empty")

        with self._lock:
            if profile_id not in self._profiles:
                raise CredentialNotFoundError(f"Credential profile not found: {profile_id}")
            return self._profiles[profile_id]

    def update(self, profile: AuthenticationProfile) -> AuthenticationProfile:
        """Update an existing profile or raise if it does not exist."""
        self._validate_profile(profile)

        with self._lock:
            if profile.id not in self._profiles:
                raise CredentialNotFoundError(f"Credential profile not found: {profile.id}")
            self._profiles[profile.id] = profile
            return profile

    def delete(self, profile_id: str) -> None:
        """Delete a stored profile if it exists."""
        if not profile_id:
            raise CredentialValidationError("Profile id must not be empty")

        with self._lock:
            if profile_id not in self._profiles:
                raise CredentialNotFoundError(f"Credential profile not found: {profile_id}")
            del self._profiles[profile_id]

    def list_profiles(self) -> list[AuthenticationProfile]:
        """Return a snapshot of all stored profiles."""
        with self._lock:
            return list(self._profiles.values())

    def exists(self, profile_id: str) -> bool:
        """Return whether a profile ID exists in the store."""
        if not profile_id:
            return False

        with self._lock:
            return profile_id in self._profiles

    def _validate_profile(self, profile: AuthenticationProfile) -> None:
        """Validate profile data before storing or updating it."""
        if not isinstance(profile, AuthenticationProfile):
            raise CredentialValidationError("Profile must be an AuthenticationProfile")

        if not profile.id:
            raise CredentialValidationError("Profile id must not be empty")

        if profile.expires_at is not None and profile.last_validated_at is not None:
            if profile.expires_at < profile.last_validated_at:
                raise CredentialValidationError("Profile expiration is earlier than last validation time")
