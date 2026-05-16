from __future__ import annotations

from sqlalchemy import text

from app.core import Settings
from app.db import get_engine, ping_database


def check_database_connection(settings: Settings) -> dict[str, str]:
    ping_database(settings)
    engine = get_engine(settings)
    with engine.connect() as connection:
        if engine.dialect.name == "sqlite":
            row = connection.execute(text("SELECT sqlite_version()")).one()
            return {
                "database": "sqlite",
                "version": f"SQLite {row[0]}",
            }

        row = connection.execute(text("SELECT current_database(), version()")).one()
        return {
            "database": str(row[0]),
            "version": str(row[1]).split(",")[0],
        }


def ping_postgres(settings: Settings) -> dict[str, str]:
    return check_database_connection(settings)
