import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SensorMeasurement:
    sensor_id: str
    ph: float
    turbidity: float  # NTU
    level: float  # mètres
    flow: float  # m³/s
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: float = 0.0
    longitude: float = 0.0
    temperature_c: float = 0.0
    oxygene_dissous_mgl: float = 0.0
    qualite_signal: str | None = None
    firmware_version: str | None = None


class IoTSensorSimulator:
    def __init__(self, sensor_id: str):
        self.sensor_id = sensor_id

    def capture(
        self,
        ph: float,
        turbidity: float,
        level: float,
        flow: float,
    ) -> SensorMeasurement:
        return SensorMeasurement(
            sensor_id=self.sensor_id,
            ph=ph,
            turbidity=turbidity,
            level=level,
            flow=flow,
        )
