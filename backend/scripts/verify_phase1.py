from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from common import Settings, load_settings

from app.cli import check_db, smoke_firebase, smoke_http
from app.services import check_kafka_connection, check_storage_connection


def verify(settings: Settings, token: str | None = None) -> int:
    _ = settings
    status = check_db()
    if status != 0:
        return status
    try:
        storage_details = check_storage_connection(load_settings())
        kafka_details = check_kafka_connection(load_settings())
    except Exception as error:
        print(
            json.dumps(
                {
                    "command": "verify-phase1",
                    "status": "error",
                    "error": error.__class__.__name__,
                    "message": str(error),
                },
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                "command": "verify-phase1",
                "status": "ok",
                "storage": storage_details,
                "kafka": kafka_details,
            },
            sort_keys=True,
        )
    )
    if token:
        status = smoke_firebase(token)
        if status != 0:
            return status
    return smoke_http()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Phase 1 dependencies.")
    parser.add_argument("--token", default="", help="Optional Firebase ID token to verify.")
    args = parser.parse_args(argv)

    return verify(load_settings(), token=args.token or None)


if __name__ == "__main__":
    raise SystemExit(main())
