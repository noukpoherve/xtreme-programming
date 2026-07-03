"""
Background poller for Hub'Eau water-quality data.

Polls official French water-quality stations every N hours (lab data is
slow-moving, no need for high frequency), converts each snapshot to the
canonical UrbanHub `WaterMeasurementEvent` shape, and publishes to Kafka
on the `mesure.qualite.eau` topic.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from iot_service.config import settings
from iot_service.hubeau_qualite_client import (
    HubEauQualiteClient,
    LatestQualityMeasurement,
)
from iot_service.kafka_producer import MeasurementProducer
from iot_service.station_mapping import StationMapping, STATION_MAPPING

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PollResult:
    """Result of a single Hub'Eau quality poll cycle."""

    stations_polled: int
    messages_published: int


class HubEauQualityPoller:
    """
    Periodically fetches Hub'Eau water-quality data and publishes it.

    Usage:
        producer = MeasurementProducer(...)
        await producer.start()
        poller = HubEauQualityPoller(producer)
        await poller.run()  # blocking
    """

    def __init__(
        self,
        producer: MeasurementProducer,
        client: HubEauQualiteClient | None = None,
        interval_seconds: int = settings.quality_poll_interval_seconds,
    ) -> None:
        self._producer = producer
        self._client = client or HubEauQualiteClient()
        self._interval = interval_seconds
        self._stop_event = asyncio.Event()
        self._cycles_completed = 0
        self._messages_published = 0

    def request_stop(self) -> None:
        self._stop_event.set()

    @property
    def cycles_completed(self) -> int:
        return self._cycles_completed

    @property
    def messages_published(self) -> int:
        return self._messages_published

    @property
    def station_count(self) -> int:
        return len(STATION_MAPPING)

    @property
    def excluded_sensor_ids(self) -> set[str]:
        """Sensor IDs whose data comes from Hub'Eau (not simulated)."""
        return {m.sensor_id for m in STATION_MAPPING}

    async def run(self) -> None:
        """Run the polling loop until stop is requested."""
        logger.info(
            "Hub'Eau quality poller started: %d stations, interval=%ds",
            len(STATION_MAPPING),
            self._interval,
        )

        while not self._stop_event.is_set():
            try:
                await self._poll_once()
            except Exception:
                logger.exception("Hub'Eau quality poll cycle failed")

            self._cycles_completed += 1

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self._interval,
                )
            except asyncio.TimeoutError:
                pass  # Normal: tick

    async def poll_once_now(self) -> int:
        """Run one poll cycle immediately. Returns the number of events published."""
        result = await self._poll_once()
        return result.messages_published

    async def _poll_once(self) -> PollResult:
        """Poll every mapped station once, publish what we got."""
        published = 0
        for mapping in STATION_MAPPING:
            try:
                snapshot = self._client.get_latest(mapping.station_code)
            except Exception:
                logger.exception(
                    "Hub'Eau fetch failed station=%s sensor=%s",
                    mapping.station_code,
                    mapping.sensor_id,
                )
                continue

            if snapshot is None:
                logger.debug(
                    "No Hub'Eau data for station=%s sensor=%s",
                    mapping.station_code,
                    mapping.sensor_id,
                )
                continue

            event = self._to_event(snapshot, mapping)
            try:
                sent = await self._producer.send(event)
                if sent:
                    published += 1
            except Exception:
                logger.exception("Publish failed for sensor=%s", mapping.sensor_id)

        self._messages_published += published
        logger.info(
            "Hub'Eau quality cycle %d: %d/%d events published",
            self._cycles_completed,
            published,
            len(STATION_MAPPING),
        )
        return PollResult(
            stations_polled=len(STATION_MAPPING),
            messages_published=published,
        )

    @staticmethod
    def _to_event(
        snapshot: LatestQualityMeasurement,
        mapping: StationMapping,
    ) -> dict[str, Any]:
        """Build a WaterMeasurementEvent-shaped dict from a Hub'Eau snapshot."""
        timestamp = snapshot.sampled_at or datetime.now(UTC)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)

        return {
            "event_type": "mesure.qualite.eau",
            "event_id": str(uuid.uuid4()),
            "trace_id": str(uuid.uuid4()),
            "capteur_id": mapping.sensor_id,
            "timestamp": timestamp.isoformat(),
            "localisation": {
                "latitude": snapshot.latitude or mapping.latitude,
                "longitude": snapshot.longitude or mapping.longitude,
                "point_reference": mapping.sensor_name,
            },
            "mesures": {
                "ph": snapshot.ph if snapshot.ph is not None else 7.0,
                "turbidite_ntu": 0.0,  # Hub'Eau doesn't measure turbidity
                "temperature_c": (
                    snapshot.temperature_c
                    if snapshot.temperature_c is not None
                    else 15.0
                ),
                "niveau_m": 0.0,
                "debit_m3s": 0.0,
                "oxygene_dissous_mgl": (
                    snapshot.dissolved_oxygen_mgl
                    if snapshot.dissolved_oxygen_mgl is not None
                    else 8.0
                ),
            },
            "qualite_signal": "GOOD",
            "firmware_version": "Hub'Eau v2",
            "data_source": "real",
        }
