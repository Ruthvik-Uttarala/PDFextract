from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core import ArtifactType, FailureCode, FileRole, JobStage, JobStatus, Settings
from app.core.errors import ApiError
from app.db.models import FileRecord, Job, ProcessingAttempt
from app.db.repositories import (
    create_extraction_result,
    create_file_record,
    create_output_artifact,
    create_processing_attempt,
    get_file_record,
    get_job,
    get_latest_attempt_number,
    get_processing_attempt,
    mark_attempt_failed,
    mark_attempt_succeeded,
    mark_job_completed,
    mark_job_failed,
    mark_job_processing,
    set_current_output_artifact,
    start_processing_attempt,
)
from app.services.excel_service import generate_excel_workbook
from app.services.extraction_service import extract_document_data
from app.services.pdf_reader_service import read_pdf_document
from app.services.storage_service import build_processed_key, get_object_bytes, put_object_bytes
from app.services.validation_service import validate_normalized_output


@dataclass(frozen=True)
class WorkerExecutionResult:
    job_id: str
    processing_attempt_id: str | None
    status: str
    document_type: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "job_id": self.job_id,
            "processing_attempt_id": self.processing_attempt_id,
            "status": self.status,
            "document_type": self.document_type,
        }


def process_worker_event(
    session: Session,
    *,
    settings: Settings,
    event_payload: dict[str, Any],
    worker_request_id: str | None = None,
) -> WorkerExecutionResult:
    payload = normalize_worker_payload(event_payload)
    job_id = str(payload.get("job_id") or "").strip()
    if not job_id:
        raise ApiError(code=FailureCode.BAD_REQUEST, message="Worker event is missing job_id.")

    job = get_job(session, job_id)
    if job is None:
        raise ApiError(
            code=FailureCode.JOB_NOT_FOUND,
            message="The requested job does not exist.",
            details={"job_id": job_id},
        )

    existing_attempt_id = _coerce_optional_string(payload.get("processing_attempt_id"))
    if job.job_status == JobStatus.COMPLETED and existing_attempt_id is None:
        return WorkerExecutionResult(
            job_id=job.id,
            processing_attempt_id=job.latest_attempt_id,
            status="noop_completed",
            document_type=job.document_type,
        )

    attempt = _ensure_processing_attempt(
        session,
        job=job,
        payload=payload,
        worker_request_id=worker_request_id or str(uuid4()),
    )
    mark_job_processing(
        session,
        job=job,
        attempt_id=attempt.id,
        current_stage=JobStage.WORKER_STARTED,
    )
    session.commit()

    try:
        source_record = _get_source_file_record(session, job)
        job.current_stage = JobStage.PDF_READING
        session.commit()

        pdf_bytes = get_object_bytes(settings, key=source_record.storage_key)
        prepared_pdf = read_pdf_document(pdf_bytes, source_filename=job.source_filename)

        job.document_type = prepared_pdf.document_type
        job.current_stage = JobStage.GEMINI_EXTRACTION
        session.commit()

        extraction = extract_document_data(settings, prepared_pdf)
        job.document_type = extraction.document_type
        job.current_stage = JobStage.VALIDATION

        validation_result = validate_normalized_output(extraction.normalized_json)
        create_extraction_result(
            session,
            job_id=job.id,
            processing_attempt_id=attempt.id,
            document_type=extraction.document_type,
            schema_version=extraction.schema_version,
            extracted_json=extraction.extracted_json,
            normalized_json=extraction.normalized_json,
            validation_passed=validation_result.valid,
            validation_errors=validation_result.errors or None,
        )
        session.commit()

        if not validation_result.valid:
            raise ApiError(
                code=FailureCode.VALIDATION_FAILED,
                message="The extracted output did not pass validation.",
                details={"validation_errors": validation_result.errors},
            )

        job.current_stage = JobStage.EXCEL_GENERATION
        try:
            workbook_bytes, _sheet_names = generate_excel_workbook(
                job_id=job.id,
                source_filename=job.source_filename,
                normalized_json=extraction.normalized_json,
            )
        except Exception as error:
            raise ApiError(
                code=FailureCode.EXCEL_GENERATION_FAILED,
                message="The Excel output could not be generated.",
                details={"reason": str(error)},
            ) from error
        session.commit()

        job.current_stage = JobStage.ARTIFACT_STORAGE
        processed_key = build_processed_key(settings, job.user_id, job.id)
        try:
            storage_metadata = put_object_bytes(
                settings,
                key=processed_key,
                body=workbook_bytes,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as error:
            raise ApiError(
                code=FailureCode.OUTPUT_STORAGE_FAILED,
                message="The Excel output could not be stored.",
                details={"reason": str(error)},
            ) from error
        processed_file = create_file_record(
            session,
            job_id=job.id,
            file_role=FileRole.PROCESSED_EXCEL,
            original_filename="output.xlsx",
            storage_bucket=str(storage_metadata["bucket"]),
            storage_key=str(storage_metadata["key"]),
            content_type=str(storage_metadata["content_type"]),
            size_bytes=_coerce_size_bytes(storage_metadata),
            etag=str(storage_metadata.get("etag") or "") or None,
        )
        artifact = create_output_artifact(
            session,
            job_id=job.id,
            processing_attempt_id=attempt.id,
            artifact_type=ArtifactType.EXCEL,
            file_record_id=processed_file.id,
            is_current=True,
        )
        set_current_output_artifact(session, artifact=artifact)
        job.current_stage = JobStage.COMPLETION_PERSISTED
        mark_attempt_succeeded(session, attempt=attempt)
        mark_job_completed(
            session,
            job=job,
            attempt_id=attempt.id,
            current_stage=JobStage.COMPLETION_PERSISTED,
        )
        session.commit()
        return WorkerExecutionResult(
            job_id=job.id,
            processing_attempt_id=attempt.id,
            status=job.job_status,
            document_type=job.document_type,
        )
    except ApiError as error:
        _mark_processing_failure(session, job=job, attempt=attempt, error=error)
        raise
    except FileNotFoundError as error:
        api_error = ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The source PDF could not be found.",
            status_code=404,
            details={"reason": str(error)},
        )
        _mark_processing_failure(session, job=job, attempt=attempt, error=api_error)
        raise api_error from error
    except Exception as error:
        api_error = ApiError(
            code=FailureCode.INTERNAL_ERROR,
            message="The worker failed unexpectedly.",
            details={"reason": str(error)},
        )
        _mark_processing_failure(session, job=job, attempt=attempt, error=api_error)
        raise api_error from error


def normalize_worker_payload(event: dict[str, Any]) -> dict[str, Any]:
    if "job_id" in event:
        return event

    records = event.get("records")
    if isinstance(records, dict):
        for record_batch in records.values():
            if not isinstance(record_batch, list):
                continue
            for record in record_batch:
                if not isinstance(record, dict):
                    continue
                encoded_value = record.get("value")
                if isinstance(encoded_value, str):
                    return json.loads(base64.b64decode(encoded_value).decode("utf-8"))

    aws_records = event.get("Records")
    if isinstance(aws_records, list):
        for record in aws_records:
            if not isinstance(record, dict):
                continue
            body = record.get("body")
            if isinstance(body, str):
                return json.loads(body)

    raise ApiError(code=FailureCode.BAD_REQUEST, message="Unsupported worker event format.")


def _ensure_processing_attempt(
    session: Session,
    *,
    job: Job,
    payload: dict[str, Any],
    worker_request_id: str,
) -> ProcessingAttempt:
    existing_attempt_id = _coerce_optional_string(payload.get("processing_attempt_id"))
    if existing_attempt_id:
        attempt = get_processing_attempt(session, existing_attempt_id)
        if attempt is None:
            raise ApiError(
                code=FailureCode.BAD_REQUEST,
                message="Worker payload referenced an unknown processing attempt.",
                details={"processing_attempt_id": existing_attempt_id},
            )
        return start_processing_attempt(
            session,
            attempt=attempt,
            worker_request_id=worker_request_id,
            started_at=datetime.now(UTC),
        )

    attempt_number = get_latest_attempt_number(session, job_id=job.id) + 1
    return create_processing_attempt(
        session,
        job_id=job.id,
        attempt_number=attempt_number,
        trigger_type=str(payload.get("attempt_type") or "initial"),
        status=JobStatus.PROCESSING,
        worker_request_id=worker_request_id,
        started_at=datetime.now(UTC),
    )


def _get_source_file_record(session: Session, job: Job) -> FileRecord:
    if not job.source_file_id:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The source PDF reference is missing for this job.",
            status_code=404,
        )

    source_record = get_file_record(session, job.source_file_id)
    if source_record is None:
        raise ApiError(
            code=FailureCode.ARTIFACT_NOT_FOUND,
            message="The source PDF reference is missing for this job.",
            status_code=404,
        )
    return source_record


def _mark_processing_failure(
    session: Session,
    *,
    job: Job,
    attempt: ProcessingAttempt,
    error: ApiError,
) -> None:
    retryable = error.code not in {
        FailureCode.STORAGE_WRITE_FAILED,
        FailureCode.UPLOAD_INVALID_TYPE,
        FailureCode.UPLOAD_EMPTY,
    }
    mark_attempt_failed(
        session,
        attempt=attempt,
        failure_code=error.code,
        failure_message=error.message,
    )
    mark_job_failed(
        session,
        job=job,
        attempt_id=attempt.id,
        current_stage=job.current_stage or JobStage.WORKER_STARTED,
        failure_code=error.code,
        failure_message=error.message,
        retryable=retryable,
    )
    session.commit()


def _coerce_optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_size_bytes(storage_metadata: dict[str, object]) -> int:
    value = storage_metadata.get("size_bytes")
    if value is None:
        return 0
    return int(str(value))
