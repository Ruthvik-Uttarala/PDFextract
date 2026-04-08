from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import Settings
from app.core.errors import ConfigurationError, DependencyError


def build_engine(settings: Settings) -> Engine:
    if not settings.database_url:
        raise ConfigurationError("DATABASE_URL is required")
    return create_engine(settings.database_url, future=True, pool_pre_ping=True)


def ping_database(settings: Settings) -> None:
    try:
        with build_engine(settings).connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - surfaced through readiness routes/scripts
        raise DependencyError(f"PostgreSQL check failed: {exc}") from exc
