"""Authentication resolution and local validation service."""

from __future__ import annotations

from datetime import datetime

from app.schemas.api_specification import EndpointEnrichmentMetadata
from app.schemas.auth import (
    AuthenticationContext,
    AuthenticationProfile,
    AuthenticationType,
    AuthenticationValidationResult,
    AuthenticationValidationStatus,
)
from app.services.auth.credential_store import CredentialStore
from app.services.auth.validator import AuthenticationValidator


class AuthenticationManager:
    """Resolve and validate authentication profiles for endpoints."""

    def __init__(self, credential_store: CredentialStore, validator: AuthenticationValidator | None = None) -> None:
        self._credential_store = credential_store
        self._validator = validator or AuthenticationValidator()

    def resolve_authentication(
        self,
        endpoint: object,
        enrichment: EndpointEnrichmentMetadata | None = None,
    ) -> AuthenticationValidationResult:
        """Resolve and validate authentication for an endpoint-like object."""
        endpoint_id = getattr(endpoint, "id", None) or getattr(endpoint, "name", None) or "unknown"
        auth_type, unsupported = self._determine_auth_type(enrichment)

        if unsupported:
            return AuthenticationValidationResult(
                success=False,
                status=AuthenticationValidationStatus.UNSUPPORTED,
                message="Unsupported authentication type",
                profile_id=None,
                error_code="unsupported_auth_type",
                details={"endpoint_id": endpoint_id, "auth_type": str(getattr(enrichment, "auth_type", ""))},
            )

        if auth_type is None:
            return AuthenticationValidationResult(
                success=True,
                status=AuthenticationValidationStatus.VALID,
                message="No authentication required",
                profile_id=None,
                details={"endpoint_id": endpoint_id},
            )

        profile = self._find_profile(auth_type)
        if profile is None:
            return AuthenticationValidationResult(
                success=False,
                status=AuthenticationValidationStatus.MISSING,
                message="No matching credential profile found",
                profile_id=None,
                error_code="missing_profile",
                details={"endpoint_id": endpoint_id, "auth_type": auth_type.value},
            )

        return self.validate_profile(profile, endpoint_id=endpoint_id)

    def validate_profile(
        self,
        profile: AuthenticationProfile,
        *,
        endpoint_id: str | None = None,
    ) -> AuthenticationValidationResult:
        """Validate a credential profile locally without external network calls."""
        result = self._validator.validate_profile(profile)
        if endpoint_id is not None:
            result.details["endpoint_id"] = endpoint_id
        return result

    def get_authentication_context(
        self,
        endpoint: object,
        enrichment: EndpointEnrichmentMetadata | None = None,
    ) -> AuthenticationContext:
        """Build a downstream authentication context object for scan execution."""
        endpoint_id = getattr(endpoint, "id", None) or getattr(endpoint, "name", None) or "unknown"
        auth_type, unsupported = self._determine_auth_type(enrichment)
        profile: AuthenticationProfile | None = None
        validation_status = AuthenticationValidationStatus.PENDING

        if unsupported:
            validation_status = AuthenticationValidationStatus.UNSUPPORTED
        elif auth_type is not None:
            profile = self._find_profile(auth_type)
            if profile is None:
                validation_status = AuthenticationValidationStatus.MISSING
            else:
                result = self._validator.validate_profile(profile)
                validation_status = result.status

        return AuthenticationContext(
            endpoint_id=endpoint_id,
            authentication_type=auth_type or AuthenticationType.API_KEY,
            profile_id=profile.id if profile is not None else None,
            validation_status=validation_status,
            credential_metadata=profile.credential_metadata.model_dump() if profile and profile.credential_metadata is not None else {},
        )

    def _determine_auth_type(self, enrichment: EndpointEnrichmentMetadata | None) -> tuple[AuthenticationType | None, bool]:
        """Infer the required auth type from enrichment metadata."""
        if enrichment is None:
            return None, False

        if not enrichment.auth_required:
            return None, False

        auth_type = getattr(enrichment, "auth_type", None)
        if auth_type is None:
            return AuthenticationType.API_KEY, False

        mapping = {
            "bearer": AuthenticationType.BEARER_TOKEN,
            "jwt": AuthenticationType.JWT,
            "basic": AuthenticationType.BASIC_AUTH,
            "oauth": AuthenticationType.OAUTH2,
            "oauth2": AuthenticationType.OAUTH2,
            "api_key": AuthenticationType.API_KEY,
            "apikey": AuthenticationType.API_KEY,
            "api-key": AuthenticationType.API_KEY,
        }
        resolved = mapping.get(str(auth_type).lower())
        return (resolved, resolved is None)

    def _find_profile(self, auth_type: AuthenticationType) -> AuthenticationProfile | None:
        """Find the first profile matching the requested auth type."""
        profiles = self._credential_store.list_profiles()
        for profile in profiles:
            if profile.auth_type == auth_type:
                return profile
        return None

    def _supported_auth_types(self) -> set[AuthenticationType]:
        """Return the supported auth types for local validation."""
        return {
            AuthenticationType.API_KEY,
            AuthenticationType.BEARER_TOKEN,
            AuthenticationType.JWT,
            AuthenticationType.BASIC_AUTH,
            AuthenticationType.OAUTH2,
        }
