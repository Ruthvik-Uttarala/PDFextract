from __future__ import annotations

import os
import sys
from collections.abc import Callable, Generator
from io import BytesIO
from pathlib import Path

import fitz
import pytest
from flask.testing import FlaskClient
from sqlalchemy.engine import Engine

from app.core.config import Settings
from app.db import Base, get_engine, reset_engine_cache
from app.db.models import (  # noqa: F401
    AdminAction,
    ExtractionResult,
    FileRecord,
    Job,
    OutputArtifact,
    ProcessingAttempt,
    User,
)
from app.main import create_app
from app.services.kafka_service import ensure_topics
from app.services.storage_service import ensure_bucket_and_prefixes

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


TEST_DATABASE_URL = os.getenv(
    "PDFEXTRACT_TEST_DATABASE_URL",
    "postgresql+psycopg://pdfextract:pdfextract@localhost:54329/pdfextract",
)
TEST_S3_ENDPOINT = os.getenv("PDFEXTRACT_TEST_S3_ENDPOINT", "http://127.0.0.1:9000")
TEST_KAFKA_BOOTSTRAP = os.getenv("PDFEXTRACT_TEST_KAFKA_BOOTSTRAP", "127.0.0.1:9092")


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        app_env="test",
        database_url=TEST_DATABASE_URL,
        firebase_project_id="pdfextract-local",
        s3_bucket_name="pdfextract-local",
        s3_endpoint_url=TEST_S3_ENDPOINT,
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        kafka_bootstrap_servers=TEST_KAFKA_BOOTSTRAP,
        admin_email_allowlist="admin@example.com",
        gemini_mock_mode=True,
        cors_allowed_origins="http://127.0.0.1:3000,http://localhost:3000",
    )


@pytest.fixture(scope="session", autouse=True)
def ensure_local_dependencies(settings: Settings) -> None:
    ensure_bucket_and_prefixes(settings)
    ensure_topics(settings)


@pytest.fixture(scope="session")
def engine(settings: Settings) -> Generator[Engine, None, None]:
    reset_engine_cache()
    current_engine = get_engine(settings)
    yield current_engine
    Base.metadata.drop_all(bind=current_engine)
    reset_engine_cache()


@pytest.fixture(autouse=True)
def reset_database(engine: Engine) -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(settings: Settings) -> FlaskClient:
    app = create_app(settings, testing=True)
    return app.test_client()


@pytest.fixture()
def auth_headers() -> Callable[[str], dict[str, str]]:
    def build_headers(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return build_headers


@pytest.fixture()
def invoice_pdf_bytes() -> bytes:
    return _build_pdf_bytes(
        [
            "Invoice",
            "Vendor: Northwind Supplies",
            "Invoice Number: INV-1001",
            "Invoice Date: 2026-04-08",
            "Due Date: 2026-04-15",
            "Currency: USD",
            "Consulting Services | 2 | 1500 | 3000",
            "Total: 3000",
        ]
    )


@pytest.fixture()
def report_pdf_bytes() -> bytes:
    return _build_pdf_bytes(
        [
            "RESEARCH REPORT",
            "Title: 2026 Market Outlook",
            "Authors: Jamie Lee, Morgan Patel",
            "Published Date: 2026-04-08",
            "EXECUTIVE SUMMARY",
            "Findings across the first quarter.",
            "INTRODUCTION",
            "This report reviews current market conditions.",
            "CONCLUSION",
            "Demand remains steady.",
        ]
    )


def _build_pdf_bytes(lines: list[str]) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "\n".join(lines))
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def build_upload_data(file_name: str, payload: bytes) -> dict[str, tuple[BytesIO, str]]:
    return {"file": (BytesIO(payload), file_name)}
