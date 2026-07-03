"""Pydantic models for authentication profiles and credential metadata."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuthenticationType(str, Enum):
    """Supported authentication schemes for endpoint scanning."""

    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    JWT = "jwt"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"


class AuthenticationValidationStatus(str, Enum):
    """Runtime validation state for a credential profile."""

    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    MISSING = "missing"
    UNSUPPORTED = "unsupported"


class CredentialMetadataBase(BaseModel):
    """Common metadata shared by all credential definitions."""

    model_config = ConfigDict(extra="forbid")

    description: str | None = None


class ApiKeyCredentialMetadata(CredentialMetadataBase):
    """Metadata for API key-based authentication."""

    key_name: str = Field(..., min_length=1)
    location: Literal["header", "query", "cookie"] = "header"
    value: str | None = None
    prefix: str | None = None


class BearerTokenCredentialMetadata(CredentialMetadataBase):
    """Metadata for bearer-token authentication."""

    header_name: str = Field(default="Authorization", min_length=1)
    prefix: str = Field(default="Bearer", min_length=1)
    token: str | None = None


class JwtCredentialMetadata(CredentialMetadataBase):
    """Metadata for JWT-based authentication."""

    header_name: str = Field(default="Authorization", min_length=1)
    prefix: str = Field(default="Bearer", min_length=1)
    issuer: str | None = None
    audience: str | None = None
    claim_name: str = Field(default="sub", min_length=1)
    token: str | None = None


class BasicAuthCredentialMetadata(CredentialMetadataBase):
    """Metadata for HTTP Basic authentication."""

    username_field: str = Field(default="username", min_length=1)
    password_field: str = Field(default="password", min_length=1)
    username: str | None = None
    password: str | None = None


class OAuth2CredentialMetadata(CredentialMetadataBase):
    """Metadata for OAuth2-based authentication."""

    token_url: str | None = None
    authorization_url: str | None = None
    scopes: list[str] = Field(default_factory=list)
    grant_type: str = Field(default="client_credentials", min_length=1)
    access_token: str | None = None
    refresh_token: str | None = None


CredentialMetadata = (
    ApiKeyCredentialMetadata
    | BearerTokenCredentialMetadata
    | JwtCredentialMetadata
    | BasicAuthCredentialMetadata
    | OAuth2CredentialMetadata
)


class AuthenticationProfile(BaseModel):
    """Describes how a target endpoint or scan should authenticate."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    auth_type: AuthenticationType
    credential_reference: str | None = None
    credential_metadata: CredentialMetadata | None = None
    validation_status: AuthenticationValidationStatus = AuthenticationValidationStatus.PENDING
    expires_at: datetime | None = None
    last_validated_at: datetime | None = None
    is_required: bool = True
    scopes: list[str] = Field(default_factory=list)
    description: str | None = None

    @model_validator(mode="after")
    def validate_expiration(self) -> "AuthenticationProfile":
        """Ensure expiration metadata is only used when present."""
        if self.expires_at is not None and self.last_validated_at is not None:
            if self.expires_at < self.last_validated_at:
                raise ValueError("expires_at must be greater than or equal to last_validated_at")
        return self


class AuthenticationValidationResult(BaseModel):
    """Structured result of a credential validation attempt."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    status: AuthenticationValidationStatus = AuthenticationValidationStatus.PENDING
    message: str = ""
    profile_id: str | None = None
    error_code: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AuthenticationContext(BaseModel):
    """Context object for downstream scan execution and request injection."""

    model_config = ConfigDict(extra="forbid")

    endpoint_id: str
    authentication_type: AuthenticationType
    profile_id: str | None = None
    validation_status: AuthenticationValidationStatus = AuthenticationValidationStatus.PENDING
    credential_metadata: dict[str, Any] = Field(default_factory=dict)


class RequestAuthenticationData(BaseModel):
    """Authentication data attached to an outgoing request."""

    model_config = ConfigDict(extra="forbid")

    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
