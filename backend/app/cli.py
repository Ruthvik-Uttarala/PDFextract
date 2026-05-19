from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from app.core import get_settings
from app.main import create_app
from app.services import (
    build_processed_key,
    build_source_key,
    canonical_storage_prefixes,
    check_database_connection,
    delete_object,
    ensure_bucket_and_prefixes,
    ensure_topics,
    firebase_status,
    object_exists,
    put_processed_artifact,
    put_source_pdf,
    verify_token,
)


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, sort_keys=True))


def check_db() -> int:
    settings = get_settings()
    try:
        details = check_database_connection(settings)
    except Exception as error:  # pragma: no cover - handled in CLI smoke use
        _emit({"command": "check-db", "status": "error", "message": str(error)})
        return 1
    _emit({"command": "check-db", "status": "ok", "details": details})
    return 0


def ensure_storage() -> int:
    settings = get_settings()
    try:
        details = ensure_bucket_and_prefixes(settings)
        receiving, processed = canonical_storage_prefixes(settings)
    except Exception as error:  # pragma: no cover - handled in CLI smoke use
        _emit({"command": "ensure-storage", "status": "error", "message": str(error)})
        return 1
    _emit(
        {
            "command": "ensure-storage",
            "status": "ok",
            "details": details,
            "prefixes": {"receiving": receiving, "processed": processed},
        }
    )
    return 0


def smoke_s3_artifacts(user_id: str, job_id: str, cleanup: bool) -> int:
    settings = get_settings()
    try:
        source_artifact = put_source_pdf(
            settings,
            user_id=user_id,
            job_id=job_id,
            body=b"%PDF-1.4\n% PDFextract smoke test\n",
        )
        processed_artifact = put_processed_artifact(
            settings,
            user_id=user_id,
            job_id=job_id,
            artifact_name="result.json",
            body=b'{"status": "ok"}\n',
            content_type="application/json",
        )
        source_exists = object_exists(settings, key=source_artifact.key)
        processed_exists = object_exists(settings, key=processed_artifact.key)
        if cleanup:
            delete_object(settings, key=source_artifact.key)
            delete_object(settings, key=processed_artifact.key)
    except Exception as error:
        _emit({"command": "smoke-s3-artifacts", "status": "error", "message": str(error)})
        return 1

    _emit(
        {
            "command": "smoke-s3-artifacts",
            "status": "ok",
            "bucket": settings.s3_bucket_name,
            "user_id": user_id,
            "job_id": job_id,
            "cleanup": cleanup,
            "source_key": source_artifact.key,
            "source_exists": source_exists,
            "processed_key": processed_artifact.key,
            "processed_exists": processed_exists,
        }
    )
    return 0


def check_storage_layout(user_id: str, job_id: str) -> int:
    settings = get_settings()
    try:
        receiving, processed = canonical_storage_prefixes(settings)
        source_key = build_source_key(settings, user_id, job_id)
        processed_key = build_processed_key(settings, user_id, job_id)
    except Exception as error:  # pragma: no cover - handled in CLI smoke use
        _emit({"command": "check-storage-layout", "status": "error", "message": str(error)})
        return 1
    _emit(
        {
            "command": "check-storage-layout",
            "status": "ok",
            "source_key": source_key,
            "processed_key": processed_key,
            "prefixes": {"receiving": receiving, "processed": processed},
            "user_id": user_id,
            "job_id": job_id,
        }
    )
    return 0


def ensure_kafka_topics() -> int:
    settings = get_settings()
    try:
        details = ensure_topics(settings)
    except Exception as error:  # pragma: no cover - handled in CLI smoke use
        _emit({"command": "ensure-kafka-topics", "status": "error", "message": str(error)})
        return 1
    _emit({"command": "ensure-kafka-topics", "status": "ok", "details": details})
    return 0


def smoke_firebase(token: str | None = None) -> int:
    settings = get_settings()
    try:
        status = firebase_status(settings)
        payload: dict[str, Any] = {
            "command": "smoke-firebase",
            "status": "ok",
            "details": status,
        }
        if token:
            payload["claims"] = verify_token(settings, token)
            payload["token_verified"] = True
        else:
            payload["token_verified"] = False
            payload["token_verification"] = "skipped"
    except Exception as error:  # pragma: no cover - handled in CLI smoke use
        _emit({"command": "smoke-firebase", "status": "error", "message": str(error)})
        return 1
    _emit(payload)
    return 0


def smoke_http() -> int:
    app = create_app(get_settings(), testing=True)
    client = app.test_client()

    health_response = client.get("/api/health")
    ready_response = client.get("/api/ready")
    me_response = client.get("/api/me")

    _emit(
        {
            "command": "smoke-http",
            "status": "ok",
            "responses": {
                "health": {
                    "status": health_response.status_code,
                    "body": health_response.get_json(),
                },
                "ready": {
                    "status": ready_response.status_code,
                    "body": ready_response.get_json(),
                },
                "me": {"status": me_response.status_code, "body": me_response.get_json()},
            },
        }
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("check-db")
    subparsers.add_parser("ensure-storage")

    storage_parser = subparsers.add_parser("check-storage-layout")
    storage_parser.add_argument("--user-id", required=True)
    storage_parser.add_argument("--job-id", required=True)

    s3_smoke_parser = subparsers.add_parser("smoke-s3-artifacts")
    s3_smoke_parser.add_argument("--user-id", default="smoke-user")
    s3_smoke_parser.add_argument(
        "--job-id",
        default=f"smoke-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
    )
    s3_smoke_parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the smoke-test objects after verification.",
    )

    subparsers.add_parser("ensure-kafka-topics")

    firebase_parser = subparsers.add_parser("smoke-firebase")
    firebase_parser.add_argument("--token", default="")

    subparsers.add_parser("smoke-http")

    args = parser.parse_args(argv)

    if args.command == "check-db":
        return check_db()
    if args.command == "ensure-storage":
        return ensure_storage()
    if args.command == "check-storage-layout":
        return check_storage_layout(args.user_id, args.job_id)
    if args.command == "smoke-s3-artifacts":
        return smoke_s3_artifacts(args.user_id, args.job_id, bool(args.cleanup))
    if args.command == "ensure-kafka-topics":
        return ensure_kafka_topics()
    if args.command == "smoke-firebase":
        return smoke_firebase(args.token or None)
    if args.command == "smoke-http":
        return smoke_http()
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
