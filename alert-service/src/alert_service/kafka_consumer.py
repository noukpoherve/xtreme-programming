import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError

from alert_service.config import settings
from alert_service.kafka_producer import AlertProducer
from alert_service.models import WaterMeasurementEvent
from alert_service.service import alert_service

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3


class MeasurementConsumer:
    """Kafka consumer that feeds water-quality measurements into the alert service."""

    def __init__(
        self,
        bootstrap_servers: str = settings.kafka_bootstrap_servers,
        input_topic: str = settings.water_quality_topic,
        producer: AlertProducer | None = None,
    ):
        self._bootstrap = bootstrap_servers
        self._input_topic = input_topic
        self._producer = producer or AlertProducer(bootstrap_servers=bootstrap_servers)
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    async def start(self):
        await self._producer.start()
        self._consumer = AIOKafkaConsumer(
            self._input_topic,
            bootstrap_servers=self._bootstrap,
            group_id=settings.kafka_consumer_group,
            auto_offset_reset=settings.kafka_auto_offset_reset,
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

            success = False
            last_error = None
            for attempt in range(_MAX_RETRIES):
                try:
                    await self._process(msg)
                    success = True
                    break
                except Exception as exc:
                    last_error = exc
                    logger.exception(
                        "Failed to process Kafka message (attempt %d/%d)",
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        await asyncio.sleep(2**attempt)

            if success:
                await self._consumer.commit()
            else:
                # Do NOT commit: the message will be re-processed by another
                # consumer in the group after rebalancing, or by this consumer
                # after restart. Pause to avoid a tight error loop.
                logger.error(
                    "Giving up on message after %d attempts; offset NOT committed",
                    _MAX_RETRIES,
                    exc_info=last_error,
                )
                # Pause this partition so the consumer doesn't spin on the poison message
                await self._consumer.pause(*self._consumer.assignment())
                # Resume after a short backoff to allow operators to fix the issue
                await asyncio.sleep(30)
                self._consumer.resume(*self._consumer.assignment())

    async def _process(self, msg):
        payload = json.loads(msg.value.decode("utf-8"))
        measurement = WaterMeasurementEvent.model_validate(payload)

        # The processor keeps per-sensor state across messages.
        # process_measurement is async: it persists to DB and updates state.
        alerts = await alert_service.process_measurement(measurement)

        for alert in alerts:
            result = await alert_service.process_alert(alert)
            await self._producer.send(alert)
            logger.info(
                "Alert processed from Kafka alert_id=%s trace_id=%s severity=%s",
                result["alert_id"],
                result["trace_id"],
                alert.severity.value,
            )
