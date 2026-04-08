from __future__ import annotations

from typing import Any

from flask import Blueprint, current_app, jsonify, request

from app.core.config import Settings, get_settings
from app.services import firebase_service

auth_blueprint = Blueprint("auth_routes", __name__)


def _settings() -> Settings:
    settings = current_app.extensions.get("pdfextract_settings")
    if isinstance(settings, Settings):
        return settings
    return get_settings()


def _extract_bearer_token() -> str | None:
    header = request.headers.get("Authorization", "").strip()
    if not header.startswith("Bearer "):
        return None
    return header.removeprefix("Bearer ").strip() or None


@auth_blueprint.get("/api/me")
def me() -> Any:
    token = _extract_bearer_token()
    if token is None:
        return jsonify({"error": "missing_bearer_token"}), 401

    settings = _settings()
    status = firebase_service.firebase_status(settings)
    if not bool(status["configured"]):
        return jsonify({"error": "firebase_not_configured", "details": status}), 503

    try:
        decoded_token = firebase_service.verify_bearer_token(settings, token)
    except Exception as error:  # pragma: no cover - exercised by smoke checks when configured
        return jsonify({"error": "invalid_token", "details": str(error)}), 401

    return (
        jsonify(
            {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "role": "user",
                "firebase_project_id": settings.firebase_project_id,
            }
        ),
        200,
    )
