from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from app.api.request_context import get_correlation_id, get_db_session, get_settings_from_app
from app.services.auth_service import get_authenticated_user, require_auth
from app.services.upload_service import submit_upload

uploads_blueprint = Blueprint("uploads_routes", __name__)


@uploads_blueprint.post("/api/uploads")
@require_auth
def upload_pdf() -> Any:
    payload = submit_upload(
        get_db_session(),
        settings=get_settings_from_app(),
        user=get_authenticated_user(),
        uploaded_file=request.files.get("file"),
        correlation_id=get_correlation_id(),
    )
    return jsonify(payload), 201
