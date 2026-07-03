"""Authentication validation service for profiles, contexts, and request auth data."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.auth import (
    AuthenticationContext,
    AuthenticationProfile,
    AuthenticationValidationResult,
    AuthenticationValidationStatus,
    AuthenticationType,
    RequestAuthenticationData,
)
from app.services.auth.exceptions import CredentialValidationError


class AuthenticationValidator:
    """Validate authentication models and request authentication payloads."""

    def validate_profile(self, profile: AuthenticationProfile) -> AuthenticationValidationResult:
        """Validate a credential profile for local use."""
        if profile.auth_type not in self._supported_auth_types():
            return AuthenticationValidationResult(
                success=False,
                status=AuthenticationValidationStatus.UNSUPPORTED,
                message="Unsupported authentication type",
                profile_id=profile.id,
                error_code="unsupported_auth_type",
                details={"auth_type": profile.auth_type.value},
            )

        if profile.expires_at is not None and datetime.now() >= profile.expires_at:
            return AuthenticationValidationResult(
                success=False,
                status=AuthenticationValidationStatus.EXPIRED,
                message="Credential profile has expired",
                profile_id=profile.id,
                error_code="expired_credentials",
                details={"expires_at": profile.expires_at.isoformat()},
            )

        if profile.credential_metadata is None:
            return AuthenticationValidationResult(
                success=False,
                status=AuthenticationValidationStatus.INVALID,
                message="Credential metadata is required",
                profile_id=profile.id,
                error_code="missing_metadata",
                details={"auth_type": profile.auth_type.value},
            )

        return AuthenticationValidationResult(
            success=True,
            status=AuthenticationValidationStatus.VALID,
            message="Credential profile is valid",
            profile_id=profile.id,
            details={"auth_type": profile.auth_type.value},
        )

    def validate_context(self, context: AuthenticationContext) -> None:
        """Validate an authentication context before request injection."""
        if not context.profile_id:
            raise CredentialValidationError("Authentication context missing profile_id")

        if context.authentication_type not in self._supported_auth_types():
            raise CredentialValidationError("Unsupported authentication type in context")

        if context.validation_status != AuthenticationValidationStatus.VALID:
            raise CredentialValidationError(
                f"Authentication context validation failed: {context.validation_status.value}"
            )

        if not isinstance(context.credential_metadata, dict) or not context.credential_metadata:
            raise CredentialValidationError("Authentication context missing credential metadata")

    def validate_request_auth(self, data: RequestAuthenticationData) -> None:
        """Validate generated request authentication payloads."""
        if not data.headers and not data.query_params and not data.cookies:
            raise CredentialValidationError("Request authentication data is empty")

        for name, value in data.headers.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(value, str) or not value.strip():
                raise CredentialValidationError("Malformed authentication header data")

        for name, value in data.query_params.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(value, str) or not value.strip():
                raise CredentialValidationError("Malformed authentication query parameter data")

        for name, value in data.cookies.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(value, str) or not value.strip():
                raise CredentialValidationError("Malformed authentication cookie data")

    def _supported_auth_types(self) -> set[AuthenticationType]:
        return {
            AuthenticationType.API_KEY,
            AuthenticationType.BEARER_TOKEN,
            AuthenticationType.JWT,
            AuthenticationType.BASIC_AUTH,
            AuthenticationType.OAUTH2,
        }
