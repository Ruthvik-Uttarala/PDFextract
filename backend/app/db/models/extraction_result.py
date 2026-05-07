from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, PrimaryKeyMixin, TimestampMixin


class ExtractionResult(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "extraction_results"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), nullable=False, index=True)
    processing_attempt_id: Mapped[str] = mapped_column(
        ForeignKey("processing_attempts.id"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    extracted_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    normalized_json: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    validation_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validation_errors: Mapped[list[dict[str, object]] | None] = mapped_column(JSONB, nullable=True)
