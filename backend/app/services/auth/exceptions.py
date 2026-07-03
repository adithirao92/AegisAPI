"""Exceptions raised by credential storage and authentication operations."""

from __future__ import annotations


class CredentialStoreError(Exception):
    """Base exception for credential store failures."""


class CredentialNotFoundError(CredentialStoreError):
    """Raised when a requested credential profile cannot be found."""


class DuplicateCredentialError(CredentialStoreError):
    """Raised when a credential profile with the same identifier already exists."""


class CredentialValidationError(CredentialStoreError):
    """Raised when a credential profile is invalid for storage or use."""
