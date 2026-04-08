from __future__ import annotations

from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials

from app.core import Settings


def firebase_status(settings: Settings) -> dict[str, str | bool]:
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
        "project_id": settings.firebase_project_id or "unset",
    }


def _get_or_initialize_app(settings: Settings) -> firebase_admin.App:
    app_name = "pdfextract-backend"

    try:
        return firebase_admin.get_app(app_name)
    except ValueError as error:
        options = (
            {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
        )

        if settings.firebase_auth_emulator_host:
            return firebase_admin.initialize_app(options=options, name=app_name)

        if not settings.google_application_credentials:
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set.") from error

        credential_path = Path(settings.google_application_credentials)
        if not credential_path.exists():
            raise RuntimeError(
                f"Firebase service account file does not exist: {credential_path.as_posix()}"
            ) from error

        return firebase_admin.initialize_app(
            credentials.Certificate(str(credential_path)),
            options=options,
            name=app_name,
        )


def verify_token(settings: Settings, bearer_token: str) -> dict[str, object]:
    app = _get_or_initialize_app(settings)
    return auth.verify_id_token(bearer_token, app=app)


def initialize_firebase_app(settings: Settings) -> firebase_admin.App:
    return _get_or_initialize_app(settings)


def verify_bearer_token(settings: Settings, bearer_token: str) -> dict[str, object]:
    return verify_token(settings, bearer_token)
