"""
Extrait EC03 — UrbanHub iot-service (configuration).
Source canonique : iot-service/src/iot_service/config.py
Aucun secret : uniquement variables d'environnement avec défauts locaux.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "iot-service"
    app_version: str = "0.1.0"
    kafka_bootstrap_servers: str = "localhost:9092"
    water_quality_topic: str = "mesure.qualite.eau"
    alert_service_url: str = "http://localhost:8000"
    poll_interval_seconds: int = 300
    quality_poll_interval_seconds: int = 6 * 3600
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
                os.getenv("SIMULATOR_INTERVAL_SECONDS", cls.simulator_interval_seconds)
            ),
            simulator_jitter_seconds=float(
                os.getenv("SIMULATOR_JITTER_SECONDS", cls.simulator_jitter_seconds)
            ),
            simulator_exclude_sensors=frozenset(exclude),
        )


settings = Settings.from_env()
