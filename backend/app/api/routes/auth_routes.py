from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify

from app.api.request_context import get_db_session
from app.services.auth_service import get_authenticated_user, require_auth

auth_blueprint = Blueprint("auth_routes", __name__)


@auth_blueprint.get("/api/me")
@require_auth
def me() -> Any:
    user = get_authenticated_user()
    get_db_session().commit()
    return (
        jsonify(
            {
                "id": user.id,
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role,
                "is_active": user.is_active,
            }
        ),
        200,
    )
