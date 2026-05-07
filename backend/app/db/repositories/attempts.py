from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.db.models import ProcessingAttempt


def get_latest_attempt_number(session: Session, *, job_id: str) -> int:
    statement = select(func.max(ProcessingAttempt.attempt_number)).where(
        ProcessingAttempt.job_id == job_id
    )
    value = session.execute(statement).scalar_one()
    return int(value or 0)


def create_processing_attempt(
    session: Session,
    *,
    job_id: str,
    attempt_number: int,
    trigger_type: str,
    status: str,
    worker_request_id: str | None = None,
    started_at: datetime | None = None,
) -> ProcessingAttempt:
    attempt = ProcessingAttempt(
        job_id=job_id,
        attempt_number=attempt_number,
        trigger_type=trigger_type,
        status=status,
        worker_request_id=worker_request_id,
        started_at=started_at or utcnow(),
    )
    session.add(attempt)
    session.flush()
    return attempt


def start_processing_attempt(
    session: Session,
    *,
    attempt: ProcessingAttempt,
    worker_request_id: str | None = None,
    started_at: datetime | None = None,
) -> ProcessingAttempt:
    attempt.status = "processing"
    attempt.worker_request_id = worker_request_id
    attempt.started_at = started_at or utcnow()
    session.flush()
    return attempt


def get_processing_attempt(session: Session, attempt_id: str) -> ProcessingAttempt | None:
    return session.get(ProcessingAttempt, attempt_id)


def list_processing_attempts_for_job(session: Session, *, job_id: str) -> list[ProcessingAttempt]:
    statement = (
        select(ProcessingAttempt)
        .where(ProcessingAttempt.job_id == job_id)
        .order_by(ProcessingAttempt.attempt_number.desc())
    )
    return list(session.execute(statement).scalars())


def mark_attempt_succeeded(
    session: Session,
    *,
    attempt: ProcessingAttempt,
    ended_at: datetime | None = None,
) -> ProcessingAttempt:
    attempt.status = "completed"
    attempt.ended_at = ended_at or utcnow()
    attempt.failure_code = None
    attempt.failure_message = None
    session.flush()
    return attempt


def mark_attempt_failed(
    session: Session,
    *,
    attempt: ProcessingAttempt,
    failure_code: str,
    failure_message: str,
    ended_at: datetime | None = None,
) -> ProcessingAttempt:
    attempt.status = "failed"
    attempt.ended_at = ended_at or utcnow()
    attempt.failure_code = failure_code
    attempt.failure_message = failure_message
    session.flush()
    return attempt
