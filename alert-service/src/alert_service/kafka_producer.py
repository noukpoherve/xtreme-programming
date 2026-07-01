import json
import logging
import os

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

from alert_service.models import AlertPayload
from alert_service.ports import AlertSender

_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_TOPIC = os.getenv("POLLUTION_ALERT_TOPIC", "alerte.pollution.detectee")

logger = logging.getLogger(__name__)


class AlertProducer(AlertSender):
    """Implémentation Kafka du port AlertSender."""

    def __init__(self, bootstrap_servers: str = _KAFKA_BOOTSTRAP, topic: str = _TOPIC):
        self._bootstrap = bootstrap_servers
        self._topic = topic
        self._producer: AIOKafkaProducer | None = None
        self._ready = False

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
        try:
            await self._producer.start()
            self._ready = True
            logger.info("Kafka alert producer started")
        except KafkaConnectionError:
            logger.warning("Kafka not available, alert producer will not send messages")
            self._ready = False

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def send(self, alert: AlertPayload) -> None:
        if not self._ready or not self._producer:
            logger.debug("Kafka alert producer not ready, skipping send")
            return
        payload = json.dumps(alert.model_dump(mode="json"), ensure_ascii=False).encode(
            "utf-8"
        )
        key = alert.sensor_id.encode("utf-8")
        headers = [("trace_id", alert.trace_id.encode("utf-8"))]
        await self._producer.send(
            self._topic,
            value=payload,
            key=key,
            headers=headers,
        )
        logger.info(
            "Published alert alert_id=%s trace_id=%s sensor=%s",
            alert.alert_id,
            alert.trace_id,
            alert.sensor_id,
        )
