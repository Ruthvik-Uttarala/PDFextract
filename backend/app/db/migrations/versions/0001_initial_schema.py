"""Create canonical PDFextract schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-08 00:00:00.000000
"""

# ruff: noqa: E501

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("firebase_uid", name=op.f("uq_users_firebase_uid")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_firebase_uid"), "users", ["firebase_uid"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("job_status", sa.String(length=32), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=True),
        sa.Column("source_file_id", sa.String(length=36), nullable=True),
        sa.Column("latest_attempt_id", sa.String(length=36), nullable=True),
        sa.Column("source_filename", sa.String(length=512), nullable=False),
        sa.Column("current_stage", sa.String(length=64), nullable=True),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("is_retryable", sa.Boolean(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_jobs_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
    )
    op.create_index(
        op.f("ix_jobs_job_status_submitted_at"),
        "jobs",
        ["job_status", "submitted_at"],
        unique=False,
    )
    op.create_index(op.f("ix_jobs_user_id"), "jobs", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_jobs_user_id_submitted_at"), "jobs", ["user_id", "submitted_at"], unique=False
    )

    op.create_table(
        "file_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("file_role", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=True),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("etag", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_file_records_job_id_jobs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_records")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_file_records_storage_key")),
    )
    op.create_index(op.f("ix_file_records_file_role"), "file_records", ["file_role"], unique=False)
    op.create_index(op.f("ix_file_records_job_id"), "file_records", ["job_id"], unique=False)

    op.create_table(
        "processing_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("worker_request_id", sa.String(length=255), nullable=True),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_processing_attempts_job_id_jobs")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processing_attempts")),
    )
    op.create_index(
        op.f("ix_processing_attempts_job_id"), "processing_attempts", ["job_id"], unique=False
    )

    op.create_table(
        "extraction_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("processing_attempt_id", sa.String(length=36), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=True),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("extracted_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalized_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("validation_passed", sa.Boolean(), nullable=False),
        sa.Column("validation_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_extraction_results_job_id_jobs")
        ),
        sa.ForeignKeyConstraint(
            ["processing_attempt_id"],
            ["processing_attempts.id"],
            name=op.f("fk_extraction_results_processing_attempt_id_processing_attempts"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extraction_results")),
    )
    op.create_index(
        op.f("ix_extraction_results_job_id"), "extraction_results", ["job_id"], unique=False
    )
    op.create_index(
        op.f("ix_extraction_results_processing_attempt_id"),
        "extraction_results",
        ["processing_attempt_id"],
        unique=False,
    )

    op.create_table(
        "output_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("processing_attempt_id", sa.String(length=36), nullable=False),
        sa.Column("artifact_type", sa.String(length=32), nullable=False),
        sa.Column("file_record_id", sa.String(length=36), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["file_record_id"],
            ["file_records.id"],
            name=op.f("fk_output_artifacts_file_record_id_file_records"),
        ),
        sa.ForeignKeyConstraint(
            ["job_id"], ["jobs.id"], name=op.f("fk_output_artifacts_job_id_jobs")
        ),
        sa.ForeignKeyConstraint(
            ["processing_attempt_id"],
            ["processing_attempts.id"],
            name=op.f("fk_output_artifacts_processing_attempt_id_processing_attempts"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_output_artifacts")),
        sa.UniqueConstraint("file_record_id", name=op.f("uq_output_artifacts_file_record_id")),
    )
    op.create_index(
        op.f("ix_output_artifacts_job_id"), "output_artifacts", ["job_id"], unique=False
    )
    op.create_index(
        op.f("ix_output_artifacts_processing_attempt_id"),
        "output_artifacts",
        ["processing_attempt_id"],
        unique=False,
    )

    op.create_table(
        "admin_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("admin_user_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["admin_user_id"], ["users.id"], name=op.f("fk_admin_actions_admin_user_id_users")
        ),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_admin_actions_job_id_jobs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_actions")),
    )
    op.create_index(
        op.f("ix_admin_actions_admin_user_id"), "admin_actions", ["admin_user_id"], unique=False
    )
    op.create_index(op.f("ix_admin_actions_job_id"), "admin_actions", ["job_id"], unique=False)

    op.create_foreign_key(
        op.f("fk_jobs_source_file_id_file_records"),
        "jobs",
        "file_records",
        ["source_file_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_jobs_latest_attempt_id_processing_attempts"),
        "jobs",
        "processing_attempts",
        ["latest_attempt_id"],
        ["id"],
    )
    op.create_unique_constraint(op.f("uq_jobs_source_file_id"), "jobs", ["source_file_id"])


def downgrade() -> None:
    op.drop_constraint(op.f("uq_jobs_source_file_id"), "jobs", type_="unique")
    op.drop_constraint(
        op.f("fk_jobs_latest_attempt_id_processing_attempts"), "jobs", type_="foreignkey"
    )
    op.drop_constraint(op.f("fk_jobs_source_file_id_file_records"), "jobs", type_="foreignkey")
    op.drop_index(op.f("ix_admin_actions_job_id"), table_name="admin_actions")
    op.drop_index(op.f("ix_admin_actions_admin_user_id"), table_name="admin_actions")
    op.drop_table("admin_actions")
    op.drop_index(op.f("ix_output_artifacts_processing_attempt_id"), table_name="output_artifacts")
    op.drop_index(op.f("ix_output_artifacts_job_id"), table_name="output_artifacts")
    op.drop_table("output_artifacts")
    op.drop_index(
        op.f("ix_extraction_results_processing_attempt_id"), table_name="extraction_results"
    )
    op.drop_index(op.f("ix_extraction_results_job_id"), table_name="extraction_results")
    op.drop_table("extraction_results")
    op.drop_index(op.f("ix_processing_attempts_job_id"), table_name="processing_attempts")
    op.drop_table("processing_attempts")
    op.drop_index(op.f("ix_file_records_job_id"), table_name="file_records")
    op.drop_index(op.f("ix_file_records_file_role"), table_name="file_records")
    op.drop_table("file_records")
    op.drop_index(op.f("ix_jobs_user_id_submitted_at"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_user_id"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_job_status_submitted_at"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_users_firebase_uid"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
