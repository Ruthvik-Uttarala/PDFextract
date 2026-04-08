from __future__ import annotations

from worker.handlers.process_document import process_document


def handler(event, context):
    return process_document(event, context)
