from __future__ import annotations

from typing import Any

from app.core import get_settings
from app.db import session_scope
from app.services.worker_service import process_worker_event


def run_local_worker(event_payload: dict[str, Any]) -> dict[str, str | None]:
    settings = get_settings()
    with session_scope(settings) as session:
        result = process_worker_event(session, settings=settings, event_payload=event_payload)
    return result.to_dict()
