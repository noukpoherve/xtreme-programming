from abc import ABC, abstractmethod

from alert_service.models import AlertPayload


class AlertSender(ABC):
    """Port — abstrait tout canal d'envoi d'alertes (Kafka, webhook, email…).

    Respecte le principe DIP : MeasurementConsumer dépend de cette abstraction,
    pas de l'implémentation Kafka concrète.
    """

    @abstractmethod
    async def send(self, alert: AlertPayload) -> None: ...

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
