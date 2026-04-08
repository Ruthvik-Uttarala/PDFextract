from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ExtractionResult


def create_extraction_result(
    session: Session,
    *,
    job_id: str,
    processing_attempt_id: str,
    document_type: str | None,
    schema_version: str,
    extracted_json: dict[str, object],
    normalized_json: dict[str, object] | None,
    validation_passed: bool,
    validation_errors: list[dict[str, object]] | None,
) -> ExtractionResult:
    result = ExtractionResult(
        job_id=job_id,
        processing_attempt_id=processing_attempt_id,
        document_type=document_type,
        schema_version=schema_version,
        extracted_json=extracted_json,
        normalized_json=normalized_json,
        validation_passed=validation_passed,
        validation_errors=validation_errors,
    )
    session.add(result)
    session.flush()
    return result


def get_extraction_result_for_attempt(
    session: Session,
    *,
    processing_attempt_id: str,
) -> ExtractionResult | None:
    return session.execute(
        select(ExtractionResult).where(
            ExtractionResult.processing_attempt_id == processing_attempt_id
        )
    ).scalar_one_or_none()
