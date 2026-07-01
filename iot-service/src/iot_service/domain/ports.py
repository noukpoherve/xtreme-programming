from abc import ABC, abstractmethod

from iot_service.domain.models import SensorMeasurement


class MeasurementWriter(ABC):
    """Port — abstrait tout canal d'écriture de mesures (Kafka, fichier, base de données…).

    Respecte le principe DIP : les modules de haut niveau (main, poll_loop)
    dépendent de cette abstraction, pas des implémentations concrètes.
    """

    @abstractmethod
    async def write(self, measurement: SensorMeasurement) -> None: ...

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
