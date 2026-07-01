import json
import logging
import os
import uuid
from datetime import UTC

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

from iot_service.domain.models import SensorMeasurement
from iot_service.domain.ports import MeasurementWriter

_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_TOPIC = os.getenv("WATER_QUALITY_TOPIC", "mesure.qualite.eau")

logger = logging.getLogger(__name__)


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


class MeasurementProducer(MeasurementWriter):
    """Implémentation Kafka du port MeasurementWriter."""

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
            logger.info("Kafka producer started")
        except KafkaConnectionError:
            logger.warning("Kafka not available, producer will not send messages")
            self._ready = False

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()

    async def write(self, measurement: SensorMeasurement) -> None:
        if not self._ready or not self._producer:
            logger.debug("Kafka producer not ready, skipping write")
            return
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
