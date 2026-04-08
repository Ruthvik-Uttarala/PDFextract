from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from app.api.request_context import get_correlation_id, get_db_session, get_settings_from_app
from app.core import AdminActionType, FailureCode
from app.core.errors import ApiError
from app.db.repositories import create_admin_action, get_job
from app.services.auth_service import get_authenticated_user, require_admin
from app.services.job_service import get_admin_job_payload, list_admin_job_payloads, retry_job

admin_blueprint = Blueprint("admin_routes", __name__)


@admin_blueprint.get("/api/admin/jobs")
@require_admin
def list_admin_jobs() -> Any:
    session = get_db_session()
    payload = {"jobs": list_admin_job_payloads(session)}
    session.commit()
    return jsonify(payload), 200


@admin_blueprint.get("/api/admin/jobs/<job_id>")
@require_admin
def get_admin_job(job_id: str) -> Any:
    session = get_db_session()
    payload = get_admin_job_payload(session, job_id=job_id, settings=get_settings_from_app())
    if payload is None:
        raise ApiError(
            code=FailureCode.JOB_NOT_FOUND,
            message="The requested job was not found.",
            status_code=404,
        )

    create_admin_action(
        session,
        job_id=job_id,
        admin_user_id=get_authenticated_user().id,
        action_type=AdminActionType.JOB_INSPECTED,
    )
    session.commit()
    return jsonify(payload), 200


@admin_blueprint.post("/api/admin/jobs/<job_id>/retry")
@require_admin
def retry_admin_job(job_id: str) -> Any:
    session = get_db_session()
    job = get_job(session, job_id)
    if job is None:
        raise ApiError(
            code=FailureCode.JOB_NOT_FOUND,
            message="The requested job was not found.",
            status_code=404,
        )

    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes") if isinstance(payload, dict) else None

    try:
        result = retry_job(
            session,
            settings=get_settings_from_app(),
            job=job,
            admin_user=get_authenticated_user(),
            correlation_id=get_correlation_id(),
            notes=str(notes) if notes is not None else None,
        )
    except ValueError as error:
        raise ApiError(
            code=FailureCode.RETRY_NOT_ALLOWED,
            message=str(error),
            status_code=409,
        ) from error

    session.commit()
    return jsonify(result), 202
