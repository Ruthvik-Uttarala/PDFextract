from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.constants import JobStatus
from app.db.base import utcnow
from app.db.models import Job


def create_job(
    session: Session,
    *,
    user_id: str,
    source_filename: str,
    source_file_id: str | None = None,
) -> Job:
    job = Job(
        user_id=user_id,
        source_filename=source_filename,
        source_file_id=source_file_id,
        job_status=JobStatus.QUEUED,
        submitted_at=utcnow(),
    )
    session.add(job)
    session.flush()
    return job


def get_job(session: Session, job_id: str) -> Job | None:
    return session.get(Job, job_id)


def get_job_for_user(session: Session, *, job_id: str, user_id: str) -> Job | None:
    return session.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user_id)
    ).scalar_one_or_none()


def list_jobs_for_user(session: Session, *, user_id: str, limit: int = 50) -> list[Job]:
    statement = (
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(desc(Job.submitted_at), desc(Job.created_at))
        .limit(limit)
    )
    return list(session.execute(statement).scalars())


def list_jobs_for_admin(session: Session, *, limit: int = 100) -> list[Job]:
    statement = select(Job).order_by(desc(Job.submitted_at), desc(Job.created_at)).limit(limit)
    return list(session.execute(statement).scalars())


def update_job_queue_state(
    session: Session,
    *,
    job: Job,
    latest_attempt_id: str | None,
    current_stage: str,
) -> Job:
    job.job_status = JobStatus.QUEUED
    job.current_stage = current_stage
    job.latest_attempt_id = latest_attempt_id
    job.failure_code = None
    job.failure_message = None
    job.processing_started_at = None
    job.completed_at = None
    job.failed_at = None
    session.flush()
    return job


def mark_job_processing(
    session: Session,
    *,
    job: Job,
    attempt_id: str,
    current_stage: str,
    started_at: datetime | None = None,
) -> Job:
    job.job_status = JobStatus.PROCESSING
    job.current_stage = current_stage
    job.latest_attempt_id = attempt_id
    job.processing_started_at = started_at or utcnow()
    job.completed_at = None
    job.failed_at = None
    job.failure_code = None
    job.failure_message = None
    session.flush()
    return job


def mark_job_completed(
    session: Session,
    *,
    job: Job,
    attempt_id: str,
    current_stage: str,
    completed_at: datetime | None = None,
) -> Job:
    job.job_status = JobStatus.COMPLETED
    job.current_stage = current_stage
    job.latest_attempt_id = attempt_id
    job.completed_at = completed_at or utcnow()
    job.failed_at = None
    job.failure_code = None
    job.failure_message = None
    session.flush()
    return job


def mark_job_failed(
    session: Session,
    *,
    job: Job,
    attempt_id: str | None,
    current_stage: str,
    failure_code: str,
    failure_message: str,
    retryable: bool = True,
    failed_at: datetime | None = None,
) -> Job:
    job.job_status = JobStatus.FAILED
    job.current_stage = current_stage
    job.latest_attempt_id = attempt_id
    job.failure_code = failure_code
    job.failure_message = failure_message
    job.is_retryable = retryable
    job.failed_at = failed_at or utcnow()
    job.completed_at = None
    session.flush()
    return job
