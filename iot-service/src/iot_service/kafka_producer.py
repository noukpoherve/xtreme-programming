import json
import logging
import os
import uuid
from datetime import UTC
from enum import Enum

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError

from iot_service.sensor_service import SensorMeasurement

_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_TOPIC = os.getenv("WATER_QUALITY_TOPIC", "mesure.qualite.eau")

logger = logging.getLogger(__name__)


class ProducerState(str, Enum):
    """Kafka producer lifecycle states"""
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"


def build_measurement_event(measurement: SensorMeasurement) -> dict:
    trace_id = str(uuid.uuid4())
    return {
        "event_type": "mesure.qualite.eau",
        "event_id": measurement.uuid,
        "trace_id": trace_id,
        "capteur_id": measurement.sensor_id,
        "timestamp": measurement.timestamp.astimezone(UTC).isoformat(),
        "localisation": {
            "latitude": measurement.latitude,
            "longitude": measurement.longitude,
            "point_reference": f"Station {measurement.sensor_id}",
        },
        "mesures": {
            "ph": measurement.ph,
            "turbidite_ntu": measurement.turbidity,
            "temperature_c": measurement.temperature_c,
            "niveau_m": measurement.level,
            "debit_m3s": measurement.flow,
            "oxygene_dissous_mgl": measurement.oxygene_dissous_mgl,
        },
        "qualite_signal": measurement.qualite_signal,
        "firmware_version": measurement.firmware_version,
    }


class MeasurementProducer:
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
            logger.info("Kafka producer started successfully")
        except KafkaConnectionError as e:
            self._state = ProducerState.FAILED
            logger.warning("Kafka not available, producer startup failed: %s", e)
        except Exception as e:
            self._state = ProducerState.FAILED
            logger.exception("Unexpected error while starting Kafka producer: %s", e)

    async def stop(self):
        """Stop the Kafka producer"""
        if self._producer:
            await self._producer.stop()
        self._state = ProducerState.STOPPED
        logger.info("Kafka producer stopped")

    async def send(self, measurement: SensorMeasurement) -> bool:
        """
        Send a measurement event to Kafka.
        
        Returns:
            True if sent successfully, False otherwise.
            
        Note:
            - Serialization errors (client-side) return False without marking producer as FAILED
            - Connection errors (server-side) mark producer as FAILED
        """
        if not self.is_ready or not self._producer:
            logger.debug(
                "Kafka producer not ready (state=%s), cannot send measurement",
                self._state
            )
            return False

        try:
            event = build_measurement_event(measurement)
            payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
            key = event["capteur_id"].encode("utf-8")
            headers = [("trace_id", event["trace_id"].encode("utf-8"))]
            
            await self._producer.send(self._topic, value=payload, key=key, headers=headers)
            logger.info(
                "Published measurement event_id=%s trace_id=%s capteur=%s",
                event["event_id"],
                event["trace_id"],
                event["capteur_id"],
            )
            return True
            
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            # Serialization error: client-side issue, don't mark producer as failed
            logger.warning(
                "Failed to serialize measurement event_id=%s: %s (client error)",
                measurement.uuid,
                e,
            )
            return False
            
        except (KafkaConnectionError, KafkaError) as e:
            # Connection/Kafka error: server-side issue, mark producer as failed
            logger.error(
                "Kafka error while publishing measurement event_id=%s: %s",
                measurement.uuid,
                e,
            )
            self._state = ProducerState.FAILED
            return False
            
        except Exception as e:
            # Unexpected error: log and mark as failed to be safe
            logger.exception(
                "Unexpected error publishing measurement event_id=%s",
                measurement.uuid,
            )
            self._state = ProducerState.FAILED
            return False
