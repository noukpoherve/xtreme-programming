import json
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from alert_service.config import settings
from alert_service.models import AlertPayload, WaterMeasurementEvent
from alert_service.service import alert_service

logger = logging.getLogger(__name__)


class KafkaAlertBridge:
    def __init__(self) -> None:
        self._consumer = AIOKafkaConsumer(
            settings.water_quality_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers
        )
        self._task = None
        self._running = False

    async def start(self) -> None:
        await self._producer.start()
        await self._consumer.start()
        self._running = True

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None
        await self._consumer.stop()
        await self._producer.stop()

    def schedule(self) -> None:
        if self._task is None:
            import asyncio

            self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        logger.info(
            "Kafka bridge started for topic=%s group=%s",
            settings.water_quality_topic,
            settings.kafka_consumer_group,
        )
        async for message in self._consumer:
            if not self._running:
                break
            payload = json.loads(message.value.decode("utf-8"))
            measurement = WaterMeasurementEvent.model_validate(payload)
            alerts = alert_service.build_alerts_from_measurement(measurement)
            for alert in alerts:
                await self._handle_alert(alert)
            await self._consumer.commit()

    async def _handle_alert(self, alert: AlertPayload) -> None:
        response = await alert_service.process_alert(alert)
        logger.info(
            "Alert processed from Kafka alert_id=%s trace_id=%s status=%s",
            response["alert_id"],
            response["trace_id"],
            response["status"],
        )
        await self._producer.send_and_wait(
            settings.pollution_alert_topic,
            json.dumps(alert.model_dump(mode="json"), ensure_ascii=False).encode(
                "utf-8"
            ),
            key=alert.sensor_id.encode("utf-8"),
            headers=[("trace_id", alert.trace_id.encode("utf-8"))],
        )


class NoopKafkaBridge:
    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    def schedule(self) -> None:
        return None
