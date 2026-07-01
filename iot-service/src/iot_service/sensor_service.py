from dataclasses import dataclass

from iot_service.domain.models import SensorMeasurement


@dataclass
class Sensor:
    """Responsabilité unique : modéliser l'état d'un capteur physique.

    Connaît son identité et ses métadonnées matérielles.
    Ne sait rien de Kafka, de fichiers ou d'alertes.
    """

    sensor_id: str
    latitude: float = 0.0
    longitude: float = 0.0
    firmware_version: str = "2.4.1"
    qualite_signal: str = "GOOD"
    temperature_c: float = 14.3
    oxygene_dissous_mgl: float = 7.1

    def capture(
        self,
        ph: float,
        turbidity: float,
        level: float,
        flow: float,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> SensorMeasurement:
        """Produit une mesure immuable à partir des relevés bruts fournis."""
        return SensorMeasurement(
            sensor_id=self.sensor_id,
            ph=ph,
            turbidity=turbidity,
            level=level,
            flow=flow,
            latitude=latitude if latitude is not None else self.latitude,
            longitude=longitude if longitude is not None else self.longitude,
            temperature_c=self.temperature_c,
            oxygene_dissous_mgl=self.oxygene_dissous_mgl,
            qualite_signal=self.qualite_signal,
            firmware_version=self.firmware_version,
        )
