from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional in stripped environments
    load_dotenv = None  # type: ignore[assignment]


BACKEND_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://pdfextract:pdfextract@localhost:54329/pdfextract"
    firebase_project_id: str = ""
    google_application_credentials: str = ""
    firebase_auth_emulator_host: str = ""
    firebase_test_id_token: str = ""
    firebase_test_uid: str = "test-user"
    firebase_test_email: str = "test-user@example.com"
    firebase_test_name: str = "Test User"
    s3_bucket_name: str = "pdfextract-local"
    s3_endpoint_url: str = "http://localhost:9000"
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    kafka_bootstrap_servers: str = "localhost:9092"
    gemini_model_name: str = "gemini-1.5-pro"
    gemini_project_id: str = ""
    gemini_location: str = "us-central1"
    gemini_mock_mode: bool = True
    receiving_prefix: str = "receiving"
    processed_prefix: str = "processed"
    log_level: str = "INFO"
    s3_force_path_style: bool = True
    admin_email_allowlist: str = ""
    admin_retry_limit: int = 3
    download_chunk_size: int = 65536
    api_base_url: str = "http://127.0.0.1:8000"
    cors_allowed_origins: str = "http://127.0.0.1:3000,http://localhost:3000"

    @property
    def firebase_emulator_host(self) -> str:
        return self.firebase_auth_emulator_host

    @property
    def admin_emails(self) -> set[str]:
        values = [value.strip().lower() for value in self.admin_email_allowlist.split(",")]
        return {value for value in values if value}

    @property
    def allowed_cors_origins(self) -> set[str]:
        values = [value.strip() for value in self.cors_allowed_origins.split(",")]
        return {value for value in values if value}

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    def canonical_prefixes(self) -> tuple[str, str]:
        receiving = self.receiving_prefix.strip().strip("/")
        processed = self.processed_prefix.strip().strip("/")
        return receiving, processed

    @classmethod
    def from_env(cls) -> Settings:
        _load_dotenv()
        return cls(
            app_env=_read_env("APP_ENV", cls.app_env) or cls.app_env,
            database_url=_read_env("DATABASE_URL", cls.database_url) or cls.database_url,
            firebase_project_id=_read_env("FIREBASE_PROJECT_ID", cls.firebase_project_id)
            or cls.firebase_project_id,
            google_application_credentials=_read_env(
                "GOOGLE_APPLICATION_CREDENTIALS",
                cls.google_application_credentials,
            )
            or cls.google_application_credentials,
            firebase_auth_emulator_host=_read_env(
                "FIREBASE_AUTH_EMULATOR_HOST",
                _read_env("FIREBASE_EMULATOR_HOST", cls.firebase_auth_emulator_host)
                or cls.firebase_auth_emulator_host,
            )
            or "",
            firebase_test_id_token=_read_env("FIREBASE_TEST_ID_TOKEN", cls.firebase_test_id_token)
            or cls.firebase_test_id_token,
            firebase_test_uid=_read_env("FIREBASE_TEST_UID", cls.firebase_test_uid)
            or cls.firebase_test_uid,
            firebase_test_email=_read_env("FIREBASE_TEST_EMAIL", cls.firebase_test_email)
            or cls.firebase_test_email,
            firebase_test_name=_read_env("FIREBASE_TEST_NAME", cls.firebase_test_name)
            or cls.firebase_test_name,
            s3_bucket_name=_read_env("S3_BUCKET_NAME", cls.s3_bucket_name) or cls.s3_bucket_name,
            s3_endpoint_url=_read_env("S3_ENDPOINT_URL", cls.s3_endpoint_url)
            or cls.s3_endpoint_url,
            aws_access_key_id=_read_env("AWS_ACCESS_KEY_ID", cls.aws_access_key_id)
            or cls.aws_access_key_id,
            aws_secret_access_key=_read_env("AWS_SECRET_ACCESS_KEY", cls.aws_secret_access_key)
            or cls.aws_secret_access_key,
            kafka_bootstrap_servers=_read_env(
                "KAFKA_BOOTSTRAP_SERVERS",
                cls.kafka_bootstrap_servers,
            )
            or cls.kafka_bootstrap_servers,
            gemini_model_name=_read_env("GEMINI_MODEL_NAME", cls.gemini_model_name)
            or cls.gemini_model_name,
            gemini_project_id=_read_env("GEMINI_PROJECT_ID", cls.gemini_project_id)
            or cls.gemini_project_id,
            gemini_location=_read_env("GEMINI_LOCATION", cls.gemini_location)
            or cls.gemini_location,
            gemini_mock_mode=_read_bool(
                os.getenv("GEMINI_MOCK_MODE"),
                default=cls.gemini_mock_mode,
            ),
            receiving_prefix=_read_env("RECEIVING_PREFIX", cls.receiving_prefix)
            or cls.receiving_prefix,
            processed_prefix=_read_env("PROCESSED_PREFIX", cls.processed_prefix)
            or cls.processed_prefix,
            log_level=_read_env("LOG_LEVEL", cls.log_level) or cls.log_level,
            s3_force_path_style=_read_bool(
                os.getenv("S3_FORCE_PATH_STYLE"),
                default=cls.s3_force_path_style,
            ),
            admin_email_allowlist=_read_env("ADMIN_EMAIL_ALLOWLIST", cls.admin_email_allowlist)
            or cls.admin_email_allowlist,
            admin_retry_limit=_read_int(
                os.getenv("ADMIN_RETRY_LIMIT"),
                default=cls.admin_retry_limit,
            ),
            download_chunk_size=_read_int(
                os.getenv("DOWNLOAD_CHUNK_SIZE"),
                default=cls.download_chunk_size,
            ),
            api_base_url=_read_env("API_BASE_URL", cls.api_base_url) or cls.api_base_url,
            cors_allowed_origins=_read_env(
                "CORS_ALLOWED_ORIGINS",
                cls.cors_allowed_origins,
            )
            or cls.cors_allowed_origins,
        )


def _load_dotenv() -> None:
    if load_dotenv is None:
        return
    for relative_path in (".env", ".env.local"):
        env_path = BACKEND_ROOT / relative_path
        if env_path.exists():
            load_dotenv(env_path, override=False)


def _read_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _read_bool(value: str | None, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int(value: str | None, *, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


load_settings = get_settings
