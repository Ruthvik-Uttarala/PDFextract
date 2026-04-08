from __future__ import annotations

from typing import Any

from app.core import get_settings
from app.db import session_scope
from app.services.worker_service import process_worker_event


def process_document(event: dict[str, Any], context: Any) -> dict[str, str | None]:
    settings = get_settings()
    request_id = getattr(context, "aws_request_id", None)
    with session_scope(settings) as session:
        result = process_worker_event(
            session,
            settings=settings,
            event_payload=event,
            worker_request_id=str(request_id) if request_id else None,
        )
    return result.to_dict()
