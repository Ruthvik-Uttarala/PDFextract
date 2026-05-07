from __future__ import annotations

from sqlalchemy import text

from app.core import Settings
from app.db import get_engine, ping_database


def check_database_connection(settings: Settings) -> dict[str, str]:
    ping_database(settings)
    with get_engine(settings).connect() as connection:
        row = connection.execute(text("SELECT current_database(), version()")).one()
    return {
        "database": str(row[0]),
        "version": str(row[1]).split(",")[0],
    }


def ping_postgres(settings: Settings) -> dict[str, str]:
    return check_database_connection(settings)
