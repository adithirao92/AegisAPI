"""Attach authentication headers and parameters to outgoing HTTP requests."""

from __future__ import annotations

import base64
from typing import Any

from app.schemas.auth import (
    AuthenticationContext,
    AuthenticationType,
    RequestAuthenticationData,
)
from app.services.auth.exceptions import CredentialValidationError
from app.services.auth.validator import AuthenticationValidator


class AuthenticationInjector:
    """Convert validated authentication contexts into request-ready auth data."""

    def __init__(self, validator: AuthenticationValidator | None = None) -> None:
        self._validator = validator or AuthenticationValidator()

    def inject_headers(self, context: AuthenticationContext) -> dict[str, str]:
        """Return headers required to authenticate a request."""
        self._validate_context(context)

        if context.authentication_type == AuthenticationType.API_KEY:
            return self._inject_api_key_headers(context)
        if context.authentication_type in {AuthenticationType.BEARER_TOKEN, AuthenticationType.JWT, AuthenticationType.OAUTH2}:
            return self._inject_bearer_like_headers(context)
        if context.authentication_type == AuthenticationType.BASIC_AUTH:
            return self._inject_basic_auth_headers(context)

        raise CredentialValidationError("Unsupported authentication type for header injection")

    def inject_query_params(self, context: AuthenticationContext) -> dict[str, str]:
        """Return query parameters required to authenticate a request."""
        self._validate_context(context)

        if context.authentication_type == AuthenticationType.API_KEY:
            return self._inject_api_key_query_params(context)

        return {}

    def build_request_auth(self, context: AuthenticationContext) -> RequestAuthenticationData:
        """Build a request authentication payload from a validated context."""
        self._validate_context(context)

        headers = self.inject_headers(context)
        query_params = self.inject_query_params(context)
        cookies = self._inject_api_key_cookies(context) if context.authentication_type == AuthenticationType.API_KEY else {}

        request_auth = RequestAuthenticationData(
            headers=headers,
            query_params=query_params,
            cookies=cookies,
        )
        self._validator.validate_request_auth(request_auth)
        return request_auth

    def _validate_context(self, context: AuthenticationContext) -> None:
        try:
            self._validator.validate_context(context)
        except CredentialValidationError:
            raise

    def _supported_types(self) -> set[AuthenticationType]:
        return {
            AuthenticationType.API_KEY,
            AuthenticationType.BEARER_TOKEN,
            AuthenticationType.JWT,
            AuthenticationType.BASIC_AUTH,
            AuthenticationType.OAUTH2,
        }

    def _supported_types(self) -> set[AuthenticationType]:
        return {
            AuthenticationType.API_KEY,
            AuthenticationType.BEARER_TOKEN,
            AuthenticationType.JWT,
            AuthenticationType.BASIC_AUTH,
            AuthenticationType.OAUTH2,
        }

    def _inject_api_key_headers(self, context: AuthenticationContext) -> dict[str, str]:
        metadata = context.credential_metadata
        location = self._get_str(metadata, "location", default="header")
        if location != "header":
            return {}

        key_name = self._get_str(metadata, "key_name")
        value = self._get_str(metadata, "value")
        prefix = self._get_optional_str(metadata, "prefix")

        return {key_name: self._format_value(prefix, value)}

    def _inject_api_key_query_params(self, context: AuthenticationContext) -> dict[str, str]:
        metadata = context.credential_metadata
        location = self._get_str(metadata, "location", default="header")
        if location != "query":
            return {}

        key_name = self._get_str(metadata, "key_name")
        value = self._get_str(metadata, "value")
        prefix = self._get_optional_str(metadata, "prefix")

        return {key_name: self._format_value(prefix, value)}

    def _inject_api_key_cookies(self, context: AuthenticationContext) -> dict[str, str]:
        metadata = context.credential_metadata
        location = self._get_str(metadata, "location", default="header")
        if location != "cookie":
            return {}

        key_name = self._get_str(metadata, "key_name")
        value = self._get_str(metadata, "value")
        prefix = self._get_optional_str(metadata, "prefix")

        return {key_name: self._format_value(prefix, value)}

    def _inject_bearer_like_headers(self, context: AuthenticationContext) -> dict[str, str]:
        metadata = context.credential_metadata
        token = self._get_str(metadata, "token", default=metadata.get("access_token"))
        header_name = self._get_str(metadata, "header_name", default="Authorization")
        prefix = self._get_str(metadata, "prefix", default="Bearer")

        return {header_name: self._format_value(prefix, token)}

    def _inject_basic_auth_headers(self, context: AuthenticationContext) -> dict[str, str]:
        metadata = context.credential_metadata
        username = self._get_str(metadata, "username")
        password = self._get_str(metadata, "password")

        credentials = f"{username}:{password}".encode("utf-8")
        encoded = base64.b64encode(credentials).decode("utf-8")
        return {"Authorization": f"Basic {encoded}"}

    def _get_str(self, metadata: dict[str, Any], key: str, default: Any = None) -> str:
        value = metadata.get(key, default)
        if value is None or not isinstance(value, str) or not value.strip():
            raise CredentialValidationError(f"Missing or invalid credential metadata field: {key}")
        return value.strip()

    def _get_optional_str(self, metadata: dict[str, Any], key: str) -> str | None:
        value = metadata.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise CredentialValidationError(f"Invalid credential metadata field: {key}")
        return value.strip()

    def _format_value(self, prefix: str | None, value: str) -> str:
        if prefix:
            return f"{prefix} {value}"
        return value
