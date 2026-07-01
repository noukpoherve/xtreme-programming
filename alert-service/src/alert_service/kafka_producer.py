import json
import logging
import os
from enum import Enum

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError

from alert_service.models import AlertPayload

_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_TOPIC = os.getenv("POLLUTION_ALERT_TOPIC", "alerte.pollution.detectee")

logger = logging.getLogger(__name__)


class ProducerState(str, Enum):
    """Kafka producer lifecycle states"""
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
        """Get current producer state"""
        return self._state

    @property
    def is_ready(self) -> bool:
        """Check if producer is ready to send messages"""
        return self._state == ProducerState.RUNNING

    async def start(self):
        """Start the Kafka producer"""
        if self._state != ProducerState.STOPPED:
            logger.warning("Producer already started (state=%s)", self._state)
            return

        self._state = ProducerState.STARTING
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
        
        try:
            await self._producer.start()
            self._state = ProducerState.RUNNING
            logger.info("Kafka alert producer started successfully")
        except KafkaConnectionError as e:
            self._state = ProducerState.FAILED
            logger.warning("Kafka not available, alert producer startup failed: %s", e)
        except Exception as e:
            self._state = ProducerState.FAILED
            logger.exception("Unexpected error while starting Kafka alert producer: %s", e)

    async def stop(self):
        """Stop the Kafka producer"""
        if self._producer:
            await self._producer.stop()
        self._producer = None
        self._state = ProducerState.STOPPED
        logger.info("Kafka alert producer stopped")

    async def send(self, alert: AlertPayload) -> bool:
        """
        Send an alert event to Kafka.
        
        Returns:
            True if sent successfully, False otherwise.
            
        Note:
            - Serialization errors (client-side) return False without marking producer as FAILED
            - Connection errors (server-side) mark producer as FAILED
        """
        if not self.is_ready or not self._producer:
            logger.debug(
                "Kafka alert producer not ready (state=%s), cannot send alert",
                self._state
            )
            return False

        try:
            payload = json.dumps(alert.model_dump(mode="json"), ensure_ascii=False).encode("utf-8")
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
            
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError) as e:
            # Serialization error: client-side issue, don't mark producer as failed
            logger.warning(
                "Failed to serialize alert alert_id=%s: %s (client error)",
                alert.alert_id,
                e,
            )
            return False
            
        except (KafkaConnectionError, KafkaError) as e:
            # Connection/Kafka error: server-side issue, mark producer as failed
            logger.error(
                "Kafka error while publishing alert alert_id=%s: %s",
                alert.alert_id,
                e,
            )
            self._state = ProducerState.FAILED
            return False
            
        except Exception as e:
            # Unexpected error: log and mark as failed to be safe
            logger.exception(
                "Unexpected error publishing alert alert_id=%s",
                alert.alert_id,
            )
            self._state = ProducerState.FAILED
            return False
