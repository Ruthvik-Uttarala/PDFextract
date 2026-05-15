from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core import (
    AdminActionType,
    FailureCode,
    FileRole,
    JobStage,
    JobStatus,
    Settings,
)
from app.db.models import Job, User
from app.db.repositories import (
    create_admin_action,
    create_processing_attempt,
    get_current_output_artifact,
    get_file_record,
    get_job,
    get_job_for_user,
    get_latest_attempt_number,
    get_latest_extraction_result_for_job,
    list_admin_actions_for_job,
    list_jobs_for_admin,
    list_jobs_for_user,
    list_processing_attempts_for_job,
    mark_attempt_failed,
    mark_job_failed,
    update_job_queue_state,
)
from app.services.kafka_service import build_job_event, publish_retry_event


@dataclass(frozen=True)
class JobArtifactInfo:
    available: bool
    file_record_id: str | None
    storage_key: str | None


def list_user_job_payloads(session: Session, *, user: User) -> list[dict[str, object]]:
    return [
        serialize_job_summary(session, job) for job in list_jobs_for_user(session, user_id=user.id)
    ]


def get_user_job_payload(session: Session, *, user: User, job_id: str) -> dict[str, object] | None:
    job = get_job_for_user(session, job_id=job_id, user_id=user.id)
    if job is None:
        return None
    return serialize_job_detail(session, job=job, include_admin=False)


def list_admin_job_payloads(session: Session) -> list[dict[str, object]]:
    return [
        serialize_job_summary(session, job, include_owner=True)
        for job in list_jobs_for_admin(session)
    ]


def get_admin_job_payload(
    session: Session,
    *,
    job_id: str,
    settings: Settings | None = None,
) -> dict[str, object] | None:
    job = get_job(session, job_id)
    if job is None:
        return None
    return serialize_job_detail(session, job=job, include_admin=True, settings=settings)


def retry_job(
    session: Session,
    *,
    settings: Settings,
    job: Job,
    admin_user: User,
    correlation_id: str,
    notes: str | None = None,
) -> dict[str, object]:
    eligibility = get_retry_eligibility(session, settings=settings, job=job)
    if not eligibility["retry_allowed"]:
        raise ValueError(str(eligibility["reason"]))

    attempt_number = get_latest_attempt_number(session, job_id=job.id) + 1
    attempt = create_processing_attempt(
        session,
        job_id=job.id,
        attempt_number=attempt_number,
        trigger_type="retry",
        status=JobStatus.QUEUED,
    )
    create_admin_action(
        session,
        job_id=job.id,
        admin_user_id=admin_user.id,
        action_type=AdminActionType.RETRY_REQUESTED,
        notes=notes,
    )
    update_job_queue_state(
        session,
        job=job,
        latest_attempt_id=attempt.id,
        current_stage=JobStage.SOURCE_STORED,
    )
    session.commit()

    event = build_job_event(
        job_id=job.id,
        attempt_type="retry",
        requested_by=admin_user.id,
        correlation_id=correlation_id,
        processing_attempt_id=attempt.id,
    )
    try:
        publish_retry_event(settings, event)
    except Exception:
        mark_attempt_failed(
            session,
            attempt=attempt,
            failure_code=FailureCode.KAFKA_PUBLISH_FAILED,
            failure_message="The retry event could not be queued.",
        )
        mark_job_failed(
            session,
            job=job,
            attempt_id=attempt.id,
            current_stage=JobStage.SOURCE_STORED,
            failure_code=FailureCode.KAFKA_PUBLISH_FAILED,
            failure_message="The retry event could not be queued.",
            retryable=True,
        )
        session.commit()
        raise

    job.current_stage = JobStage.EVENT_PUBLISHED
    return {
        "job_id": job.id,
        "processing_attempt_id": attempt.id,
        "status": job.job_status,
        "current_stage": job.current_stage,
    }


def serialize_job_summary(
    session: Session,
    job: Job,
    *,
    include_owner: bool = False,
) -> dict[str, object]:
    artifact = get_job_artifact_info(session, job)
    source_file = get_file_record(session, job.source_file_id) if job.source_file_id else None
    payload: dict[str, object] = {
        "job_id": job.id,
        "source_filename": job.source_filename,
        "source_file_size_bytes": source_file.size_bytes if source_file else None,
        "status": job.job_status,
        "document_type": job.document_type,
        "current_stage": job.current_stage,
        "submitted_at": _iso(job.submitted_at),
        "processing_started_at": _iso(job.processing_started_at),
        "completed_at": _iso(job.completed_at),
        "failed_at": _iso(job.failed_at),
        "output_ready": artifact.available,
        "failure_message": _friendly_failure_message(job.failure_code, job.failure_message),
    }
    if include_owner:
        payload["user_id"] = job.user_id
    return payload


def serialize_job_detail(
    session: Session,
    *,
    job: Job,
    include_admin: bool,
    settings: Settings | None = None,
) -> dict[str, object]:
    payload = serialize_job_summary(session, job, include_owner=include_admin)
    payload["timeline"] = _build_timeline(job)
    payload["download_available"] = get_job_artifact_info(session, job).available
    payload["extraction"] = _build_extraction_preview(session, job=job)

    if include_admin:
        attempts = list_processing_attempts_for_job(session, job_id=job.id)
        payload["failure_code"] = job.failure_code
        payload["attempts"] = [
            {
                "processing_attempt_id": attempt.id,
                "attempt_number": attempt.attempt_number,
                "trigger_type": attempt.trigger_type,
                "status": attempt.status,
                "started_at": _iso(attempt.started_at),
                "ended_at": _iso(attempt.ended_at),
                "worker_request_id": attempt.worker_request_id,
                "failure_code": attempt.failure_code,
                "failure_message": attempt.failure_message,
            }
            for attempt in attempts
        ]
        payload["admin_actions"] = [
            {
                "admin_action_id": action.id,
                "admin_user_id": action.admin_user_id,
                "action_type": action.action_type,
                "notes": action.notes,
                "created_at": _iso(action.created_at),
            }
            for action in list_admin_actions_for_job(session, job_id=job.id)
        ]
        artifact = get_current_output_artifact(session, job_id=job.id)
        artifact_file = get_file_record(session, artifact.file_record_id) if artifact else None
        payload["storage"] = {
            "source_file_id": job.source_file_id,
            "current_output_file_record_id": artifact.file_record_id if artifact else None,
            "current_output_storage_key": artifact_file.storage_key if artifact_file else None,
        }
        payload["retry"] = get_retry_eligibility(session, settings=settings, job=job)

    return payload


def _build_extraction_preview(session: Session, *, job: Job) -> dict[str, object] | None:
    result = get_latest_extraction_result_for_job(session, job_id=job.id)
    if result is None:
        return None

    normalized_json = result.normalized_json if isinstance(result.normalized_json, dict) else None
    extracted_json = result.extracted_json if isinstance(result.extracted_json, dict) else {}

    return {
        "schema_version": result.schema_version,
        "document_type": result.document_type,
        "text_preview": _build_extraction_text_preview(normalized_json, extracted_json),
        "tables": _build_extraction_tables_preview(normalized_json),
        "images": [],
        "normalized_json": normalized_json,
        "extracted_json": extracted_json,
        "validation_passed": result.validation_passed,
        "validation_errors": result.validation_errors or [],
    }


def _build_extraction_text_preview(
    normalized_json: dict[str, object] | None,
    extracted_json: dict[str, object],
) -> str:
    if normalized_json and normalized_json.get("document_type") == "invoice":
        vendor_raw = normalized_json.get("vendor")
        vendor_name = vendor_raw.get("name") if isinstance(vendor_raw, dict) else None
        invoice_number = normalized_json.get("invoice_number")
        invoice_date = normalized_json.get("invoice_date")
        due_date = normalized_json.get("due_date")
        total_amount = normalized_json.get("total_amount")
        currency = normalized_json.get("currency") or "USD"
        line_items_raw = normalized_json.get("line_items")
        line_items = line_items_raw if isinstance(line_items_raw, list) else []

        lines = [
            "Invoice extraction summary",
            f"Vendor: {vendor_name or 'Unknown'}",
            f"Invoice Number: {invoice_number or 'Unknown'}",
            f"Invoice Date: {invoice_date or 'Unknown'}",
            f"Due Date: {due_date or 'Unknown'}",
            f"Total Amount: {total_amount or 'Unknown'} {currency}",
            "",
            "Line items:",
        ]
        for item in line_items:
            if not isinstance(item, dict):
                continue
            description = item.get("description") or "Item"
            quantity = item.get("quantity") or "-"
            unit_price = item.get("unit_price") or "-"
            line_total = item.get("line_total") or "-"
            lines.append(f"- {description}: qty {quantity}, unit {unit_price}, total {line_total}")
        return "\n".join(lines).strip()

    if normalized_json and normalized_json.get("document_type") == "research_report":
        title = normalized_json.get("title") or "Untitled report"
        authors = normalized_json.get("authors")
        sections = normalized_json.get("sections")
        lines = [f"Title: {title}"]
        if isinstance(authors, list) and authors:
            lines.append(f"Authors: {', '.join(str(author) for author in authors)}")
        if isinstance(sections, list):
            lines.append("")
            for section in sections:
                if not isinstance(section, dict):
                    continue
                heading = section.get("heading") or "Section"
                content = section.get("content") or ""
                lines.append(f"{heading}\n{content}".strip())
        return "\n\n".join(lines).strip()

    return str(extracted_json)


def _build_extraction_tables_preview(
    normalized_json: dict[str, object] | None,
) -> list[dict[str, object]]:
    if not isinstance(normalized_json, dict):
        return []

    if normalized_json.get("document_type") == "invoice":
        line_items = normalized_json.get("line_items")
        if not isinstance(line_items, list):
            return []
        rows: list[list[str]] = []
        for item in line_items:
            if not isinstance(item, dict):
                continue
            rows.append(
                [
                    str(item.get("description") or ""),
                    str(item.get("quantity") or ""),
                    str(item.get("unit_price") or ""),
                    str(item.get("line_total") or ""),
                ]
            )
        return [
            {
                "name": "Line Items",
                "columns": ["Description", "Quantity", "Unit Price", "Line Total"],
                "rows": rows,
            }
        ]

    if normalized_json.get("document_type") == "research_report":
        sections = normalized_json.get("sections")
        if not isinstance(sections, list):
            return []
        section_rows: list[list[str]] = []
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_rows.append(
                [str(section.get("heading") or ""), str(section.get("content") or "")]
            )
        return [
            {
                "name": "Sections",
                "columns": ["Heading", "Content"],
                "rows": section_rows,
            }
        ]

    return []


def get_retry_eligibility(
    session: Session,
    *,
    settings: Settings | None,
    job: Job,
) -> dict[str, object]:
    attempts = list_processing_attempts_for_job(session, job_id=job.id)
    retry_limit = settings.admin_retry_limit if settings is not None else None
    source_exists = job.source_file_id is not None and (
        get_file_record(session, job.source_file_id) is not None
    )

    retry_allowed = (
        job.job_status == JobStatus.FAILED
        and job.is_retryable
        and source_exists
        and (retry_limit is None or len(attempts) < retry_limit)
    )
    if retry_allowed:
        reason = None
    elif job.job_status != JobStatus.FAILED:
        reason = "Job is not in failed state."
    elif not job.is_retryable:
        reason = "Job is marked non-retryable."
    elif not source_exists:
        reason = "Source file is missing."
    else:
        reason = "Retry limit has been reached."

    return {
        "retry_allowed": retry_allowed,
        "reason": reason,
        "attempt_count": len(attempts),
        "retry_limit": retry_limit,
    }


def get_job_artifact_info(session: Session, job: Job) -> JobArtifactInfo:
    artifact = get_current_output_artifact(session, job_id=job.id)
    if artifact is None:
        return JobArtifactInfo(available=False, file_record_id=None, storage_key=None)

    file_record = get_file_record(session, artifact.file_record_id)
    if file_record is None or file_record.file_role != FileRole.PROCESSED_EXCEL:
        return JobArtifactInfo(available=False, file_record_id=None, storage_key=None)

    return JobArtifactInfo(
        available=True,
        file_record_id=file_record.id,
        storage_key=file_record.storage_key,
    )


def _build_timeline(job: Job) -> list[dict[str, object]]:
    step_order = [
        ("extract_text", "Extracting text"),
        ("detect_tables", "Detecting tables"),
        ("extract_images", "Extracting images"),
        ("run_ocr", "Running OCR"),
    ]
    current_index = _processing_step_index(job.current_stage)
    if current_index < 0:
        current_index = 0

    timeline: list[dict[str, object]] = []
    for index, (stage, label) in enumerate(step_order):
        state = "pending"
        if job.job_status == JobStatus.COMPLETED:
            state = "completed"
        elif index < current_index:
            state = "completed"
        elif index == current_index:
            state = "current"
        if job.job_status == JobStatus.FAILED and index == current_index:
            state = "failed"

        timeline.append(
            {
                "stage": stage,
                "label": label,
                "state": state,
            }
        )
    return timeline


def _processing_step_index(stage: str | None) -> int:
    if stage in {
        JobStage.UPLOAD_RECEIVED,
        JobStage.SOURCE_STORED,
        JobStage.EVENT_PUBLISHED,
        JobStage.WORKER_STARTED,
        JobStage.PDF_READING,
    }:
        return 0
    if stage == JobStage.GEMINI_EXTRACTION:
        return 1
    if stage in {JobStage.NORMALIZATION, JobStage.VALIDATION}:
        return 2
    if stage in {
        JobStage.EXCEL_GENERATION,
        JobStage.ARTIFACT_STORAGE,
        JobStage.COMPLETION_PERSISTED,
    }:
        return 3
    return -1


def _friendly_failure_message(failure_code: str | None, fallback: str | None) -> str | None:
    if not failure_code:
        return fallback

    messages = {
        FailureCode.KAFKA_PUBLISH_FAILED: (
            "The upload was stored, but processing could not be queued."
        ),
        FailureCode.PDF_READ_FAILED: "The PDF could not be read for extraction.",
        FailureCode.GEMINI_REQUEST_FAILED: (
            "The extraction service could not process this document."
        ),
        FailureCode.VALIDATION_FAILED: "The extracted document data was incomplete or unusable.",
        FailureCode.ARTIFACT_NOT_FOUND: "The Excel output is not currently available.",
    }
    return messages.get(failure_code, fallback)


def _iso(value: object) -> str | None:
    if value is None:
        return None
    return str(value.isoformat()) if hasattr(value, "isoformat") else str(value)
