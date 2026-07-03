"""
Centralized application settings for iot-service.

All environment-variable driven configuration lives here so that other
modules can import a single `Settings` object instead of scattering
`os.getenv` calls across the codebase.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable container for iot-service configuration."""

    # Service
    app_name: str = "iot-service"
    app_version: str = "0.1.0"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    water_quality_topic: str = "mesure.qualite.eau"

    # Alert service (used by quality poller to enrich events)
    alert_service_url: str = "http://localhost:8000"

    # Legacy hydrometry poller
    poll_interval_seconds: int = 300

    # Hub'Eau quality poller
    quality_poll_interval_seconds: int = 6 * 3600

    # Local simulator
    simulator_interval_seconds: float = 300.0
    simulator_jitter_seconds: float = 30.0
    simulator_exclude_sensors: frozenset[str] = frozenset(
        {
            "SEINE-VITRY-001",
            "SEINE-CHARENTON-002",
            "SEINE-BERCY-003",
            "SEINE-AUSTERLITZ-004",
            "SEINE-CONCORDE-006",
            "SEINE-COLOMBES-012",
        }
    )

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables."""
        exclude_raw = os.getenv("SIMULATOR_EXCLUDE_SENSORS")
        exclude = (
            {s.strip() for s in exclude_raw.split(",") if s.strip()}
            if exclude_raw is not None
            else cls.simulator_exclude_sensors
        )

        return cls(
            kafka_bootstrap_servers=os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", cls.kafka_bootstrap_servers
            ),
            water_quality_topic=os.getenv(
                "WATER_QUALITY_TOPIC", cls.water_quality_topic
            ),
            alert_service_url=os.getenv("ALERT_SERVICE_URL", cls.alert_service_url),
            poll_interval_seconds=int(
                os.getenv("POLL_INTERVAL_SECONDS", cls.poll_interval_seconds)
            ),
            quality_poll_interval_seconds=int(
                os.getenv(
                    "QUALITY_POLL_INTERVAL_SECONDS", cls.quality_poll_interval_seconds
                )
            ),
            simulator_interval_seconds=float(
                os.getenv(
                    "SIMULATOR_INTERVAL_SECONDS", cls.simulator_interval_seconds
                )
            ),
            simulator_jitter_seconds=float(
                os.getenv("SIMULATOR_JITTER_SECONDS", cls.simulator_jitter_seconds)
            ),
            simulator_exclude_sensors=frozenset(exclude),
        )


# Module-level singleton so every module can `from iot_service.config import settings`
settings = Settings.from_env()
