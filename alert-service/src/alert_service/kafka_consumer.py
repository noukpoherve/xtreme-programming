import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError

from alert_service.kafka_producer import AlertProducer
from alert_service.models import WaterMeasurementEvent
from alert_service.ports import AlertSender
from alert_service.service import alert_service

logger = logging.getLogger(__name__)

_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_INPUT_TOPIC = os.getenv("WATER_QUALITY_TOPIC", "mesure.qualite.eau")
_MAX_RETRIES = 3


class MeasurementConsumer:
    def __init__(
        self,
        bootstrap_servers: str = _KAFKA_BOOTSTRAP,
        input_topic: str = _INPUT_TOPIC,
        producer: AlertSender | None = None,
    ):
        self._bootstrap = bootstrap_servers
        self._input_topic = input_topic
        self._producer: AlertSender = producer or AlertProducer(
            bootstrap_servers=bootstrap_servers
        )
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    async def start(self):
        await self._producer.start()
        self._consumer = AIOKafkaConsumer(
            self._input_topic,
            bootstrap_servers=self._bootstrap,
            group_id="alert-service-group",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        try:
            await self._consumer.start()
            self._running = True
            logger.info("Kafka consumer started on topic %s", self._input_topic)
        except KafkaConnectionError:
            logger.warning("Kafka not available, consumer will not run")
            self._running = False

    async def stop(self):
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        await self._producer.stop()

    async def run(self):
        if not self._running or not self._consumer:
            return
        async for msg in self._consumer:
            if not self._running:
                break
            for attempt in range(_MAX_RETRIES):
                try:
                    await self._process(msg)
                    break
                except Exception:
                    logger.exception(
                        "Failed to process Kafka message (attempt %d/%d)",
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(2**attempt)
            else:
                logger.error(
                    "Giving up on message after %d attempts, committing offset",
                    _MAX_RETRIES,
                )
                await self._consumer.commit()

    async def _process(self, msg):
        payload = json.loads(msg.value.decode("utf-8"))
        measurement = WaterMeasurementEvent.model_validate(payload)
        alerts = alert_service.build_alerts_from_measurement(measurement)

        for alert in alerts:
            result = await alert_service.process_alert(alert)
            await self._producer.send(alert)
            logger.info(
                "Alert processed from Kafka alert_id=%s trace_id=%s status=%s",
                result["alert_id"],
                result["trace_id"],
                result["status"],
            )

        await self._consumer.commit()
