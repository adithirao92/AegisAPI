"""Authentication Manager (SDS Section 3.5)."""

from app.services.auth.credential_store import InMemoryCredentialStore
from app.services.auth.exceptions import (
    CredentialNotFoundError,
    CredentialStoreError,
    CredentialValidationError,
    DuplicateCredentialError,
)
from app.services.auth.manager import AuthenticationManager
from app.services.auth.auth_injector import AuthenticationInjector
from app.services.auth.validator import AuthenticationValidator
from app.schemas.auth import RequestAuthenticationData

__all__ = [
    "AuthenticationManager",
    "AuthenticationInjector",
    "RequestAuthenticationData",
    "CredentialNotFoundError",
    "CredentialStoreError",
    "CredentialValidationError",
    "DuplicateCredentialError",
    "InMemoryCredentialStore",
]
