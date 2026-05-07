from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.errors import ConfigurationError, DependencyError


def build_engine(settings: Settings) -> Engine:
    if not settings.database_url:
        raise ConfigurationError("DATABASE_URL is required")

    return _build_engine_for_database_url(settings.database_url)


@lru_cache(maxsize=1)
def _build_engine_for_database_url(database_url: str) -> Engine:
    if not database_url:
        raise ConfigurationError("DATABASE_URL is required")

    return create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
    )


def get_engine(settings: Settings) -> Engine:
    return _build_engine_for_database_url(settings.database_url)


def get_session_factory(settings: Settings) -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(settings),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
        class_=Session,
    )


def create_session(settings: Settings) -> Session:
    return get_session_factory(settings)()


@contextmanager
def session_scope(settings: Settings) -> Iterator[Session]:
    session = create_session(settings)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping_database(settings: Settings) -> None:
    try:
        with get_engine(settings).connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - surfaced through readiness routes/scripts
        raise DependencyError(f"PostgreSQL check failed: {exc}") from exc


def reset_engine_cache() -> None:
    _build_engine_for_database_url.cache_clear()
