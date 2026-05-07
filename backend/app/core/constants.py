from __future__ import annotations

from dataclasses import dataclass


class UserRole:
    USER = "user"
    ADMIN = "admin"


class JobStatus:
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    ALL = (QUEUED, PROCESSING, COMPLETED, FAILED)


class JobStage:
    UPLOAD_RECEIVED = "upload_received"
    SOURCE_STORED = "source_stored"
    EVENT_PUBLISHED = "event_published"
    WORKER_STARTED = "worker_started"
    PDF_READING = "pdf_reading"
    GEMINI_EXTRACTION = "gemini_extraction"
    NORMALIZATION = "normalization"
    VALIDATION = "validation"
    EXCEL_GENERATION = "excel_generation"
    ARTIFACT_STORAGE = "artifact_storage"
    COMPLETION_PERSISTED = "completion_persisted"

    ALL = (
        UPLOAD_RECEIVED,
        SOURCE_STORED,
        EVENT_PUBLISHED,
        WORKER_STARTED,
        PDF_READING,
        GEMINI_EXTRACTION,
        NORMALIZATION,
        VALIDATION,
        EXCEL_GENERATION,
        ARTIFACT_STORAGE,
        COMPLETION_PERSISTED,
    )


class FileRole:
    SOURCE_PDF = "source_pdf"
    PROCESSED_EXCEL = "processed_excel"


class DocumentType:
    INVOICE = "invoice"
    RESEARCH_REPORT = "research_report"


class AttemptTriggerType:
    INITIAL = "initial"
    RETRY = "retry"


class ArtifactType:
    EXCEL = "excel"


class AdminActionType:
    RETRY_REQUESTED = "retry_requested"
    JOB_INSPECTED = "job_inspected"


class FailureCode:
    AUTH_INVALID = "AUTH_INVALID"
    AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
    BAD_REQUEST = "BAD_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UPLOAD_MISSING = "UPLOAD_MISSING"
    UPLOAD_INVALID_TYPE = "UPLOAD_INVALID_TYPE"
    UPLOAD_EMPTY = "UPLOAD_EMPTY"
    STORAGE_WRITE_FAILED = "STORAGE_WRITE_FAILED"
    KAFKA_PUBLISH_FAILED = "KAFKA_PUBLISH_FAILED"
    PDF_READ_FAILED = "PDF_READ_FAILED"
    GEMINI_REQUEST_FAILED = "GEMINI_REQUEST_FAILED"
    EXTRACTION_PARSE_FAILED = "EXTRACTION_PARSE_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    EXCEL_GENERATION_FAILED = "EXCEL_GENERATION_FAILED"
    OUTPUT_STORAGE_FAILED = "OUTPUT_STORAGE_FAILED"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    RETRY_NOT_ALLOWED = "RETRY_NOT_ALLOWED"
    DEPENDENCY_NOT_READY = "DEPENDENCY_NOT_READY"


TIMELINE_STAGE_LABELS = {
    JobStage.UPLOAD_RECEIVED: "uploaded",
    JobStage.SOURCE_STORED: "stored",
    JobStage.WORKER_STARTED: "processing started",
    JobStage.GEMINI_EXTRACTION: "extraction complete",
    JobStage.EXCEL_GENERATION: "output generated",
    JobStage.COMPLETION_PERSISTED: "ready for download",
}


@dataclass(frozen=True)
class KafkaTopicSet:
    submit: str = "document.jobs.submit"
    retry: str = "document.jobs.retry"


KAFKA_TOPICS = KafkaTopicSet()
