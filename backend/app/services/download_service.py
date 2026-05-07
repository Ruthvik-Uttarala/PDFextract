from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core import FailureCode, JobStatus
from app.core.errors import ApiError
from app.db.models import Job
from app.db.repositories import get_current_output_artifact, get_file_record


def resolve_download_artifact(session: Session, *, job: Job) -> dict[str, Any]:
    if job.job_status != JobStatus.COMPLETED:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The Excel output is not available for this job.",
            status_code=404,
        )

    artifact = get_current_output_artifact(session, job_id=job.id)
    if artifact is None:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The Excel output is not available for this job.",
            status_code=404,
        )

    file_record = get_file_record(session, artifact.file_record_id)
    if file_record is None:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The Excel output is not available for this job.",
            status_code=404,
        )

    filename = f"{Path(job.source_filename).stem or 'output'}.xlsx"
    return {
        "file_record_id": file_record.id,
        "storage_key": file_record.storage_key,
        "content_type": file_record.content_type
        or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "download_filename": filename,
    }
