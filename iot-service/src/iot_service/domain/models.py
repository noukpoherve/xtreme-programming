import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class SensorMeasurement:
    """Entité métier immuable — snapshot d'une mesure physique à un instant T."""

    sensor_id: str
    ph: float
    turbidity: float  # NTU
    level: float  # mètres
    flow: float  # m³/s
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: float = 0.0
    longitude: float = 0.0
    temperature_c: float = 14.3
    oxygene_dissous_mgl: float = 7.1
    qualite_signal: str = "GOOD"
    firmware_version: str = "2.4.1"
