from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core import ArtifactType, FailureCode, JobStatus
from app.core.errors import ApiError
from app.db.models import FileRecord, Job, OutputArtifact
from app.db.repositories import (
    get_current_output_artifact_by_type,
    get_file_record,
    list_output_artifacts_for_job,
)


def resolve_download_artifact(session: Session, *, job: Job) -> dict[str, Any]:
    artifact, file_record = _resolve_current_artifact_by_type(
        session,
        job=job,
        artifact_type=ArtifactType.EXCEL,
        missing_message="The Excel output is not available for this job.",
    )
    filename = f"{Path(job.source_filename).stem or 'output'}.xlsx"
    return _download_payload(
        artifact=artifact,
        file_record=file_record,
        default_content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        download_filename=filename,
    )


def resolve_json_download_artifact(session: Session, *, job: Job) -> dict[str, Any]:
    artifact, file_record = _resolve_current_artifact_by_type(
        session,
        job=job,
        artifact_type=ArtifactType.JSON,
        missing_message="The JSON output is not available for this job.",
    )
    filename = f"{Path(job.source_filename).stem or 'output'}.json"
    return _download_payload(
        artifact=artifact,
        file_record=file_record,
        default_content_type="application/json",
        download_filename=filename,
    )


def resolve_text_download_artifact(session: Session, *, job: Job) -> dict[str, Any]:
    artifact, file_record = _resolve_current_artifact_by_type(
        session,
        job=job,
        artifact_type=ArtifactType.TEXT,
        missing_message="The text output is not available for this job.",
    )
    filename = f"{Path(job.source_filename).stem or 'output'}.txt"
    return _download_payload(
        artifact=artifact,
        file_record=file_record,
        default_content_type="text/plain; charset=utf-8",
        download_filename=filename,
    )


def resolve_table_download_artifact(
    session: Session, *, job: Job, table_index: int
) -> dict[str, Any]:
    _assert_job_has_completed_artifacts(
        job=job,
        message="The table output is not available for this job.",
    )
    if table_index < 1:
        raise ApiError(
            code=FailureCode.BAD_REQUEST,
            message="table_index must be a positive integer.",
            status_code=400,
        )

    table_name = f"table_{table_index}.csv"
    file_record = _find_attempt_file_record_by_name(
        session,
        job=job,
        artifact_type=ArtifactType.TABLE_CSV,
        filename=table_name,
    )
    return _download_payload(
        artifact=None,
        file_record=file_record,
        default_content_type="text/csv; charset=utf-8",
        download_filename=table_name,
    )


def resolve_image_download_artifact(session: Session, *, job: Job, image_id: str) -> dict[str, Any]:
    _assert_job_has_completed_artifacts(
        job=job,
        message="The image output is not available for this job.",
    )
    image_index = _parse_image_index(image_id)
    image_prefix = f"image_{image_index}."
    file_record = _find_attempt_file_record_by_prefix(
        session,
        job=job,
        artifact_type=ArtifactType.IMAGE,
        filename_prefix=image_prefix,
    )
    return _download_payload(
        artifact=None,
        file_record=file_record,
        default_content_type="application/octet-stream",
        download_filename=file_record.original_filename or f"image_{image_index}",
    )


def _resolve_current_artifact_by_type(
    session: Session,
    *,
    job: Job,
    artifact_type: str,
    missing_message: str,
) -> tuple[OutputArtifact, FileRecord]:
    _assert_job_has_completed_artifacts(job=job, message=missing_message)
    artifact = get_current_output_artifact_by_type(
        session,
        job_id=job.id,
        artifact_type=artifact_type,
    )
    if artifact is None:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message=missing_message,
            status_code=404,
        )
    file_record = get_file_record(session, artifact.file_record_id)
    if file_record is None:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message=missing_message,
            status_code=404,
        )
    return artifact, file_record


def _find_attempt_file_record_by_name(
    session: Session,
    *,
    job: Job,
    artifact_type: str,
    filename: str,
) -> FileRecord:
    file_records = _list_latest_attempt_file_records(
        session,
        job=job,
        artifact_type=artifact_type,
    )
    for record in file_records:
        if (record.original_filename or "").strip() == filename:
            return record
    raise ApiError(
        code=FailureCode.ARTIFACT_NOT_FOUND,
        message="The requested artifact is not available for this job.",
        status_code=404,
    )


def _find_attempt_file_record_by_prefix(
    session: Session,
    *,
    job: Job,
    artifact_type: str,
    filename_prefix: str,
) -> FileRecord:
    file_records = _list_latest_attempt_file_records(
        session,
        job=job,
        artifact_type=artifact_type,
    )
    for record in file_records:
        if (record.original_filename or "").strip().startswith(filename_prefix):
            return record
    raise ApiError(
        code=FailureCode.ARTIFACT_NOT_FOUND,
        message="The requested artifact is not available for this job.",
        status_code=404,
    )


def _list_latest_attempt_file_records(
    session: Session,
    *,
    job: Job,
    artifact_type: str,
) -> list[FileRecord]:
    if not job.latest_attempt_id:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The requested artifact is not available for this job.",
            status_code=404,
        )
    artifacts = list_output_artifacts_for_job(session, job_id=job.id)
    records: list[FileRecord] = []
    for artifact in artifacts:
        if artifact.processing_attempt_id != job.latest_attempt_id:
            continue
        if artifact.artifact_type != artifact_type:
            continue
        file_record = get_file_record(session, artifact.file_record_id)
        if file_record is not None:
            records.append(file_record)
    return records


def _download_payload(
    *,
    artifact: OutputArtifact | None,
    file_record: FileRecord,
    default_content_type: str,
    download_filename: str,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact.id if artifact is not None else None,
        "file_record_id": file_record.id,
        "storage_key": file_record.storage_key,
        "content_type": file_record.content_type or default_content_type,
        "download_filename": download_filename,
        "size_bytes": file_record.size_bytes,
    }


def _assert_job_has_completed_artifacts(*, job: Job, message: str) -> None:
    if job.job_status != JobStatus.COMPLETED:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message=message,
            status_code=404,
        )


def _parse_image_index(image_id: str) -> int:
    normalized = image_id.strip().lower()
    if not normalized:
        raise ApiError(
            code=FailureCode.BAD_REQUEST,
            message="image_id is required.",
            status_code=400,
        )
    match = re.search(r"(\d+)", normalized)
    if not match:
        raise ApiError(
            code=FailureCode.BAD_REQUEST,
            message="image_id must contain an image index.",
            status_code=400,
        )
    return int(match.group(1))
