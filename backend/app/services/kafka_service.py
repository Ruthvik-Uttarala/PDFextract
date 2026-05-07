from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from confluent_kafka import Consumer, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from app.core import KAFKA_TOPICS, Settings
from app.core.errors import DependencyError

REQUIRED_TOPICS = (KAFKA_TOPICS.submit, KAFKA_TOPICS.retry)


@dataclass(frozen=True)
class KafkaJobEvent:
    job_id: str
    attempt_type: str
    requested_at: str
    requested_by: str
    correlation_id: str
    processing_attempt_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        payload = {
            "job_id": self.job_id,
            "attempt_type": self.attempt_type,
            "requested_at": self.requested_at,
            "requested_by": self.requested_by,
            "correlation_id": self.correlation_id,
        }
        if self.processing_attempt_id:
            payload["processing_attempt_id"] = self.processing_attempt_id
        return payload


def build_job_event(
    *,
    job_id: str,
    attempt_type: str,
    requested_by: str,
    correlation_id: str,
    processing_attempt_id: str | None = None,
    requested_at: datetime | None = None,
) -> KafkaJobEvent:
    return KafkaJobEvent(
        job_id=job_id,
        attempt_type=attempt_type,
        requested_at=(requested_at or datetime.now(UTC)).isoformat(),
        requested_by=requested_by,
        correlation_id=correlation_id,
        processing_attempt_id=processing_attempt_id,
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


def publish_submit_event(settings: Settings, event: KafkaJobEvent) -> dict[str, str]:
    return publish_job_event(settings, topic=KAFKA_TOPICS.submit, event=event)


def publish_retry_event(settings: Settings, event: KafkaJobEvent) -> dict[str, str]:
    return publish_job_event(settings, topic=KAFKA_TOPICS.retry, event=event)


def publish_job_event(settings: Settings, *, topic: str, event: KafkaJobEvent) -> dict[str, str]:
    producer = _create_producer(settings)
    payload = json.dumps(event.to_dict()).encode("utf-8")

    try:
        producer.produce(topic, value=payload, key=event.job_id.encode("utf-8"))
        producer.flush(10)
    except Exception as exc:
        raise DependencyError(f"Kafka publish failed: {exc}") from exc

    return {"topic": topic, "job_id": event.job_id}


def consume_single_event(
    settings: Settings,
    *,
    topic: str,
    group_id: str,
    timeout: float = 10.0,
) -> dict[str, Any] | None:
    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([topic])
    try:
        message = consumer.poll(timeout)
        if message is None:
            return None
        if message.error():
            raise DependencyError(f"Kafka consume failed: {message.error()}")
        return json.loads(message.value().decode("utf-8"))
    finally:
        consumer.close()


def _create_admin_client(settings: Settings) -> AdminClient:
    return AdminClient(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "socket.timeout.ms": 5000,
        }
    )


def _create_producer(settings: Settings) -> Producer:
    return Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
