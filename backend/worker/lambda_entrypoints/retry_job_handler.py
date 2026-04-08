from __future__ import annotations

from worker.handlers.retry_document import retry_document


def handler(event, context):
    return retry_document(event, context)
