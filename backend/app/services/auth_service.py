from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from http import HTTPStatus
from typing import Any, TypeVar, cast

from flask import g, request

from app.core import FailureCode, Settings, UserRole
from app.core.errors import ApiError
from app.db.models import User
from app.db.repositories import upsert_user_from_claims
from app.services.firebase_service import initialize_firebase_app, verify_bearer_token

Handler = TypeVar("Handler", bound=Callable[..., Any])


@dataclass(frozen=True)
class AuthenticatedContext:
    bearer_token: str
    claims: dict[str, Any]
    user: User


def initialize_auth(settings: Settings) -> None:
    initialize_firebase_app(settings)


def get_bearer_token_from_request() -> str:
    header = request.headers.get("Authorization", "").strip()
    if not header.startswith("Bearer "):
        raise ApiError(
            code=FailureCode.AUTH_INVALID,
            message="Authentication required.",
            status_code=HTTPStatus.UNAUTHORIZED,
        )

    token = header.removeprefix("Bearer ").strip()
    if not token:
        raise ApiError(
            code=FailureCode.AUTH_INVALID,
            message="Authentication required.",
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    return token


def authenticate_request(settings: Settings) -> AuthenticatedContext:
    existing = getattr(g, "auth_context", None)
    if isinstance(existing, AuthenticatedContext):
        return existing

    session = getattr(g, "db_session", None)
    if session is None:
        raise RuntimeError("DB session has not been attached to the request context")

    bearer_token = get_bearer_token_from_request()
    try:
        claims = dict(verify_bearer_token(settings, bearer_token))
    except Exception as exc:
        raise ApiError(
            code=FailureCode.AUTH_INVALID,
            message="Authentication failed.",
            status_code=HTTPStatus.UNAUTHORIZED,
            details={"reason": str(exc)},
        ) from exc

    user = upsert_user_from_claims(
        session,
        claims=claims,
        admin_email_allowlist=settings.admin_emails,
    )
    if not user.is_active:
        raise ApiError(
            code=FailureCode.AUTH_FORBIDDEN,
            message="This account is inactive.",
            status_code=HTTPStatus.FORBIDDEN,
        )

    context = AuthenticatedContext(
        bearer_token=bearer_token,
        claims=claims,
        user=user,
    )
    g.auth_context = context
    g.current_user = user
    g.auth_claims = claims
    return context


def require_auth(handler: Handler) -> Handler:
    @wraps(handler)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        authenticate_request(get_request_settings())
        return handler(*args, **kwargs)

    return cast(Handler, wrapped)


def require_admin(handler: Handler) -> Handler:
    @wraps(handler)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        context = authenticate_request(get_request_settings())
        if context.user.role != UserRole.ADMIN:
            raise ApiError(
                code=FailureCode.AUTH_FORBIDDEN,
                message="Admin access is required.",
                status_code=HTTPStatus.FORBIDDEN,
            )
        return handler(*args, **kwargs)

    return cast(Handler, wrapped)


def get_authenticated_user() -> User:
    context = getattr(g, "auth_context", None)
    if not isinstance(context, AuthenticatedContext):
        raise RuntimeError("Authenticated user is not available on this request")
    return context.user


def get_authenticated_claims() -> dict[str, Any]:
    context = getattr(g, "auth_context", None)
    if not isinstance(context, AuthenticatedContext):
        raise RuntimeError("Authenticated claims are not available on this request")
    return context.claims


def get_request_settings() -> Settings:
    settings = getattr(g, "settings", None)
    if not isinstance(settings, Settings):
        raise RuntimeError("Settings are not available on this request")
    return settings
