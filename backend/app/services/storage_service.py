from __future__ import annotations

from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core import Settings


def canonical_storage_prefixes(settings: Settings) -> tuple[str, str]:
    receiving = settings.receiving_prefix.strip().strip("/")
    processed = settings.processed_prefix.strip().strip("/")
    if receiving != "receiving" or processed != "processed":
        raise ValueError("storage prefixes must be receiving and processed")
    return receiving, processed


def _create_s3_client(settings: Settings) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4"),
    )


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
    for prefix in (settings.receiving_prefix, settings.processed_prefix):
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
    return {
        "endpoint": settings.s3_endpoint_url,
        "bucket": settings.s3_bucket_name,
    }


def ping_storage(settings: Settings) -> dict[str, str]:
    return check_storage_connection(settings)
