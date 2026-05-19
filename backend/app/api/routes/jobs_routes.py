from __future__ import annotations

import json
from typing import Any

from flask import Blueprint, Response, jsonify

from app.api.request_context import get_db_session, get_settings_from_app
from app.core import FailureCode, UserRole
from app.core.errors import ApiError
from app.db.repositories import (
    get_job as get_job_by_id,
)
from app.db.repositories import (
    get_job_for_user,
    get_latest_extraction_result_for_job,
)
from app.services.auth_service import get_authenticated_user, require_auth
from app.services.download_service import resolve_download_artifact
from app.services.job_service import get_user_job_payload, list_user_job_payloads
from app.services.storage_service import object_exists, stream_object

jobs_blueprint = Blueprint("jobs_routes", __name__)


@jobs_blueprint.get("/api/jobs")
@require_auth
def list_jobs() -> Any:
    session = get_db_session()
    payload = {"jobs": list_user_job_payloads(session, user=get_authenticated_user())}
    session.commit()
    return jsonify(payload), 200


@jobs_blueprint.get("/api/jobs/<job_id>")
@require_auth
def get_job_detail(job_id: str) -> Any:
    session = get_db_session()
    payload = get_user_job_payload(session, user=get_authenticated_user(), job_id=job_id)
    if payload is None:
        raise ApiError(
            code=FailureCode.JOB_NOT_FOUND,
            message="The requested job was not found.",
            status_code=404,
        )
    session.commit()
    return jsonify(payload), 200


@jobs_blueprint.get("/api/jobs/<job_id>/download")
@require_auth
def download_job_output(job_id: str) -> Response:
    session = get_db_session()
    current_user = get_authenticated_user()
    job = get_job_for_user(session, job_id=job_id, user_id=current_user.id)
    if job is None and current_user.role == UserRole.ADMIN:
        job = get_job_by_id(session, job_id)
    if job is None:
        raise ApiError(
            code=FailureCode.JOB_NOT_FOUND,
            message="The requested job was not found.",
            status_code=404,
        )

    download = resolve_download_artifact(session, job=job)
    storage_key = str(download["storage_key"])
    settings = get_settings_from_app()
    if not object_exists(settings, key=storage_key):
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The Excel output is not available for this job.",
            status_code=404,
        )

    session.commit()
    response = Response(
        stream_object(settings, key=storage_key),
        mimetype=str(download["content_type"]),
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{download["download_filename"]}"'
    )
    return response


@jobs_blueprint.get("/api/jobs/<job_id>/download/json")
@require_auth
def download_job_json(job_id: str) -> Response:
    session = get_db_session()
    current_user = get_authenticated_user()
    job = get_job_for_user(session, job_id=job_id, user_id=current_user.id)
    if job is None and current_user.role == UserRole.ADMIN:
        job = get_job_by_id(session, job_id)
    if job is None:
        raise ApiError(
            code=FailureCode.JOB_NOT_FOUND,
            message="The requested job was not found.",
            status_code=404,
        )

    extraction = get_latest_extraction_result_for_job(session, job_id=job.id)
    if extraction is None:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The JSON output is not available for this job.",
            status_code=404,
        )

    payload = (
        extraction.normalized_json if extraction.normalized_json else extraction.extracted_json
    )
    response_body = json.dumps(payload, indent=2, ensure_ascii=True)
    session.commit()
    response = Response(response_body, mimetype="application/json")
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{job.source_filename.rsplit(".", 1)[0]}.json"'
    )
    return response
