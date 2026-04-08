from __future__ import annotations

import argparse
from collections.abc import Sequence

from common import Settings, load_settings

from app.cli import ensure_kafka_topics, ensure_storage


def bootstrap(settings: Settings) -> int:
    _ = settings
    storage_status = ensure_storage()
    if storage_status != 0:
        return storage_status
    return ensure_kafka_topics()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Phase 1 local infra checks.")
    parser.parse_args(argv)
    return bootstrap(load_settings())


if __name__ == "__main__":
    raise SystemExit(main())
