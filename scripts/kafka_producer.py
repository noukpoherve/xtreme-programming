import json
import socket
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

from confluent_kafka import Producer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kafka_settings import KAFKA_BOOTSTRAP_SERVERS, WATER_QUALITY_TOPIC


def build_water_quality_event() -> dict:
    event_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    return {
        "event_type": "mesure.qualite.eau",
        "event_id": event_id,
        "trace_id": trace_id,
        "capteur_id": "SEINE-PONT-ALMA-001",
        "timestamp": datetime.now(UTC).isoformat(),
        "localisation": {
            "latitude": 48.8637,
            "longitude": 2.3017,
            "point_reference": "Pont de l'Alma",
        },
        "mesures": {
            "ph": 6.2,
            "turbidite_ntu": 145,
            "temperature_c": 14.3,
            "niveau_m": 2.87,
            "debit_m3s": 312.5,
            "oxygene_dissous_mgl": 7.1,
        },
        "qualite_signal": "GOOD",
        "firmware_version": "2.4.1",
    }


def delivery_report(error, message) -> None:
    if error is not None:
        print(f"delivery failed: {error}", file=sys.stderr)
        return

    print(
        "message delivered "
        f"topic={message.topic()} partition={message.partition()} offset={message.offset()}"
    )


def main() -> None:
    event = build_water_quality_event()
    producer = Producer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "client.id": socket.gethostname(),
        }
    )

    payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
    headers = [("trace_id", event["trace_id"].encode("utf-8"))]

    producer.produce(
        WATER_QUALITY_TOPIC,
        key=event["capteur_id"],
        value=payload,
        headers=headers,
        callback=delivery_report,
    )
    producer.flush()

    print(f"event_id={event['event_id']}")
    print(f"trace_id={event['trace_id']}")


if __name__ == "__main__":
    main()
