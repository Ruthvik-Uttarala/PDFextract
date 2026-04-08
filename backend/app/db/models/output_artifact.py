from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ArtifactType
from app.db.base import Base, PrimaryKeyMixin, TimestampMixin


class OutputArtifact(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "output_artifacts"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    processing_attempt_id: Mapped[str] = mapped_column(
        ForeignKey("processing_attempts.id"),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ArtifactType.EXCEL,
    )
    file_record_id: Mapped[str] = mapped_column(
        ForeignKey("file_records.id"),
        nullable=False,
        unique=True,
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
