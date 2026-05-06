import json
import os
import socket
import uuid
from datetime import UTC

from iot_service.sensor_service import SensorMeasurement

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
WATER_QUALITY_TOPIC = os.getenv("WATER_QUALITY_TOPIC", "mesure.qualite.eau")


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


class KafkaMeasurementPublisher:
    def __init__(self, bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS):
        from confluent_kafka import Producer

        if not bootstrap_servers:
            raise ValueError("KAFKA_BOOTSTRAP_SERVERS is required")
        self.bootstrap_servers = bootstrap_servers
        self._producer = Producer(
            {
                "bootstrap.servers": self.bootstrap_servers,
                "client.id": socket.gethostname(),
            }
        )

    def publish(self, measurement: SensorMeasurement) -> dict:
        event = build_measurement_event(measurement)
        payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
        headers = [("trace_id", event["trace_id"].encode("utf-8"))]

        self._producer.produce(
            WATER_QUALITY_TOPIC,
            key=event["capteur_id"],
            value=payload,
            headers=headers,
        )
        self._producer.flush()

        return {
            "topic": WATER_QUALITY_TOPIC,
            "bootstrap_servers": self.bootstrap_servers,
            "event_id": event["event_id"],
            "trace_id": event["trace_id"],
            "capteur_id": event["capteur_id"],
            "published": True,
        }


class NoopMeasurementPublisher:
    def publish(self, measurement: SensorMeasurement) -> dict:
        event = build_measurement_event(measurement)
        return {
            "topic": WATER_QUALITY_TOPIC,
            "bootstrap_servers": None,
            "event_id": event["event_id"],
            "trace_id": event["trace_id"],
            "capteur_id": event["capteur_id"],
            "published": False,
        }
