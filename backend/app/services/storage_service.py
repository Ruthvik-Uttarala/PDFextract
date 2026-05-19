from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core import Settings
from app.core.errors import DependencyError


@dataclass(frozen=True)
class StoredArtifact:
    bucket: str
    key: str
    content_type: str
    size_bytes: int
    etag: str | None = None


@dataclass(frozen=True)
class ArtifactDownload:
    bucket: str
    key: str
    content_type: str
    size_bytes: int | None


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
    return build_processed_artifact_key(
        settings,
        user_id=user_id,
        job_id=job_id,
        artifact_name="output.xlsx",
    )


def build_processed_artifact_key(
    settings: Settings,
    *,
    user_id: str,
    job_id: str,
    artifact_name: str,
) -> str:
    _, processed_prefix = canonical_storage_prefixes(settings)
    normalized_name = artifact_name.strip().lstrip("/")
    if not normalized_name:
        raise ValueError("Processed artifact name cannot be empty")
    return f"{processed_prefix}/{user_id}/{job_id}/{normalized_name}"


def ensure_bucket_and_prefixes(settings: Settings) -> dict[str, str | list[str]]:
    if _use_local_storage(settings):
        base = _local_storage_root(settings)
        receiving_prefix, processed_prefix = canonical_storage_prefixes(settings)
        local_prefix_markers: list[str] = []
        for prefix in (receiving_prefix, processed_prefix):
            marker_path = base / prefix / ".keep"
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            marker_path.write_bytes(b"")
            local_prefix_markers.append(f"{prefix}/.keep")
        return {
            "bucket": settings.s3_bucket_name,
            "prefix_markers": local_prefix_markers,
        }

    client = _create_s3_client(settings)
    _ensure_remote_bucket(client, settings)

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
    if _use_local_storage(settings):
        base = _local_storage_root(settings)
        base.mkdir(parents=True, exist_ok=True)
        return {"endpoint": f"file://{base}", "bucket": settings.s3_bucket_name}

    client = _create_s3_client(settings)
    client.list_buckets()
    return {"endpoint": _display_endpoint(settings), "bucket": settings.s3_bucket_name}


def ping_storage(settings: Settings) -> dict[str, str]:
    return check_storage_connection(settings)


def put_source_pdf(
    settings: Settings,
    *,
    user_id: str,
    job_id: str,
    body: bytes,
) -> StoredArtifact:
    key = build_source_key(settings, user_id, job_id)
    return _put_object_bytes(
        settings,
        key=key,
        body=body,
        content_type="application/pdf",
    )


def put_processed_artifact(
    settings: Settings,
    *,
    user_id: str,
    job_id: str,
    artifact_name: str,
    body: bytes,
    content_type: str,
) -> StoredArtifact:
    key = build_processed_artifact_key(
        settings,
        user_id=user_id,
        job_id=job_id,
        artifact_name=artifact_name,
    )
    return _put_object_bytes(
        settings,
        key=key,
        body=body,
        content_type=content_type,
    )


def get_artifact_download(settings: Settings, *, key: str) -> ArtifactDownload:
    if _use_local_storage(settings):
        path = _local_path_for_key(settings, key)
        if not path.exists():
            raise FileNotFoundError(key)
        return ArtifactDownload(
            bucket=settings.s3_bucket_name,
            key=key,
            content_type="application/octet-stream",
            size_bytes=path.stat().st_size,
        )

    client = _create_s3_client(settings)
    try:
        head = client.head_object(Bucket=settings.s3_bucket_name, Key=key)
    except ClientError as exc:
        if _is_not_found(exc):
            raise FileNotFoundError(key) from exc
        raise

    return ArtifactDownload(
        bucket=settings.s3_bucket_name,
        key=key,
        content_type=str(head.get("ContentType") or "application/octet-stream"),
        size_bytes=int(head["ContentLength"]) if "ContentLength" in head else None,
    )


def list_job_artifacts(settings: Settings, *, user_id: str, job_id: str) -> list[str]:
    source_prefix = build_source_key(settings, user_id, job_id).rsplit("/", 1)[0] + "/"
    _, processed_root = canonical_storage_prefixes(settings)
    processed_prefix = f"{processed_root}/{user_id}/{job_id}/"
    prefixes = [source_prefix, processed_prefix]

    if _use_local_storage(settings):
        root = _local_storage_root(settings)
        keys: list[str] = []
        for prefix in prefixes:
            prefix_path = root / prefix
            if not prefix_path.exists():
                continue
            for file_path in prefix_path.rglob("*"):
                if file_path.is_file():
                    keys.append(str(file_path.relative_to(root)).replace("\\", "/"))
        return sorted(keys)

    client = _create_s3_client(settings)
    remote_keys: list[str] = []
    for prefix in prefixes:
        continuation_token: str | None = None
        while True:
            params: dict[str, Any] = {
                "Bucket": settings.s3_bucket_name,
                "Prefix": prefix,
                "MaxKeys": 1000,
            }
            if continuation_token:
                params["ContinuationToken"] = continuation_token
            response = client.list_objects_v2(**params)
            for item in response.get("Contents", []):
                key = str(item.get("Key") or "")
                if key:
                    remote_keys.append(key)
            if not response.get("IsTruncated"):
                break
            continuation_token = str(response.get("NextContinuationToken") or "")
            if not continuation_token:
                break
    return sorted(remote_keys)


def put_object_bytes(
    settings: Settings,
    *,
    key: str,
    body: bytes,
    content_type: str,
) -> dict[str, object]:
    artifact = _put_object_bytes(
        settings,
        key=key,
        body=body,
        content_type=content_type,
    )
    return {
        "bucket": artifact.bucket,
        "key": artifact.key,
        "etag": artifact.etag or "",
        "size_bytes": artifact.size_bytes,
        "content_type": artifact.content_type,
    }


def get_object_bytes(settings: Settings, *, key: str) -> bytes:
    if _use_local_storage(settings):
        target_path = _local_path_for_key(settings, key)
        if not target_path.exists():
            raise FileNotFoundError(key)
        return target_path.read_bytes()

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
    if _use_local_storage(settings):
        payload = get_object_bytes(settings, key=key)
        read_size = chunk_size or settings.download_chunk_size
        for index in range(0, len(payload), read_size):
            yield payload[index : index + read_size]
        return

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
    if _use_local_storage(settings):
        return _local_path_for_key(settings, key).exists()

    client = _create_s3_client(settings)
    try:
        client.head_object(Bucket=settings.s3_bucket_name, Key=key)
    except ClientError as exc:
        if _is_not_found(exc):
            return False
        raise
    return True


def delete_object(settings: Settings, *, key: str) -> None:
    if _use_local_storage(settings):
        target_path = _local_path_for_key(settings, key)
        if target_path.exists():
            target_path.unlink()
        return

    client = _create_s3_client(settings)
    client.delete_object(Bucket=settings.s3_bucket_name, Key=key)


def _put_object_bytes(
    settings: Settings,
    *,
    key: str,
    body: bytes,
    content_type: str,
) -> StoredArtifact:
    if _use_local_storage(settings):
        target_path = _local_path_for_key(settings, key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(body)
        return StoredArtifact(
            bucket=settings.s3_bucket_name,
            key=key,
            content_type=content_type,
            size_bytes=len(body),
            etag=None,
        )

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

    return StoredArtifact(
        bucket=settings.s3_bucket_name,
        key=key,
        content_type=content_type,
        size_bytes=len(body),
        etag=str(response.get("ETag", "")).strip('"') or None,
    )


def _use_local_storage(settings: Settings) -> bool:
    return settings.demo_mode or settings.storage_backend.strip().lower() == "local"


def _local_storage_root(settings: Settings) -> Path:
    return Path(settings.local_storage_path).resolve()


def _local_path_for_key(settings: Settings, key: str) -> Path:
    normalized_key = key.strip().lstrip("/")
    if not normalized_key:
        raise ValueError("Storage key cannot be empty")
    return _local_storage_root(settings) / normalized_key


def _create_s3_client(settings: Settings) -> Any:
    addressing_style = "path" if settings.s3_force_path_style else "auto"
    session = boto3.session.Session()

    client_kwargs: dict[str, Any] = {
        "service_name": "s3",
        "region_name": settings.aws_region,
        "config": Config(signature_version="s3v4", s3={"addressing_style": addressing_style}),
    }
    endpoint_url = settings.s3_endpoint_url.strip()
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
    if settings.aws_access_key_id.strip():
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id.strip()
    if settings.aws_secret_access_key.strip():
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key.strip()
    return session.client(**client_kwargs)


def _ensure_remote_bucket(client: Any, settings: Settings) -> None:
    try:
        client.head_bucket(Bucket=settings.s3_bucket_name)
        return
    except ClientError as error:
        status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status_code != 404:
            raise

    if settings.aws_region == "us-east-1":
        client.create_bucket(Bucket=settings.s3_bucket_name)
    else:
        client.create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
        )


def _display_endpoint(settings: Settings) -> str:
    endpoint = settings.s3_endpoint_url.strip()
    if endpoint:
        return endpoint
    return f"https://s3.{settings.aws_region}.amazonaws.com"


def _is_not_found(error: ClientError) -> bool:
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    error_code = str(error.response.get("Error", {}).get("Code", ""))
    return status_code == 404 or error_code in {"404", "NoSuchKey", "NotFound"}
