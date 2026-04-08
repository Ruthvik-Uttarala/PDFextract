from __future__ import annotations

from confluent_kafka.admin import AdminClient, NewTopic

from app.core import Settings

REQUIRED_TOPICS = ("document.jobs.submit", "document.jobs.retry")


def _create_admin_client(settings: Settings) -> AdminClient:
    return AdminClient(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "socket.timeout.ms": 5000,
        }
    )


def check_kafka_connection(settings: Settings) -> dict[str, str | int]:
    metadata = _create_admin_client(settings).list_topics(timeout=10)
    return {
        "brokers": len(metadata.brokers),
        "bootstrap_servers": settings.kafka_bootstrap_servers,
    }


def ping_kafka(settings: Settings) -> dict[str, str | int]:
    return check_kafka_connection(settings)


def ensure_topics(settings: Settings) -> dict[str, list[str]]:
    admin_client = _create_admin_client(settings)
    metadata = admin_client.list_topics(timeout=10)
    existing_topics = set(metadata.topics.keys())

    topics_to_create = [
        NewTopic(topic, num_partitions=1, replication_factor=1)
        for topic in REQUIRED_TOPICS
        if topic not in existing_topics
    ]

    if topics_to_create:
        results = admin_client.create_topics(topics_to_create)
        for future in results.values():
            future.result()

    return {"topics": list(REQUIRED_TOPICS)}
