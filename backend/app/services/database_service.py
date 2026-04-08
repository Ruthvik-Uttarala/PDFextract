from __future__ import annotations

from psycopg import connect

from app.core import Settings


def check_database_connection(settings: Settings) -> dict[str, str | int]:
    with connect(settings.database_url, connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), version()")
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("PostgreSQL did not return a version row.")
            database_name, version = row

    return {
        "database": str(database_name),
        "version": str(version).split(",")[0],
    }


def ping_postgres(settings: Settings) -> dict[str, str | int]:
    return check_database_connection(settings)
