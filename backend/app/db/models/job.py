from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import JobStage, JobStatus
from app.db.base import Base, PrimaryKeyMixin, UpdatedTimestampMixin, utcnow


class Job(PrimaryKeyMixin, UpdatedTimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_user_id_submitted_at", "user_id", "submitted_at"),
        Index("ix_jobs_job_status_submitted_at", "job_status", "submitted_at"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    job_status: Mapped[str] = mapped_column(String(32), nullable=False, default=JobStatus.QUEUED)
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("file_records.id"),
        nullable=True,
        unique=True,
    )
    latest_attempt_id: Mapped[str | None] = mapped_column(
        ForeignKey("processing_attempts.id"),
        nullable=True,
    )
    source_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    current_stage: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default=JobStage.UPLOAD_RECEIVED,
    )
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
