from __future__ import annotations

from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials

from app.core import Settings
from app.core.errors import AuthenticationError


def firebase_status(settings: Settings) -> dict[str, str | bool]:
    if _accepts_deterministic_test_token(settings):
        return {
            "configured": True,
            "mode": "deterministic-test-token",
            "project_id": settings.firebase_project_id or "local-test",
        }

    if settings.firebase_auth_emulator_host:
        return {
            "configured": True,
            "mode": "emulator",
            "project_id": settings.firebase_project_id or "unset",
        }

    if settings.google_application_credentials:
        credential_path = Path(settings.google_application_credentials)
        if credential_path.exists():
            return {
                "configured": True,
                "mode": "service-account",
                "project_id": settings.firebase_project_id or "unset",
            }
        return {
            "configured": False,
            "mode": "service-account-missing",
            "project_id": settings.firebase_project_id or "unset",
        }

    if settings.firebase_project_id:
        return {
            "configured": True,
            "mode": "project-config",
            "project_id": settings.firebase_project_id,
        }

    return {
        "configured": False,
        "mode": "unconfigured",
        "project_id": "unset",
    }


def verify_token(settings: Settings, bearer_token: str) -> dict[str, object]:
    normalized = bearer_token.strip()
    if not normalized:
        raise AuthenticationError("Missing Firebase bearer token")

    test_claims = _maybe_build_test_claims(settings, normalized)
    if test_claims is not None:
        return test_claims

    try:
        app = _get_or_initialize_app(settings)
        decoded = auth.verify_id_token(normalized, app=app)
    except Exception as exc:  # pragma: no cover - depends on external Firebase/Admin setup
        raise AuthenticationError(f"Firebase token verification failed: {exc}") from exc
    return decoded


def initialize_firebase_app(settings: Settings) -> firebase_admin.App:
    return _get_or_initialize_app(settings)


def verify_bearer_token(settings: Settings, bearer_token: str) -> dict[str, object]:
    return verify_token(settings, bearer_token)


def _maybe_build_test_claims(settings: Settings, bearer_token: str) -> dict[str, object] | None:
    if not _accepts_deterministic_test_token(settings):
        return None

    expected = settings.firebase_test_id_token or "test-token"
    if bearer_token != expected:
        return None

    return {
        "uid": settings.firebase_test_uid,
        "user_id": settings.firebase_test_uid,
        "email": settings.firebase_test_email,
        "name": settings.firebase_test_name,
        "email_verified": True,
        "aud": settings.firebase_project_id or "pdfextract-local",
        "iss": (
            "https://securetoken.google.com/"
            f"{settings.firebase_project_id or 'pdfextract-local'}"
        ),
    }


def _accepts_deterministic_test_token(settings: Settings) -> bool:
    return settings.app_env in {"local", "test"}


def _get_or_initialize_app(settings: Settings) -> firebase_admin.App:
    app_name = "pdfextract-backend"

    try:
        return firebase_admin.get_app(app_name)
    except ValueError:
        options = (
            {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
        )

        if settings.firebase_auth_emulator_host:
            return firebase_admin.initialize_app(options=options, name=app_name)

        if not settings.google_application_credentials:
            raise AuthenticationError("GOOGLE_APPLICATION_CREDENTIALS is not set.") from None

        credential_path = Path(settings.google_application_credentials)
        if not credential_path.exists():
            raise AuthenticationError(
                f"Firebase service account file does not exist: {credential_path.as_posix()}"
            ) from None

        return firebase_admin.initialize_app(
            credentials.Certificate(str(credential_path)),
            options=options,
            name=app_name,
        )
