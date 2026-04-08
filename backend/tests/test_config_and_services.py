from __future__ import annotations

from app.core.config import Settings
from app.services.storage_service import canonical_storage_prefixes


def test_settings_canonical_prefixes() -> None:
    settings = Settings(receiving_prefix="receiving", processed_prefix="processed")
    assert settings.canonical_prefixes() == ("receiving", "processed")


def test_canonical_storage_prefixes_enforces_contract() -> None:
    settings = Settings(receiving_prefix="receiving", processed_prefix="processed")
    assert canonical_storage_prefixes(settings) == ("receiving", "processed")
