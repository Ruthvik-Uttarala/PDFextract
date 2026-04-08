from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.errors import AuthenticationError, ConfigurationError
from app.services import firebase_service


def verify_firebase_identity(settings: Settings, bearer_token: str) -> dict[str, Any]:
    if not bearer_token:
        raise AuthenticationError("Missing Firebase bearer token")
    return firebase_service.verify_bearer_token(settings, bearer_token)


def require_firebase_configuration(settings: Settings) -> None:
    if not settings.firebase_project_id:
        raise ConfigurationError("FIREBASE_PROJECT_ID is required")
