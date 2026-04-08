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
    database_url: str = "postgresql://pdfextract:pdfextract@localhost:54329/pdfextract"
    firebase_project_id: str = ""
    google_application_credentials: str = ""
    firebase_auth_emulator_host: str = ""
    s3_bucket_name: str = "pdfextract-local"
    s3_endpoint_url: str = "http://localhost:9000"
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    kafka_bootstrap_servers: str = "localhost:9092"
    gemini_model_name: str = "gemini-1.5-pro"
    receiving_prefix: str = "receiving"
    processed_prefix: str = "processed"
    firebase_test_id_token: str = ""
    log_level: str = "INFO"
    s3_force_path_style: bool = True

    @property
    def firebase_emulator_host(self) -> str:
        return self.firebase_auth_emulator_host

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
                "GOOGLE_APPLICATION_CREDENTIALS", cls.google_application_credentials
            )
            or cls.google_application_credentials,
            firebase_auth_emulator_host=_read_env(
                "FIREBASE_AUTH_EMULATOR_HOST",
                _read_env("FIREBASE_EMULATOR_HOST", cls.firebase_auth_emulator_host)
                or cls.firebase_auth_emulator_host,
            )
            or "",
            s3_bucket_name=_read_env("S3_BUCKET_NAME", cls.s3_bucket_name) or cls.s3_bucket_name,
            s3_endpoint_url=_read_env("S3_ENDPOINT_URL", cls.s3_endpoint_url)
            or cls.s3_endpoint_url,
            aws_access_key_id=_read_env("AWS_ACCESS_KEY_ID", cls.aws_access_key_id)
            or cls.aws_access_key_id,
            aws_secret_access_key=_read_env("AWS_SECRET_ACCESS_KEY", cls.aws_secret_access_key)
            or cls.aws_secret_access_key,
            kafka_bootstrap_servers=_read_env(
                "KAFKA_BOOTSTRAP_SERVERS", cls.kafka_bootstrap_servers
            )
            or cls.kafka_bootstrap_servers,
            gemini_model_name=_read_env("GEMINI_MODEL_NAME", cls.gemini_model_name)
            or cls.gemini_model_name,
            receiving_prefix=_read_env("RECEIVING_PREFIX", cls.receiving_prefix)
            or cls.receiving_prefix,
            processed_prefix=_read_env("PROCESSED_PREFIX", cls.processed_prefix)
            or cls.processed_prefix,
            firebase_test_id_token=_read_env("FIREBASE_TEST_ID_TOKEN", cls.firebase_test_id_token)
            or cls.firebase_test_id_token,
            log_level=_read_env("LOG_LEVEL", cls.log_level) or cls.log_level,
            s3_force_path_style=_read_bool(
                os.getenv("S3_FORCE_PATH_STYLE"), default=cls.s3_force_path_style
            ),
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


load_settings = get_settings
