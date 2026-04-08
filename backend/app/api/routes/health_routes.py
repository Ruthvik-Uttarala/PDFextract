from __future__ import annotations

from typing import Any

from flask import Blueprint, current_app, jsonify

from app.core.config import Settings, get_settings
from app.services import database_service, kafka_service, storage_service

health_blueprint = Blueprint("health_routes", __name__)


def _settings() -> Settings:
    settings = current_app.extensions.get("pdfextract_settings")
    if isinstance(settings, Settings):
        return settings
    return get_settings()


@health_blueprint.get("/api/health")
def health() -> Any:
    return ({"service": "pdfextract-backend", "status": "ok"}, 200)


@health_blueprint.get("/api/ready")
def ready() -> Any:
    settings = _settings()
    checks: dict[str, dict[str, object]] = {}
    failures = False

    for name, checker in (
        ("postgres", database_service.ping_postgres),
        ("minio", storage_service.ping_storage),
        ("kafka", kafka_service.ping_kafka),
    ):
        try:
            checks[name] = {"ok": True, "details": checker(settings)}
        except Exception as error:  # pragma: no cover - surfaced in smoke validation
            failures = True
            checks[name] = {"ok": False, "details": str(error)}

    return (
        jsonify({"status": "not_ready" if failures else "ready", "checks": checks}),
        503 if failures else 200,
    )
