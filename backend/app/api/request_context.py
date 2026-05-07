from __future__ import annotations

from flask import current_app, g
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import User


def get_settings_from_app() -> Settings:
    request_settings = getattr(g, "settings", None)
    if isinstance(request_settings, Settings):
        return request_settings

    app_settings = current_app.extensions.get("pdfextract_settings")
    if isinstance(app_settings, Settings):
        return app_settings

    return get_settings()


def get_db_session() -> Session:
    session = getattr(g, "db_session", None)
    if not isinstance(session, Session):
        raise RuntimeError("DB session is not attached to the request")
    return session


def get_correlation_id() -> str:
    correlation_id = getattr(g, "correlation_id", None)
    return correlation_id if isinstance(correlation_id, str) else "unknown"


def get_current_user() -> User:
    user = getattr(g, "current_user", None)
    if not isinstance(user, User):
        raise RuntimeError("Authenticated user is not attached to the request")
    return user


def get_auth_claims() -> dict[str, object]:
    claims = getattr(g, "auth_claims", None)
    if not isinstance(claims, dict):
        raise RuntimeError("Authenticated claims are not attached to the request")
    return claims
