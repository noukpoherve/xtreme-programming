import json
import sys
from pathlib import Path
from time import monotonic

from confluent_kafka import Consumer, KafkaException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kafka_settings import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CONSUMER_GROUP,
    KAFKA_CONSUMER_TIMEOUT_SECONDS,
    WATER_QUALITY_TOPIC,
)


def decode_headers(headers) -> dict[str, str]:
    if not headers:
        return {}

    return {
        key: value.decode("utf-8") if isinstance(value, bytes) else str(value)
        for key, value in headers
    }


def main() -> None:
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": KAFKA_CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([WATER_QUALITY_TOPIC])

    print(
        f"waiting for one event on topic={WATER_QUALITY_TOPIC} "
        f"group={KAFKA_CONSUMER_GROUP}"
    )
    deadline = monotonic() + KAFKA_CONSUMER_TIMEOUT_SECONDS

    try:
        while monotonic() < deadline:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                raise KafkaException(message.error())

            payload = json.loads(message.value().decode("utf-8"))
            headers = decode_headers(message.headers())

            print(
                "event received "
                f"topic={message.topic()} partition={message.partition()} "
                f"offset={message.offset()}"
            )
            print(json.dumps({"headers": headers, "payload": payload}, indent=2))

            consumer.commit(message=message)
            break
        else:
            raise TimeoutError(
                "no Kafka message received "
                f"within {KAFKA_CONSUMER_TIMEOUT_SECONDS} seconds"
            )
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
