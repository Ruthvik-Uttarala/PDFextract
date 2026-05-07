from __future__ import annotations

from http import HTTPStatus
from typing import Any

from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage

from app.core import FailureCode, FileRole, JobStage, Settings
from app.core.errors import ApiError
from app.db.models import User
from app.db.repositories import create_file_record, create_job, mark_job_failed
from app.services.job_service import serialize_job_summary
from app.services.kafka_service import build_job_event, publish_submit_event
from app.services.storage_service import build_source_key, put_object_bytes

ALLOWED_PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream"}


def submit_upload(
    session: Session,
    *,
    settings: Settings,
    user: User,
    uploaded_file: FileStorage | None,
    correlation_id: str,
) -> dict[str, Any]:
    file_bytes, original_filename, content_type = validate_pdf_upload(uploaded_file)
    job = create_job(session, user_id=user.id, source_filename=original_filename)

    source_key = build_source_key(settings, user.id, job.id)
    try:
        storage_metadata = put_object_bytes(
            settings,
            key=source_key,
            body=file_bytes,
            content_type=content_type,
        )
    except Exception as exc:
        mark_job_failed(
            session,
            job=job,
            attempt_id=None,
            current_stage=JobStage.UPLOAD_RECEIVED,
            failure_code=FailureCode.STORAGE_WRITE_FAILED,
            failure_message="The source PDF could not be stored.",
            retryable=False,
        )
        session.commit()
        raise ApiError(
            code=FailureCode.STORAGE_WRITE_FAILED,
            message="The PDF could not be stored.",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details={"job_id": job.id, "reason": str(exc)},
        ) from exc

    file_record = create_file_record(
        session,
        job_id=job.id,
        file_role=FileRole.SOURCE_PDF,
        original_filename=original_filename,
        storage_bucket=str(storage_metadata["bucket"]),
        storage_key=str(storage_metadata["key"]),
        content_type=content_type,
        size_bytes=_coerce_size_bytes(storage_metadata),
        etag=str(storage_metadata.get("etag") or "") or None,
    )
    job.source_file_id = file_record.id
    job.current_stage = JobStage.SOURCE_STORED
    session.commit()

    event = build_job_event(
        job_id=job.id,
        attempt_type="initial",
        requested_by=user.id,
        correlation_id=correlation_id,
    )
    try:
        publish_submit_event(settings, event)
    except Exception as exc:
        mark_job_failed(
            session,
            job=job,
            attempt_id=None,
            current_stage=JobStage.SOURCE_STORED,
            failure_code=FailureCode.KAFKA_PUBLISH_FAILED,
            failure_message="The job was stored but could not be queued for processing.",
            retryable=True,
        )
        session.commit()
        raise ApiError(
            code=FailureCode.KAFKA_PUBLISH_FAILED,
            message="The upload was saved, but processing could not be queued.",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details={"job_id": job.id, "reason": str(exc)},
        ) from exc

    job.current_stage = JobStage.EVENT_PUBLISHED
    session.commit()
    return serialize_job_summary(session, job)


def validate_pdf_upload(uploaded_file: FileStorage | None) -> tuple[bytes, str, str]:
    if uploaded_file is None:
        raise ApiError(
            code=FailureCode.UPLOAD_MISSING,
            message="A PDF file is required.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    original_filename = (uploaded_file.filename or "").strip()
    if not original_filename:
        raise ApiError(
            code=FailureCode.UPLOAD_MISSING,
            message="A PDF file is required.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    content_type = (
        (uploaded_file.mimetype or uploaded_file.content_type or "application/pdf").strip().lower()
    )
    if content_type not in ALLOWED_PDF_CONTENT_TYPES:
        raise ApiError(
            code=FailureCode.UPLOAD_INVALID_TYPE,
            message="Only PDF uploads are supported.",
            status_code=HTTPStatus.BAD_REQUEST,
            details={"content_type": content_type},
        )

    if not original_filename.lower().endswith(".pdf"):
        raise ApiError(
            code=FailureCode.UPLOAD_INVALID_TYPE,
            message="Only PDF uploads are supported.",
            status_code=HTTPStatus.BAD_REQUEST,
            details={"filename": original_filename},
        )

    file_bytes = uploaded_file.read()
    if not file_bytes:
        raise ApiError(
            code=FailureCode.UPLOAD_EMPTY,
            message="The uploaded PDF is empty.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if not file_bytes.startswith(b"%PDF"):
        raise ApiError(
            code=FailureCode.UPLOAD_INVALID_TYPE,
            message="The uploaded file is not a valid PDF.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    return file_bytes, original_filename, "application/pdf"


def _coerce_size_bytes(storage_metadata: dict[str, object]) -> int:
    value = storage_metadata.get("size_bytes")
    if value is None:
        return 0
    return int(str(value))
