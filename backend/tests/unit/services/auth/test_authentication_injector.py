import base64

from app.schemas.auth import (
    AuthenticationContext,
    AuthenticationType,
    AuthenticationValidationStatus,
    RequestAuthenticationData,
)
from app.services.auth.auth_injector import AuthenticationInjector
from app.services.auth.exceptions import CredentialValidationError


def make_context(
    auth_type: AuthenticationType,
    metadata: dict[str, str],
    status: AuthenticationValidationStatus = AuthenticationValidationStatus.VALID,
) -> AuthenticationContext:
    return AuthenticationContext(
        endpoint_id="endpoint-1",
        authentication_type=auth_type,
        profile_id="profile-1",
        validation_status=status,
        credential_metadata=metadata,
    )


def test_api_key_injects_header() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.API_KEY,
        {
            "key_name": "x-api-key",
            "location": "header",
            "value": "secret-value",
        },
    )

    auth_data = injector.build_request_auth(context)

    assert auth_data.headers == {"x-api-key": "secret-value"}
    assert auth_data.query_params == {}
    assert auth_data.cookies == {}


def test_api_key_injects_query_param() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.API_KEY,
        {
            "key_name": "api_key",
            "location": "query",
            "value": "query-value",
        },
    )

    auth_data = injector.build_request_auth(context)

    assert auth_data.headers == {}
    assert auth_data.query_params == {"api_key": "query-value"}
    assert auth_data.cookies == {}


def test_api_key_injects_cookie() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.API_KEY,
        {
            "key_name": "session_id",
            "location": "cookie",
            "value": "cookie-value",
        },
    )

    auth_data = injector.build_request_auth(context)

    assert auth_data.headers == {}
    assert auth_data.query_params == {}
    assert auth_data.cookies == {"session_id": "cookie-value"}


def test_bearer_token_injects_authorization_header() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.BEARER_TOKEN,
        {
            "token": "bearer-token",
            "header_name": "Authorization",
            "prefix": "Bearer",
        },
    )

    auth_data = injector.build_request_auth(context)

    assert auth_data.headers == {"Authorization": "Bearer bearer-token"}
    assert auth_data.query_params == {}
    assert auth_data.cookies == {}


def test_jwt_injects_authorization_header() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.JWT,
        {
            "token": "jwt-token",
            "header_name": "Authorization",
            "prefix": "Bearer",
        },
    )

    auth_data = injector.build_request_auth(context)

    assert auth_data.headers == {"Authorization": "Bearer jwt-token"}


def test_basic_auth_injects_authorization_header() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.BASIC_AUTH,
        {
            "username": "user",
            "password": "pass",
        },
    )

    auth_data = injector.build_request_auth(context)
    expected = base64.b64encode(b"user:pass").decode("utf-8")

    assert auth_data.headers == {"Authorization": f"Basic {expected}"}


def test_oauth2_injects_bearer_header() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.OAUTH2,
        {
            "access_token": "oauth-token",
            "header_name": "Authorization",
            "prefix": "Bearer",
        },
    )

    auth_data = injector.build_request_auth(context)

    assert auth_data.headers == {"Authorization": "Bearer oauth-token"}


def test_unsupported_auth_type_raises() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.API_KEY,
        {
            "key_name": "x-api-key",
            "location": "header",
            "value": "secret-value",
        },
        status=AuthenticationValidationStatus.UNSUPPORTED,
    )

    try:
        injector.build_request_auth(context)
        assert False, "Expected CredentialValidationError"
    except CredentialValidationError as exc:
        assert "validation failed" in str(exc)


def test_missing_credentials_raises() -> None:
    injector = AuthenticationInjector()
    context = make_context(
        AuthenticationType.BEARER_TOKEN,
        {},
    )

    try:
        injector.build_request_auth(context)
        assert False, "Expected CredentialValidationError"
    except CredentialValidationError as exc:
        assert "Authentication context missing credential metadata" in str(exc)
