import logging
import uuid
from typing import Optional, Protocol

from alert_service.models import (
    AlertPayload,
    Localisation,
    WaterMeasurementEvent,
)
from alert_service.repository import AlertRepository

logger = logging.getLogger(__name__)


class AlertRule(Protocol):
    def evaluate(self, measurement: WaterMeasurementEvent) -> list[AlertPayload]:
        ...


class DefaultAlertRule:
    PH_WARNING_LOW = 6.5
    PH_WARNING_HIGH = 8.5
    PH_CRITICAL_LOW = 6.0
    PH_CRITICAL_HIGH = 9.0
    TURBIDITY_WARNING = 10.0
    TURBIDITY_CRITICAL = 50.0

    def evaluate(self, measurement: WaterMeasurementEvent) -> list[AlertPayload]:
        alerts: list[AlertPayload] = []
        ph = measurement.mesures.ph
        if ph < self.PH_CRITICAL_LOW or ph > self.PH_CRITICAL_HIGH:
            alerts.append(
                self._build_alert(
                    measurement,
                    severity="CRITICAL",
                    alert_type="ph",
                    message=f"pH critique detecte: {ph}",
                )
            )
        elif ph < self.PH_WARNING_LOW or ph > self.PH_WARNING_HIGH:
            alerts.append(
                self._build_alert(
                    measurement,
                    severity="WARNING",
                    alert_type="ph",
                    message=f"pH en attention: {ph}",
                )
            )

        turbidity = measurement.mesures.turbidite_ntu
        if turbidity > self.TURBIDITY_CRITICAL:
            alerts.append(
                self._build_alert(
                    measurement,
                    severity="CRITICAL",
                    alert_type="turbidity",
                    message=f"Turbidite critique detectee: {turbidity} NTU",
                )
            )
        elif turbidity > self.TURBIDITY_WARNING:
            alerts.append(
                self._build_alert(
                    measurement,
                    severity="WARNING",
                    alert_type="turbidity",
                    message=f"Turbidite en attention: {turbidity} NTU",
                )
            )
        return alerts

    def _build_alert(
        self,
        measurement: WaterMeasurementEvent,
        severity: str,
        alert_type: str,
        message: str,
    ) -> AlertPayload:
        return AlertPayload(
            alert_id=str(uuid.uuid4()),
            event_id=measurement.event_id,
            sensor_id=measurement.capteur_id,
            timestamp=measurement.timestamp,
            severity=severity,
            type=alert_type,
            message=message,
            localisation=Localisation(
                latitude=measurement.localisation.latitude,
                longitude=measurement.localisation.longitude,
                point_reference=measurement.localisation.point_reference,
            ),
            trace_id=measurement.trace_id,
            metadata={
                "overall_status": severity,
                "source_event_type": measurement.event_type,
            },
        )


class AlertService:
    def __init__(self, rules: list[AlertRule] | None = None, repository: AlertRepository | None = None):
        self._rules = rules or [DefaultAlertRule()]
        self._repository = repository or AlertRepository()

    async def process_alert(self, payload: AlertPayload) -> dict:
        logger.info("Alert received: %s (trace_id=%s)", payload.alert_id, payload.trace_id)
        await self._repository.save(payload)
        return {
            "alert_id": payload.alert_id,
            "status": "CREATED",
            "trace_id": payload.trace_id,
        }

    def build_alerts_from_measurement(
        self, measurement: WaterMeasurementEvent
    ) -> list[AlertPayload]:
        alerts: list[AlertPayload] = []
        for rule in self._rules:
            alerts.extend(rule.evaluate(measurement))
        return alerts

    async def get_alert(self, alert_id: str) -> Optional[AlertPayload]:
        return await self._repository.get(alert_id)

    async def get_all_alerts(self, limit: int = 100, offset: int = 0) -> list[AlertPayload]:
        return await self._repository.get_all(limit, offset)

    async def get_alerts_by_sensor(self, sensor_id: str) -> list[AlertPayload]:
        return await self._repository.get_by_sensor(sensor_id)

    async def update_alert(self, alert_id: str, payload: AlertPayload) -> bool:
        return await self._repository.update(alert_id, payload)

    async def delete_alert(self, alert_id: str) -> bool:
        return await self._repository.delete(alert_id)

    async def count_alerts(self) -> int:
        return await self._repository.count()


alert_service = AlertService()
