from __future__ import annotations

import base64
import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
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
from app.services.storage_service import get_object_bytes, put_processed_artifact
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
        extracted_tables = _serialize_tables_for_payload(prepared_pdf.tables)
        enriched_extracted_json = dict(extraction.extracted_json)
        enriched_extracted_json["text_content"] = prepared_pdf.full_text
        enriched_extracted_json["extracted_tables"] = extracted_tables
        job.document_type = extraction.document_type
        job.current_stage = JobStage.VALIDATION

        validation_result = validate_normalized_output(extraction.normalized_json)
        create_extraction_result(
            session,
            job_id=job.id,
            processing_attempt_id=attempt.id,
            document_type=extraction.document_type,
            schema_version=extraction.schema_version,
            extracted_json=enriched_extracted_json,
            normalized_json=extraction.normalized_json,
            validation_passed=validation_result.valid,
            validation_errors=validation_result.errors or None,
        )
        session.commit()

        if not validation_result.valid:
            formatted_errors = "; ".join(
                f"{error.get('field')}: {error.get('message')}"
                for error in validation_result.errors[:3]
                if isinstance(error, dict)
            )
            message = "The extracted output did not pass validation."
            if formatted_errors:
                message = f"{message} {formatted_errors}"
            raise ApiError(
                code=FailureCode.VALIDATION_FAILED,
                message=message,
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
        normalized_payload = extraction.normalized_json or extraction.extracted_json
        json_bytes = json.dumps(normalized_payload, indent=2, ensure_ascii=True).encode("utf-8")
        text_bytes = prepared_pdf.full_text.encode("utf-8")

        try:
            excel_artifact = put_processed_artifact(
                settings,
                user_id=job.user_id,
                job_id=job.id,
                artifact_name="output.xlsx",
                body=workbook_bytes,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            json_artifact = put_processed_artifact(
                settings,
                user_id=job.user_id,
                job_id=job.id,
                artifact_name="result.json",
                body=json_bytes,
                content_type="application/json",
            )
            text_artifact = put_processed_artifact(
                settings,
                user_id=job.user_id,
                job_id=job.id,
                artifact_name="text.txt",
                body=text_bytes,
                content_type="text/plain; charset=utf-8",
            )
        except Exception as error:
            raise ApiError(
                code=FailureCode.OUTPUT_STORAGE_FAILED,
                message="A required artifact could not be stored.",
                details={"reason": str(error)},
            ) from error

        _persist_output_artifact(
            session,
            job_id=job.id,
            attempt_id=attempt.id,
            artifact_type=ArtifactType.EXCEL,
            file_role=FileRole.PROCESSED_EXCEL,
            original_filename="output.xlsx",
            stored=excel_artifact,
            set_as_current=True,
        )
        _persist_output_artifact(
            session,
            job_id=job.id,
            attempt_id=attempt.id,
            artifact_type=ArtifactType.JSON,
            file_role=FileRole.PROCESSED_JSON,
            original_filename="result.json",
            stored=json_artifact,
            set_as_current=True,
        )
        _persist_output_artifact(
            session,
            job_id=job.id,
            attempt_id=attempt.id,
            artifact_type=ArtifactType.TEXT,
            file_role=FileRole.PROCESSED_TEXT,
            original_filename="text.txt",
            stored=text_artifact,
            set_as_current=True,
        )

        for table_payload in extracted_tables:
            table_index_raw = table_payload.get("table_index")
            if not isinstance(table_index_raw, int):
                continue
            table_index = table_index_raw
            csv_bytes = _table_payload_to_csv_bytes(table_payload)
            table_stored = put_processed_artifact(
                settings,
                user_id=job.user_id,
                job_id=job.id,
                artifact_name=f"tables/table_{table_index}.csv",
                body=csv_bytes,
                content_type="text/csv; charset=utf-8",
            )
            _persist_output_artifact(
                session,
                job_id=job.id,
                attempt_id=attempt.id,
                artifact_type=ArtifactType.TABLE_CSV,
                file_role=FileRole.PROCESSED_TABLE_CSV,
                original_filename=f"table_{table_index}.csv",
                stored=table_stored,
                set_as_current=False,
            )

        for image in prepared_pdf.images:
            image_stored = put_processed_artifact(
                settings,
                user_id=job.user_id,
                job_id=job.id,
                artifact_name=f"images/{image.filename}",
                body=image.bytes_data,
                content_type=image.content_type,
            )
            _persist_output_artifact(
                session,
                job_id=job.id,
                attempt_id=attempt.id,
                artifact_type=ArtifactType.IMAGE,
                file_role=FileRole.PROCESSED_IMAGE,
                original_filename=image.filename,
                stored=image_stored,
                set_as_current=False,
            )

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


def _persist_output_artifact(
    session: Session,
    *,
    job_id: str,
    attempt_id: str,
    artifact_type: str,
    file_role: str,
    original_filename: str,
    stored: Any,
    set_as_current: bool,
) -> FileRecord:
    file_record = create_file_record(
        session,
        job_id=job_id,
        file_role=file_role,
        original_filename=original_filename,
        storage_bucket=stored.bucket,
        storage_key=stored.key,
        content_type=stored.content_type,
        size_bytes=stored.size_bytes,
        etag=stored.etag,
    )
    artifact = create_output_artifact(
        session,
        job_id=job_id,
        processing_attempt_id=attempt_id,
        artifact_type=artifact_type,
        file_record_id=file_record.id,
        is_current=True,
    )
    if set_as_current:
        set_current_output_artifact(session, artifact=artifact, artifact_type=artifact_type)
    return file_record


def _serialize_tables_for_payload(
    tables: list[list[list[str | None]]],
) -> list[dict[str, object]]:
    serialized: list[dict[str, object]] = []
    for index, table in enumerate(tables, start=1):
        normalized_rows = [[str(cell or "").strip() for cell in row] for row in table if row]
        if not normalized_rows:
            continue

        first_row = normalized_rows[0]
        columns = [cell or f"column_{col + 1}" for col, cell in enumerate(first_row)]
        rows = normalized_rows[1:]
        if not rows:
            rows = []

        serialized.append(
            {
                "table_index": index,
                "name": f"Table {index}",
                "columns": columns,
                "rows": rows,
            }
        )
    return serialized


def _table_payload_to_csv_bytes(table_payload: dict[str, object]) -> bytes:
    columns_raw = table_payload.get("columns")
    rows_raw = table_payload.get("rows")
    columns = [str(value) for value in columns_raw] if isinstance(columns_raw, list) else []
    rows = rows_raw if isinstance(rows_raw, list) else []

    buffer = StringIO()
    writer = csv.writer(buffer)
    if columns:
        writer.writerow(columns)
    for row in rows:
        if isinstance(row, list):
            writer.writerow([str(value) for value in row])
    return buffer.getvalue().encode("utf-8")


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
