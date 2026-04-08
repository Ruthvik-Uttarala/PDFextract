from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core import Settings
from app.core.errors import DependencyError


def canonical_storage_prefixes(settings: Settings) -> tuple[str, str]:
    receiving = settings.receiving_prefix.strip().strip("/")
    processed = settings.processed_prefix.strip().strip("/")
    if receiving != "receiving" or processed != "processed":
        raise ValueError("Storage prefixes must be receiving and processed")
    return receiving, processed


def build_source_key(settings: Settings, user_id: str, job_id: str) -> str:
    receiving_prefix, _ = canonical_storage_prefixes(settings)
    return f"{receiving_prefix}/{user_id}/{job_id}/source.pdf"


def build_processed_key(settings: Settings, user_id: str, job_id: str) -> str:
    _, processed_prefix = canonical_storage_prefixes(settings)
    return f"{processed_prefix}/{user_id}/{job_id}/output.xlsx"


def ensure_bucket_and_prefixes(settings: Settings) -> dict[str, str | list[str]]:
    client = _create_s3_client(settings)

    try:
        client.head_bucket(Bucket=settings.s3_bucket_name)
    except ClientError as error:
        status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status_code == 404:
            client.create_bucket(Bucket=settings.s3_bucket_name)
        else:
            raise

    created_prefix_markers: list[str] = []
    for prefix in canonical_storage_prefixes(settings):
        marker_key = f"{prefix}/.keep"
        client.put_object(Bucket=settings.s3_bucket_name, Key=marker_key, Body=b"")
        created_prefix_markers.append(marker_key)

    return {
        "bucket": settings.s3_bucket_name,
        "prefix_markers": created_prefix_markers,
    }


def check_storage_connection(settings: Settings) -> dict[str, str]:
    client = _create_s3_client(settings)
    client.list_buckets()
    return {"endpoint": settings.s3_endpoint_url, "bucket": settings.s3_bucket_name}


def ping_storage(settings: Settings) -> dict[str, str]:
    return check_storage_connection(settings)


def put_object_bytes(
    settings: Settings,
    *,
    key: str,
    body: bytes,
    content_type: str,
) -> dict[str, object]:
    client = _create_s3_client(settings)
    try:
        response = client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
    except Exception as exc:
        raise DependencyError(f"Object storage write failed: {exc}") from exc

    return {
        "bucket": settings.s3_bucket_name,
        "key": key,
        "etag": str(response.get("ETag", "")).strip('"'),
        "size_bytes": len(body),
        "content_type": content_type,
    }


def get_object_bytes(settings: Settings, *, key: str) -> bytes:
    client = _create_s3_client(settings)
    try:
        response = client.get_object(Bucket=settings.s3_bucket_name, Key=key)
    except ClientError as exc:
        if _is_not_found(exc):
            raise FileNotFoundError(key) from exc
        raise
    return response["Body"].read()


def stream_object(
    settings: Settings, *, key: str, chunk_size: int | None = None
) -> Iterator[bytes]:
    client = _create_s3_client(settings)
    try:
        response = client.get_object(Bucket=settings.s3_bucket_name, Key=key)
    except ClientError as exc:
        if _is_not_found(exc):
            raise FileNotFoundError(key) from exc
        raise

    body = response["Body"]
    read_size = chunk_size or settings.download_chunk_size
    while True:
        chunk = body.read(read_size)
        if not chunk:
            break
        yield chunk


def object_exists(settings: Settings, *, key: str) -> bool:
    client = _create_s3_client(settings)
    try:
        client.head_object(Bucket=settings.s3_bucket_name, Key=key)
    except ClientError as exc:
        if _is_not_found(exc):
            return False
        raise
    return True


def delete_object(settings: Settings, *, key: str) -> None:
    client = _create_s3_client(settings)
    client.delete_object(Bucket=settings.s3_bucket_name, Key=key)


def _create_s3_client(settings: Settings) -> Any:
    addressing_style = "path" if settings.s3_force_path_style else "auto"
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": addressing_style}),
    )


def _is_not_found(error: ClientError) -> bool:
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    error_code = str(error.response.get("Error", {}).get("Code", ""))
    return status_code == 404 or error_code in {"404", "NoSuchKey", "NotFound"}
