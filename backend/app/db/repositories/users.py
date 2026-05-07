from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import UserRole
from app.db.models import User


def get_user_by_firebase_uid(session: Session, firebase_uid: str) -> User | None:
    return session.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    ).scalar_one_or_none()


def upsert_user_from_claims(
    session: Session,
    *,
    claims: dict[str, Any],
    admin_email_allowlist: set[str],
) -> User:
    firebase_uid = str(claims.get("uid") or claims.get("user_id") or "").strip()
    if not firebase_uid:
        raise ValueError("Firebase claims are missing uid")

    email = _clean_optional_string(claims.get("email"))
    display_name = _clean_optional_string(claims.get("name"))
    role = UserRole.ADMIN if email and email.lower() in admin_email_allowlist else UserRole.USER

    user = get_user_by_firebase_uid(session, firebase_uid)
    if user is None:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            role=role,
            is_active=True,
        )
        session.add(user)
        session.flush()
        return user

    user.email = email
    user.display_name = display_name
    user.role = role
    user.is_active = True
    session.flush()
    return user


def _clean_optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
