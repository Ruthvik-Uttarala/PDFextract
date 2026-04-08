from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FileRecord


def create_file_record(
    session: Session,
    *,
    job_id: str,
    file_role: str,
    storage_bucket: str,
    storage_key: str,
    original_filename: str | None = None,
    content_type: str | None = None,
    size_bytes: int | None = None,
    etag: str | None = None,
) -> FileRecord:
    record = FileRecord(
        job_id=job_id,
        file_role=file_role,
        storage_bucket=storage_bucket,
        storage_key=storage_key,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=size_bytes,
        etag=etag,
    )
    session.add(record)
    session.flush()
    return record


def get_file_record(session: Session, file_record_id: str) -> FileRecord | None:
    return session.get(FileRecord, file_record_id)


def list_file_records_for_job(session: Session, *, job_id: str) -> list[FileRecord]:
    return list(
        session.execute(
            select(FileRecord)
            .where(FileRecord.job_id == job_id)
            .order_by(FileRecord.created_at.desc())
        ).scalars()
    )


def get_file_record_by_role(session: Session, *, job_id: str, file_role: str) -> FileRecord | None:
    return session.execute(
        select(FileRecord).where(FileRecord.job_id == job_id, FileRecord.file_role == file_role)
    ).scalar_one_or_none()
