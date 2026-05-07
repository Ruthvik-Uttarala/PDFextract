from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models import OutputArtifact


def create_output_artifact(
    session: Session,
    *,
    job_id: str,
    processing_attempt_id: str,
    artifact_type: str,
    file_record_id: str,
    is_current: bool = True,
) -> OutputArtifact:
    artifact = OutputArtifact(
        job_id=job_id,
        processing_attempt_id=processing_attempt_id,
        artifact_type=artifact_type,
        file_record_id=file_record_id,
        is_current=is_current,
    )
    session.add(artifact)
    session.flush()
    return artifact


def list_output_artifacts_for_job(session: Session, *, job_id: str) -> list[OutputArtifact]:
    statement = (
        select(OutputArtifact)
        .where(OutputArtifact.job_id == job_id)
        .order_by(OutputArtifact.created_at.desc())
    )
    return list(session.execute(statement).scalars())


def get_current_output_artifact(session: Session, *, job_id: str) -> OutputArtifact | None:
    return session.execute(
        select(OutputArtifact).where(
            OutputArtifact.job_id == job_id,
            OutputArtifact.is_current.is_(True),
        )
    ).scalar_one_or_none()


def set_current_output_artifact(
    session: Session,
    *,
    artifact: OutputArtifact,
) -> OutputArtifact:
    session.execute(
        update(OutputArtifact)
        .where(OutputArtifact.job_id == artifact.job_id)
        .values(is_current=False)
    )
    artifact.is_current = True
    session.flush()
    return artifact
