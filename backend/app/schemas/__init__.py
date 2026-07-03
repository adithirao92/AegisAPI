"""Pydantic v2 schemas for API contracts and inter-module data transfer."""

from app.schemas.api_specification import (
    DiscoveryCatalog,
    EndpointModel,
    GraphQLArgument,
    GraphQLOperation,
    ParameterDefinition,
)
from app.schemas.auth import (
    ApiKeyCredentialMetadata,
    AuthenticationContext,
    AuthenticationProfile,
    AuthenticationType,
    AuthenticationValidationResult,
    AuthenticationValidationStatus,
    BasicAuthCredentialMetadata,
    BearerTokenCredentialMetadata,
    CredentialMetadataBase,
    JwtCredentialMetadata,
    OAuth2CredentialMetadata,
)

__all__ = [
    "ApiKeyCredentialMetadata",
    "AuthenticationContext",
    "AuthenticationProfile",
    "AuthenticationType",
    "AuthenticationValidationResult",
    "AuthenticationValidationStatus",
    "BasicAuthCredentialMetadata",
    "BearerTokenCredentialMetadata",
    "CredentialMetadataBase",
    "DiscoveryCatalog",
    "EndpointModel",
    "GraphQLArgument",
    "GraphQLOperation",
    "JwtCredentialMetadata",
    "OAuth2CredentialMetadata",
    "ParameterDefinition",
]
