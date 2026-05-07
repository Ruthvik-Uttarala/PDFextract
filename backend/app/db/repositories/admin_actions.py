from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AdminAction


def create_admin_action(
    session: Session,
    *,
    job_id: str,
    admin_user_id: str,
    action_type: str,
    notes: str | None = None,
) -> AdminAction:
    action = AdminAction(
        job_id=job_id,
        admin_user_id=admin_user_id,
        action_type=action_type,
        notes=notes,
    )
    session.add(action)
    session.flush()
    return action


def list_admin_actions_for_job(session: Session, *, job_id: str) -> list[AdminAction]:
    statement = (
        select(AdminAction)
        .where(AdminAction.job_id == job_id)
        .order_by(AdminAction.created_at.desc())
    )
    return list(session.execute(statement).scalars())
