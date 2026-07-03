"""
Simulation orchestrator: drives all sensors in parallel and publishes to Kafka.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass

from iot_service.config import settings
from iot_service.kafka_producer import MeasurementProducer
from iot_service.simulator.generator import MeasurementGenerator
from iot_service.simulator.sensors import SENSORS, SensorProfile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimulationConfig:
    """Tunable parameters for the simulation."""

    interval_seconds: float = settings.simulator_interval_seconds
    jitter_seconds: float = settings.simulator_jitter_seconds
    cycle_count: int | None = None

    @classmethod
    def from_env(cls) -> "SimulationConfig":
        """Legacy factory kept for callers; now delegates to central config."""
        return cls()


class SimulationOrchestrator:
    """
    Drives all sensors in parallel and publishes their measurements to Kafka.

    Some sensor_ids may be excluded (those with a real Hub'Eau data source).
    Override via the SIMULATOR_EXCLUDE_SENSORS environment variable.
    """

    def __init__(
        self,
        producer: MeasurementProducer,
        config: SimulationConfig | None = None,
        exclude_sensor_ids: frozenset[str] | None = None,
    ) -> None:
        self._producer = producer
        self._config = config or SimulationConfig.from_env()
        self._exclude_sensor_ids = (
            exclude_sensor_ids
            if exclude_sensor_ids is not None
            else settings.simulator_exclude_sensors
        )
        self._generators: dict[str, MeasurementGenerator] = {}
        self._stop_event = asyncio.Event()
        self._cycles_completed = 0

    def register_all_sensors(self) -> None:
        """Register a generator for every sensor not in the exclusion list."""
        registered = 0
        for sensor in SENSORS:
            if sensor.sensor_id in self._exclude_sensor_ids:
                continue
            self.register_sensor(sensor)
            registered += 1
        logger.info(
            "Registered %d sensors (excluded %d: %s)",
            registered,
            len(self._exclude_sensor_ids),
            ", ".join(sorted(self._exclude_sensor_ids)),
        )

    def register_sensor(self, sensor: SensorProfile) -> None:
        """Register a single sensor with a seeded generator."""
        if sensor.sensor_id not in self._generators:
            self._generators[sensor.sensor_id] = MeasurementGenerator(sensor)

    @property
    def sensors(self) -> list[SensorProfile]:
        return [gen.sensor for gen in self._generators.values()]

    @property
    def excluded_sensor_ids(self) -> set[str]:
        return set(self._exclude_sensor_ids)

    @property
    def cycles_completed(self) -> int:
        return self._cycles_completed

    def request_stop(self) -> None:
        self._stop_event.set()

    async def run(self) -> None:
        if not self._generators:
            self.register_all_sensors()

        logger.info(
            "Starting simulation: %d sensors, interval=%.1fs ±%.1fs",
            len(self._generators),
            self._config.interval_seconds,
            self._config.jitter_seconds,
        )

        while not self._stop_event.is_set():
            await self._run_one_cycle()
            self._cycles_completed += 1

            if (
                self._config.cycle_count is not None
                and self._cycles_completed >= self._config.cycle_count
            ):
                logger.info(
                    "Reached cycle limit (%d), stopping", self._config.cycle_count
                )
                break

            wait_time = self._config.interval_seconds + random.uniform(
                -self._config.jitter_seconds,
                self._config.jitter_seconds,
            )
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=max(0.1, wait_time),
                )
            except asyncio.TimeoutError:
                pass

    async def _run_one_cycle(self) -> None:
        tasks = []
        for generator in self._generators.values():
            measurement = generator.generate()
            tasks.append(self._producer.send(measurement))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        sent = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - sent
        if failed:
            for sensor_id, r in zip(self._generators.keys(), results):
                if isinstance(r, Exception):
                    logger.warning(
                        "Simulator send failed for %s: %r",
                        sensor_id,
                        r,
                    )
        logger.debug(
            "Cycle %d: %d sent, %d failed",
            self._cycles_completed,
            sent,
            failed,
        )
