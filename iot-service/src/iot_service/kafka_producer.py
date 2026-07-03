"""
Unified Kafka producer for the iot-service.

Publishes water-quality measurements to the `mesure.qualite.eau` topic.
Accepts both the simulator's `GeneratedMeasurement` dataclass and dict events,
normalizing them to the canonical UrbanHub event shape before serialization.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict
from datetime import UTC
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

from iot_service.config import settings

logger = logging.getLogger(__name__)

# Minimal protocol-ish attribute names used to detect input shape
_GENERATED_SHAPE = {"event_id", "capteur_id", "mesures"}


class MeasurementProducer:
    """Async Kafka producer for water-quality measurements."""

    def __init__(
        self,
        bootstrap_servers: str = settings.kafka_bootstrap_servers,
        topic: str = settings.water_quality_topic,
    ):
        self._bootstrap = bootstrap_servers
        self._topic = topic
        self._producer: AIOKafkaProducer | None = None
        self._ready = False
        self._messages_sent = 0

    @property
    def is_ready(self) -> bool:
        """Whether the producer is connected and able to send."""
        return self._ready

    @property
    def messages_sent(self) -> int:
        """Total number of messages successfully sent."""
        return self._messages_sent

    async def start(self) -> None:
        """Start the Kafka producer (non-fatal if Kafka is unavailable)."""
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
        try:
            await self._producer.start()
            self._ready = True
            logger.info("Kafka producer started, topic=%s", self._topic)
        except KafkaConnectionError:
            logger.warning(
                "Kafka not available at %s, producer will not send messages",
                self._bootstrap,
            )
            self._ready = False

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer:
            await self._producer.stop()
            self._ready = False

    async def send(self, measurement: Any) -> bool:
        """
        Publish a measurement to Kafka.

        Accepts:
        - GeneratedMeasurement (simulator/orchestrator shape)
        - dict already in canonical WaterMeasurementEvent shape

        Returns True on success, False on failure.
        """
        if not self._ready or not self._producer:
            logger.debug("Producer not ready, skipping send")
            return False

        try:
            event = _normalize(measurement)
        except Exception:
            logger.exception("Failed to normalize measurement for Kafka")
            return False

        payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
        key = event["capteur_id"].encode("utf-8")
        headers = [("trace_id", event["trace_id"].encode("utf-8"))]

        try:
            await self._producer.send(
                self._topic,
                value=payload,
                key=key,
                headers=headers,
            )
            self._messages_sent += 1
            logger.info(
                "Published measurement event_id=%s trace_id=%s capteur=%s",
                event["event_id"],
                event["trace_id"],
                event["capteur_id"],
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send measurement event_id=%s capteur=%s",
                event.get("event_id", "?"),
                event.get("capteur_id", "?"),
            )
            return False


def _normalize(measurement: Any) -> dict[str, Any]:
    """Convert any supported measurement shape to the canonical event dict."""
    if isinstance(measurement, dict):
        return _ensure_complete(measurement)

    fields = set(vars(measurement).keys())

    if _GENERATED_SHAPE.issubset(fields):
        return _generated_measurement_to_event(measurement)

    raise TypeError(f"Unsupported measurement type: {type(measurement)}")


def _generated_measurement_to_event(m: Any) -> dict[str, Any]:
    """Normalize the simulator's GeneratedMeasurement shape."""
    event = asdict(m)
    event["timestamp"] = event["timestamp"].astimezone(UTC).isoformat()
    return _ensure_complete(event)


def _ensure_complete(event: dict[str, Any]) -> dict[str, Any]:
    """Guarantee that the canonical event has all expected keys with defaults."""
    event.setdefault("event_type", "mesure.qualite.eau")
    event.setdefault("trace_id", str(uuid.uuid4()))
    event.setdefault("qualite_signal", "GOOD")
    event.setdefault("firmware_version", "2.4.1")
    event.setdefault("data_source", "simulated")
    return event
