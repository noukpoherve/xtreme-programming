import json
import logging
import os
from enum import Enum

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

from alert_service.models import AlertPayload

_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_TOPIC = os.getenv("POLLUTION_ALERT_TOPIC", "alerte.pollution.detectee")

logger = logging.getLogger(__name__)


class ProducerState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"


class AlertProducer:
    def __init__(self, bootstrap_servers: str = _KAFKA_BOOTSTRAP, topic: str = _TOPIC):
        self._bootstrap = bootstrap_servers
        self._topic = topic
        self._producer: AIOKafkaProducer | None = None
        self._state = ProducerState.STOPPED

    @property
    def state(self) -> ProducerState:
        return self._state

    async def start(self):
        self._state = ProducerState.STARTING
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
        try:
            await self._producer.start()
            self._state = ProducerState.RUNNING
            logger.info("Kafka alert producer started")
        except KafkaConnectionError:
            self._state = ProducerState.FAILED
            logger.warning("Kafka not available, alert producer will not send messages")
        except Exception:
            self._state = ProducerState.FAILED
            logger.exception("Unexpected error while starting Kafka alert producer")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
        self._producer = None
        self._state = ProducerState.STOPPED

    async def send(self, alert: AlertPayload) -> bool:
        if self._state != ProducerState.RUNNING or not self._producer:
            logger.debug("Kafka alert producer not ready, skipping send")
            return False
        try:
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
            return True
        except Exception:
            self._state = ProducerState.FAILED
            logger.exception("Failed to publish alert alert_id=%s", alert.alert_id)
            return False
